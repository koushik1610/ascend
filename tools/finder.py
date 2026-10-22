#!/usr/bin/env python3
"""finder.py: pull open roles from public ATS job boards at zero tokens (Ascend 2.0, M5).

  python3 tools/finder.py run WS [--json]
  python3 tools/finder.py add WS --source web|linkedin --file workspace/<name>/data/<rows>.json   # rows Claude found
  python3 tools/finder.py probe "Company Name" [...]     # which boards answer for a company (setup)

  python3 tools/finder.py probe --careers URL ["Company"]   # board entries linked from a careers page

Reads the board list from workspace/<name>/data/sources.json and calls each board's public JSON API:
Greenhouse, Ashby, Lever, Workable, SmartRecruiters, Workday and Eightfold. No login, no scraping, no model.
Workday and Eightfold boards need more than a slug (see templates/sources.example.json); Eightfold is
polled slowly, and a board that answers 429 is "throttled" for the day, never closed.

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
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import _v2data as d  # noqa: E402
from _paths import PathOutsideWorkspace, resolve_out  # noqa: E402

ENDPOINTS = {
    "greenhouse": ("https://boards-api.greenhouse.io", "/v1/boards/{slug}/jobs?content=true"),
    "ashby": ("https://api.ashbyhq.com", "/posting-api/job-board/{slug}?includeCompensation=true"),
    "lever": ("https://api.lever.co", "/v0/postings/{slug}?mode=json"),
    "workable": ("https://apply.workable.com", "/api/v1/widget/accounts/{slug}"),
    "smartrecruiters": ("https://api.smartrecruiters.com", "/v1/companies/{slug}/postings"),
}
TEXT_LIMIT = 8000
UA = {"User-Agent": "Ascend/2.0 (job search; public board API)"}


WD_MAX = 200            # Workday rows read per board per day
EF_MAX = 100
EF_SPACING = 2.0        # seconds between Eightfold requests: Netflix's answers 429 to a burst
SAFE = re.compile(r"[A-Za-z0-9_-]+")
HOST = re.compile(r"[a-z0-9-]+(\.[a-z0-9-]+)+")
WD_PATH = re.compile(r"/job/[A-Za-z0-9_\-.%~/]+")


THROTTLED = object()


class Partial(list):
    """A board list cut off at its cap: what is missing from it may still be open, so nothing is closed."""


class Throttled(Exception):
    """The board asked us to slow down (HTTP 429). Not a failure: nothing on it is closed."""


def _base(default):
    override = os.environ.get("ASCEND_ATS_BASE", "")      # tests only, and only on this machine
    return override.rstrip("/") if urlparse(override).hostname in ("127.0.0.1", "localhost") else default


def _url(ats, slug):
    host, path = ENDPOINTS[ats]
    return _base(host) + path.format(slug=slug)


def _get_json(url, body=None):
    headers = dict(UA, Accept="application/json")
    if body is not None:
        headers["Content-Type"] = "application/json"
    req = Request(url, data=None if body is None else json.dumps(body).encode(), headers=headers)
    try:
        with urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except HTTPError as e:
        if e.code == 429:
            raise Throttled(url) from None
        raise


def _search_text(filters):
    """Workday and Eightfold search on the server: the first target-title pattern, regex syntax removed."""
    first = next(iter((filters or {}).get("title_include") or []), "")
    return re.sub(r"\s+", " ", re.sub(r"\\[bBwWsSdD]|[\\^$()\[\]{}?*+|.]", " ", first)).strip()


def _title_ok(title, filters):
    f = filters or {}
    inc, exc = f.get("title_include") or [], f.get("title_exclude") or []
    return ((not inc or any(re.search(p, title or "", re.I) for p in inc))
            and not any(re.search(p, title or "", re.I) for p in exc))


def workday_site(board):
    """https://{slug}.{pod}.myworkdayjobs.com/{site}, or ValueError when the entry could point anywhere else."""
    slug, pod, site = board.get("slug") or "", board.get("pod") or "", board.get("site") or ""
    if not (SAFE.fullmatch(slug) and re.fullmatch(r"wd\d{1,3}", pod) and SAFE.fullmatch(site)):
        raise ValueError(f"workday board {slug!r} needs slug, pod (wd1, wd5...) and site")
    return f"https://{slug}.{pod}.myworkdayjobs.com/{site}"


