#!/usr/bin/env python3
"""hub.py: the Ascend 2.0 dashboard, computed from the data files at zero tokens (M3).

  python3 tools/hub.py build WS [--json] [--today YYYY-MM-DD]

Every number on the page comes from files a tool wrote: postings and prefilter results (M5), the
queue, classified mail (M1), the status ledger (M2) and token usage (M7). Any of them may be
missing; the page shows what exists. The output is one self-contained HTML file with the data
embedded, so it opens offline and keeps the hub's `connect-src 'none'` policy: nothing on the page
can call out, and nothing needs to.

Honesty rule, same as `pipeline.py funnel`: below 10 applications a percentage is noise, so rates
are withheld and only counts are shown.
"""

import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import _v2data as d  # noqa: E402
import pipeline  # noqa: E402
from _paths import PathOutsideWorkspace, resolve_out  # noqa: E402

REPO = TOOLS.parent
TEMPLATE = REPO / "templates" / "hub.template.html"
# Valid JSON on purpose: tests/smoke.py parses every template's JSON block.
PLACEHOLDER = '{"__hub_data__": "replaced by tools/hub.py build"}'
REPLY_CATEGORIES = {"info-request", "assessment", "interview-invite", "rejection"}
PIN_CATEGORIES = {"info-request", "assessment"}
OPEN_STATUSES = {"queued", "applied", "responded"}
REPLIED_STATUSES = {"responded", "screen", "onsite", "offer", "rejected"}
INTERVIEW_STATUSES = {"screen", "onsite", "offer"}
OPEN_DECISIONS = {"matched", "needs-you", "queued"}
MIN_FOR_RATES = 10
GHOST_DAYS = 30
LOW_REPLY = 0.05


def _day(s):
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return date.fromisoformat(str(s)[:10])
        except ValueError:
            return None


def _jobs(ws):
    """slug → {nn, company, title, status} from the job folders."""
    out = {}
    for job in pipeline.job_dirs(ws):
        log = job / "application-log.md"
        text = log.read_text(encoding="utf-8") if log.is_file() else ""
        m = pipeline.LOG_HEADING.search(text)
        out[job.name] = {"nn": job.name.split("-", 1)[0], "company": m.group(1) if m else job.name,
                         "title": m.group(2) if m else "", "status": pipeline.parse_state(log).get("status", "queued")}
    return out


def _row_status(folder_status, queue_state):
    """The folder's status once the job has moved (applied, screen...). While the folder still says
    `queued`, the user's decision in the queue (approved, rejected...) is the more current fact."""
    if folder_status and folder_status != "queued":
        return folder_status
    if queue_state and queue_state != "matched":
        return queue_state
    return folder_status or queue_state or "matched"


