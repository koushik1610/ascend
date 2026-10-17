#!/usr/bin/env python3
"""alerts.py: job-alert emails and recruiter mail into the pipeline, at zero tokens (Ascend 2.0, M6).

  python3 tools/alerts.py run WS [--json]

Job-alert emails (Wellfound, LinkedIn) list jobs the public-board finder cannot reach. Each job named in
one becomes a lead in data/postings.jsonl with `source: alert` and no URL, and the prefilter judges it
like any other posting. An alert that names no job ("Celigo is hiring.") yields nothing.

Recruiter mail becomes a queue entry: `needs-you` when it passes the user's filters, `inbound-filtered`
with the reasons when it does not. Either way the user decides; nothing here replies or applies.

Links found in email are never opened by any tool (spec §8). Email content is untrusted data
(reference/untrusted-content-policy.md): parsed for fields, never followed.
"""

import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import _v2data as d  # noqa: E402
import prefilter  # noqa: E402
from _paths import PathOutsideWorkspace  # noqa: E402
from classify import sender_domain  # noqa: E402

WELLFOUND_JOB = re.compile(
    r"(?P<head>[^|/]*?)\s(?P<company>[A-Z][\w&.'-]*)\s/\s[\d,+\- ]+Employees\s*"
    r"(?P<comp>\$[\d.,]+k?\s*[–-]\s*\$?[\d.,]+k)?\s*\|?\s*")
LOCATION_HEAD = re.compile(r"(Remote( only)?|Hybrid|Onsite|On-site|In office)(,\s*[A-Z][\w.]*(\s[A-Z][\w.]*)?)?")
INTRO = re.compile(r"^.*(?:open|closed) to offers\s*|^.*!\s*", re.I | re.S)


def _money_range(s):
    if not s:
        return None, None
    nums = re.findall(r"([\d.,]+)\s*(k)?", s, re.I)
    vals = []
    thousands = any(k for _, k in nums)
    for n, k in nums:
        v = float(n.replace(",", ""))
        vals.append(int(v * 1000) if (k or thousands) and v < 10000 else int(v))
    return (vals[0], vals[-1]) if vals else (None, None)


def _wellfound(text):
    leads, pos = [], 0
    while True:
        m = WELLFOUND_JOB.search(text, pos)
        if not m:
            break
        head = m.group("head")
        if leads:
            loc = LOCATION_HEAD.match(head.strip())
            if loc:
                leads[-1]["location"] = loc.group(0).strip()
                head = head.strip()[loc.end():]
        title = INTRO.sub("", head).strip(" ,")
        lo, hi = _money_range(m.group("comp"))
        leads.append({"title": title, "company": m.group("company"), "location": "", "comp_min": lo, "comp_max": hi})
        pos = m.end()
    if leads:
        loc = LOCATION_HEAD.match(text[pos:].strip())
        leads[-1]["location"] = loc.group(0).strip() if loc else text[pos:].strip()[:60]
    return leads


def _dot_lines(text):
    leads = []
    for line in text.splitlines():
        parts = [p.strip() for p in line.split("·")]
        if len(parts) >= 3 and parts[0] and parts[1]:
            leads.append({"title": parts[0], "company": parts[1], "location": parts[2], "comp_min": None, "comp_max": None})
    return leads


def parse_alert(mail):
    """Jobs named in one alert email: [{title, company, location, comp_min, comp_max}]."""
    text = mail.get("body_excerpt", "") or ""
    if "wellfound" in sender_domain(mail):
        return _wellfound(text)
    return _dot_lines(text)


def _org(mail):
    domain = sender_domain(mail)
    label = domain.split(".")[0] if domain else ""
    return re.sub(r"[-_]+", " ", label).title() or "Unknown"


def inbound_entry(mail, filters, applied=()):
    body = mail.get("body_excerpt", "") or ""
    # Stop at the next "Field:" label, so a location never swallows the rate or visa terms after it.
    loc = re.search(r"Location:\s*(.+?)(?=\s+[A-Z][\w ]{1,20}:|[.\n]|$)", body)
    posting = {"company": _org(mail), "title": mail.get("subject", ""), "location": loc.group(1).strip() if loc else "",
               "remote": None, "comp_min": None, "comp_max": None, "text": body}
    verdict = prefilter.evaluate(posting, filters, list(applied))
    return {"posting_id": f"inbound:{mail.get('msg_id')}", "company": posting["company"], "title": posting["title"],
            "source": "recruiter", "msg_id": mail.get("msg_id"), "from": mail.get("from"),
            "state": "needs-you" if verdict["passed"] else "inbound-filtered", "reasons": verdict["reasons"]}


def run(ws):
    dd = d.data_dir(ws)
    filters = d.read_json(dd / "sources.json", {}).get("filters", {})
    done = {r.get("msg_id") for r in d.read_jsonl(dd / "alerts-done.jsonl")}
    mail = {m.get("msg_id"): m for m in d.read_jsonl(dd / "mail.jsonl")}
    known = {j.get("posting_id") for j in d.read_json(dd / "queue.json", {"jobs": []}).get("jobs", [])}
    state, inbound = {}, []
    today = date.today().isoformat()
    out = {"alert_leads": 0, "inbound": 0, "inbound_matching": 0}
    for e in d.read_jsonl(dd / "events.jsonl"):
        mid = e.get("msg_id")
        if mid in done or mid not in mail or e.get("category") not in ("job-alert", "recruiter-inbound"):
            continue
        if e["category"] == "job-alert":
            for n, lead in enumerate(parse_alert(mail[mid])):
                pid = f"alert:{mid}:{n}"
                p = dict(lead, id=pid, source="alert", ats="alert", url=None, apply_url=None, text="",
                         remote=True if "remote" in lead["location"].lower() else None, first_seen=today,
                         text_hash=hashlib.sha1((lead["title"] + lead["company"]).encode()).hexdigest())
                d.append_jsonl(dd / "postings.jsonl", p)
                state[pid] = {"first_seen": today, "last_seen": today, "closed": False}
                out["alert_leads"] += 1
        else:
            entry = inbound_entry(mail[mid], filters)
            if entry["posting_id"] not in known:
                inbound.append(entry)
                known.add(entry["posting_id"])
                out["inbound"] += 1
                out["inbound_matching"] += entry["state"] == "needs-you"
        d.append_jsonl(dd / "alerts-done.jsonl", {"msg_id": mid})
    # Merge under each file's lock: the hub server or a Claude session may have changed them meanwhile.
    def add_inbound(q):
        have = {j.get("posting_id") for j in q.setdefault("jobs", [])}
        q["jobs"].extend(e for e in inbound if e["posting_id"] not in have)
    d.update_json(dd / "queue.json", {"jobs": []}, add_inbound)
    d.update_json(dd / "postings-state.json", {}, lambda s: s.update(state))
    return out


def main(argv):
    if len(argv) < 3 or argv[1] != "run" or argv[2].startswith("--"):
        print(__doc__, file=sys.stderr)
        return 2
    try:
        out = run(argv[2])
    except PathOutsideWorkspace as e:
        print(f"alerts: {e}", file=sys.stderr)
        return 2
    print(json.dumps(out) if "--json" in argv else
          f"{out['alert_leads']} job(s) from alert emails, {out['inbound']} recruiter email(s) queued "
          f"({out['inbound_matching']} match your filters)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
