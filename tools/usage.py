#!/usr/bin/env python3
"""usage.py: what each Claude stage costs, recorded per run (Ascend 2.0, M7).

  python3 tools/usage.py record WS --stage STAGE --chars-in N --chars-out N [--engine A|B|C] [--mode M] [--items K] [--backfill]
  python3 tools/usage.py summary WS [--json]
  python3 tools/usage.py estimate WS --engine A|B|C [--mode assisted|automatic] [--jobs N] [--json]

Claude Code does not report token counts to the agent, so each stage records the characters it read and
wrote and this tool converts at 4 characters per token. Every figure carries `estimated: true` and the hub
labels it that way. The conversion is typically within about 20% for English text and JSON.

The estimate uses the user's own measured averages once a stage has 3 or more items recorded, and the design's
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
# Finding + mail, before any application. Engine C from the from-scratch run (2026-10-17: ~3.5K for a day of
# connector mail, finding at zero tokens), with room for reading job mail in full. Engine A's sync and
# finding cost nothing; only the model pass on unplaced mail does. Engine B is unmeasured: its web
# searches read pages, so it is set well above C.
BASE_DAILY = {"A": 5_000, "B": 60_000, "C": 10_000}
BASE_STAGES = ("mail", "web_search", "linkedin_search")     # what a day costs before any application
# Per application, until measured. Score: ~500 measured per job on rerun 1. Tailor (Phase 5 reads the master,
# the posting and the templates and writes a résumé, outreach and log) is not measured yet.
STAGE_DEFAULT = {"score": 600, "tailor": 12_000}
DEFAULT_JOBS = 5                                            # assisted: applications the user sends in a day
JOB_STAGES = {"assisted": ["score", "tailor"], "automatic": ["score", "tailor"]}    # submitting is zero tokens
MIN_SAMPLES = 3


def tokens(chars):
    return math.ceil(max(0, int(chars)) / CHARS_PER_TOKEN)


def record(ws, stage, chars_in, chars_out, run_id=None, engine=None, mode=None, items=1, backfill=False):
    row = {"stage": stage, "input_tokens": tokens(chars_in), "output_tokens": tokens(chars_out), "estimated": True,
           "items": int(items), "engine": engine, "mode": mode, "run_id": run_id,
           "at": datetime.now().isoformat(timespec="seconds")}
    if backfill:            # the first read's month of mail: a one-time cost, never part of the daily base
        row["backfill"] = True
    d.append_jsonl(d.data_dir(ws) / "usage.jsonl", row)
    return row


def _per_item(rows):
    n = sum(max(1, r.get("items", 1)) for r in rows)
    return sum(r.get("input_tokens", 0) + r.get("output_tokens", 0) for r in rows) / n


def _samples(rows):
    return sum(max(1, int(r.get("items", 1) or 1)) for r in rows)


def estimate(ws, engine, mode="assisted", jobs=DEFAULT_JOBS):
    """Each stage uses its own measured average once it has MIN_SAMPLES records, else its default, so the
    estimate moves toward real figures one stage at a time. The daily base is measured per recorded day."""
    rows = d.read_jsonl(Path(ws) / "data" / "usage.jsonl")
    by_stage = {}
    for r in rows:
        by_stage.setdefault(r.get("stage"), []).append(r)
    stages, per_job = {}, 0
    for s in JOB_STAGES[mode]:
        got = by_stage.get(s, [])
        measured = _samples(got) >= MIN_SAMPLES        # one batch of 25 scored jobs is 25 samples
        stages[s] = "measured" if measured else "default"
        per_job += _per_item(got) if measured else STAGE_DEFAULT[s]
    days = {}
    for r in rows:
        if r.get("stage") in BASE_STAGES and r.get("engine") in (engine, None) and not r.get("backfill"):
            day = str(r.get("at", ""))[:10]
            days[day] = days.get(day, 0) + r.get("input_tokens", 0) + r.get("output_tokens", 0)
    stages["base"] = "measured" if len(days) >= MIN_SAMPLES else "default"
    base = round(sum(days.values()) / len(days)) if len(days) >= MIN_SAMPLES else BASE_DAILY[engine]
    kinds = set(stages.values())
    basis = "measured" if kinds == {"measured"} else "default" if kinds == {"default"} else "partly measured"
    per_job = round(per_job)
    return {"engine": engine, "mode": mode, "jobs": jobs, "per_job": per_job, "daily": base + jobs * per_job,
            "basis": basis, "stages": stages}


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
                     engine=_opt(args, "--engine"), mode=_opt(args, "--mode"), items=_opt(args, "--items", 1),
                     backfill="--backfill" in args)
    elif cmd == "summary":
        out = summary(ws)
    else:
        out = estimate(ws, _opt(args, "--engine", "A"), _opt(args, "--mode", "assisted"), int(_opt(args, "--jobs", DEFAULT_JOBS)))
    print(json.dumps(out, indent=None if "--json" in args else 2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
