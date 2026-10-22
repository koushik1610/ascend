#!/usr/bin/env python3
"""apply.py: the apply sheet, the gates every send goes through, and the record of what was sent (Ascend 2.0).

  python3 tools/apply.py sheet  WS POSTING_ID                                   # the apply sheet, gated
  python3 tools/apply.py status WS

Recording a send is the hub's "I submitted it" button (ui/server.py calls record()); it is not a command,
so nothing but the user's click marks a job applied.

The user submits every application in their own browser. The sheet is built only when the job is
approved, it is not a duplicate, its résumé passes lint_artifacts.py, and every answer comes from the
user's own profile. Work authorization, sponsorship, salary and start date are always listed under
ask_user and never pre-filled, even when the profile records them.

The automatic runner (tools/autoapply.py) uses the same pack checks plus ready(): the job is on a
Greenhouse, Ashby or Lever board in the user's sources.json, its link is rebuilt from that board (never
taken from a stored row) onto an exact allowed host, and its fit, rule filter and per-company limit pass.
The four questions above are filled only from data/apply-answers.json, which the user writes.

Nothing here transmits anything.
"""

import json
import re
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import _v2data as d  # noqa: E402
import jobqueue  # noqa: E402
import pipeline  # noqa: E402

PROFILE_FIELDS = ["name", "email", "phone", "location", "linkedin", "website", "github",
                  "work_authorization", "sponsorship", "salary_expectation", "start_date"]
STALE_SECONDS = 60    # the pack builder writes the PDF moments before resume.md; an edit later is stale
ALWAYS_ASK = ["work_authorization", "sponsorship", "salary_expectation", "start_date"]


def _first(items, default=None):
    for x in items:
        return x
    return default


class Refused(Exception):
    """The gate said no. The message says why, in words the user can act on."""


class NotYet(Refused):
    """The job has no tailored pack yet: a Claude session builds it. Waiting, not a problem."""


AUTO_ATS = ("greenhouse", "ashby", "lever")
ALLOWED_HOSTS = {"job-boards.greenhouse.io", "boards.greenhouse.io", "jobs.ashbyhq.com", "jobs.lever.co"}
UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
AUTO_URL = {"greenhouse": (r"\d{1,15}", "https://job-boards.greenhouse.io/{slug}/jobs/{id}"),
            "ashby": (UUID, "https://jobs.ashbyhq.com/{slug}/{id}/application"),
            "lever": (UUID, "https://jobs.lever.co/{slug}/{id}/apply")}
COMPANY_DAYS = 30


def allowed(url):
    """May the runner, or Claude after the user's yes, open this to submit? https, an exact allowed host, and
    nothing a browser could read as a different host (userinfo, a port, backslashes, encoded slashes)."""
    if not isinstance(url, str) or any(c in url for c in "\\@ \t\r\n") or re.search(r"%(2f|5c|40)", url, re.I):
        return False
    try:
        u = urlparse(url)
    except ValueError:
        return False
    return u.scheme == "https" and u.netloc == (u.hostname or "") and u.hostname in ALLOWED_HOSTS


def _boards(ws):
    return d.read_json(Path(ws) / "data" / "sources.json", {}).get("boards", []) or []


def apply_url_for(ws, posting_id):
    """The application page for a board posting, built from the board entry in the user's sources.json and
    the posting's own ID. None for anything else: Workday, Eightfold, links Claude added, a malformed ID."""
    m = re.fullmatch(r"(greenhouse|ashby|lever):([A-Za-z0-9_-]+):([A-Za-z0-9-]+)", posting_id or "")
    if not m:
        return None
    ats, slug, native = m.groups()
    rx, fmt = AUTO_URL[ats]
    if not re.fullmatch(rx, native) or not any(b.get("ats") == ats and b.get("slug") == slug for b in _boards(ws)):
        return None
    url = fmt.format(slug=slug, id=native)
    return url if allowed(url) else None


def answers(ws):
    """What a form may be filled with: the profile's contact fields, then the user's own apply-answers.json
    (work authorization, sponsorship, salary, start date, demographic choices), then the answer bank."""
    ws = Path(ws)
    profile = d.read_json(ws / "data" / "profile.json", {})
    out = {k: profile[k] for k in PROFILE_FIELDS if profile.get(k) and k not in ALWAYS_ASK}
    own = d.read_json(ws / "data" / "apply-answers.json", {})
    out.update({k: v for k, v in (own if isinstance(own, dict) else {}).items()
                if not k.startswith("_") and v not in (None, "")})
    bank = d.read_json(ws / "data" / "answer-bank.json", [])
    out["_bank"] = [b for b in (bank if isinstance(bank, list) else [])
                    if isinstance(b, dict) and b.get("question") and b.get("answer")]
    return out


