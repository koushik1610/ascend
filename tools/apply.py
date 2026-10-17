#!/usr/bin/env python3
"""apply.py: the apply sheet and the record of what was sent (Ascend 2.0, M8, assisted mode).

  python3 tools/apply.py sheet  WS POSTING_ID                                   # the apply sheet, gated
  python3 tools/apply.py record WS POSTING_ID submitted|unclear|stopped [--reason TEXT]
  python3 tools/apply.py status WS

The user submits every application in their own browser. The sheet is built only when the job is
approved, it is not a duplicate, its résumé passes lint_artifacts.py, and every answer comes from the
user's own profile. Work authorization, sponsorship, salary and start date are always listed under
ask_user and never pre-filled, even when the profile records them.

Nothing here transmits anything. Agent-submit and fully automatic modes are developed on the
ascend-v2-agent-modes branch and are not part of this release.
"""

import json
import re
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import _v2data as d  # noqa: E402
import jobqueue  # noqa: E402
import pipeline  # noqa: E402

PROFILE_FIELDS = ["name", "email", "phone", "location", "linkedin", "website", "github",
                  "work_authorization", "sponsorship", "salary_expectation", "start_date"]
ALWAYS_ASK = ["work_authorization", "sponsorship", "salary_expectation", "start_date"]


def _first(items, default=None):
    for x in items:
        return x
    return default


class Refused(Exception):
    """The gate said no. The message says why, in words the user can act on."""


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


def sheet(ws, posting_id):
    ws = Path(ws)
    entry = _entry(ws, posting_id)
    if entry.get("state") != "approved":
        raise Refused(f"{entry.get('company')} is {entry.get('state')}, not approved")
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
    answers = {k: profile[k] for k in PROFILE_FIELDS if profile.get(k) and k not in ALWAYS_ASK}
    ask = ALWAYS_ASK + [k for k in ("name", "email", "phone") if not profile.get(k)]
    out = {"posting_id": posting_id, "company": entry.get("company"), "title": entry.get("title"),
           "apply_url": entry.get("apply_url") or entry.get("url") or entry.get("posting_id"),
           "resume_pdf": str(pdfs[0]), "answers": answers, "ask_user": ask, "cover_note": _hook(job),
           "built_at": datetime.now().isoformat(timespec="seconds")}
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", posting_id)[:120]
    d.write_json_atomic(d.data_dir(ws) / "apply-sheets" / f"{safe}.json", out)
    return out


def status(ws):
    log = d.read_jsonl(Path(ws) / "data" / "apply-log.jsonl")
    today = date.today().isoformat()
    return dict(submitted_today=sum(1 for r in log if r.get("result") == "submitted"
                                                  and str(r.get("at", "")).startswith(today)))


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
    cmds = ("sheet", "record", "status")
    if len(argv) < 3 or argv[1] not in cmds:
        print(__doc__, file=sys.stderr)
        return 2
    cmd, args = argv[1], argv[2:]
    try:
        ws = args[0]
        if cmd == "sheet":
            out = sheet(ws, args[1])
        elif cmd == "record":
            out = record(ws, args[1], args[2], _opt(args, "--reason", ""))
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
