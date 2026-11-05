#!/usr/bin/env python3
"""jobqueue.py: the scored queue the user approves from (Ascend 2.0, M7).

  python3 tools/jobqueue.py candidates WS [--limit N]          # survivors waiting for a score (compact JSON)
  python3 tools/jobqueue.py score WS POSTING_ID --fit N --why TEXT [--gaps "a; b"]
  python3 tools/jobqueue.py gaps WS [--floor 3]        # which gap recurs across the scored queue
  python3 tools/jobqueue.py set-state WS POSTING_ID STATE
  python3 tools/jobqueue.py list WS

Named jobqueue, not queue: a tools/queue.py would shadow the standard library module that
concurrent.futures and http.server import.

`candidates` is where the scoring stage's token budget is set: each survivor is trimmed to the fields a
fit judgement needs and the first 1,500 characters of the posting.
"""

import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import _v2data as d  # noqa: E402
import _untrusted  # noqa: E402

STATES = ["matched", "approved", "rejected", "needs-you", "applying", "applied", "applied?", "inbound-filtered"]
SENT = {"applying", "applied", "applied?"}       # once sent, a job only moves on to applied
HUB_ONLY = {"approved", "applied"}               # the user's own click in the hub, never a CLI call
TEXT_BUDGET = 1500
# Most postings open with paragraphs about the company. The budget goes to the role instead: start at
# the first heading that introduces it. Found on a real run, where the first 1,500 characters of
# Affirm's and Twilio's postings were entirely company boilerplate.
ROLE_START = re.compile(r"(about the role|about this role|the role\b|in this role|what you('|’)ll do|"
                        r"what you will do|responsibilities|your impact|you will:|the opportunity)", re.I)


def _queue(ws):
    return d.read_json(Path(ws) / "data" / "queue.json", {"jobs": []})


# A board slug is often the company name plus a region or corporate suffix (doordashusa, acmehq).
SLUG_SUFFIXES = ("usa", "us", "hq", "inc", "jobs", "careers", "global", "labs", "io", "ai", "co", "corp", "group")


def same_company(a, b):
    import pipeline
    from prefilter import company_key
    return pipeline._same_company_key(company_key(a), company_key(b))


def role_key(company, title):
    import pipeline
    from prefilter import company_key
    return f"{company_key(company)}|{pipeline.normalize_title(title)}"


def age_days(posted_on):
    """Days since the BOARD said the role went up, or None when the board gave no date.

    None is not zero. A posting with no date is unknown age, and the one thing worse than not
    knowing is treating unknown as fresh — which is what `first_seen` did, since on a workspace's
    first run every posting was "first seen today" including a 90-day-old requisition.
    """
    if not posted_on:
        return None
    try:
        return (date.today() - date.fromisoformat(str(posted_on)[:10])).days
    except ValueError:
        return None


def _age_key(posted_on):
    """Sort key: fresher first, unknown age last (never ahead of a known-fresh posting)."""
    a = age_days(posted_on)
    return (1, 0) if a is None else (0, a)


def role_text(text):
    m = ROLE_START.search(text or "")
    return (text or "")[m.start():] if m else (text or "")


def servable_text(text, findings):
    """The last seam before posting text reaches the model: de-smuggle, THEN trim to budget.

    `finder.clean` already does this for board rows, but not every row came from a board:
    `finder.py add --source web|linkedin` ingests rows the model wrote, and postings.jsonl holds
    rows written before this check existed. Doing it here too means every row is covered whatever
    wrote it, and the order matters — a smuggled payload is one invisible code point per character,
    so trimming to TEXT_BUDGET first would let it keep eating the allowance the scorer is given.
    """
    clean, f = _untrusted.clean_untrusted(text or "", is_html=False)
    findings.extend(f)
    return role_text(clean)[:TEXT_BUDGET]


def candidates(ws, limit=25):
    dd = Path(ws) / "data"
    jobs = _queue(ws).get("jobs", [])
    queued = {j.get("posting_id") for j in jobs}
    # The same role can reach the queue under two IDs (a URL from an earlier run, a board ID from the
    # finder). Match on company + normalized title too, so it is never scored or applied to twice.
    import pipeline
    queued_roles = [(j.get("company"), pipeline.normalize_title(j.get("title"))) for j in jobs]

    def already_queued(p):
        t = pipeline.normalize_title(p.get("title"))
        return any(t == qt and same_company(p.get("company"), qc) for qc, qt in queued_roles)
    latest = {}
    for c in d.read_jsonl(dd / "candidates.jsonl"):
        latest[c.get("posting_id")] = c
    posts = {p.get("id"): p for p in d.read_jsonl(dd / "postings.jsonl")}
    closed = {pid for pid, st in d.read_json(dd / "postings-state.json", {}).items() if st.get("closed")}
    rows = [(c, posts[pid]) for pid, c in latest.items() if c.get("passed") and pid not in queued and pid in posts
            and pid not in closed and not already_queued(posts[pid])]
    # Overlap first, then FRESHNESS as the tie-break. `reference/ats-and-keywords.md` says
    # recruiters review in arrival order and to apply early; before posted_on was captured there was
    # nothing to sort on, so two equally-matched roles were ordered arbitrarily and a 90-day-old
    # requisition could outrank one posted yesterday. Unknown dates sort last, never first.
    rows.sort(key=lambda r: (-r[0].get("keyword_overlap", 0), _age_key(r[1].get("posted_on"))))
    findings = []
    out = [{"posting_id": p["id"], "company": p.get("company"), "title": p.get("title"), "location": p.get("location"),
            "comp": [p.get("comp_min"), p.get("comp_max")], "keyword_overlap": c.get("keyword_overlap"),
            "url": p.get("url"), "posted_on": p.get("posted_on"), "age_days": age_days(p.get("posted_on")),
            "text": servable_text(p.get("text"), findings)} for c, p in rows[:limit]]
    if findings:
        print("  " + _untrusted.summarize(findings), file=sys.stderr)
    return out