def _sent_to(ws, company, today):
    since = (today - timedelta(days=COMPANY_DAYS)).isoformat()
    q = {j.get("posting_id"): j for j in jobqueue._queue(ws).get("jobs", [])}
    sent = set()
    for r in d.read_jsonl(Path(ws) / "data" / "apply-log.jsonl"):
        c = r.get("company") or (q.get(r.get("posting_id")) or {}).get("company")
        if r.get("result") in ("submitted", "unclear") and not r.get("dry_run") and str(r.get("at", ""))[:10] >= since \
                and jobqueue.same_company(c, company):
            sent.add(r.get("posting_id"))
    for j in q.values():
        if j.get("state") == "applied" and (j.get("applied_on") or "") >= since and jobqueue.same_company(j.get("company"), company):
            sent.add(j.get("posting_id"))
    return len(sent)


def ready(ws, entry, cfg, today=None):
    """[] when the runner may send this job, else the reasons it may not. The pack is checked by pack()."""
    ws, today = Path(ws), today or date.today()
    pid, why = entry.get("posting_id") or "", []
    if entry.get("state") not in ("matched", "approved"):
        why.append(f"it is {entry.get('state')}, not matched or approved")
    if pid.split(":", 1)[0] not in AUTO_ATS:
        why.append("only Greenhouse, Ashby and Lever are applied to automatically")
    elif not any(pid.startswith(f"{b.get('ats')}:{b.get('slug')}:") for b in _boards(ws)):
        why.append("its company is not on a board in your sources.json")
    elif not apply_url_for(ws, pid):
        why.append("its application link could not be rebuilt from the board")
    fit = entry.get("fit")
    if not isinstance(fit, int) or isinstance(fit, bool):
        why.append("not scored yet")
    elif fit < cfg.get("fit_threshold", 75):
        why.append(f"fit {fit} is below {cfg.get('fit_threshold', 75)}")
    verdict = None
    for c in d.read_jsonl(ws / "data" / "candidates.jsonl"):
        if c.get("posting_id") == pid:
            verdict = c.get("passed")
    if verdict is not True:
        why.append("it did not pass your rule filter")
    if d.read_json(ws / "data" / "postings-state.json", {}).get(pid, {}).get("closed"):
        why.append("the posting has closed")
    n = _sent_to(ws, entry.get("company"), today)
    if n >= cfg.get("company_cap", 2):
        why.append(f"{n} applications to {entry.get('company')} in the last {COMPANY_DAYS} days already")
    return why


KNOWN_HOSTS = ("greenhouse.io", "lever.co", "ashbyhq.com", "workable.com", "smartrecruiters.com",
               "myworkdayjobs.com", "workday.com")


def _known_link(url):
    """Display only: is this an https link on a known application system, with nothing that makes a browser
    read the host differently from Python (backslashes, spaces, user:password@)? Nothing is ever opened by
    Ascend; this decides whether the sheet warns the user to check the address."""
    url = url or ""
    if any(c in url for c in "\\ \t\r\n") or "%2f" in url.lower() or "%5c" in url.lower():
        return False
    try:
        u = urlparse(url)
    except ValueError:
        return False
    host = (u.hostname or "").lower()
    return (u.scheme == "https" and not u.username and not u.password and u.netloc.lower() in (host, host + ":443")
            and any(host == h or host.endswith("." + h) for h in KNOWN_HOSTS))


def _entry(ws, posting_id):
    entry = _first(j for j in jobqueue._queue(ws).get("jobs", []) if j.get("posting_id") == posting_id)
    if entry is None:
        raise Refused(f"{posting_id} is not in the queue")
    return entry


