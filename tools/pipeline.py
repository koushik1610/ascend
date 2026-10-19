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
  python3 tools/pipeline.py ingest  WS [--json]      # Ascend 2.0: classified mail → status changes
  python3 tools/pipeline.py guard   WS --company C --title T [--posting-id P]   # exit 3 = duplicate

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


def job_folder(ws, nn):
    """The folder whose name starts with exactly `NN-`, else None. Never a substring: a link that could
    land on another role's folder would attach that role's résumé to this application."""
    if not re.fullmatch(r"\d{2,3}", str(nn or "")):
        return None
    hits = [p for p in job_dirs(Path(ws)) if p.name.split("-", 1)[0] == str(nn)]
    return hits[0] if len(hits) == 1 else None


def folder_job(job):
    """(company, title, jd_url, fit, status) read from a v1 job folder's application log."""
    log = job / "application-log.md"
    text = log.read_text(encoding="utf-8") if log.is_file() else ""
    m = LOG_HEADING.search(text)
    url = re.search(r"^\|\s*JD\s*\|\s*(https://[^\s|]+)", text, re.M)
    fit = re.search(r"^\|\s*Fit Score\s*\|\s*(\d{1,3})\s*/\s*100", text, re.M)
    return (m.group(1).strip() if m else None, m.group(2).strip() if m else None, url.group(1) if url else None,
            int(fit.group(1)) if fit else None, parse_state(log).get("status", "queued"))


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
            "level_discussed", "comp_discussed", "work_sample", "offer_deadline"]


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


def transition(ws, job, status, when, source, note="", opts=None):
    """Move one job to `status` on `when`: rewrite its state block, append a ledger row.

    The single write path for a status change. `log` (a person typing) and `ingest` (Gmail) both
    come through here, so the cadence, the follow-up dates and the ledger row are identical no matter
    who recorded the event. Returns (previous_status, the state keys written).
    """
    opts = opts or {}
    log = job / "application-log.md"
    cur = parse_state(log)
    prev = cur.get("status", "queued")
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
    if status == "offer" and opts.get("deadline"):
        # The highest-stakes clock in a search, and it used to have nowhere to go: `offer` is not in
        # CADENCE, so `log` wrote no next_followup_due, and cmd_overdue skipped offer-status jobs
        # outright. A Monday offer with a Friday deadline surfaced on no daily brief at all.
        upd["offer_deadline"] = opts["deadline"]
    if status == "screen":
        upd["screen_booked_on"] = when
        if opts.get("contact"):
            upd["screen_with"] = opts["contact"]

    write_state(log, upd)
    append_ledger(ws, job.name, when, prev, status, source, note)
    return prev, upd


# ── commands ────────────────────────────────────────────────────────────────
def cmd_log(ws, args):
    if len(args) < 2:
        return die("usage: log WS NN STATUS [--on DATE] [--note TEXT] [--contact NAME] "
                   "[--deadline DATE]")
    nn, status = args[0], args[1].lower()
    if status not in STATUSES:
        return die(f"unknown status {status!r}. One of: {', '.join(STATUSES)}")
    opts = {}
    it = iter(args[2:])
    for a in it:
        if a in ("--on", "--note", "--contact", "--deadline"):
            opts[a.lstrip("-")] = next(it, "")
    job = find_job(ws, nn)
    if not job:
        return die(f"no unique job folder for {nn!r} under {ws / 'jobs'}")
    log = job / "application-log.md"
    if not log.is_file():
        return die(f"{log} does not exist. Build the CORE apply pack first (Phase 5).")

    when = opts.get("on") or str(date.today())
    prev, upd = transition(ws, job, status, when, "log", opts.get("note", ""), opts)
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
        if not st or st.get("status") in ("rejected", "move-on"):
            continue
        # An offer's deadline is the one date that cannot be missed, so it is reported regardless of
        # how far out it is — not only once it has already passed.
        if st.get("status") == "offer":
            dl = st.get("offer_deadline")
            if dl:
                try:
                    d = _today(dl)
                    rows.append((str(d), job.name, "offer",
                                 "OFFER DEADLINE - decide or ask for an extension "
                                 "(`/ascend offers`)", (today - d).days))
                except ValueError:
                    pass
            else:
                rows.append((str(today), job.name, "offer",
                             "offer logged with no deadline - ask for the date, then "
                             "`log <NN> offer --deadline YYYY-MM-DD`", 0))
            continue
        due, ref_exp = st.get("next_followup_due"), st.get("referral_expires_on")
        # A work sample the target set rewards is a pre-application blocker. The field existed and
        # nothing read it, so setting `work_sample: building` was invisible to every surface.
        if st.get("work_sample") in ("none", "building") and st.get("status") != "queued":
            rows.append((str(today), job.name, st.get("status", "?"),
                         f"work sample {st['work_sample']} - the loop rewards an artifact "
                         "(`/ascend work-sample`)", 0))
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
        # An offer deadline is reported before it lands, so the row can legitimately be in the
        # future. "-3d late" read as a bug; say "in 3d".
        when = f"{late}d late" if late > 0 else ("due today" if late == 0 else f"in {-late}d")
        print(f"  {d}  {slug:<44} [{status}] {action}  ({when})")
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


