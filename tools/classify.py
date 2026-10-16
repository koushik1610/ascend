#!/usr/bin/env python3
"""classify.py: sort employer mail into categories by rule, at zero tokens (Ascend 2.0, M1).

Most mail about a job application says one of a handful of things in a handful of ways, and the
sender is usually an applicant tracking system. Rules catch those for free. Only mail that still
looks job-related after every rule has missed is marked `needs_llm`, so a batch goes to Claude and
receipts, newsletters and family mail never cost a token.

Email content is UNTRUSTED DATA (reference/untrusted-content-policy.md). This module only matches
patterns against it. Nothing in a message is ever executed, fetched or followed.
"""

import json
import math
import re
import sys
from datetime import date, datetime, timedelta

CATEGORIES = ["acknowledgement", "rejection", "info-request", "assessment", "interview-invite",
              "status-update", "recruiter-inbound", "job-alert", "other"]

# Senders that only ever write about hiring: applicant tracking systems and assessment vendors.
ATS_DOMAINS = {"greenhouse.io", "greenhouse-mail.io", "lever.co", "ashbyhq.com", "myworkday.com",
               "workday.com", "smartrecruiters.com", "workable.com", "icims.com", "jobvite.com",
               "taleo.net", "successfactors.com", "bamboohr.com", "recruitee.com", "rippling.com",
               "codesignal.com", "hackerrank.com", "codility.com", "coderpad.io"}
ALERT_SENDERS = {"jobalerts-noreply@linkedin.com", "jobs-noreply@linkedin.com", "alert@indeed.com",
                 "alerts@indeed.com", "noreply@glassdoor.com", "alerts@glassdoor.com",
                 "alert@ziprecruiter.com"}


def _rx(*parts):
    return re.compile("|".join(parts), re.I)


# Checked in this order; the first category with a hit wins. Rejection comes first because most
# rejections open with a thank-you that would otherwise read as an acknowledgement.
RULES = [
    ("rejection", _rx(r"\bunfortunately\b", r"not (be )?moving forward", r"will not be (moving|proceeding)",
                      r"not be proceeding", r"decided to (move forward|proceed|pursue|go) with (other|another)",
                      r"pursue other candidates", r"\bother candidates\b", r"\bnot (been )?selected\b",
                      r"position has been filled", r"regret to inform", r"no longer (being )?considered")),
    ("assessment", _rx(r"\bassessment\b", r"coding challenge", r"take[- ]home", r"hackerrank", r"codesignal",
                       r"codility", r"coderpad", r"online test", r"technical exercise")),
    ("interview-invite", _rx(r"schedule (your |an |a |the )?(interview|call|time|chat)", r"share your availability",
                             r"send (me )?your availability", r"availability (for|using)", r"are you available",
                             r"calendly", r"/meeting/", r"book a time", r"invite you to interview",
                             r"interview invitation", r"phone screen",
                             r"set up (a|an) (technical |video |phone )?(interview|call)", r"video interview",
                             r"move you forward")),
    ("info-request", _rx(r"additional information", r"complete your application", r"action required",
                         r"verify your (email|identity)", r"questionnaire", r"remaining questions",
                         r"please (provide|complete|answer|confirm|respond)", r"could you (please )?provide")),
    ("acknowledgement", _rx(r"thank(s| you) for (applying|your application|your interest|submitting)",
                            r"received your application", r"application (has been |was )?(received|submitted)")),
    ("status-update", _rx(r"status of your application", r"application (status|update)", r"under review",
                          r"still reviewing", r"moved to the .{0,40}(stage|review)", r"update on your .{0,30}application")),
    ("recruiter-inbound", _rx(r"came across your (profile|work|background)", r"reaching out", r"your background",
                              r"role we're opening", r"open to (a )?(quick )?(chat|conversation|call|new roles)",
                              r"opportunity with", r"(great|strong) fit")),
]
# Interview wording only counts in a sentence that is not conditional ("If selected, a recruiter
# will contact you to schedule a call" is an acknowledgement's promise, not an invitation).
CONDITIONAL = re.compile(r"\b(if|should|once|when)\b", re.I)
JOBBY = re.compile(r"\b(application|applied|candidate|interview|recruit\w*|hiring|position|job offer)\b", re.I)


