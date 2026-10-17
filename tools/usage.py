#!/usr/bin/env python3
"""usage.py: what each Claude stage costs, recorded per run (Ascend 2.0, M7).

  python3 tools/usage.py record WS --stage STAGE --chars-in N --chars-out N [--engine A|B|C] [--mode M] [--items K]
  python3 tools/usage.py summary WS [--json]
  python3 tools/usage.py estimate WS --engine A|B|C [--mode assisted] [--jobs N] [--json]

Claude Code does not report token counts to the agent, so each stage records the characters it read and
wrote and this tool converts at 4 characters per token. Every figure carries `estimated: true` and the hub
labels it that way. The conversion is typically within about 20% for English text and JSON.

The estimate uses the user's own measured averages once a stage has 3 or more records, and the design's
defaults until then.
"""

import json
import math
import sys
from datetime import datetime
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import _v2data as d  # noqa: E402

CHARS_PER_TOKEN = 4
BASE_DAILY = {"A": 85_000, "B": 700_000, "C": 140_000}      # finding + mail, before any application
PER_JOB = {"assisted": 7_500, "agent": 55_000, "automatic": 55_000}
JOB_STAGES = {"assisted": ["score", "tailor"], "agent": ["score", "tailor", "apply"],
              "automatic": ["score", "tailor", "apply"]}
MIN_SAMPLES = 3


def tokens(chars):
    return math.ceil(max(0, int(chars)) / CHARS_PER_TOKEN)


def record(ws, stage, chars_in, chars_out, run_id=None, engine=None, mode=None, items=1):
    row = {"stage": stage, "input_tokens": tokens(chars_in), "output_tokens": tokens(chars_out), "estimated": True,
           "items": int(items), "engine": engine, "mode": mode, "run_id": run_id,
           "at": datetime.now().isoformat(timespec="seconds")}
    d.append_jsonl(d.data_dir(ws) / "usage.jsonl", row)
    return row


def _per_item(rows):
    n = sum(max(1, r.get("items", 1)) for r in rows)
    return sum(r.get("input_tokens", 0) + r.get("output_tokens", 0) for r in rows) / n


def estimate(ws, engine, mode, jobs=20):
    rows = d.read_jsonl(Path(ws) / "data" / "usage.jsonl")
    by_stage = {}
    for r in rows:
        by_stage.setdefault(r.get("stage"), []).append(r)
    stages = JOB_STAGES[mode]
    measured = all(len(by_stage.get(s, [])) >= MIN_SAMPLES for s in stages)
    per_job = round(sum(_per_item(by_stage[s]) for s in stages)) if measured else PER_JOB[mode]
    return {"engine": engine, "mode": mode, "jobs": jobs, "per_job": per_job,
            "daily": BASE_DAILY[engine] + jobs * per_job, "basis": "measured" if measured else "default"}


def summary(ws):
    out = {}
    for r in d.read_jsonl(Path(ws) / "data" / "usage.jsonl"):
        s = out.setdefault(r.get("stage"), {"records": 0, "tokens": 0})
        s["records"] += 1
        s["tokens"] += r.get("input_tokens", 0) + r.get("output_tokens", 0)
    return out


def _opt(args, name, default=None):
    return args[args.index(name) + 1] if name in args and args.index(name) + 1 < len(args) else default


def main(argv):
    if len(argv) < 3 or argv[1] not in ("record", "summary", "estimate"):
        print(__doc__, file=sys.stderr)
        return 2
    cmd, ws, args = argv[1], argv[2], argv[3:]
    if cmd == "record":
        out = record(ws, _opt(args, "--stage", "unknown"), _opt(args, "--chars-in", 0), _opt(args, "--chars-out", 0),
                     engine=_opt(args, "--engine"), mode=_opt(args, "--mode"), items=_opt(args, "--items", 1))
    elif cmd == "summary":
        out = summary(ws)
    else:
        out = estimate(ws, _opt(args, "--engine", "A"), _opt(args, "--mode", "assisted"), int(_opt(args, "--jobs", 20)))
    print(json.dumps(out, indent=None if "--json" in args else 2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
