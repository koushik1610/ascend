#!/usr/bin/env python3
"""prefilter.py: hard rules over found postings, at zero tokens (Ascend 2.0, M5).

  python3 tools/prefilter.py run WS [--json]

Applies the filters in workspace/<name>/data/sources.json to every posting the finder has stored and
appends one row per posting to data/candidates.jsonl: passed or not, why, and the share of the user's
keywords the posting mentions. Only survivors are worth a model's time (Phase 27 scores them), so this
is where most of Ascend 2.0's token savings come from.

Incremental: a posting already judged under the same filters is skipped. Change the filters and every
posting is judged again. A closed posting never passes.
"""

import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import _v2data as d  # noqa: E402
import pipeline  # noqa: E402
from _paths import PathOutsideWorkspace  # noqa: E402
from classify import company_tokens  # noqa: E402


# Bump when the rules themselves change, so postings judged by older rules are judged again.
RULES_VERSION = 2


def _any(patterns, text):
    return next((p for p in patterns or [] if re.search(p, text or "", re.I)), None)


UNPLACED = re.compile(r"\b(remote|anywhere|hybrid|work from home|wfh|flexible|friendly|travel|required)\b|[-,()/|&;.]",
                      re.I)
# "United States" as boards actually write it. A job titled "Remote - California" is a US job.
US_STATES = ["alabama", "alaska", "arizona", "arkansas", "california", "colorado", "connecticut", "delaware",
             "florida", "georgia", "hawaii", "idaho", "illinois", "indiana", "iowa", "kansas", "kentucky",
             "louisiana", "maine", "maryland", "massachusetts", "michigan", "minnesota", "mississippi", "missouri",
             "montana", "nebraska", "nevada", "new hampshire", "new jersey", "new mexico", "new york",
             "north carolina", "north dakota", "ohio", "oklahoma", "oregon", "pennsylvania", "rhode island",
             "south carolina", "south dakota", "tennessee", "texas", "utah", "vermont", "virginia", "washington",
             "west virginia", "wisconsin", "wyoming", "district of columbia"]
US_PLACES = ["u s", "u s a", "united states of america", "north america", "nyc", "sf", "bay area", "silicon valley", "seattle", "san francisco",
             "los angeles", "san jose", "boston", "austin", "dallas", "houston", "denver", "chicago", "atlanta",
             "miami", "phoenix", "portland", "salt lake", "dc", "d c", "raleigh", "pittsburgh", "philadelphia",
             "san diego", "minneapolis", "nashville", "detroit", "columbus"]
US_ALIASES = {"united states", "us", "usa", "u.s.", "u.s.a."}
REMOTE_IN_TEXT = re.compile(r"\b(this (role|position) is (fully )?remote|remote[- ](first|eligible|friendly)|"
                            r"work (fully )?remote(ly)?|remote within|100% remote|fully remote)\b", re.I)


def location_ok(loc, allowed):
    """"Remote" says nothing about country. A location passes when it names an allowed region (whole
    words, so "us" never matches inside "Australia"), or when it names no region at all."""
    regions = [a.lower() for a in allowed if not UNPLACED.fullmatch(a.strip())]
    if US_ALIASES & set(regions):
        regions += US_STATES + US_PLACES
    plain = re.sub(r"\s+", " ", re.sub(r"[.]", " ", loc.lower()))
    if not UNPLACED.sub(" ", plain).strip():
        return True
    return any(re.search(r"\b" + re.escape(r.replace(".", " ").strip()) + r"\b", plain) for r in regions)


def company_key(name):
    return "".join(company_tokens(name))


