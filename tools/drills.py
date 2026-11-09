#!/usr/bin/env python3
"""drills.py: the interview-answer ledger, so practice weeks apart is comparable (stdlib only).

  python3 tools/drills.py record WS --from ROW.json
  python3 tools/drills.py summary WS [--job NN] [--json]

One row per answer, appended to WS/data/drills.jsonl and never rewritten:

  {"job": "05" | "general", "source": "mock" | "real", "question": "...", "story": "S3" | "none",
   "scores": {"substance": 1-5, "structure": 1-5, "relevance": 1-5, "credibility": 1-5,
              "differentiation": 1-5}}

The dimensions and their anchors live in reference/interview-prep-framework.md §6. `mock` rows come
from prompts/17-interview-me.md, `real` rows from prompts/31-interview-debrief.md.

WHY THE ROW COMES FROM A FILE. The Bash allow-list pins this tool by path prefix and places no
constraint on its arguments. A question typed onto the command line is free text inside a shell
string, and a recalled interview question or a pasted transcript can carry anything. So the only
argument is a path, it must resolve inside the workspace, and every field is validated before it is
stored. The text is data: nothing here ever interprets it.

`summary` reports per-dimension averages, the trend (the first five answers against the last five,
once there are ten), the weakest dimension, and story use: how often each story was told, which ones
carry more than a third of the answers, and which stories in interview-packet/star-stories.md have
never been told aloud.
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import _data as d  # noqa: E402
from _paths import is_allowed  # noqa: E402

DIMENSIONS = ("substance", "structure", "relevance", "credibility", "differentiation")
SOURCES = ("mock", "real")
STORY_ID = re.compile(r"^(?:[SDE]\d{1,3}|none)$")
JOB_ID = re.compile(r"^(?:\d{1,3}|general)$")
MAX_QUESTION = 300
TREND_WINDOW = 5
OVERUSE_SHARE = 1 / 3
OVERUSE_MIN_ANSWERS = 6


class Invalid(ValueError):
    pass


def _clean(text):
    """Printable text on one line. Control and format characters go, so a row can't hide anything."""
    text = "".join(" " if ch.isspace() else ch for ch in str(text)
                   if ch.isspace() or (ch.isprintable() and not 0xE0000 <= ord(ch) <= 0xE007F))
    return re.sub(r"\s+", " ", text).strip()[:MAX_QUESTION]


def validate(row):
    if not isinstance(row, dict):
        raise Invalid("the row must be a JSON object")
    job = str(row.get("job", "")).strip()
    if not JOB_ID.match(job):
        raise Invalid(f"job must be a queue number or 'general', got {job!r}")
    source = row.get("source")
    if source not in SOURCES:
        raise Invalid(f"source must be one of {SOURCES}, got {source!r}")
    question = _clean(row.get("question", ""))
    if not question:
        raise Invalid("question is empty")
    story = str(row.get("story", "none")).strip()
    if not STORY_ID.match(story):
        raise Invalid(f"story must be a story, deep-dive or master ID (S3, D2, E14) or 'none', got {story!r}")
    scores = row.get("scores")
    if not isinstance(scores, dict) or set(scores) != set(DIMENSIONS):
        raise Invalid("scores must have exactly: " + ", ".join(DIMENSIONS))
    clean_scores = {}
    for k in DIMENSIONS:
        v = scores[k]
        if isinstance(v, bool) or not isinstance(v, int) or not 1 <= v <= 5:
            raise Invalid(f"score {k} must be a whole number from 1 to 5, got {v!r}")
        clean_scores[k] = v
    return {"job": job, "source": source, "question": question, "story": story, "scores": clean_scores}


