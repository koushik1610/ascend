#!/usr/bin/env python3
"""finder.py: pull open roles from public ATS job boards at zero tokens (Ascend 2.0, M5).

  python3 tools/finder.py run WS [--json]
  python3 tools/finder.py add WS --source web|linkedin --json '[{...}]'   # rows Claude found

Reads the board list from workspace/<name>/data/sources.json and calls each board's public JSON API:
Greenhouse, Ashby, Lever, Workable and SmartRecruiters. No login, no scraping, no model.

New postings append to data/postings.jsonl. data/postings-state.json keeps first and last seen dates and
whether a posting has closed. A posting is closed only when its board answered successfully without it:
a board that is down for a day must not close every job on it.

Posting text is untrusted data (reference/untrusted-content-policy.md). It is stored and matched against,
never followed.
"""

import hashlib
import html
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path
from urllib.request import Request, urlopen

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import _v2data as d  # noqa: E402
from _paths import PathOutsideWorkspace  # noqa: E402

ENDPOINTS = {
    "greenhouse": ("https://boards-api.greenhouse.io", "/v1/boards/{slug}/jobs?content=true"),
    "ashby": ("https://api.ashbyhq.com", "/posting-api/job-board/{slug}?includeCompensation=true"),
    "lever": ("https://api.lever.co", "/v0/postings/{slug}?mode=json"),
    "workable": ("https://apply.workable.com", "/api/v1/widget/accounts/{slug}"),
    "smartrecruiters": ("https://api.smartrecruiters.com", "/v1/companies/{slug}/postings"),
}
TEXT_LIMIT = 6000
UA = {"User-Agent": "Ascend/2.0 (job search; public board API)"}


def _url(ats, slug):
    host, path = ENDPOINTS[ats]
    return os.environ.get("ASCEND_ATS_BASE", host) + path.format(slug=slug)


def fetch_board(ats, slug):
    """The board's raw job list, or None when the board could not be read."""
    try:
        with urlopen(Request(_url(ats, slug), headers=UA), timeout=20) as r:
            data = json.loads(r.read().decode("utf-8", "replace"))
    except Exception:
        return None
    if ats == "lever":
        return data if isinstance(data, list) else None
    if ats == "smartrecruiters":
        return data.get("content", [])
    return data.get("jobs", [])


def clean(s):
    s = html.unescape(s or "")
    s = re.sub(r"(?is)<(script|style).*?</\1>", " ", s)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()[:TEXT_LIMIT]


