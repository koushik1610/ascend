#!/usr/bin/env python3
"""daily.py: the scheduled Ascend 2.0 sync, zero tokens (M10).

  python3 tools/daily.py WS

Runs every stage that needs no model, in order, each isolated so one failure never stops the rest:
Gmail sync (engine A, when connected), classify, ingest, finder, prefilter, alerts, hub build. Stages that
need Claude (reading Gmail through the connector for engines B and C, scoring, tailoring, agent apply)
wait for the next `/ascend run-v2` session. One row per run lands in data/run-log.jsonl.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import _v2data as d  # noqa: E402


def _engine(ws):
    return (d.read_json(Path(ws) / ".ascend-state.json", {}).get("run_defaults") or {}).get("engine", "A")


def run(ws):
    ws = Path(ws)
    engine = _engine(ws)
    stages = []

    def stage(name, fn):
        try:
            detail = fn()
            stages.append({"stage": name, "ok": True, "detail": detail})
        except Exception as e:      # isolated on purpose: record and keep going
            stages.append({"stage": name, "ok": False, "detail": f"{type(e).__name__}: {e}"})

    def gmail():
        import gmail_sync
        import run as runplan
        if engine != "A":
            return f"skipped: engine {engine} reads Gmail in a Claude session"
        if not (ws / "gmail-client.json").is_file() or not runplan._has_token(ws):
            return "skipped: engine A is not connected"
        out = gmail_sync.sync(ws)
        return f"{out['new']} new via {out['mode']}"

    def classify_():
        import subprocess
        r = subprocess.run([sys.executable, str(TOOLS / "classify.py"), "run", str(ws), "--json"],
                           capture_output=True, text=True, check=True)
        return r.stdout.strip()

    def ingest():
        import subprocess
        r = subprocess.run([sys.executable, str(TOOLS / "pipeline.py"), "ingest", str(ws), "--json"],
                           capture_output=True, text=True, check=True)
        return r.stdout.strip()

    def find():
        import finder
        out = finder.run(ws)
        return f"{out['new']} new, {out['closed']} closed" + (f", unreachable: {', '.join(out['failed'])}" if out["failed"] else "")

    def pre():
        import prefilter
        return json.dumps(prefilter.run(ws))

    def alerts_():
        import alerts
        return json.dumps(alerts.run(ws))

    def hub_():
        import hub
        return str(hub.build(ws))

    for name, fn in [("gmail", gmail), ("classify", classify_), ("ingest", ingest), ("finder", find),
                     ("prefilter", pre), ("alerts", alerts_), ("hub", hub_)]:
        stage(name, fn)
    out = {"at": datetime.now().isoformat(timespec="seconds"), "engine": engine, "stages": stages}
    d.append_jsonl(d.data_dir(ws) / "run-log.jsonl", out)
    return out


def main(argv):
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    out = run(argv[1])
    for s in out["stages"]:
        print(f"{'ok ' if s['ok'] else 'ERR'} {s['stage']:<10} {s['detail']}")
    return 0 if all(s["ok"] for s in out["stages"]) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