def sender(msg):
    m = re.search(r"[\w.+-]+@[\w.-]+", msg.get("from", "") or "")
    return m.group(0).lower() if m else ""


def sender_domain(msg):
    s = sender(msg)
    return s.split("@", 1)[1] if "@" in s else ""


def is_ats(msg):
    d = sender_domain(msg)
    return any(d == a or d.endswith("." + a) for a in ATS_DOMAINS)


def _text(msg):
    return f"{msg.get('subject', '') or ''}\n{msg.get('body_excerpt', '') or ''}"


def _interview_hit(text, rx):
    for sentence in re.split(r"(?<=[.!?\n])\s+", text):
        hit = rx.search(sentence)
        if hit and not CONDITIONAL.search(sentence[:hit.start()]):
            return hit
    return None


def classify_message(msg):
    """Rule verdict for one message: {category, confidence, rule, needs_llm}."""
    text = _text(msg)
    ats = is_ats(msg)
    if sender(msg) in ALERT_SENDERS:
        return {"category": "job-alert", "confidence": 0.95, "rule": "sender:alert", "needs_llm": False}
    for category, rx in RULES:
        if category == "recruiter-inbound" and ats:
            continue
        hit = _interview_hit(text, rx) if category == "interview-invite" else rx.search(text)
        if hit:
            return {"category": category, "confidence": 0.95 if ats else 0.85,
                    "rule": f"{category}:{hit.group(0).lower()[:40]}", "needs_llm": False}
    return {"category": "other", "confidence": 0.5, "rule": "none",
            "needs_llm": bool(ats or JOBBY.search(text))}


# ── Matching mail to a queued job ────────────────────────────────────────────
SUFFIXES = {"inc", "llc", "ltd", "corp", "corporation", "co", "company", "technologies", "group", "plc", "gmbh"}


def company_tokens(name):
    words = re.findall(r"[a-z0-9]+", (name or "").lower())
    return [w for w in words if w not in SUFFIXES] or words


def _alnum(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def match_job(msg, jobs):
    """The queued job this message is about: its `nn` when it has a folder, else its `posting_id`.

    Three signals, any one is enough: the company in an ATS sender's local part
    (nvidia@myworkday.com), the company as the sender's own domain (x@acme-robotics.example), or the
    company name as whole words in the subject or body. Whole words, so 'HP' never matches 'Champion'.
    """
    local, _, domain = sender(msg).partition("@")
    first_label = _alnum(domain.split(".")[0]) if domain and not is_ats(msg) else ""
    text = _text(msg)
    hits = []
    for job in jobs:
        tokens = company_tokens(job.get("company"))
        if not tokens:
            continue
        key = "".join(tokens)
        by_sender = is_ats(msg) and _alnum(local) == key
        by_domain = bool(first_label) and first_label == key
        by_text = re.search(r"\b" + r"[\W_]*".join(map(re.escape, tokens)) + r"\b", text, re.I)
        if by_sender or by_domain or by_text:
            hits.append(job)
    if not hits:
        return None
    best = next((j for j in hits if j.get("nn")), hits[0])
    return best.get("nn") or best.get("posting_id")


# ── Due dates for info requests and assessments ──────────────────────────────
MONTHS = {m: i for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july",
                                       "august", "september", "october", "november", "december"], 1)}
WITHIN = re.compile(r"within (\d{1,3}) (business |calendar )?(day|hour)s?", re.I)
BY_DATE = re.compile(r"\bby (" + "|".join(MONTHS) + r") (\d{1,2})\b", re.I)
DEFAULT_DAYS = 3


def _msg_date(msg):
    try:
        return datetime.fromisoformat((msg.get("date") or "").replace("Z", "+00:00")).date()
    except ValueError:
        return date.today()