def evaluate(posting, filters, applied):
    """applied: (company_key, normalized_title) pairs already sent."""
    title, text = posting.get("title", ""), posting.get("text", "")
    loc = (posting.get("location") or "").lower()
    reasons, ok = [], True

    def fail(why):
        nonlocal ok
        ok = False
        reasons.append(why)

    if filters.get("title_include") and not _any(filters["title_include"], title):
        fail("title does not match your target titles")
    hit = _any(filters.get("title_exclude"), title)
    if hit:
        fail(f"excluded title ({hit})")
    if filters.get("seniority") and not _any(filters["seniority"], title):
        fail("seniority not in your targets")
    if filters.get("remote_only"):
        remote = posting.get("remote")
        if remote is None and "remote" not in loc and REMOTE_IN_TEXT.search(text[:4000]):
            reasons.append("remote per the description (the board does not flag it)")
        elif remote is False or (remote is None and "remote" not in loc):
            fail(f"not remote ({posting.get('location') or 'location not stated'})")
    if filters.get("locations") and not location_ok(loc, filters["locations"]):
        fail(f"location outside your list ({posting.get('location') or 'not stated'})")
    floor = filters.get("comp_floor")
    if floor:
        top = posting.get("comp_max") or posting.get("comp_min")
        if top is None:
            reasons.append("comp unknown")
        elif top < floor:
            fail(f"pay below your floor (tops out at {top:,})")
    blob = f"{title}\n{text}".lower()
    kw = next((k for k in filters.get("exclude_keywords", []) or [] if k.lower() in blob), None)
    if kw:
        fail(f"excluded keyword: {kw}")
    if company_key(posting.get("company")) in {company_key(b) for b in filters.get("blocklist", []) or []}:
        fail("company on your blocklist")
    key, ntitle = company_key(posting.get("company")), pipeline.normalize_title(title)
    if any(t == ntitle and pipeline._same_company_key(key, c) for c, t in applied):
        fail("already applied")
    keywords = [k.lower() for k in filters.get("keywords", []) or []]
    overlap = round(sum(1 for k in keywords if k in blob) / len(keywords), 3) if keywords else 0.0
    return {"passed": ok, "reasons": reasons, "keyword_overlap": overlap}


def run(ws):
    dd = d.data_dir(ws)
    filters = d.read_json(dd / "sources.json", {}).get("filters", {})
    fhash = hashlib.sha1(json.dumps([RULES_VERSION, filters], sort_keys=True).encode()).hexdigest()[:12]
    done = {c.get("posting_id") for c in d.read_jsonl(dd / "candidates.jsonl") if c.get("filters_hash") == fhash}
    state = d.read_json(dd / "postings-state.json", {})
    applied = [(rco, rtitle) for _, rco, rtitle, _ in pipeline._applied_records(Path(ws))]
    now = datetime.now().isoformat(timespec="seconds")
    out = {"evaluated": 0, "passed": 0}
    # One role posted in several locations is one role: only its first passing posting goes forward,
    # so it is scored (and paid for) once.
    passing = {}
    for c in d.read_jsonl(dd / "candidates.jsonl"):
        if c.get("filters_hash") == fhash and c.get("passed") and c.get("role_key"):
            passing.setdefault(c["role_key"], c["posting_id"])
    for p in d.read_jsonl(dd / "postings.jsonl"):
        if p.get("id") in done:
            continue
        done.add(p.get("id"))
        if state.get(p.get("id"), {}).get("closed"):
            r = {"passed": False, "reasons": ["closed: no longer on the company's board"], "keyword_overlap": 0.0}
        else:
            r = evaluate(p, filters, applied)
        role = f"{company_key(p.get('company'))}|{pipeline.normalize_title(p.get('title'))}"
        if r["passed"] and role in passing:
            r = dict(r, passed=False, reasons=[f"same role as {passing[role]} (another location)"] + r["reasons"])
        elif r["passed"]:
            passing[role] = p.get("id")
        d.append_jsonl(dd / "candidates.jsonl",
                       dict(r, posting_id=p.get("id"), role_key=role, filters_hash=fhash, evaluated_at=now))
        out["evaluated"] += 1
        out["passed"] += r["passed"]
    return out


def main(argv):
    if len(argv) < 3 or argv[1] != "run" or argv[2].startswith("--"):
        print(__doc__, file=sys.stderr)
        return 2
    try:
        out = run(argv[2])
    except PathOutsideWorkspace as e:
        print(f"prefilter: {e}", file=sys.stderr)
        return 2
    print(json.dumps(out) if "--json" in argv else f"judged {out['evaluated']} posting(s), {out['passed']} passed")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
