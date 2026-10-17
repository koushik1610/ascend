#!/usr/bin/env python3
"""schedule.py: run the zero-token Ascend 2.0 sync every day (M10).

  python3 tools/schedule.py install WS --at HH:MM
  python3 tools/schedule.py remove WS
  python3 tools/schedule.py show WS

Installs one cron line, tagged `Ascend-V2-SYNC-<name>`, that runs `tools/daily.py` for the workspace and
appends to workspace/<name>/daily.log. Uses the same safe crontab handling as the daily brief
(tools/_cron.py): an unreadable crontab is never overwritten, and a backup is kept.
"""

import json
import shlex
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import _cron  # noqa: E402

REPO = TOOLS.parent


def _tag(ws):
    return f"Ascend-V2-SYNC-{Path(ws).name}"


def install(ws, hhmm):
    try:
        h, m = [int(x) for x in hhmm.split(":")]
        if not (0 <= h < 24 and 0 <= m < 60):
            raise ValueError
    except ValueError:
        return {"ok": False, "error": f"bad time {hhmm!r}, use HH:MM"}
    ws = Path(ws).resolve()
    line = (f"{m} {h} * * * {shlex.quote(sys.executable)} {shlex.quote(str(REPO / 'tools' / 'daily.py'))} "
            f"{shlex.quote(str(ws))} >> {shlex.quote(str(ws / 'daily.log'))} 2>&1")
    return _cron.install(_tag(ws), line, ws)


def remove(ws):
    return _cron.remove(_tag(ws))


def show(ws):
    ok, text, err = _cron.read()
    return {"ok": ok, "line": next((l for l in text.splitlines() if _tag(ws) in l), None), "error": err}


def main(argv):
    if len(argv) < 3 or argv[1] not in ("install", "remove", "show"):
        print(__doc__, file=sys.stderr)
        return 2
    if argv[1] == "install":
        out = install(argv[2], argv[argv.index("--at") + 1] if "--at" in argv else "")
    elif argv[1] == "remove":
        out = remove(argv[2])
    else:
        out = show(argv[2])
    print(json.dumps(out, indent=2))
    return 0 if out.get("ok") else 3


if __name__ == "__main__":
    sys.exit(main(sys.argv))