def eightfold_host(board):
    host, domain = (board.get("host") or "").lower(), (board.get("domain") or "").lower()
    if not (HOST.fullmatch(host) and HOST.fullmatch(domain)):
        raise ValueError(f"eightfold board {board.get('slug')!r} needs host and domain")
    return host, domain


def _workday(board, filters):
    site = workday_site(board)
    api = _base(site.rsplit("/", 1)[0]) + f"/wday/cxs/{board['slug']}/{board['site']}"
    search, rows, total = board.get("search") or _search_text(filters), [], None
    while len(rows) < WD_MAX:
        page = _get_json(api + "/jobs", {"appliedFacets": {}, "limit": 20, "offset": len(rows), "searchText": search})
        got = page.get("jobPostings") if isinstance(page, dict) else None
        if not isinstance(got, list):
            return None
        total = page.get("total") if total is None else total     # later pages answer total 0
        rows += got
        if len(got) < 20 or len(rows) >= (total or 0):
            break
    out = Partial() if len(rows) >= WD_MAX or (total or 0) > len(rows) else []
    for r in rows:
        path = r.get("externalPath") or ""
        if not WD_PATH.fullmatch(path) or ".." in path or "//" in path:
            continue
        r = dict(r)
        if _title_ok(r.get("title"), filters):
            try:
                r["_info"] = _get_json(api + path).get("jobPostingInfo") or {}
            except Throttled:
                raise
            except Exception:
                r["_info"] = {}
        out.append(r)
    return out


def _eightfold(board, filters):
    host, domain = eightfold_host(board)
    api = _base(f"https://{host}") + "/api/apply/v2/jobs"
    search, rows, count = quote(board.get("search") or _search_text(filters)), [], None
    while len(rows) < EF_MAX:
        if rows:
            time.sleep(EF_SPACING)
        page = _get_json(f"{api}?domain={quote(domain)}&query={search}&start={len(rows)}&num=10")
        got = page.get("positions") if isinstance(page, dict) else None
        if not isinstance(got, list):
            return None
        count = page.get("count") if count is None else count
        rows += got
        if len(got) < 10 or len(rows) >= (count or 0):
            break
    out = Partial() if len(rows) >= EF_MAX or (count or 0) > len(rows) else []
    for r in rows:
        if not isinstance(r.get("id"), int):
            continue
        r = dict(r)
        if _title_ok(r.get("name"), filters):
            time.sleep(EF_SPACING)
            try:
                r["_desc"] = _get_json(f"{api}/{r['id']}?domain={quote(domain)}").get("job_description") or ""
            except Throttled:
                raise
            except Exception:
                r["_desc"] = ""
        out.append(r)
    return out


def fetch_board(ats, slug, board=None, filters=None):
    """The board's raw job list, or None when the board could not be read. Raises Throttled on HTTP 429."""
    if ats in ("workday", "eightfold"):
        try:
            return (_workday if ats == "workday" else _eightfold)(dict(board or {}, slug=slug), filters)
        except Throttled:
            raise
        except Exception:
            return None
    try:
        with urlopen(Request(_url(ats, slug), headers=UA), timeout=20) as r:
            data = json.loads(r.read().decode("utf-8", "replace"))
    except Exception:
        return None
    # An answer without the job list (maintenance page, error object) is a failed read, not an empty
    # board: treating it as empty would close every posting on the board.
    if ats == "lever":
        return data if isinstance(data, list) else None
    key = "content" if ats == "smartrecruiters" else "jobs"
    jobs = data.get(key) if isinstance(data, dict) else None
    return jobs if isinstance(jobs, list) else None