def due_date(msg, category):
    """ISO due date for info-request and assessment mail, else None."""
    if category not in ("info-request", "assessment"):
        return None
    sent = _msg_date(msg)
    text = _text(msg)
    m = WITHIN.search(text)
    if m:
        n = int(m.group(1))
        days = math.ceil(n / 24) if m.group(3).lower() == "hour" else n
        return (sent + timedelta(days=days)).isoformat()
    m = BY_DATE.search(text)
    if m:
        month, day = MONTHS[m.group(1).lower()], int(m.group(2))
        try:
            d = date(sent.year, month, day)
            if d < sent:
                d = date(sent.year + 1, month, day)
            return d.isoformat()
        except ValueError:
            pass
    return (sent + timedelta(days=DEFAULT_DAYS)).isoformat()


# ── CLI ──────────────────────────────────────────────────────────────────────
USAGE = """usage:
  python3 tools/classify.py run WS [--json]
      Classify every message in WS/data/mail.jsonl that has no event yet. Appends to
      WS/data/events.jsonl and, for mail the rules could not place, WS/data/classify-pending.jsonl.
      Safe to re-run: messages already classified are skipped.
  python3 tools/classify.py one --from F --subject S --body B [--date ISO]
      Classify one message and print the result as JSON (no files touched)."""


def event_for(msg, jobs, now):
    verdict = classify_message(msg)
    return {"msg_id": msg.get("msg_id"), "category": verdict["category"], "confidence": verdict["confidence"],
            "rule": verdict["rule"], "needs_llm": verdict["needs_llm"], "match": match_job(msg, jobs),
            "due": due_date(msg, verdict["category"]), "date": msg.get("date"), "classified_at": now}


def cmd_run(ws, as_json):
    import _v2data as d
    from _paths import PathOutsideWorkspace
    try:
        dd = d.data_dir(ws)
    except PathOutsideWorkspace as e:
        print(f"classify: {e}", file=sys.stderr)
        return 2
    jobs = d.read_json(dd / "queue.json", {}).get("jobs", [])
    done = {e.get("msg_id") for e in d.read_jsonl(dd / "events.jsonl")}
    now = datetime.now().isoformat(timespec="seconds")
    counts, new = {}, 0
    for msg in d.read_jsonl(dd / "mail.jsonl"):
        mid = msg.get("msg_id")
        if not mid or mid in done:
            continue
        ev = event_for(msg, jobs, now)
        d.append_jsonl(dd / "events.jsonl", ev)
        if ev["needs_llm"]:
            d.append_jsonl(dd / "classify-pending.jsonl", {"msg_id": mid, "queued_at": now})
        done.add(mid)
        counts[ev["category"]] = counts.get(ev["category"], 0) + 1
        new += 1
    pending = sum(1 for e in d.read_jsonl(dd / "events.jsonl") if e.get("needs_llm"))
    if as_json:
        print(json.dumps({"new": new, "by_category": counts, "needs_llm": pending}))
    else:
        print(f"classified {new} new message(s); {pending} waiting for a model pass")
        for c in CATEGORIES:
            if counts.get(c):
                print(f"  {c:<18} {counts[c]}")
    return 0


def _opt(args, name, default=""):
    return args[args.index(name) + 1] if name in args and args.index(name) + 1 < len(args) else default


def main(argv):
    if len(argv) < 2 or argv[1] not in ("run", "one"):
        print(USAGE, file=sys.stderr)
        return 2
    if argv[1] == "run":
        if len(argv) < 3 or argv[2].startswith("--"):
            print(USAGE, file=sys.stderr)
            return 2
        return cmd_run(argv[2], "--json" in argv)
    args = argv[2:]
    msg = {"msg_id": "one", "from": _opt(args, "--from"), "subject": _opt(args, "--subject"),
           "body_excerpt": _opt(args, "--body")[:2000],
           "date": _opt(args, "--date", datetime.now().isoformat(timespec="seconds"))}
    print(json.dumps(event_for(msg, [], datetime.now().isoformat(timespec="seconds"))))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
