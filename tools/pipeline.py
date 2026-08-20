#!/usr/bin/env python3
"""pipeline.py — the capture act and the reads that depend on it (stdlib only).

The ghost detector, the funnel scoreboard and every weekly count used to be computed by the agent
re-reading every `jobs/*/application-log.md` and eyeballing dates. That is non-reproducible (two runs
of the same brief disagree) and it was reading fields nobody ever filled in, because Ascend's only
write-back surface was a checklist the user had to open and hand-edit.

So the write path comes first. `log` is one command at the moment something happens; everything else
here just reads what it wrote.

  python3 tools/pipeline.py log WS NN STATUS [--on DATE] [--note TEXT] [--contact NAME]
  python3 tools/pipeline.py overdue WS [--today DATE]
  python3 tools/pipeline.py funnel  WS [--json]
  python3 tools/pipeline.py show    WS [NN]

WS is the workspace directory (workspace/<name>). Writes stay inside it, always.

DESIGN RULES, in descending order of how much damage breaking them does:

  1. `application-log.md` is HUMAN-AUTHORED and is never regenerated. Only the fenced
     ```ascend-state block is rewritten, in place, key by key. Your retro notes, your interview
     scratch, your thank-you tracker: untouched. `workspace/` is gitignored and has no version
     history, so a regeneration bug here is unrecoverable data loss.
  2. The ledger is APPEND-ONLY. `data/status-log.tsv` gains a row per transition and is never
     edited; a correction is a new row with source=correction. Same rule as "selection, not
     invention," applied to the tracker.
  3. Files are canonical. The TSV is derived from, and reconcilable with, the markdown.
"""

import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

STATUSES = ["queued", "applied", "responded", "screen", "onsite", "offer", "rejected", "move-on"]
# Days of silence after which each state wants a nudge. Mirrors the cadence table in
# prompts/13-daily-briefing.md; that prompt is the human-facing source, this is the machine one.
CADENCE = {"applied": 7, "responded": 5, "screen": 5, "onsite": 2}
STATE_BLOCK = re.compile(r"```ascend-state\n(.*?)```", re.S)
# Pre-STATE-block workspaces wrote these as prose bullets. Keep parsing them so an existing run
# doesn't have to be migrated to benefit.
LEGACY = re.compile(r"^\s*[-*]?\s*`?(\w+)`?\s*:\s*(.*?)\s*$")


def die(msg, code=2):
    print(f"pipeline: {msg}", file=sys.stderr)
    return code


def _today(s=None):
    return datetime.strptime(s, "%Y-%m-%d").date() if s else date.today()


def job_dirs(ws):
    d = ws / "jobs"
    return sorted(p for p in d.iterdir() if p.is_dir()) if d.is_dir() else []


def find_job(ws, nn):
    """NN is the two-digit queue rank, or any unique substring of the folder name."""
    hits = [p for p in job_dirs(ws) if p.name.startswith(f"{nn}-") or nn.lower() in p.name.lower()]
    if len(hits) == 1:
        return hits[0]
    return None


def parse_state(path):
    """Read the fenced state block, falling back to legacy prose key: value lines."""
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    m = STATE_BLOCK.search(text)
    body = m.group(1) if m else text
    out = {}
    for line in body.splitlines():
        line = line.split("#", 1)[0] if m else line   # comments only inside the fenced block
        mm = LEGACY.match(line)
        if mm and mm.group(1) in ALL_KEYS:
            out[mm.group(1)] = mm.group(2).strip()
    return {k: v for k, v in out.items() if v}


ALL_KEYS = ["status", "applied_on", "last_contact_on", "next_followup_due", "next_action",
            "referral_state", "referral_contact", "referral_fallback", "referral_asked_on",
            "referral_expires_on", "screen_booked_on", "screen_with", "screen_outcome",
            "level_discussed", "comp_discussed", "work_sample"]


