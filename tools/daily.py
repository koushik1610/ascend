#!/usr/bin/env python3
"""daily.py: the scheduled Ascend 2.0 sync, zero tokens (M10).

  python3 tools/daily.py WS
  python3 tools/daily.py WS --retention-only      # mail retention alone, for runs without the schedule

Runs every stage that needs no model, in order, each isolated so one failure never stops the rest:
Gmail sync (engine A), classify, ingest, finder, prefilter, alerts, automatic apply (only when turned on
in the hub), mail retention, hub build. A stage
that cannot do its job fails with the fix in its message (Gmail signed out, no boards to poll), so the
day's log never reads "ok" over a sync that did nothing. Stages that
need Claude (reading Gmail through the connector for engines B and C, scoring, tailoring, agent apply)
wait for the next `/ascend run-v2` session. One row per run lands in data/run-log.jsonl.
"""

import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import _v2data as d  # noqa: E402


RETENTION_DAYS = 180
TRIM_AFTER_DAYS = 14


def _engine(ws):
    return (d.read_json(Path(ws) / ".ascend-state.json", {}).get("run_defaults") or {}).get("engine")


AUTOMATED = re.compile(r"^(no-?reply|do-?not-?reply|donotreply|info|hello|news|newsletter|notifications?|team|"
                       r"marketing|updates?)[@+.]", re.I)


def _automated(sender):
    """A machine-sent address. Its non-job mail keeps headers only from day one; a person's waits 14 days."""
    import classify
    addr = classify.sender({"from": sender or ""})
    return bool(AUTOMATED.search(addr) or classify.BULK_SENDER.search(addr.partition("@")[2]))


def prune(ws, today=None):
    """Spec §8 retention: drop mail older than retention_days (sources.json, default 180), and keep only the
    headers of mail placed as not job-related once it is TRIM_AFTER_DAYS old. Mail waiting for a model, and
    mail in a thread that has job mail (a recruiter's follow-up), keep their excerpt. Claude's staging files
    are removed: they hold copies that would outlive this."""
    dd = d.data_dir(ws)
    days = d.read_json(dd / "sources.json", {}).get("retention_days") or RETENTION_DAYS
    cutoff = (date.fromisoformat(today) if today else date.today()) - timedelta(days=int(days))
    import classify
    latest = {e.get("msg_id"): e for e in classify.latest_events(d.read_jsonl(dd / "events.jsonl"))}
    trim_before = ((date.fromisoformat(today) if today else date.today()) - timedelta(days=TRIM_AFTER_DAYS)).isoformat()
    job_threads = {m.get("thread_id") for m in d.read_jsonl(dd / "mail.jsonl") if m.get("thread_id") and
                   (latest.get(m.get("msg_id")) or {}).get("category") not in (None, "other", "job-alert")}
    out = {"dropped": 0, "trimmed": 0}

    def keep(rows):
        kept = []
        for m in rows:
            if (m.get("date") or "")[:10] and m["date"][:10] < cutoff.isoformat():
                out["dropped"] += 1
                continue
            e = latest.get(m.get("msg_id")) or {}
            if (e.get("category") == "other" and not e.get("needs_llm") and m.get("body_excerpt")
                    and m.get("thread_id") not in job_threads
                    and ((m.get("date") or "")[:10] < trim_before or _automated(m.get("from")))):
                m = dict(m, body_excerpt="")
                out["trimmed"] += 1
            kept.append(m)
        return kept
    if (dd / "mail.jsonl").exists():
        d.rewrite_jsonl(dd / "mail.jsonl", keep)
    import gmail_sync
    for name in gmail_sync.STAGING:
        if (dd / name).is_file():
            (dd / name).unlink()
    return out


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
        if not engine:
            raise RuntimeError("no run settings yet: run `/ascend run-v2` once to choose an engine")
        if engine != "A":
            return f"skipped: engine {engine} reads Gmail in a Claude session"
        if not (ws / "gmail-client.json").is_file():
            raise RuntimeError("engine A has no Gmail client: see docs/GMAIL-SETUP.md")
        if not runplan._has_token(ws):
            raise RuntimeError(f"Gmail is signed out, so replies are not being tracked. "
                               f"Run: python3 tools/gmail_sync.py connect {ws}")
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
        if not d.read_json(ws / "data" / "sources.json", {}).get("boards"):
            raise RuntimeError("no boards to poll in data/sources.json: see templates/sources.example.json")
        out = finder.run(ws)
        if out["failed"] and len(out["failed"]) == out["boards"]:
            raise RuntimeError(f"every board was unreachable ({', '.join(out['failed'])}): check the slugs in "
                               "data/sources.json")
        return (f"{out['new']} new, {out['closed']} closed" + (f", unreachable: {', '.join(out['failed'])}" if out["failed"] else "")
                + (f", throttled: {', '.join(out['throttled'])}" if out.get("throttled") else ""))

    def pre():
        import prefilter
        return json.dumps(prefilter.run(ws))

    def alerts_():
        import alerts
        return json.dumps(alerts.run(ws))

    def autoapply_():
        import autoapply
        out = autoapply.run(ws)
        if out["error"]:
            raise RuntimeError(out["error"])
        if out["skipped"]:
            return f"skipped: {out['skipped']}"
        return (f"{out['submitted']} submitted, {out['unclear']} unclear, {out['stopped']} stopped"
                + (f", {len(out['waiting'])} waiting for a résumé" if out["waiting"] else ""))

    def hub_():
        import hub
        return str(hub.build(ws))

    for name, fn in [("gmail", gmail), ("classify", classify_), ("ingest", ingest), ("finder", find),
                     ("prefilter", pre), ("alerts", alerts_), ("autoapply", autoapply_), ("retention", lambda: json.dumps(prune(ws))),
                     ("hub", hub_)]:
        stage(name, fn)
    out = {"at": datetime.now().isoformat(timespec="seconds"), "engine": engine, "stages": stages}
    d.append_jsonl(d.data_dir(ws) / "run-log.jsonl", out)
    return out


def main(argv):
    if len(argv) < 2 or argv[1].startswith("-"):
        print(__doc__, file=sys.stderr)
        return 2
    if "--retention-only" in argv:          # for runs without the scheduled sync (prompts/29 Step 4)
        print(json.dumps(prune(argv[1])))
        return 0
    out = run(argv[1])
    for s in out["stages"]:
        print(f"{'ok ' if s['ok'] else 'ERR'} {s['stage']:<10} {s['detail']}")
    return 0 if all(s["ok"] for s in out["stages"]) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
