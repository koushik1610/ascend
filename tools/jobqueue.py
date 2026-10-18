#!/usr/bin/env python3
"""jobqueue.py: the scored queue the user approves from (Ascend 2.0, M7).

  python3 tools/jobqueue.py candidates WS [--limit N]          # survivors waiting for a score (compact JSON)
  python3 tools/jobqueue.py score WS POSTING_ID --fit N --why TEXT [--gaps "a; b"]
  python3 tools/jobqueue.py score WS --file SCORES.json             # [{"posting_id", "fit", "why", "gaps": [..]}]
  python3 tools/jobqueue.py set-state WS POSTING_ID STATE
  python3 tools/jobqueue.py link WS POSTING_ID NN                     # after Phase 5 builds the job's folder
  python3 tools/jobqueue.py sync WS                                   # bring v1 job folders into the queue
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


from classify import SLUG_SUFFIXES  # noqa: E402,F401  (pipeline._same_company_key reads it from here)


def same_company(a, b):
    import pipeline
    from prefilter import company_key
    return pipeline._same_company_key(company_key(a), company_key(b))


def role_key(company, title):
    import pipeline
    from prefilter import company_key
    return f"{company_key(company)}|{pipeline.normalize_title(title)}"


def role_text(text):
    m = ROLE_START.search(text or "")
    return (text or "")[m.start():] if m else (text or "")


def _same_role(company_a, title_a, company_b, title_b):
    import pipeline
    return same_company(company_a, company_b) and pipeline.normalize_title(title_a) == pipeline.normalize_title(title_b)


def sync_folders(ws):
    """Bring every v1 job folder into the queue, linked by `nn`, so mail matching, the duplicate check and
    the apply sheet all see the user's live applications. A folder joins the entry for the same posting
    (its JD link) or the same company and title; otherwise it gets its own entry. A folder past "queued"
    was sent, so its entry is applied. Safe to run any number of times."""
    import pipeline
    from finder import ats_id
    ws = Path(ws)
    folders = []
    for job in pipeline.job_dirs(ws):
        nn = job.name.split("-", 1)[0]
        if not re.fullmatch(r"\d{2,3}", nn) or pipeline.job_folder(ws, nn) is None:
            continue
        company, title, url, fit, status = pipeline.folder_job(job)
        if company and title:
            folders.append((nn, company, title, url, fit, status))
    out = {"added": 0, "linked": 0}
    if not folders:
        return out

    def change(q):
        jobs = q.setdefault("jobs", [])
        for nn, company, title, url, fit, status in folders:
            sent = status != "queued"
            pid = ats_id(url) or f"v1:{nn}"
            entry = next((j for j in jobs if j.get("nn") == nn), None)
            if entry is None:
                entry = next((j for j in jobs if not j.get("nn") and (j.get("posting_id") == pid or
                              _same_role(j.get("company"), j.get("title"), company, title))), None)
                if entry is not None:
                    entry["nn"] = nn
                    out["linked"] += 1
            if entry is None:
                entry = {"posting_id": pid, "company": company, "title": title, "url": url, "apply_url": url,
                         "nn": nn, "state": "matched", "source": "v1", "fit": fit,
                         "why": "Your job folder from an earlier Ascend run."}
                jobs.append(entry)
                out["added"] += 1
            if sent and entry.get("state") not in SENT:
                entry["state"] = "applied"
        return out
    d.update_json(Path(ws) / "data" / "queue.json", {"jobs": []}, change)
    return out


def link(ws, posting_id, nn):
    """Point a queue entry at the job folder Phase 5 built for it. The folder must exist under exactly
    that number and be for the same company and title: a wrong link would send another role's résumé."""
    import pipeline
    job = pipeline.job_folder(ws, nn)
    if job is None:
        raise ValueError(f"no job folder numbered {nn!r} (use the two-digit number at the start of its name)")
    company, title, *_ = pipeline.folder_job(job)

    def change(q):
        entry = next((j for j in q.get("jobs", []) if j.get("posting_id") == posting_id), None)
        if entry is None:
            raise KeyError(posting_id)
        if not _same_role(entry.get("company"), entry.get("title"), company, title):
            raise ValueError(f"{job.name} is for {company}, {title}: a different role from "
                             f"{entry.get('company')}, {entry.get('title')}")
        other = next((j for j in q["jobs"] if j.get("nn") == nn and j is not entry), None)
        if other is not None:
            raise ValueError(f"{job.name} is already linked to {other.get('posting_id')}")
        entry["nn"] = nn
        return dict(entry)
    return d.update_json(Path(ws) / "data" / "queue.json", {"jobs": []}, change)