# ── ingest: Gmail events → status transitions (Ascend 2.0, M2) ───────────────
# What each classified email means for the job it is about. Categories not listed (status updates,
# recruiter inbound, job alerts, other) are information, not a change of state.
EVENT_STATUS = {"acknowledgement": "applied", "info-request": "responded", "assessment": "responded",
                "interview-invite": "screen", "rejection": "rejected"}
TERMINAL = {"offer", "rejected", "move-on"}
DUE_ACTION = {"info-request": "answer the info request", "assessment": "complete the assessment"}


def _job_for_match(ws, match, queue):
    """An event's `match` is a job folder's NN, or a posting ID that queue.json maps to an NN."""
    if not match:
        return None
    nn = match
    if not re.fullmatch(r"\d{2,3}", str(match)):
        nn = next((j.get("nn") for j in queue if j.get("posting_id") == match and j.get("nn")), None)
    return job_folder(ws, nn) if nn else None


def cmd_ingest(ws, args):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import _v2data as d
    data = ws / "data"
    from classify import latest_events, match_detail
    import jobqueue
    jobqueue.sync_folders(ws)          # job folders from earlier runs are jobs mail can be about
    # Keyed by message AND category: a model's later resolution of an already-ingested message (rule
    # said "other", the model says "interview-invite") is a new fact and must be applied.
    rows = d.read_jsonl(data / "ingested.jsonl")
    done = {r["key"] for r in rows if r.get("key")} | {r.get("msg_id") for r in rows if not r.get("key")}
    queue = d.read_json(data / "queue.json", {}).get("jobs", [])
    mail = {m.get("msg_id"): m for m in d.read_jsonl(data / "mail.jsonl")}
    order = {s: i for i, s in enumerate(STATUSES)}
    out = {"applied": 0, "skipped": 0, "unmatched": 0, "transitions": []}

    def key(e):
        return f"{e.get('msg_id')}|{e.get('category')}"

    events = sorted((e for e in latest_events(d.read_jsonl(data / "events.jsonl"))
                     if key(e) not in done and (e.get("rule") == "model" or e.get("msg_id") not in done)),
                    key=lambda e: e.get("date") or "")
    for e in events:
        target = EVENT_STATUS.get(e.get("category"))
        if not target:
            d.append_jsonl(data / "ingested.jsonl", {"msg_id": e.get("msg_id"), "key": key(e)})
            out["skipped"] += 1
            continue
        when = (e.get("date") or "")[:10]
        if not e.get("match") and e.get("msg_id") in mail:
            # Mail is classified when it arrives, often before its job is in the queue. Match it again, but
            # only against applications already sent by the mail's date: mail about an application cannot
            # predate it, and a job queued later must never inherit an older stranger's reply.
            sent = [j for j in queue if j.get("state") in BLOCKING and (not j.get("applied_on") or not when
                                                                         or j["applied_on"] <= when)]
            e = dict(e)
            e["match"], e["match_by"] = match_detail(mail[e["msg_id"]], sent)
        job = _job_for_match(ws, e.get("match"), queue)
        if not job or not (job / "application-log.md").is_file():
            out["unmatched"] += 1
            # Retried on later runs while the job may still be queued; after RETRY_DAYS it never will be
            # (an application made outside Ascend), so stop.
            if when and when < (date.today() - timedelta(days=RETRY_DAYS)).isoformat():
                d.append_jsonl(data / "ingested.jsonl", {"msg_id": e.get("msg_id"), "key": key(e), "unmatched": True})
            continue
        d.append_jsonl(data / "ingested.jsonl", {"msg_id": e.get("msg_id"), "key": key(e)})
        cur = parse_state(job / "application-log.md").get("status", "queued")
        # A company named only in the body is too weak to close a job: the hub still shows the mail.
        if target in TERMINAL and e.get("match_by") == "body":
            out["skipped"] += 1
            continue
        if cur in TERMINAL or (target != "rejected" and order[target] <= order.get(cur, 0)):
            out["skipped"] += 1
            continue
        when = (e.get("date") or str(date.today()))[:10]
        prev, _ = transition(ws, job, target, when, "gmail", f"{e.get('category')} {e.get('msg_id')}")
        if e.get("due") and e.get("category") in DUE_ACTION:
            write_state(job / "application-log.md",
                        {"next_followup_due": e["due"], "next_action": DUE_ACTION[e["category"]]})
        out["applied"] += 1
        out["transitions"].append({"job": job.name, "from": prev, "to": target, "on": when,
                                   "msg_id": e.get("msg_id")})
    if "--json" in args:
        print(json.dumps(out))
    else:
        print(f"  ingested {len(events)} event(s): {out['applied']} status change(s), "
              f"{out['unmatched']} not matched to a job, {out['skipped']} informational or no-op")
        for t in out["transitions"]:
            print(f"    {t['job']}: {t['from']} → {t['to']}  ({t['on']})")
    return 0


