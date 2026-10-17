#!/usr/bin/env python3
"""apply.py: everything around submitting an application, except the clicking (Ascend 2.0, M8).

  python3 tools/apply.py sheet  WS POSTING_ID [--mode assisted|agent|automatic]   # the apply sheet, gated
  python3 tools/apply.py next   WS --mode agent|automatic [--cap 25] [--fit 75]  # next job, or why not
  python3 tools/apply.py allowed URL                                              # may an agent open it?
  python3 tools/apply.py record WS POSTING_ID submitted|unclear|stopped [--reason TEXT]
  python3 tools/apply.py pause  WS [--reason TEXT] | resume WS | status WS

The clicking happens in the user's browser (assisted) or through Claude in Chrome following
prompts/28-apply.md (agent-submit, automatic). Every mode goes through the same gate first: the job is
approved (or, in automatic mode, matched at or above the fit threshold), it is not a duplicate, its
résumé passes lint_artifacts.py, and every answer on the sheet comes from the user's own profile.
Anything the profile does not record (work authorization, sponsorship, salary, start date) is listed
under ask_user and never filled.

Sending application content to an employer is the one scoped exception to "never transmit workspace
data" (CLAUDE.md): only this job's pack and sheet, only to an allow-listed ATS URL the finder found.
"""

import json
import re
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import _v2data as d  # noqa: E402
import jobqueue  # noqa: E402
import pipeline  # noqa: E402

ATS_HOSTS = ("greenhouse.io", "lever.co", "ashbyhq.com", "workable.com", "smartrecruiters.com",
             "myworkdayjobs.com", "workday.com")
PROFILE_FIELDS = ["name", "email", "phone", "location", "linkedin", "website", "github",
                  "work_authorization", "sponsorship", "salary_expectation", "start_date"]
ALWAYS_ASK = ["work_authorization", "sponsorship", "salary_expectation", "start_date"]
FIT_THRESHOLD = 75
DAILY_CAP = 25
AUTO_PAUSE_WINDOW = 50
AUTO_PAUSE_RATE = 0.05
REPLY_CATEGORIES = {"info-request", "assessment", "interview-invite", "rejection"}


def _first(items, default=None):
    """The builtin next(), under another name: this module's `next` is the CLI verb."""
    for x in items:
        return x
    return default


class Refused(Exception):
    """The gate said no. The message says why, in words the user can act on."""


def allowed(url):
    try:
        u = urlparse(url or "")
    except ValueError:
        return False
    host = (u.hostname or "").lower()
    return u.scheme == "https" and any(host == h or host.endswith("." + h) for h in ATS_HOSTS)


def _entry(ws, posting_id):
    entry = _first(j for j in jobqueue._queue(ws).get("jobs", []) if j.get("posting_id") == posting_id)
    if entry is None:
        raise Refused(f"{posting_id} is not in the queue")
    return entry


def _eligible(entry, mode, fit_threshold):
    if entry.get("state") == "approved":
        return True
    return mode == "automatic" and entry.get("state") == "matched" and (entry.get("fit") or 0) >= fit_threshold


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


def sheet(ws, posting_id, mode="assisted", fit_threshold=FIT_THRESHOLD):
    ws = Path(ws)
    entry = _entry(ws, posting_id)
    if not _eligible(entry, mode, fit_threshold):
        raise Refused(f"{entry.get('company')} is {entry.get('state')}, not approved"
                      + (f" (automatic mode applies only to matched jobs at fit {fit_threshold}+)" if mode == "automatic" else ""))
    dup = pipeline.check_duplicate(ws, entry.get("company"), entry.get("title"),
                                   None if entry.get("nn") else posting_id)
    if dup:
        raise Refused(dup)
    job = pipeline.find_job(ws, entry["nn"]) if entry.get("nn") else None
    if not job:
        raise Refused("no apply pack yet: build it with Phase 5 (prompts/05-job-folders.md)")
    pdfs = sorted(job.glob("*.pdf"))
    if not pdfs or not (job / "resume.md").is_file():
        raise Refused(f"no résumé PDF in {job.name}: render it with Phase 8")
    _lint(ws, job / "resume.md")
    profile = d.read_json(ws / "data" / "profile.json", {})
    answers = {k: profile[k] for k in PROFILE_FIELDS if profile.get(k)}
    ask = [k for k in ALWAYS_ASK if not profile.get(k)] + [k for k in ("name", "email", "phone") if not profile.get(k)]
    out = {"posting_id": posting_id, "company": entry.get("company"), "title": entry.get("title"),
           "apply_url": entry.get("apply_url") or entry.get("url") or entry.get("posting_id"),
           "url_allowed": allowed(entry.get("apply_url") or entry.get("url") or ""),
           "resume_pdf": str(pdfs[0]), "answers": answers, "ask_user": ask, "cover_note": _hook(job),
           "mode": mode, "built_at": datetime.now().isoformat(timespec="seconds")}
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", posting_id)[:120]
    d.write_json_atomic(d.data_dir(ws) / "apply-sheets" / f"{safe}.json", out)
    return out