def candidates(ws, limit=25):
    dd = Path(ws) / "data"
    sync_folders(ws)
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
    rows.sort(key=lambda r: -r[0].get("keyword_overlap", 0))
    return [{"posting_id": p["id"], "company": p.get("company"), "title": p.get("title"), "location": p.get("location"),
             "comp": [p.get("comp_min"), p.get("comp_max")], "keyword_overlap": c.get("keyword_overlap"),
             "url": p.get("url"), "text": role_text(p.get("text"))[:TEXT_BUDGET]} for c, p in rows[:limit]]


def score(ws, posting_id, fit, why, gaps):
    fit = int(fit)
    if not 0 <= fit <= 100:
        raise ValueError("fit must be 0 to 100")
    dd = d.data_dir(ws)
    post = next((p for p in d.read_jsonl(dd / "postings.jsonl") if p.get("id") == posting_id), None)
    queued = any(j.get("posting_id") == posting_id for j in _queue(ws).get("jobs", []))
    if post is None and not queued:
        raise KeyError(f"{posting_id} is not a known posting (take IDs from `candidates`)")
    post = post or {}

    def change(q):
        entry = next((j for j in q.setdefault("jobs", []) if j.get("posting_id") == posting_id), None)
        if entry is None:
            entry = {"posting_id": posting_id, "company": post.get("company"), "title": post.get("title"),
                     "url": post.get("url"), "apply_url": post.get("apply_url"), "state": "matched"}
            q["jobs"].append(entry)
        entry.update(fit=fit, why=why, gaps=list(gaps), scored_at=datetime.now().isoformat(timespec="seconds"))
        return entry
    return d.update_json(dd / "queue.json", {"jobs": []}, change)


def set_state(ws, posting_id, state, via_hub=False, **fields):
    """The one way a queue entry changes state. Extra fields (stop_reason) are written in the same locked update.
    Approved and applied are the user's click: only the hub's server passes via_hub."""
    if state not in STATES:
        raise ValueError(f"unknown state {state!r}; one of {', '.join(STATES)}")
    if (state in HUB_ONLY or state in SENT) and not via_hub:
        raise ValueError(f"{state} is set by you in the hub's Queue tab, not from the command line")
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
        job = pipeline.job_folder(Path(ws), entry["nn"])
        if job and pipeline.parse_state(job / "application-log.md").get("status", "queued") == "queued":
            pipeline.transition(Path(ws), job, "applied", entry["applied_on"], "apply")
    return entry


def _opt(args, name, default=None):
    return args[args.index(name) + 1] if name in args and args.index(name) + 1 < len(args) else default


def main(argv):
    if len(argv) < 3 or argv[1] not in ("candidates", "score", "set-state", "link", "sync", "list"):
        print(__doc__, file=sys.stderr)
        return 2
    cmd, ws, args = argv[1], argv[2], argv[3:]
    try:
        if cmd == "candidates":
            out = candidates(ws, int(_opt(args, "--limit", 25)))
        elif cmd == "list":
            out = _queue(ws).get("jobs", [])
        elif cmd == "score" and "--file" in args:
            # Model-written text read from a file, never through the shell, where "$(...)" would expand.
            rows = json.loads(Path(_opt(args, "--file")).read_text(encoding="utf-8"))
            out = [score(ws, r["posting_id"], r["fit"], r.get("why", ""),
                         [g for g in (r.get("gaps") or []) if str(g).strip()]) for r in rows]
            out = {"scored": len(out)}
        elif cmd == "score":
            gaps = [g.strip() for g in (_opt(args, "--gaps", "") or "").split(";") if g.strip()]
            out = score(ws, args[0], _opt(args, "--fit"), _opt(args, "--why", ""), gaps)
        elif cmd == "link":
            out = link(ws, args[0], args[1])
        elif cmd == "sync":
            out = sync_folders(ws)
        else:
            out = set_state(ws, args[0], args[1])
    except (ValueError, KeyError, IndexError, json.JSONDecodeError, OSError) as e:
        print(f"jobqueue: {e}", file=sys.stderr)
        return 2
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
