#!/usr/bin/env python3
"""state.py — the run manifest, with a schema and a single writer (stdlib only).

`.ascend-state.json` is what makes a run resumable, and it is what `master_locked` rests on — the
single mechanism that turns "don't invent" from a guideline into a mode downstream phases operate in.
It was also produced entirely by LLM text generation against a prose spec: no schema, no writer, no
validation, no tests, and read straight into an API response at `ui/server.py:254`.

That is the wrong footing for the file the v1.0 interrupt-resume run (case (c)) exists to exercise. A
truncated write leaves the console at 0% forever; a plausible-but-wrong file silently re-runs or skips
a phase, and nothing notices.

  python3 tools/state.py init      WS --name NAME
  python3 tools/state.py set-phase WS PHASE STATUS     # todo | in-progress | done
  python3 tools/state.py lock      WS                  # lock the master, bump master_version
  python3 tools/state.py job       WS SLUG [--file F]… [--complete]
  python3 tools/state.py validate  WS [--json]
  python3 tools/state.py show      WS [--json]

Two properties worth keeping if this is ever rewritten:
  1. Writes are ATOMIC (tmp file + os.replace). A half-written manifest is the failure that strands a
     resumable run, and it is exactly what an interrupted run is likely to produce.
  2. `lock` REFUSES to silently unlock. Downgrading master_locked without an explicit --unlock is the
     one edit that would quietly turn selection-only mode off for every later phase.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

PHASES = ["1", "2", "3", "4", "5", "6", "7", "11"]
STATUSES = ["todo", "in-progress", "done"]


def die(msg):
    print(f"state: {msg}", file=sys.stderr)
    return 2


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def path_for(ws):
    return Path(ws) / ".ascend-state.json"


def load(ws):
    p = path_for(ws)
    if not p.is_file():
        return None, f"no manifest at {p}"
    try:
        return json.loads(p.read_text(encoding="utf-8")), None
    except ValueError as e:
        return None, f"manifest is not valid JSON: {e}"


def save(ws, data):
    """Atomic: write a sibling temp file, fsync, then os.replace. Never a partial manifest."""
    p = path_for(ws)
    data["updated"] = _now()
    tmp = p.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, p)


def validate(data):
    """Return a list of problems. Empty list means the manifest is structurally sound."""
    bad = []
    if not isinstance(data, dict):
        return ["manifest is not a JSON object"]
    if not str(data.get("name", "")).strip():
        bad.append("missing 'name'")
    ph = data.get("phases", {})
    if not isinstance(ph, dict):
        bad.append("'phases' is not an object")
    else:
        for k, v in ph.items():
            if k not in PHASES:
                bad.append(f"unknown phase {k!r} (known: {', '.join(PHASES)})")
            if not isinstance(v, str) or not v.startswith(tuple(STATUSES)):
                bad.append(f"phase {k}: status {v!r} is not one of {', '.join(STATUSES)}")
    if data.get("master_locked") and not isinstance(data.get("master_version"), int):
        bad.append("master_locked is true but master_version is not an integer "
                   "(downstream phases cite it in every Delta Log)")
    jobs = data.get("jobs", [])
    if not isinstance(jobs, list):
        bad.append("'jobs' is not a list")
    else:
        for i, j in enumerate(jobs):
            if not isinstance(j, dict) or not j.get("slug"):
                bad.append(f"jobs[{i}] has no slug")
    return bad


def cmd_init(ws, args):
    name = ""
    it = iter(args)
    for a in it:
        if a == "--name":
            name = next(it, "")
    if not name:
        return die("init needs --name NAME")
    if path_for(ws).exists():
        return die(f"manifest already exists at {path_for(ws)}; refusing to overwrite a run")
    save(ws, {"name": name, "phase": None, "master_locked": False, "master_version": 0,
              "phases": {p: "todo" for p in PHASES}, "jobs": []})
    print(f"  initialised {path_for(ws)}")
    return 0


def cmd_set_phase(ws, args):
    if len(args) < 2:
        return die("usage: set-phase WS PHASE STATUS")
    phase, status = args[0], args[1]
    if phase not in PHASES:
        return die(f"unknown phase {phase!r}")
    if not status.startswith(tuple(STATUSES)):
        return die(f"status must start with one of: {', '.join(STATUSES)}")
    data, err = load(ws)
    if err:
        return die(err)
    data.setdefault("phases", {})[phase] = status
    if status.startswith("in-progress"):
        data["phase"] = phase
    save(ws, data)
    print(f"  phase {phase} → {status}")
    return 0


def cmd_lock(ws, args):
    data, err = load(ws)
    if err:
        return die(err)
    if "--unlock" in args:
        # Deliberately explicit. Silently flipping this off would turn selection-only mode off for
        # every downstream phase, which is the whole anti-fabrication mechanism.
        data["master_locked"] = False
        save(ws, data)
        print("  master UNLOCKED. Downstream phases may rewrite bullets again until you re-lock.")
        return 0
    data["master_locked"] = True
    data["master_version"] = int(data.get("master_version") or 0) + 1
    data["master_locked_on"] = _now()
    save(ws, data)
    print(f"  master locked at version {data['master_version']}. "
          "Downstream is selection-only: reorder and trim, never reword.")
    return 0


def cmd_job(ws, args):
    if not args:
        return die("usage: job WS SLUG [--file F]... [--complete]")
    slug, files, complete = args[0], [], False
    it = iter(args[1:])
    for a in it:
        if a == "--file":
            files.append(next(it, ""))
        elif a == "--complete":
            complete = True
    data, err = load(ws)
    if err:
        return die(err)
    jobs = data.setdefault("jobs", [])
    rec = next((j for j in jobs if j.get("slug") == slug), None)
    if rec is None:
        rec = {"slug": slug, "files_done": [], "complete": False}
        jobs.append(rec)
    for f in files:
        if f and f not in rec["files_done"]:
            rec["files_done"].append(f)
    if complete:
        rec["complete"] = True
    save(ws, data)
    print(f"  {slug}: {len(rec['files_done'])} file(s)" + (", complete" if rec["complete"] else ""))
    return 0


def cmd_validate(ws, args):
    data, err = load(ws)
    if err:
        if "--json" in args:
            print(json.dumps({"ok": False, "problems": [err]}))
        else:
            print(f"  INVALID: {err}")
        return 1
    problems = validate(data)
    if "--json" in args:
        print(json.dumps({"ok": not problems, "problems": problems}, indent=2))
    else:
        for p in problems:
            print(f"  problem: {p}")
        print("  manifest is valid" if not problems else f"  INVALID ({len(problems)} problem(s))")
    return 1 if problems else 0


def cmd_show(ws, args):
    data, err = load(ws)
    if err:
        return die(err)
    if "--json" in args:
        print(json.dumps(data, indent=2))
        return 0
    print(f"  name           {data.get('name')}")
    print(f"  master         " + (f"locked v{data.get('master_version')}"
                                  if data.get("master_locked") else "UNLOCKED"))
    for p in PHASES:
        st = data.get("phases", {}).get(p)
        if st:
            print(f"  phase {p:<8} {st}")
    for j in data.get("jobs", []):
        print(f"  job {j.get('slug'):<40} {'complete' if j.get('complete') else 'partial'}")
    return 0


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    cmd, ws = argv[1], Path(argv[2])
    if cmd != "init" and not ws.is_dir():
        return die(f"workspace not found: {ws}")
    ws.mkdir(parents=True, exist_ok=True)
    fn = {"init": cmd_init, "set-phase": cmd_set_phase, "lock": cmd_lock,
          "job": cmd_job, "validate": cmd_validate, "show": cmd_show}.get(cmd)
    if not fn:
        return die(f"unknown command {cmd!r}")
    return fn(ws, argv[3:])


if __name__ == "__main__":
    sys.exit(main(sys.argv))