# Most postings open with paragraphs about the company. Stored text and the scorer's budget start at the
# first heading that introduces the role instead. Found on real runs: the first 1,500 characters of Affirm's,
# Twilio's, Upstart's and GitLab's postings were company boilerplate, and 40 of 50 survivors were cut at
# 6,000 characters before their requirements.
ROLE_START = re.compile(r"(about the role|about this role|role overview|the role\b|in this role|what you('|’)ll do|"
                        r"what you will do|what you do\b|responsibilities|your impact|you will:|"
                        r"the opportunity(?! for)|\bas (a|an|the) [^.]{3,90}?, you will)", re.I)


def role_text(text):
    m = ROLE_START.search(text or "")
    return (text or "")[m.start():] if m else (text or "")


def clean(s, limit=TEXT_LIMIT):
    s = html.unescape(s or "")
    s = re.sub(r"(?is)<(script|style).*?</\1>", " ", s)
    s = re.sub(r"<[^>]+>", " ", s)
    return role_text(re.sub(r"\s+", " ", html.unescape(s)).strip())[:limit]


def _money(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def _remote_from_text(loc):
    return True if "remote" in (loc or "").lower() else None


def normalize(ats, slug, company, j, board=None):
    if ats == "workday":
        info = j.get("_info") or {}
        loc = info.get("location") or j.get("locationsText") or ""
        rt = (info.get("remoteType") or "").lower()
        url = workday_site(dict(board or {}, slug=slug)) + j["externalPath"]
        native = info.get("jobReqId") or next(iter(j.get("bulletFields") or []), None) or j["externalPath"].rsplit("_", 1)[-1]
        p = dict(native=native, title=info.get("title") or j.get("title", ""), location=loc,
                 remote=True if rt == "remote" else False if rt in ("hybrid", "on-site", "onsite", "on site") else
                 _remote_from_text(loc), url=url, apply_url=url + "/apply",
                 text=clean(info.get("jobDescription")), comp_min=None, comp_max=None)
    elif ats == "eightfold":
        host, _ = eightfold_host(dict(board or {}, slug=slug))
        loc = j.get("location") or ", ".join(j.get("locations") or [])
        wlo = (j.get("work_location_option") or "").lower()
        # Netflix lists "Remote, United States" jobs as work_location_option "onsite": the location wins.
        url = f"https://{host}/careers/job/{j['id']}"
        p = dict(native=j["id"], title=j.get("name") or j.get("posting_name") or "", location=loc,
                 remote=True if "remote" in loc.lower() or wlo == "remote" else False if wlo in ("hybrid", "onsite") else None,
                 url=url, apply_url=url, text=clean(j.get("_desc") or j.get("job_description")), comp_min=None, comp_max=None)
    elif ats == "greenhouse":
        loc = (j.get("location") or {}).get("name", "")
        p = dict(native=j["id"], title=j.get("title", ""), location=loc, remote=_remote_from_text(loc),
                 url=j.get("absolute_url"), apply_url=f"https://job-boards.greenhouse.io/{slug}/jobs/{j['id']}",
                 text=clean(j.get("content")),
                 comp_min=None, comp_max=None)
    elif ats == "ashby":
        comp = next((c for c in (j.get("compensation") or {}).get("summaryComponents", []) or []
                     if c.get("compensationType") == "Salary"), {})
        # workplaceType first: Ashby sets isRemote on hybrid jobs too.
        wp = (j.get("workplaceType") or "").lower()
        p = dict(native=j["id"], title=j.get("title", ""), location=j.get("location", ""),
                 remote=True if wp == "remote" else False if wp in ("hybrid", "onsite", "on-site") else
                 j.get("isRemote") if isinstance(j.get("isRemote"), bool) else _remote_from_text(j.get("location")),
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
    src = d.read_json(dd / "sources.json", {})
    boards, filters = src.get("boards", []), src.get("filters") or {}

    def one(b):
        try:
            return b, fetch_board(b["ats"], b["slug"], b, filters)
        except Throttled:
            return b, THROTTLED
    with ThreadPoolExecutor(16) as ex:
        results = list(ex.map(one, boards))
    out = {"boards": len(boards), "failed": [], "empty": [], "throttled": [], "new": 0, "seen": 0, "closed": 0}
    d.update_json(dd / "postings-state.json", {}, lambda state: _merge(dd, results, state, out, today))
    # The hub shows these: a wrong slug otherwise fails quietly every day.
    d.write_json_atomic(dd / "board-health.json", {"checked": today, "boards": len(boards),
                                                   "failed": out["failed"], "empty": out["empty"],
                                                   "throttled": out["throttled"]})
    return out


def probe(company):
    """Boards on the five supported ATSs that answer for a company name, with their job count and, for
    Greenhouse, the board's own display name. For setup: a wrong slug is the commonest first-run problem."""
    words = re.findall(r"[a-z0-9]+", (company or "").lower())
    if not words:
        return []
    base = "".join(words)
    stems = [base] + ([words[0]] if len(words) > 1 and len(words[0]) >= 4 else [])
    slugs = list(dict.fromkeys([base, "-".join(words)] + [st + x for st in stems for x in ("", "hq", "inc", "usa", "jobs", "careers")]))
    tries = [(ats, slug) for ats in ENDPOINTS for slug in slugs]
    with ThreadPoolExecutor(16) as ex:
        found = list(ex.map(lambda t: (t, fetch_board(*t)), tries))
    hits = []
    for (ats, slug), jobs in found:
        if not jobs:            # SmartRecruiters and Workable answer with an empty list for any name at all
            continue
        name = None
        if ats == "greenhouse":
            try:
                with urlopen(Request(_url("greenhouse", slug).split("/jobs?")[0], headers=UA), timeout=20) as r:
                    name = json.loads(r.read().decode("utf-8", "replace")).get("name")
            except Exception:
                name = None
        hits.append({"ats": ats, "slug": slug, "jobs": len(jobs), "name": name})
    return hits


PAGE_LINKS = [
    ("workday", re.compile(r"https?://([a-z0-9-]+)\.(wd\d{1,3})\.myworkdayjobs\.com/(?:[a-z]{2}-[A-Z]{2}/)?([A-Za-z0-9_-]+)")),
    ("greenhouse", re.compile(r"https?://(?:job-)?boards(?:-api)?\.greenhouse\.io/(?:embed/job_board\?for=|v1/boards/)?([a-z0-9_-]+)")),
    ("lever", re.compile(r"https?://jobs\.lever\.co/([a-z0-9_-]+)")),
    ("ashby", re.compile(r"https?://jobs\.ashbyhq\.com/([A-Za-z0-9_.-]+)")),
]
NOT_SLUGS = {"wday", "embed", "v1", "api", "static", "assets", "jobs"}


def boards_from_page(html_text, page_url, company):
    """Board entries for every job system a careers page links to (setup). Eightfold needs its own marker on
    the page, because a bare "domain" key appears on many sites."""
    out = []

    def keep(entry):
        if entry not in out:
            out.append(entry)
    for ats, rx in PAGE_LINKS:
        for m in rx.finditer(html_text or ""):
            if ats == "workday":
                if m.group(3).lower() not in NOT_SLUGS:
                    keep({"company": company, "ats": "workday", "slug": m.group(1), "pod": m.group(2), "site": m.group(3)})
            elif m.group(1).lower() not in NOT_SLUGS:
                keep({"company": company, "ats": ats, "slug": m.group(1)})
    host = (urlparse(page_url or "").hostname or "").lower()
    dom = re.search(r'"domain"\s*:\s*"([a-z0-9.-]+\.[a-z]{2,})"', html_text or "")
    if dom and re.search(r"eightfold", html_text or "", re.I) and HOST.fullmatch(host):
        keep({"company": company, "ats": "eightfold", "slug": re.sub(r"\W", "", dom.group(1).split(".")[0]),
              "host": host, "domain": dom.group(1)})
    return out


def probe_careers(url, company):
    if not (url or "").startswith("https://"):
        raise ValueError("the careers page must be an https URL")
    with urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0 (Ascend setup probe)"}), timeout=20) as r:
        text = r.read(3_000_000).decode("utf-8", "replace")
        final = r.geturl()
    return boards_from_page(text, final, company)


def _merge(dd, results, state, out, today):
    """Fold the fetched boards into postings-state, under its lock (finder.add may run at the same time)."""
    for board, raw in results:
        where = f"{board['ats']}:{board['slug']}"
        if raw is THROTTLED:
            out["throttled"].append(where)
            continue
        if raw is None:
            out["failed"].append(where)
            continue
        if not raw:
            out["empty"].append(where)
        current = set()
        for j in raw:
            try:
                p = normalize(board["ats"], board["slug"], board.get("company"), j, board)
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
        if raw and not current:         # every job failed to read: the ATS changed its format, not the board
            out["failed"].append(where)
            continue
        if isinstance(raw, Partial):
            continue
        prefix = f"{board['ats']}:{board['slug']}:"
        for pid, st in state.items():
            if pid.startswith(prefix) and pid not in current and not st.get("closed"):
                st.update(closed=True, closed_on=today)
                out["closed"] += 1


ATS_URL = [("greenhouse", re.compile(r"https://(?:job-)?boards\.greenhouse\.io/([\w-]+)/jobs/(\d+)")),
           ("lever", re.compile(r"https://jobs\.lever\.co/([\w-]+)/([0-9a-f-]{8,})")),
           ("ashby", re.compile(r"https://jobs\.ashbyhq\.com/([\w-]+)/([0-9a-f-]{8,})"))]


def board_names(ws):
    """{"ats:slug": company} from sources.json: the board's current name, which wins over the name a posting
    was first stored with (renaming a board fixes every posting on it)."""
    return {f"{b.get('ats')}:{b.get('slug')}": b.get("company") for b in
            d.read_json(Path(ws) / "data" / "sources.json", {}).get("boards", []) if b.get("company")}


def company_of(posting, names):
    return names.get(str(posting.get("id", "")).rsplit(":", 1)[0]) or posting.get("company")


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
        try:
            if "--file" in argv:        # rows Claude wrote under the workspace: no posting text on the command line
                rows = json.loads(resolve_out(argv[argv.index("--file") + 1]).read_text(encoding="utf-8"))
            elif "--json" in argv:
                rows = json.loads(argv[argv.index("--json") + 1])
            else:
                rows = json.load(sys.stdin)
            print(json.dumps(add(argv[2], rows, src)))
        except (ValueError, PathOutsideWorkspace) as e:
            print(f"finder: {e}", file=sys.stderr)
            return 2
        return 0
    if len(argv) >= 4 and argv[1] == "probe" and argv[2] == "--careers":
        company = argv[4] if len(argv) > 4 else (urlparse(argv[3]).hostname or "").split(".")[-2:][0]
        try:
            found = probe_careers(argv[3], company)
        except (ValueError, OSError) as e:
            print(f"finder: {e}", file=sys.stderr)
            return 2
        for b in found:
            print(json.dumps(b))
        if not found:
            print("no supported job system linked from that page (Phenom, iCIMS and own-site boards are not supported)")
        return 0
    if len(argv) >= 3 and argv[1] == "probe":
        for name in argv[2:]:
            hits = probe(name)
            print(f"{name}: " + ("; ".join(f"{h['ats']}:{h['slug']} ({h['jobs']} jobs"
                                            + (f", board name {h['name']!r}" if h["name"] else "") + ")" for h in hits)
                                 or "no board on Greenhouse, Ashby, Lever, Workable or SmartRecruiters"))
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
              + (f", unreachable: {', '.join(out['failed'])}" if out["failed"] else "")
              + (f", no jobs listed: {', '.join(out['empty'])}" if out["empty"] else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