RETRY_DAYS = 30


# ── guard: never apply to the same job twice (Ascend 2.0, M2) ────────────────
GUARD_DAYS = 60
BLOCKING = {"applied", "applying", "applied?"}
TITLE_SYNONYMS = {"sr": "senior", "jr": "junior", "eng": "engineer", "engr": "engineer", "mgr": "manager",
                  "mgmt": "management", "sec": "security"}
TITLE_NOISE = {"remote", "hybrid", "onsite", "us", "usa", "the"}
LOG_HEADING = re.compile(r"^#\s*Application Log:\s*(.+?),\s*(.+?)\s*$", re.M)


def normalize_title(t):
    """'Sr. Staff Security Eng (Remote)' and 'Senior Staff Security Engineer' compare equal."""
    t = re.sub(r"\(.*?\)", " ", (t or "").lower())
    words = [TITLE_SYNONYMS.get(w, w) for w in re.findall(r"[a-z0-9]+", t)]
    return " ".join(w for w in words if w not in TITLE_NOISE)


def _company_key(name):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from classify import company_tokens
    return "".join(company_tokens(name))


def _same_company_key(a, b):
    """Equal keys, or a board slug that is the name plus a region or corporate suffix (doordashusa)."""
    if a == b:
        return True
    from jobqueue import SLUG_SUFFIXES
    short, long_ = sorted((a or "", b or ""), key=len)
    return bool(short) and long_.startswith(short) and long_[len(short):] in SLUG_SUFFIXES


def _applied_records(ws):
    """(posting_id, company_key, title_key, applied_on) for everything already sent."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import _v2data as d
    recs = []
    for j in d.read_json(ws / "data" / "queue.json", {}).get("jobs", []):
        if j.get("state") in BLOCKING:
            recs.append((j.get("posting_id"), _company_key(j.get("company")), normalize_title(j.get("title")),
                         j.get("applied_on")))
    for job in job_dirs(ws):
        log = job / "application-log.md"
        st = parse_state(log)
        if st.get("status", "queued") == "queued" or not log.is_file():
            continue
        m = LOG_HEADING.search(log.read_text(encoding="utf-8"))
        if m:
            recs.append((None, _company_key(m.group(1)), normalize_title(m.group(2)), st.get("applied_on")))
    return recs


def cmd_guard(ws, args):
    opts, it = {}, iter(args)
    for a in it:
        if a in ("--company", "--title", "--posting-id", "--today"):
            opts[a.lstrip("-")] = next(it, "")
    if not opts.get("company") or not opts.get("title"):
        return die("usage: guard WS --company C --title T [--posting-id P] [--today YYYY-MM-DD]")
    dup = check_duplicate(ws, opts["company"], opts["title"], opts.get("posting-id"), opts.get("today"))
    print(dup or "OK")
    return 3 if dup else 0


def check_duplicate(ws, company_name, title_text, pid=None, today=None):
    """'DUPLICATE <why>' when this job was already applied to, else None. Shared by guard and apply."""
    today = _today(today)
    company, title = _company_key(company_name), normalize_title(title_text)
    for rpid, rco, rtitle, applied_on in _applied_records(ws):
        if pid and rpid and pid == rpid:
            return f"DUPLICATE already applied to posting {pid}" + (f" on {applied_on}" if applied_on else "")
        if rtitle == title and _same_company_key(rco, company):
            try:
                age = (today - _today(applied_on)).days if applied_on else 0
            except ValueError:
                age = 0
            if age <= GUARD_DAYS:
                when = f"{age} day(s) ago" if applied_on else "already in progress, application date unknown"
                return f"DUPLICATE {company_name} / {title_text}: {when} (window {GUARD_DAYS} days)"
    return None


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    cmd, ws = argv[1], Path(argv[2]).resolve()
    if not ws.is_dir():
        return die(f"workspace not found: {ws}")
    if "workspace" not in ws.parts:
        return die(f"refusing to operate outside a workspace/ directory: {ws}")
    fn = {"log": cmd_log, "overdue": cmd_overdue, "funnel": cmd_funnel, "show": cmd_show,
          "ingest": cmd_ingest, "guard": cmd_guard}.get(cmd)
    if not fn:
        return die(f"unknown command {cmd!r}")
    return fn(ws, argv[3:])


if __name__ == "__main__":
    sys.exit(main(sys.argv))
