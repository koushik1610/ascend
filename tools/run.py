#!/usr/bin/env python3
"""run.py: choose an engine and an apply mode for a run, see what it will cost, check it can run (M7).

  python3 tools/run.py plan WS --engine A|B|C [--mode assisted|automatic] [--jobs N]
  python3 tools/run.py steps --engine A|B|C

Engines (spec §4): A is the deterministic core with your own Gmail sign-in, B has Claude do every stage,
C is the core with Gmail read through the claude.ai connector. Apply modes: assisted (Ascend prepares each
application and you submit it) and automatic (tools/autoapply.py submits Greenhouse, Ashby and Lever jobs
once you turn it on in the hub). Claude submitting on its own ("agent") is not offered.

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
MODES = ("assisted", "automatic")
LATER_MODES = ("agent",)
MODE_NOTE = {"assisted": "You press Submit on every application.",
             "automatic": ("Submitting costs no tokens: the runner does it on this Mac with Playwright, only after you "
                           "turn it on in the hub's Queue tab by typing \"apply for me\". Jobs it cannot finish wait in "
                           "Needs you.")}
CONNECTOR = ("Gmail: Claude reads your mail through the claude.ai Gmail connector, inside your Claude session, "
             "using a search limited to job senders and job subjects (tools/gmail_sync.py query). "
             "This repo's .claude/settings.json denies the connector's send, reply, forward, draft, label, spam and "
             "trash tools, and Drive's share, create, update, copy and trash tools.")
CONNECTOR_RISK = ("Risk you accept: mail anyone can send you is read in the same session that can fetch web pages. "
                  "Claude treats mail as data, and this repo's settings ask you before every web fetch, so a fetch an "
                  'email asked for still needs your yes. On engine C you can add "deny": ["WebFetch"] to your own '
                  ".claude/settings.local.json to rule fetches out.")
PERMISSIONS = {
    "A": ["Gmail: your own Google OAuth client with the gmail.readonly scope. The refresh token stays in your "
          "macOS Keychain. Ascend cannot send, change or delete mail."],
    "B": [CONNECTOR, CONNECTOR_RISK, "Web: Claude runs web searches for postings."],
    "C": [CONNECTOR, CONNECTOR_RISK],
}
PERMISSIONS_ALL = [
    "Job boards: public board APIs, read only, no login.",
    "Applications: Ascend never submits anything. You open each application and press Submit yourself. This repo "
    "denies Claude in Chrome's form-input, file-upload, image-upload, scripting, shortcut and batch tools. Claude in "
    "Chrome can still click and type, so keep its per-action prompts on. Claude's file tools cannot edit your queue "
    "or logs: approving a job and recording a send through Ascend are your clicks in the hub, each with a confirm "
    "(pipeline.py log, for a job you applied to elsewhere, also marks it applied).",
    "LinkedIn search (only if you ask for it): Claude in Chrome reads job result cards in your own logged-in "
    "browser. Automated browsing can break LinkedIn's terms of use and put the account at risk.",
]


def _has_token(ws):
    try:
        import gmail_sync
        return bool(gmail_sync.get_refresh(Path(ws).name))
    except (FileNotFoundError, OSError):
        return False


def _setup_problems(ws):
    """What a first v2 run needs. Without these, the daily sync runs, finds nothing and says ok."""
    ws, out = Path(ws), []
    if not (ws / "master-resume.md").is_file():
        out.append("no master-resume.md yet: run Ascend once (`/ascend`) to build it")
    boards = d.read_json(ws / "data" / "sources.json", {}).get("boards") or []
    profile = d.read_json(ws / "data" / "profile.json", {})
    if any(str(b.get("slug", "")).startswith("example-company") for b in boards):
        out.append("data/sources.json still has the template's example-company boards: replace them with yours")
    if str(profile.get("email", "")).lower().endswith("@example.com") or profile.get("name") == "Jordan Rivera":
        out.append("data/profile.json still has the template's sample name or email: put in your own")
    filters = d.read_json(ws / "data" / "sources.json", {}).get("filters") or {}
    if any("your target title" in str(x) for x in filters.get("title_include") or []):
        out.append("the filters in data/sources.json still have the template's placeholder titles: use yours")
    if not boards:
        out.append("no job boards in data/sources.json: prompts/29-run-v2.md Step 0 builds it with you "
                   "from templates/sources.example.json")
    if not d.read_json(ws / "data" / "profile.json", {}).get("email"):
        out.append("no data/profile.json with your contact details: prompts/29-run-v2.md Step 0 builds it "
                   "from templates/profile.example.json")
    return out


def plan(ws, engine, mode="assisted", jobs=usage.DEFAULT_JOBS):
    problems = _setup_problems(ws)
    if engine not in ENGINES:
        problems.append(f"unknown engine {engine!r}")
    if mode in LATER_MODES:
        problems.append(f"{mode} mode is not in this release: use automatic (the runner) or assisted")
    elif mode not in MODES:
        problems.append(f"unknown mode {mode!r}")
    if problems:
        return {"ok": False, "problems": problems, "estimate": None, "warning": "", "permissions": [],
                "prefill": [], "notes": []}
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
    import apply
    profile = d.read_json(Path(ws) / "data" / "profile.json", {})
    # Every answer an apply sheet pre-fills, by name: Step 1 shows the values to the user to confirm.
    prefill = [k for k in apply.PROFILE_FIELDS if profile.get(k) and k not in apply.ALWAYS_ASK]
    notes = _setup_notes(ws)
    if mode == "automatic":
        import autoapply
        if autoapply._filler() is None:
            notes.append(autoapply.INSTALL)
        if not (Path(ws) / "data" / "apply-answers.json").is_file():
            notes.append("no data/apply-answers.json: forms asking work authorization, sponsorship, salary or start "
                         "date stop in Needs you. Copy templates/apply-answers.example.json and fill it yourself.")
    sync = d.read_json(Path(ws) / "data" / "sync-state.json", {})
    if engine in ("B", "C") and not (sync.get("connector_last_read") or sync.get("connector_first_partial")):
        notes.append("The first Gmail read covers 30 days, a one-time cost on top of the daily estimate (about 90,000 "
                      "tokens for 90 threads on the first from-scratch run). Record it with --backfill.")
    return {"ok": ok, "problems": problems, "estimate": est, "warning": warning,
            "permissions": PERMISSIONS[engine] + PERMISSIONS_ALL, "prefill": prefill, "notes": notes}


def _setup_notes(ws):
    """Gaps that do not stop a run but change what it can do."""
    ws, out = Path(ws), []
    if not (ws / "industry-fit.md").is_file():
        out.append("no industry-fit.md (Phase 26): scoring judges must-haves from the master résumé's bullets alone")
    boards = d.read_json(ws / "data" / "sources.json", {}).get("boards") or []
    named = [b for b in boards if b.get("company") and b.get("company") != b.get("slug")]
    if boards and len(named) < len(boards):
        out.append(f"{len(boards) - len(named)} of {len(boards)} boards have no display name (company is the slug): "
                   "the hub and apply sheets show the slug. python3 tools/finder.py probe prints Greenhouse names")
    return out


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
    out = plan(args[0], _opt(args, "--engine", "A"), _opt(args, "--mode", "assisted"), int(_opt(args, "--jobs", usage.DEFAULT_JOBS)))
    print(json.dumps(out, indent=2))
    return 0 if out["ok"] else 3


if __name__ == "__main__":
    sys.exit(main(sys.argv))