def write_state(path, updates):
    """Rewrite ONLY the fenced block's keys, in place. Never touches the surrounding prose."""
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    m = STATE_BLOCK.search(text)
    if not m:
        block = "\n".join(f"{k}: {updates.get(k, '')}" for k in ALL_KEYS)
        add = f"\n\n```ascend-state\n{block}\n```\n"
        path.write_text(text + add, encoding="utf-8")
        return
    lines, seen = [], set()
    for line in m.group(1).splitlines():
        mm = LEGACY.match(line.split("#", 1)[0])
        if mm and mm.group(1) in updates:
            key = mm.group(1)
            comment = line.split("#", 1)[1] if "#" in line else ""
            lines.append(f"{key}: {updates[key]}" + (f"  #{comment}" if comment else ""))
            seen.add(key)
        else:
            lines.append(line)
    for k, v in updates.items():
        if k not in seen:
            lines.append(f"{k}: {v}")
    new = "```ascend-state\n" + "\n".join(lines).rstrip() + "\n```"
    path.write_text(text[:m.start()] + new + text[m.end():], encoding="utf-8")


def append_ledger(ws, slug, when, frm, to, source, note):
    """Append-only. A correction is a new row, never an edit (design rule 2)."""
    led = ws / "data" / "status-log.tsv"
    led.parent.mkdir(parents=True, exist_ok=True)
    if not led.exists():
        led.write_text("# slug\tdate\tfrom\tto\tsource\tnote  (APPEND-ONLY: corrections are new rows)\n",
                       encoding="utf-8")
    clean = lambda s: str(s or "").replace("\t", " ").replace("\n", " ").strip() or "-"
    with led.open("a", encoding="utf-8") as fh:
        fh.write("\t".join(clean(x) for x in (slug, when, frm, to, source, note)) + "\n")


def read_ledger(ws):
    led = ws / "data" / "status-log.tsv"
    if not led.is_file():
        return []
    rows = []
    for line in led.read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) >= 4:
            rows.append(dict(zip(["slug", "date", "from", "to", "source", "note"],
                                 parts + ["-"] * (6 - len(parts)))))
    return rows


# ── commands ────────────────────────────────────────────────────────────────
def cmd_log(ws, args):
    if len(args) < 2:
        return die("usage: log WS NN STATUS [--on DATE] [--note TEXT] [--contact NAME]")
    nn, status = args[0], args[1].lower()
    if status not in STATUSES:
        return die(f"unknown status {status!r}. One of: {', '.join(STATUSES)}")
    opts = {}
    it = iter(args[2:])
    for a in it:
        if a in ("--on", "--note", "--contact"):
            opts[a.lstrip("-")] = next(it, "")
    job = find_job(ws, nn)
    if not job:
        return die(f"no unique job folder for {nn!r} under {ws / 'jobs'}")
    log = job / "application-log.md"
    if not log.is_file():
        return die(f"{log} does not exist. Build the CORE apply pack first (Phase 5).")

    cur = parse_state(log)
    prev = cur.get("status", "queued")
    when = opts.get("on") or str(date.today())
    upd = {"status": status, "last_contact_on": when}

    if status == "applied":
        upd["applied_on"] = when
    if status in CADENCE:
        due = _today(when) + timedelta(days=CADENCE[status])
        upd["next_followup_due"] = str(due)
        upd["next_action"] = {"applied": "follow up on the application",
                              "responded": "reply / schedule",
                              "screen": "post-screen status check",
                              "onsite": "send the thank-you"}[status]
    if status in ("rejected", "move-on"):
        upd["next_followup_due"] = ""
        upd["next_action"] = "closed, pick a replacement target"
    if status == "screen":
        upd["screen_booked_on"] = when
        if opts.get("contact"):
            upd["screen_with"] = opts["contact"]

    write_state(log, upd)
    append_ledger(ws, job.name, when, prev, status, "log", opts.get("note", ""))
    print(f"  {job.name}: {prev} → {status}  ({when})")
    if upd.get("next_followup_due"):
        print(f"  next follow-up due {upd['next_followup_due']}: {upd['next_action']}")
    if status in ("rejected", "move-on"):
        print("  closed. Run `/ascend rejected " + nn + "` to capture what was said and "
              "activate a replacement target.")
    return 0