def score(ws, posting_id, fit, why, gaps):
    fit = int(fit)
    if not 0 <= fit <= 100:
        raise ValueError("fit must be 0 to 100")
    dd = d.data_dir(ws)
    post = next((p for p in d.read_jsonl(dd / "postings.jsonl") if p.get("id") == posting_id), {})

    def change(q):
        entry = next((j for j in q.setdefault("jobs", []) if j.get("posting_id") == posting_id), None)
        if entry is None:
            entry = {"posting_id": posting_id, "company": post.get("company"), "title": post.get("title"),
                     "url": post.get("url"), "apply_url": post.get("apply_url"), "state": "matched"}
            q["jobs"].append(entry)
        entry.update(fit=fit, why=why, gaps=list(gaps), scored_at=datetime.now().isoformat(timespec="seconds"))
        return entry
    return d.update_json(dd / "queue.json", {"jobs": []}, change)


def set_state(ws, posting_id, state, **fields):
    """The one way a queue entry changes state. Extra fields (stop_reason) are written in the same locked update."""
    if state not in STATES:
        raise ValueError(f"unknown state {state!r}; one of {', '.join(STATES)}")
    dd = d.data_dir(ws)

    def change(q):
        entry = next((j for j in q.get("jobs", []) if j.get("posting_id") == posting_id), None)
        if entry is None:
            raise KeyError(posting_id)
        if entry.get("state") in SENT and state != "applied":
            raise ValueError(f"{entry.get('company')} is {entry.get('state')}: a sent application cannot move back to {state}")
        entry.update(fields, state=state)
        if state == "applied" and not entry.get("applied_on"):
            entry["applied_on"] = date.today().isoformat()
        return dict(entry)
    entry = d.update_json(dd / "queue.json", {"jobs": []}, change)
    if state == "applied" and entry.get("nn"):
        # A v1 job folder records the same fact; keep the two in step through the one write path.
        import pipeline
        job = pipeline.find_job(Path(ws), entry["nn"])
        if job and pipeline.parse_state(job / "application-log.md").get("status", "queued") == "queued":
            pipeline.transition(Path(ws), job, "applied", entry["applied_on"], "apply")
    return entry


def recurring_gaps(ws, floor=3):
    """Which gap shows up across the scored queue, counted from gaps already on disk.

    `score ... --gaps` has always stored a per-job gap list; nothing ever counted one term across
    jobs, so "the thing that keeps costing me" was invisible while being fully recorded. This is a
    Counter over existing data: no new field, no model call, no new op.

    Deliberately NOT a heatmap, a tier list or a study plan with hour estimates. An hour estimate
    for learning something is a fabricated number, which `reference/number-and-honesty-policy.md`
    forbids, and a gap plan is the most comfortable-feeling work in a job search: it looks like
    progress, it is entirely within the candidate's control, and it displaces applying. So: count,
    rank, cite the jobs, stop. Surfaced only at `floor` occurrences, because one posting wanting
    Kubernetes is not a pattern.

    A named gap also rarely decides a SCREEN — the screen turns on whether the résumé matched the
    search and whether anyone vouched. Gaps decide loops, which is `prompts/10-deep-prep.md`'s job,
    per job, after a screen passes.
    """
    counts, where = {}, {}
    for j in _queue(ws).get("jobs", []):
        seen = set()
        for g in j.get("gaps") or []:
            key = " ".join(str(g).lower().split())
            if not key or key in seen:
                continue
            seen.add(key)
            counts[key] = counts.get(key, 0) + 1
            where.setdefault(key, []).append(j.get("posting_id"))
    scored = sum(1 for j in _queue(ws).get("jobs", []) if j.get("gaps") is not None)
    rows = [{"gap": k, "count": v, "of_scored": scored, "jobs": where[k][:6]}
            for k, v in counts.items() if v >= floor]
    rows.sort(key=lambda r: (-r["count"], r["gap"]))
    return {"scored_jobs": scored, "floor": floor, "recurring": rows}


def _opt(args, name, default=None):
    return args[args.index(name) + 1] if name in args and args.index(name) + 1 < len(args) else default


def main(argv):
    if len(argv) < 3 or argv[1] not in ("candidates", "score", "set-state", "list", "gaps"):
        print(__doc__, file=sys.stderr)
        return 2
    cmd, ws, args = argv[1], argv[2], argv[3:]
    try:
        if cmd == "candidates":
            out = candidates(ws, int(_opt(args, "--limit", 25)))
        elif cmd == "list":
            out = _queue(ws).get("jobs", [])
        elif cmd == "gaps":
            out = recurring_gaps(ws, int(_opt(args, "--floor", 3)))
        elif cmd == "score":
            gaps = [g.strip() for g in (_opt(args, "--gaps", "") or "").split(";") if g.strip()]
            out = score(ws, args[0], _opt(args, "--fit"), _opt(args, "--why", ""), gaps)
        else:
            if args[1] in HUB_ONLY | SENT:
                raise ValueError(f"{args[1]} is set by you in the hub's Queue tab, not from the command line")
            out = set_state(ws, args[0], args[1])
    except (ValueError, KeyError, IndexError) as e:
        print(f"jobqueue: {e}", file=sys.stderr)
        return 2
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