def _lint(ws, resume_md):
    cfg = Path(ws) / "lint-config.json"
    cmd = [sys.executable, str(TOOLS / "lint_artifacts.py")] + (["--config", str(cfg)] if cfg.is_file() else []) + \
          [str(resume_md)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        first = _first((l for l in r.stdout.splitlines() if "[" in l), r.stdout.strip()[:200])
        raise Refused(f"the résumé fails lint: {first}")


def _hook(job):
    o = job / "outreach.md"
    m = re.search(r"^>\s*(.+)$", o.read_text(encoding="utf-8"), re.M) if o.is_file() else None
    return m.group(1).strip() if m else ""


def pack(ws, entry):
    """(job folder, résumé PDF) for a queued job once its pack is complete, clean and for this role. NotYet when
    there is no pack to check; Refused when there is one and something is wrong with it."""
    ws, posting_id = Path(ws), entry.get("posting_id")
    dup = pipeline.check_duplicate(ws, entry.get("company"), entry.get("title"), posting_id)
    if dup:
        raise Refused(dup)
    if not entry.get("nn"):
        jobqueue.sync_folders(ws)               # a folder for this posting may exist from an earlier run
        entry = _entry(ws, posting_id)
    job = pipeline.job_folder(ws, entry["nn"]) if entry.get("nn") else None
    if not job:
        raise NotYet("no apply pack linked yet: build it with Phase 5 (prompts/05-job-folders.md), then run "
                     f"python3 tools/jobqueue.py link {ws} {posting_id} <NN>")
    f_company, f_title, f_url, *_ = pipeline.folder_job(job)
    from finder import ats_id
    if not jobqueue._same_role(entry.get("company"), entry.get("title"), f_company, f_title, posting_id, ats_id(f_url)):
        raise Refused(f"{job.name} is for {f_company}, {f_title}: a different role from this job")
    pdfs = sorted(job.glob("*-Resume-*.pdf"))
    if not pdfs or not (job / "resume.md").is_file():
        raise NotYet(f"no résumé PDF in {job.name}: render it with Phase 8")
    if len(pdfs) > 1:
        raise Refused(f"{len(pdfs)} résumé PDFs in {job.name}: keep only the one to send")
    _lint(ws, job / "resume.md")
    if pdfs[0].stat().st_mtime < (job / "resume.md").stat().st_mtime - STALE_SECONDS:
        raise Refused(f"{pdfs[0].name} is older than resume.md: render it again with Phase 8")
    return job, pdfs[0]


def sheet(ws, posting_id):
    ws = Path(ws)
    entry = _entry(ws, posting_id)
    if entry.get("state") not in ("approved", "needs-you"):
        raise Refused(f"{entry.get('company')} is {entry.get('state')}, not approved")
    job, pdf = pack(ws, entry)
    pdfs = [pdf]
    known = {k: v for k, v in answers(ws).items() if not k.startswith("_")}
    ask = [k for k in ALWAYS_ASK if k not in known] + [k for k in ("name", "email", "phone") if not known.get(k)]
    link = entry.get("apply_url") or entry.get("url") or entry.get("posting_id")
    gh = re.fullmatch(r"greenhouse:([\w-]+):(\d+)", posting_id or "")
    if gh:                  # Greenhouse's own job page, whatever careers site the company points at
        link = f"https://job-boards.greenhouse.io/{gh.group(1)}/jobs/{gh.group(2)}"
    entry = dict(entry, apply_url=link)
    out = {"posting_id": posting_id, "company": entry.get("company"), "title": entry.get("title"),
           "apply_url": link,
           "link_note": None if _known_link(entry.get("apply_url") or entry.get("url") or "") else
           "This link is not on a known application system. Check the address before you enter anything.",
           "resume_pdf": str(pdfs[0]), "answers": known, "ask_user": ask, "cover_note": _hook(job),
           "built_at": datetime.now().isoformat(timespec="seconds")}
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", posting_id)[:120]
    d.write_json_atomic(d.data_dir(ws) / "apply-sheets" / f"{safe}.json", out)
    return out


def status(ws):
    log = d.read_jsonl(Path(ws) / "data" / "apply-log.jsonl")
    today = date.today().isoformat()
    return dict(submitted_today=sum(1 for r in log if r.get("result") == "submitted"
                                                  and str(r.get("at", "")).startswith(today)))


def record(ws, posting_id, result="submitted"):
    """The user pressed "I submitted it". Only an approved job, or one the runner handed back (needs-you), can be
    recorded, and a second press is a no-op."""
    if result != "submitted":
        raise ValueError("this release records only submissions the user made")
    log = d.data_dir(ws) / "apply-log.jsonl"
    with d.locked(log) as p:            # two clicks at once still record one send
        entry = _entry(ws, posting_id)
        if entry.get("state") == "applied":
            return entry
        if entry.get("state") not in ("approved", "needs-you"):
            raise Refused(f"{entry.get('company')} is {entry.get('state')}, not approved")
        entry = jobqueue.set_state(ws, posting_id, "applied", via_hub=True)
        with open(p, "a", encoding="utf-8") as f:     # inside the lock already: not append_jsonl
            f.write(json.dumps({"posting_id": posting_id, "result": result, "mode": "user", "company": entry.get("company"),
                                "at": datetime.now().isoformat(timespec="seconds")}, sort_keys=True) + "\n")
    return entry


def _opt(args, name, default=None):
    return args[args.index(name) + 1] if name in args and args.index(name) + 1 < len(args) else default


def main(argv):
    cmds = ("sheet", "status")
    if len(argv) >= 2 and argv[1] == "record":
        print("apply: a send is recorded by your click on \"I submitted it\" in the hub, not from the command line",
              file=sys.stderr)
        return 2
    if len(argv) < 3 or argv[1] not in cmds:
        print(__doc__, file=sys.stderr)
        return 2
    cmd, args = argv[1], argv[2:]
    try:
        ws = args[0]
        if cmd == "sheet":
            out = sheet(ws, args[1])
        else:
            out = status(ws)
    except Refused as e:
        print(f"REFUSED {e}", file=sys.stderr)
        return 3
    except (ValueError, KeyError, IndexError) as e:
        print(f"apply: {e}", file=sys.stderr)
        return 2
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