def cmd_overdue(ws, args):
    today = _today(args[1] if len(args) > 1 and args[0] == "--today" else None)
    rows = []
    for job in job_dirs(ws):
        st = parse_state(job / "application-log.md")
        if not st or st.get("status") in ("rejected", "move-on", "offer"):
            continue
        due, ref_exp = st.get("next_followup_due"), st.get("referral_expires_on")
        if due:
            try:
                d = _today(due)
                if d <= today:
                    rows.append((str(d), job.name, st.get("status", "?"),
                                 st.get("next_action") or "follow up", (today - d).days))
            except ValueError:
                pass
        # A referral gate with no clock silently costs applications: reqs fill in arrival order.
        if ref_exp and st.get("referral_state") not in ("referred", "waived", "declined"):
            try:
                d = _today(ref_exp)
                if d <= today:
                    rows.append((str(d), job.name, "referral",
                                 f"referral expired ({st.get('referral_state', 'none')}), apply cold now",
                                 (today - d).days))
            except ValueError:
                pass
    rows.sort()
    if not rows:
        print("  nothing overdue.")
        return 0
    for d, slug, status, action, late in rows:
        print(f"  {d}  {slug:<44} [{status}] {action}  ({late}d late)" if late
              else f"  {d}  {slug:<44} [{status}] {action}  (due today)")
    return 0


def cmd_funnel(ws, args):
    counts = {s: 0 for s in STATUSES}
    for job in job_dirs(ws):
        st = parse_state(job / "application-log.md")
        counts[st.get("status", "queued") if st.get("status") in counts else "queued"] += 1
    # "ever reached" is the honest denominator: someone rejected after an onsite reached onsite.
    order = {s: i for i, s in enumerate(STATUSES)}
    ever = {s: 0 for s in STATUSES}
    for r in read_ledger(ws):
        if r["to"] in order:
            for s in STATUSES[:order[r["to"]] + 1]:
                ever[s] += 1
    out = {"now": counts, "ever_reached": ever, "total_jobs": len(job_dirs(ws))}
    if "--json" in args:
        print(json.dumps(out, indent=2))
        return 0
    print(f"  {out['total_jobs']} job folder(s)")
    for s in STATUSES:
        print(f"    {s:<10} now {counts[s]:>3}   ever {ever[s]:>3}")
    n = ever.get("applied", 0)
    print(f"\n  Applications sent: {n}")
    if n < 10:
        # Below n=10 a conversion rate is noise. Asserting one would be the same sin as inventing a
        # metric, which is the thing this project exists to refuse.
        print("  Too few applications to state a conversion rate honestly (need ~10). "
              "Counts only, no percentages.")
    else:
        for s in ("responded", "screen", "onsite", "offer"):
            print(f"    {s:<10} {ever[s]:>3}  =  {ever[s] / n * 100:.0f}% of applications")
        print("  A rate below your expectation is one observation, not a verdict about you. "
              "Pick ONE lever (usually referral rate, not application count) and re-check next week.")
    return 0


def cmd_show(ws, args):
    for job in job_dirs(ws):
        if args and not job.name.startswith(f"{args[0]}-") and args[0].lower() not in job.name.lower():
            continue
        st = parse_state(job / "application-log.md")
        print(f"  {job.name}")
        for k in ALL_KEYS:
            if st.get(k):
                print(f"    {k:<20} {st[k]}")
    return 0


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    cmd, ws = argv[1], Path(argv[2]).resolve()
    if not ws.is_dir():
        return die(f"workspace not found: {ws}")
    if "workspace" not in ws.parts:
        return die(f"refusing to operate outside a workspace/ directory: {ws}")
    fn = {"log": cmd_log, "overdue": cmd_overdue, "funnel": cmd_funnel, "show": cmd_show}.get(cmd)
    if not fn:
        return die(f"unknown command {cmd!r}")
    return fn(ws, argv[3:])


if __name__ == "__main__":
    sys.exit(main(sys.argv))