def _money(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def _remote_from_text(loc):
    return True if "remote" in (loc or "").lower() else None


def normalize(ats, slug, company, j):
    if ats == "greenhouse":
        loc = (j.get("location") or {}).get("name", "")
        p = dict(native=j["id"], title=j.get("title", ""), location=loc, remote=_remote_from_text(loc),
                 url=j.get("absolute_url"), apply_url=j.get("absolute_url"), text=clean(j.get("content")),
                 comp_min=None, comp_max=None)
    elif ats == "ashby":
        comp = next((c for c in (j.get("compensation") or {}).get("summaryComponents", []) or []
                     if c.get("compensationType") == "Salary"), {})
        p = dict(native=j["id"], title=j.get("title", ""), location=j.get("location", ""),
                 remote=j.get("isRemote") if isinstance(j.get("isRemote"), bool) else _remote_from_text(j.get("location")),
                 url=j.get("jobUrl"), apply_url=j.get("applyUrl") or j.get("jobUrl"),
                 text=clean(j.get("descriptionPlain")), comp_min=_money(comp.get("minValue")),
                 comp_max=_money(comp.get("maxValue")))
    elif ats == "lever":
        wp = (j.get("workplaceType") or "").lower()
        loc = (j.get("categories") or {}).get("location", "")
        sal = j.get("salaryRange") or {}
        text = " ".join([j.get("descriptionPlain", "")] + [l.get("content", "") for l in j.get("lists", []) or []])
        p = dict(native=j["id"], title=j.get("text", ""), location=loc,
                 remote=True if wp == "remote" else False if wp in ("onsite", "on-site", "hybrid") else _remote_from_text(loc),
                 url=j.get("hostedUrl"), apply_url=j.get("applyUrl") or j.get("hostedUrl"), text=clean(text),
                 comp_min=_money(sal.get("min")), comp_max=_money(sal.get("max")))
    elif ats == "workable":
        loc = ", ".join(x for x in (j.get("city"), j.get("country")) if x)
        p = dict(native=j["shortcode"], title=j.get("title", ""), location=loc,
                 remote=bool(j["telecommuting"]) if "telecommuting" in j else _remote_from_text(loc),
                 url=j.get("url"), apply_url=j.get("application_url") or j.get("url"),
                 text=clean(j.get("description")), comp_min=None, comp_max=None)
    elif ats == "smartrecruiters":
        l = j.get("location") or {}
        loc = ", ".join(x for x in (l.get("city"), l.get("country")) if x)
        url = f"https://jobs.smartrecruiters.com/{slug}/{j['id']}"
        p = dict(native=j["id"], title=j.get("name", ""), location=loc,
                 remote=l.get("remote") if isinstance(l.get("remote"), bool) else _remote_from_text(loc),
                 url=url, apply_url=url, text="", comp_min=None, comp_max=None)
    else:
        raise ValueError(f"unknown ats {ats!r}")
    native = p.pop("native")
    p.update(id=f"{ats}:{slug}:{native}", ats=ats, company=company or slug,
             text_hash=hashlib.sha1((p["title"] + "\n" + p["text"]).encode()).hexdigest())
    return p


def run(ws, today=None):
    today = today or date.today().isoformat()
    dd = d.data_dir(ws)
    boards = d.read_json(dd / "sources.json", {}).get("boards", [])
    with ThreadPoolExecutor(16) as ex:
        results = list(ex.map(lambda b: (b, fetch_board(b["ats"], b["slug"])), boards))
    out = {"boards": len(boards), "failed": [], "new": 0, "seen": 0, "closed": 0}
    d.update_json(dd / "postings-state.json", {}, lambda state: _merge(dd, results, state, out, today))
    return out


def _merge(dd, results, state, out, today):
    """Fold the fetched boards into postings-state, under its lock (finder.add may run at the same time)."""
    for board, raw in results:
        if raw is None:
            out["failed"].append(board["slug"])
            continue
        current = set()
        for j in raw:
            try:
                p = normalize(board["ats"], board["slug"], board.get("company"), j)
            except (KeyError, TypeError, ValueError):
                continue
            current.add(p["id"])
            if p["id"] in state:
                state[p["id"]].update(last_seen=today, closed=False)
                out["seen"] += 1
            else:
                d.append_jsonl(dd / "postings.jsonl", dict(p, first_seen=today))
                state[p["id"]] = {"first_seen": today, "last_seen": today, "closed": False}
                out["new"] += 1
        prefix = f"{board['ats']}:{board['slug']}:"
        for pid, st in state.items():
            if pid.startswith(prefix) and pid not in current and not st.get("closed"):
                st.update(closed=True, closed_on=today)
                out["closed"] += 1


ATS_URL = [("greenhouse", re.compile(r"https://(?:job-)?boards\.greenhouse\.io/([\w-]+)/jobs/(\d+)")),
           ("lever", re.compile(r"https://jobs\.lever\.co/([\w-]+)/([0-9a-f-]{8,})")),
           ("ashby", re.compile(r"https://jobs\.ashbyhq\.com/([\w-]+)/([0-9a-f-]{8,})"))]


def ats_id(url):
    """greenhouse:acme:123 for a posting URL on a board this finder knows how to poll, else None."""
    for ats, rx in ATS_URL:
        m = rx.match(url or "")
        if m:
            return f"{ats}:{m.group(1)}:{m.group(2)}"
    return None


def add(ws, rows, source):
    """Postings found by Claude (engine B's web search, LinkedIn search): validated and normalized
    exactly like board postings, so the prefilter and everything after cannot tell the difference."""
    if source not in ("web", "linkedin"):
        raise ValueError("source is web or linkedin")
    dd = d.data_dir(ws)
    stored = d.read_jsonl(dd / "postings.jsonl")
    known = {p.get("url") for p in stored} | {p.get("id") for p in stored}
    polled = {f"{b['ats']}:{b['slug']}:" for b in d.read_json(dd / "sources.json", {}).get("boards", [])}
    today = date.today().isoformat()
    out = {"added": 0, "skipped": 0}
    d.update_json(dd / "postings-state.json", {}, lambda state: _add_rows(dd, rows, source, state, known, polled, today, out))
    return out


def _add_rows(dd, rows, source, state, known, polled, today, out):
    for r in rows:
        url = (r.get("url") or "").strip()
        board_id = ats_id(url)
        if not (url.startswith("https://") and r.get("company") and r.get("title")) or url in known or (board_id and board_id in known):
            out["skipped"] += 1
            continue
        # A search result can be months old. If its board is one we poll and the board did not list it
        # on the last run, the posting has closed: keep it for the record, closed, so it never passes.
        prefix = board_id.rsplit(":", 1)[0] + ":" if board_id else None
        closed = bool(prefix in polled and any(k.startswith(prefix) for k in state) and board_id not in state)
        loc = r.get("location", "") or ""
        text = clean(r.get("text", ""))
        p = {"id": board_id or f"{source}:{hashlib.sha1(url.encode()).hexdigest()[:12]}", "ats": source, "source": source,
             "company": r["company"], "title": r["title"], "location": loc,
             "remote": r["remote"] if isinstance(r.get("remote"), bool) else _remote_from_text(loc),
             "comp_min": _money(r.get("comp_min")), "comp_max": _money(r.get("comp_max")), "url": url,
             "apply_url": r.get("apply_url") or url, "text": text, "first_seen": today,
             "text_hash": hashlib.sha1((r["title"] + "\n" + text).encode()).hexdigest()}
        d.append_jsonl(dd / "postings.jsonl", p)
        state[p["id"]] = {"first_seen": today, "last_seen": today, "closed": closed}
        known |= {url, p["id"]}
        out["added"] += 1


def main(argv):
    if len(argv) >= 3 and argv[1] == "add" and not argv[2].startswith("--"):
        src = argv[argv.index("--source") + 1] if "--source" in argv else "web"
        rows = json.loads(argv[argv.index("--json") + 1]) if "--json" in argv else json.load(sys.stdin)
        try:
            print(json.dumps(add(argv[2], rows, src)))
        except (ValueError, PathOutsideWorkspace) as e:
            print(f"finder: {e}", file=sys.stderr)
            return 2
        return 0
    if len(argv) < 3 or argv[1] != "run" or argv[2].startswith("--"):
        print(__doc__, file=sys.stderr)
        return 2
    try:
        out = run(argv[2])
    except PathOutsideWorkspace as e:
        print(f"finder: {e}", file=sys.stderr)
        return 2
    if "--json" in argv:
        print(json.dumps(out))
    else:
        print(f"{out['boards']} board(s): {out['new']} new, {out['seen']} still open, {out['closed']} closed"
              + (f", unreachable: {', '.join(out['failed'])}" if out["failed"] else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