def record(ws, row_path):
    src = Path(row_path)
    if not is_allowed(src) or "workspace" not in src.resolve().parts:
        raise Invalid(f"the row file must be inside the workspace: {row_path}")
    try:
        row = json.loads(src.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise Invalid(f"cannot read the row file: {e}")
    rec = validate(row)
    rec["at"] = datetime.now().isoformat(timespec="seconds")
    d.append_jsonl(d.data_dir(ws) / "drills.jsonl", rec)
    return rec


def _avg(rows, dim):
    return round(sum(r["scores"][dim] for r in rows) / len(rows), 2) if rows else None


def _known_stories(ws):
    path = Path(ws) / "interview-packet" / "star-stories.md"
    if not path.is_file():
        return []
    ids = re.findall(r"^#{1,4}\s*(S\d{1,3})\b", path.read_text(encoding="utf-8"), re.M)
    return sorted(set(ids), key=lambda s: int(s[1:]))


def summary(ws, job=None):
    rows = []
    for r in d.read_jsonl(Path(ws) / "data" / "drills.jsonl"):
        try:
            rows.append(validate(r) | {"at": r.get("at")})
        except Invalid:
            continue                                  # a hand-edited bad row is skipped, not fatal
    if job:
        rows = [r for r in rows if r["job"] == job]
    out = {"answers": len(rows), "by_source": {s: sum(r["source"] == s for r in rows) for s in SOURCES},
           "average": {k: _avg(rows, k) for k in DIMENSIONS}, "trend": None, "weakest": None,
           "stories": {}, "overused": [], "never_told": []}
    if not rows:
        return out
    out["weakest"] = min(DIMENSIONS, key=lambda k: out["average"][k])
    if len(rows) >= 2 * TREND_WINDOW:
        first, last = rows[:TREND_WINDOW], rows[-TREND_WINDOW:]
        out["trend"] = {k: round(_avg(last, k) - _avg(first, k), 2) for k in DIMENSIONS}
    told = [r["story"] for r in rows if r["story"] != "none"]
    for s in told:
        out["stories"][s] = out["stories"].get(s, 0) + 1
    if len(rows) >= OVERUSE_MIN_ANSWERS:
        out["overused"] = sorted(s for s, n in out["stories"].items() if n / len(rows) > OVERUSE_SHARE)
    out["never_told"] = [s for s in _known_stories(ws) if s not in out["stories"]]
    return out


def _print(s):
    print(f"answers: {s['answers']} (mock {s['by_source']['mock']}, real {s['by_source']['real']})")
    if not s["answers"]:
        print("no drills recorded yet")
        return
    for k in DIMENSIONS:
        t = s["trend"][k] if s["trend"] else None
        trend = "" if t is None else f"  trend {t:+.2f}"
        print(f"  {k:<16} {s['average'][k]:.2f}{trend}")
    if not s["trend"]:
        print(f"  trend: needs {2 * TREND_WINDOW} answers")
    print(f"weakest: {s['weakest']}")
    print("stories told: " + (", ".join(f"{k}×{v}" for k, v in sorted(s["stories"].items())) or "none"))
    print("over-used: " + (", ".join(s["overused"]) or "none"))
    print("never told: " + (", ".join(s["never_told"]) or "none"))


def main(argv):
    if len(argv) < 3 or argv[1] not in ("record", "summary"):
        print(__doc__)
        return 2
    cmd, ws = argv[1], Path(argv[2]).resolve()
    if not ws.is_dir() or "workspace" not in ws.parts:
        print(f"drills: not a workspace directory: {ws}", file=sys.stderr)
        return 2
    args = argv[3:]
    opt = {args[i]: args[i + 1] for i in range(0, len(args) - 1, 2) if args[i].startswith("--")}
    try:
        if cmd == "record":
            if "--from" not in opt:
                print("drills: record needs --from ROW.json", file=sys.stderr)
                return 2
            rec = record(ws, opt["--from"])
            print(f"recorded: {rec['source']} answer for job {rec['job']}, story {rec['story']}")
            return 0
        s = summary(ws, opt.get("--job"))
        if "--json" in args:
            print(json.dumps(s, indent=2))
        else:
            _print(s)
        return 0
    except Invalid as e:
        print(f"drills: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