def _control(ws):
    return d.read_json(Path(ws) / "data" / "apply-control.json", {"paused": False})


def pause(ws, reason="paused by you"):
    d.write_json_atomic(d.data_dir(ws) / "apply-control.json",
                        {"paused": True, "reason": reason, "at": datetime.now().isoformat(timespec="seconds")})


def resume(ws):
    d.write_json_atomic(d.data_dir(ws) / "apply-control.json", {"paused": False})


def status(ws):
    log = d.read_jsonl(Path(ws) / "data" / "apply-log.jsonl")
    today = date.today().isoformat()
    return dict(_control(ws), submitted_today=sum(1 for r in log if r.get("result") == "submitted"
                                                  and str(r.get("at", "")).startswith(today)))


def next(ws, mode, cap=DAILY_CAP, fit_threshold=FIT_THRESHOLD):  # noqa: A001 (CLI verb)
    ws = Path(ws)
    none = lambda why: {"job": None, "posting_id": None, "reason": why}  # noqa: E731
    ctl = _control(ws)
    if ctl.get("paused"):
        return none(f"paused: {ctl.get('reason', '')}")
    st = status(ws)
    if st["submitted_today"] >= cap:
        return none(f"daily cap reached ({cap})")
    if mode == "automatic":
        sent = [r for r in d.read_jsonl(ws / "data" / "apply-log.jsonl") if r.get("result") == "submitted"]
        if len(sent) >= AUTO_PAUSE_WINDOW:
            replies = sum(1 for e in d.read_jsonl(ws / "data" / "events.jsonl") if e.get("category") in REPLY_CATEGORIES)
            rate = replies / len(sent)
            if rate < AUTO_PAUSE_RATE:
                why = (f"auto-paused: reply rate {rate:.0%} over {len(sent)} applications is under "
                       f"{AUTO_PAUSE_RATE:.0%}. Check fit and targeting before sending more.")
                pause(ws, why)
                return none(why)
    jobs = [j for j in jobqueue._queue(ws).get("jobs", []) if _eligible(j, mode, fit_threshold)]
    jobs.sort(key=lambda j: -(j.get("fit") or 0))
    if not jobs:
        return none("nothing approved to apply to")
    return {"job": jobs[0], "posting_id": jobs[0]["posting_id"], "reason": ""}


def record(ws, posting_id, result, reason=""):
    if result not in ("submitted", "unclear", "stopped"):
        raise ValueError("result is submitted, unclear or stopped")
    if result == "submitted":
        entry = jobqueue.set_state(ws, posting_id, "applied")
    elif result == "unclear":
        entry = jobqueue.set_state(ws, posting_id, "applied?")
    else:
        entry = jobqueue.set_state(ws, posting_id, "needs-you")
        q = jobqueue._queue(ws)
        for j in q["jobs"]:
            if j.get("posting_id") == posting_id:
                j["stop_reason"] = reason
        d.write_json_atomic(d.data_dir(ws) / "queue.json", q)
    d.append_jsonl(d.data_dir(ws) / "apply-log.jsonl", {"posting_id": posting_id, "result": result, "reason": reason,
                                                         "at": datetime.now().isoformat(timespec="seconds")})
    return entry


def _opt(args, name, default=None):
    return args[args.index(name) + 1] if name in args and args.index(name) + 1 < len(args) else default


def main(argv):
    cmds = ("sheet", "next", "allowed", "record", "pause", "resume", "status")
    if len(argv) < 3 or argv[1] not in cmds:
        print(__doc__, file=sys.stderr)
        return 2
    cmd, args = argv[1], argv[2:]
    try:
        if cmd == "allowed":
            ok = allowed(args[0])
            print("ALLOWED" if ok else "REFUSED")
            return 0 if ok else 3
        ws = args[0]
        if cmd == "sheet":
            out = sheet(ws, args[1], _opt(args, "--mode", "assisted"))
        elif cmd == "next":
            out = next(ws, _opt(args, "--mode", "agent"), int(_opt(args, "--cap", DAILY_CAP)),
                       int(_opt(args, "--fit", FIT_THRESHOLD)))
        elif cmd == "record":
            out = record(ws, args[1], args[2], _opt(args, "--reason", ""))
        elif cmd == "pause":
            pause(ws, _opt(args, "--reason", "paused by you"))
            out = status(ws)
        elif cmd == "resume":
            resume(ws)
            out = status(ws)
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
