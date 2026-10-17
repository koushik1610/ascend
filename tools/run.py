#!/usr/bin/env python3
"""run.py: choose an engine and an apply mode for a run, see what it will cost, check it can run (M7).

  python3 tools/run.py plan WS --engine A|B|C [--mode assisted] [--jobs N]
  python3 tools/run.py steps --engine A|B|C

Engines (spec §4): A is the deterministic core with your own Gmail sign-in, B has Claude do every stage,
C is the core with Gmail read through the claude.ai connector. This release has one apply mode,
assisted: Ascend prepares each application and you submit it yourself. Agent-submit and fully automatic
are developed on the ascend-v2-agent-modes branch and are refused here.

`plan` refuses a combination that cannot run and says why, and always states the token estimate. A plan
that passes is saved as the default for scheduled runs.
"""

import json
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import _v2data as d  # noqa: E402
import usage  # noqa: E402

ENGINES = ("A", "B", "C")
MODES = ("assisted",)
LATER_MODES = ("agent", "automatic")
MODE_NOTE = {"assisted": "You press Submit on every application."}
CONNECTOR = ("Gmail: Claude reads your mail through the claude.ai Gmail connector, inside your Claude session. "
             "This repo's .claude/settings.json denies the connector's send, reply, forward, draft, label, spam and "
             "trash tools, and Drive's share, create, update, copy and trash tools.")
PERMISSIONS = {
    "A": ["Gmail: your own Google OAuth client with the gmail.readonly scope. The refresh token stays in your "
          "macOS Keychain. Ascend cannot send, change or delete mail."],
    "B": [CONNECTOR, "Web: Claude runs web searches for postings."],
    "C": [CONNECTOR],
}
PERMISSIONS_ALL = [
    "Job boards: public board APIs, read only, no login.",
    "Applications: Ascend never submits anything. You open each application and press Submit yourself.",
    "LinkedIn search (only if you ask for it): Claude in Chrome reads job result cards in your own logged-in "
    "browser. Automated browsing can break LinkedIn's terms of use and put the account at risk.",
]


def _has_token(ws):
    try:
        import gmail_sync
        return bool(gmail_sync.get_refresh(Path(ws).name))
    except (FileNotFoundError, OSError):
        return False


def plan(ws, engine, mode="assisted", jobs=20):
    problems = []
    if engine not in ENGINES:
        problems.append(f"unknown engine {engine!r}")
    if mode in LATER_MODES:
        problems.append(f"{mode} mode is not in this release: Ascend 2.0 ships assisted mode only")
    elif mode not in MODES:
        problems.append(f"unknown mode {mode!r}")
    if problems:
        return {"ok": False, "problems": problems, "estimate": None, "warning": "", "permissions": []}
    if engine == "A":
        if not (Path(ws) / "gmail-client.json").is_file():
            problems.append("engine A needs workspace/<name>/gmail-client.json (docs/GMAIL-SETUP.md). "
                            "Engine C works without it.")
        elif not _has_token(ws):
            problems.append(f"engine A is not signed in: python3 tools/gmail_sync.py connect {ws}")
    est = usage.estimate(ws, engine, mode, jobs)
    warning = (f"Estimated ~{est['daily']:,} tokens a day at {jobs} applications "
               f"(~{est['per_job']:,} tokens per application, {est['basis']} figures). {MODE_NOTE[mode]}")
    ok = not problems
    if ok:
        p = Path(ws) / ".ascend-state.json"
        state = d.read_json(p, {"name": Path(ws).name, "phases": {}})
        state["run_defaults"] = {"engine": engine, "mode": mode}
        d.write_json_atomic(p, state)
    return {"ok": ok, "problems": problems, "estimate": est, "warning": warning,
            "permissions": PERMISSIONS[engine] + PERMISSIONS_ALL}


def steps(engine):
    find = ["python3 tools/finder.py run WS", "python3 tools/prefilter.py run WS", "python3 tools/alerts.py run WS"]
    judge = ["CLAUDE: prompts/27-score-queue.md (score new survivors)",
             "CLAUDE: prompts/05-job-folders.md (tailor approved jobs)", "python3 tools/hub.py build WS"]
    if engine == "A":
        return ["python3 tools/gmail_sync.py sync WS --then-classify"] + find + judge
    if engine == "C":
        return ["CLAUDE: read new Gmail through the connector, then python3 tools/gmail_sync.py add WS (prompts/29-run-v2.md)",
                "python3 tools/classify.py run WS", "python3 tools/pipeline.py ingest WS"] + find + judge
    return ["CLAUDE: read new Gmail through the connector, then python3 tools/gmail_sync.py add WS (prompts/29-run-v2.md)",
            "CLAUDE: classify what the rules leave unplaced (python3 tools/classify.py run WS first)",
            "CLAUDE: search the web for matching postings, then python3 tools/finder.py add WS --source web",
            "python3 tools/prefilter.py run WS", "python3 tools/pipeline.py ingest WS"] + judge


def _opt(args, name, default=None):
    return args[args.index(name) + 1] if name in args and args.index(name) + 1 < len(args) else default


def main(argv):
    if len(argv) < 2 or argv[1] not in ("plan", "steps"):
        print(__doc__, file=sys.stderr)
        return 2
    args = argv[2:]
    if argv[1] == "steps":
        print("\n".join(steps(_opt(args, "--engine", "A"))))
        return 0
    if not args or args[0].startswith("--"):
        print(__doc__, file=sys.stderr)
        return 2
    out = plan(args[0], _opt(args, "--engine", "A"), _opt(args, "--mode", "assisted"), int(_opt(args, "--jobs", 20)))
    print(json.dumps(out, indent=2))
    return 0 if out["ok"] else 3


if __name__ == "__main__":
    sys.exit(main(sys.argv))