def compute(ws, today=None):
    ws = Path(ws)
    today = _day(today) if today else date.today()
    data = ws / "data"
    jobs = _jobs(ws)
    queue = d.read_json(data / "queue.json", {}).get("jobs", [])
    by_nn = {j["nn"]: slug for slug, j in jobs.items()}
    pid_to_nn = {q.get("posting_id"): q.get("nn") for q in queue if q.get("nn")}
    events = d.read_jsonl(data / "events.jsonl")
    ledger = pipeline.read_ledger(ws)

    def slug_for(match):
        nn = match if match in by_nn else pid_to_nn.get(match)
        return by_nn.get(nn) if nn else None

    # Applied: any job that left `queued`, by the ledger or by its own state block.
    applied_on = {}
    for r in sorted(ledger, key=lambda r: r["date"]):
        if r["to"] not in ("queued", "move-on") and r["slug"] not in applied_on:
            applied_on[r["slug"]] = _day(r["date"])
    for slug, j in jobs.items():
        if j["status"] not in ("queued", "move-on") and slug not in applied_on:
            applied_on[slug] = None
    reached = {}
    for r in ledger:
        reached.setdefault(r["slug"], set()).add(r["to"])
    for slug, j in jobs.items():
        reached.setdefault(slug, set()).add(j["status"])
    reply_slugs = {slug_for(e.get("match")) for e in events if e.get("category") in REPLY_CATEGORIES} - {None}
    replied = {s for s in applied_on if s in reply_slugs or reached.get(s, set()) & REPLIED_STATUSES}
    interview_slugs = {slug_for(e.get("match")) for e in events if e.get("category") == "interview-invite"} - {None}
    interviewing = {s for s in jobs if reached.get(s, set()) & INTERVIEW_STATUSES or s in interview_slugs}
    offers = {s for s in jobs if "offer" in reached.get(s, set())}

    postings = {p.get("id") for p in d.read_jsonl(data / "postings.jsonl")}
    latest = {}
    for c in d.read_jsonl(data / "candidates.jsonl"):     # append-only: the last row is the current verdict
        latest[c.get("posting_id")] = c.get("passed")
    screened = {pid for pid, ok in latest.items() if ok}
    funnel = [{"stage": s, "count": n} for s, n in [
        ("found", len(postings - {None})), ("screened", len(screened - {None})), ("matched", len(queue)),
        ("applied", len(applied_on)), ("replied", len(replied)), ("interviewing", len(interviewing)),
        ("offer", len(offers))]]

    week_start = today - timedelta(days=6)
    in_week = lambda day: day is not None and week_start <= day <= today  # noqa: E731
    def distinct(categories):
        # A reminder and an availability request about one interview are one interview: count jobs,
        # and count unmatched mail per message since there is no job to collapse it into.
        keys = {slug_for(e.get("match")) or ("msg", e.get("msg_id")) for e in events
                if e.get("category") in categories and in_week(_day(e.get("date")))}
        return len(keys)

    week = {"applied": len({r["slug"] for r in ledger if r["to"] == "applied" and in_week(_day(r["date"]))}),
            "replies": distinct(REPLY_CATEGORIES), "interviews": distinct({"interview-invite"})}

    n = len(applied_on)
    rates, warning = {"reply": None, "ghost": None}, None
    if n >= MIN_FOR_RATES:
        ghosted = [s for s, day in applied_on.items()
                   if s not in replied and day is not None and (today - day).days >= GHOST_DAYS]
        rates = {"reply": round(len(replied) / n, 3), "ghost": round(len(ghosted) / n, 3)}
        if rates["reply"] < LOW_REPLY:
            warning = (f"Your reply rate is {rates['reply'] * 100:.0f}% across {n} applications. That is one "
                       "observation, not a verdict. The usual lever is fit: fewer, closer-matched roles, and "
                       "a referral before applying where one exists.")

    def label(slug):
        if not slug:
            return None
        j = jobs[slug]
        return f"{j['nn']} {j['company']}"

    mail = {m.get("msg_id"): m for m in d.read_jsonl(data / "mail.jsonl")}
    inbox, pinned = [], []
    for e in sorted(events, key=lambda e: e.get("date") or "", reverse=True):
        slug = slug_for(e.get("match"))
        m = mail.get(e.get("msg_id"), {})
        row = {"msg_id": e.get("msg_id"), "category": e.get("category"),
               "subject": e.get("subject") or m.get("subject", ""), "from": e.get("from") or m.get("from", ""), "date": (e.get("date") or "")[:10], "job": label(slug),
               "due": e.get("due"), "needs_llm": bool(e.get("needs_llm")),
               "gmail_url": f"https://mail.google.com/mail/u/0/#all/{e.get('msg_id')}"}
        inbox.append(row)
        # Pinned until the job moves past `responded`: that is the leak this pin exists to close.
        if row["category"] in PIN_CATEGORIES and row["due"] and (not slug or jobs[slug]["status"] in OPEN_STATUSES):
            pinned.append(row)
    pinned.sort(key=lambda i: i["due"])

    rows = []
    for q in queue:
        slug = by_nn.get(q.get("nn"))
        rows.append({"nn": q.get("nn"), "posting_id": q.get("posting_id"), "company": q.get("company"),
                     "title": q.get("title"), "fit": q.get("fit"), "why": q.get("why"), "gaps": q.get("gaps") or [],
                     "status": _row_status(jobs[slug]["status"] if slug else None, q.get("state")),
                     "url": q.get("url") or q.get("posting_id"), "source": q.get("source"),
                     "reasons": q.get("reasons") or []})
    # Open decisions first, best fit first: a job not yet applied to (matched, needs-you, or a v1 folder
    # still `queued`) is waiting on the user. Everything else after, also by fit.
    rows.sort(key=lambda r: (r["status"] not in OPEN_DECISIONS, -(r["fit"] or 0)))

    usage = d.read_jsonl(data / "usage.jsonl")
    tokens = None
    if usage:
        by_stage = {}
        for u in usage:
            by_stage[u.get("stage", "?")] = by_stage.get(u.get("stage", "?"), 0) + \
                int(u.get("input_tokens", 0) or 0) + int(u.get("output_tokens", 0) or 0)
        tokens = {"by_stage": by_stage, "total": sum(by_stage.values())}

    defaults = d.read_json(ws / ".ascend-state.json", {}).get("run_defaults")
    run = None
    if defaults:
        import usage
        run = dict(defaults, estimate=usage.estimate(ws, defaults["engine"], defaults["mode"]))
    control = d.read_json(data / "apply-control.json", {"paused": False})
    return {"as_of": today.isoformat(), "run": run, "apply_control": control, "funnel": funnel, "week": week, "rates": rates, "warning": warning,
            "inbox": inbox, "pinned": pinned, "queue": rows, "tokens": tokens}


def render(ws, today=None, server=None):
    """The hub page as a string. `server` ({"token", "slug"}) is set only when ui/server.py serves it:
    that version may call back to the local server (connect-src 'self') to approve or reject jobs.
    The file written by build() has no token and connect-src 'none', so it can only be read."""
    data = compute(ws, today)
    if server:
        data["server"] = server
    # JSON inside <script>: escape <, > and & so no value (an email subject, say) can close the
    # block or open a tag. JSON.parse reads the < escape back as "<"; the HTML parser never sees it.
    blob = json.dumps(data, ensure_ascii=False).replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")
    html = TEMPLATE.read_text(encoding="utf-8").replace(PLACEHOLDER, blob)
    if PLACEHOLDER in html or blob not in html:
        raise RuntimeError("hub template is missing its data placeholder")
    if server:
        html = html.replace("connect-src 'none'", "connect-src 'self'", 1)
    return html


def build(ws, today=None):
    """Write ws/hub.html with the computed data embedded. Returns the path."""
    out = resolve_out(str(Path(ws) / "hub.html"))
    out.write_text(render(ws, today), encoding="utf-8")
    return out


def main(argv):
    if len(argv) < 3 or argv[1] != "build" or argv[2].startswith("--"):
        print(__doc__, file=sys.stderr)
        return 2
    args = argv[3:]
    today = args[args.index("--today") + 1] if "--today" in args and args.index("--today") + 1 < len(args) else None
    try:
        if "--json" in args:
            resolve_out(str(Path(argv[2]) / "hub.html"))
            print(json.dumps(compute(argv[2], today)))
            return 0
        print(build(argv[2], today))
    except PathOutsideWorkspace as e:
        print(f"hub: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
