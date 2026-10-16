#!/usr/bin/env python3
"""industry_research.py: where Phase 26's industry-language research lives, and whether it is fresh.

  python3 tools/industry_research.py status INDUSTRY DOMAIN [--today YYYY-MM-DD] [--json]
  python3 tools/industry_research.py path   INDUSTRY DOMAIN
  python3 tools/industry_research.py list   [--json]

Research lives at industryresearch/<industry>/<domain>/industry-language.md, keyed by two slugs the
intake records (for example tech/cloudsecurity, media/journalism, finance/investmentbanking). The
file's first lines carry a "**Built:** YYYY-MM-DD" stamp.

status prints one word and exits with a code the orchestrator branches on:
  FRESH    0   built in the current calendar month: reuse it, skip the research
  STALE    3   built in an earlier month: redo the research
  MISSING  4   no file for this industry/domain yet: do the research
  UNDATED  5   a file exists but has no readable Built stamp: treat as stale

"Fresh" is the calendar month on purpose. Hiring language moves slowly enough that monthly is plenty,
and a calendar rule is one a person can check by eye without running anything.
"""

import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "industryresearch"
FILE = "industry-language.md"
BUILT = re.compile(r"^\*\*Built:\*\*\s*(\d{4}-\d{2}-\d{2})\s*$", re.M)
CODES = {"FRESH": 0, "STALE": 3, "MISSING": 4, "UNDATED": 5}


def slug(s):
    """Lowercase letters and digits only, so 'Cloud Security' and 'cloud-security' land in one folder."""
    out = re.sub(r"[^a-z0-9]", "", s.lower())
    if not out:
        raise ValueError(f"empty slug from {s!r}")
    return out


def research_path(industry, domain):
    return ROOT / slug(industry) / slug(domain) / FILE


def built_date(p):
    m = BUILT.search(p.read_text(encoding="utf-8")[:2000])
    if not m:
        return None
    try:
        return date.fromisoformat(m.group(1))
    except ValueError:
        return None


def status(industry, domain, today):
    p = research_path(industry, domain)
    if not p.exists():
        return "MISSING", p, None
    b = built_date(p)
    if b is None:
        return "UNDATED", p, None
    return ("FRESH" if (b.year, b.month) == (today.year, today.month) else "STALE"), p, b


def _opt(args, name):
    if name in args:
        i = args.index(name)
        if i + 1 < len(args):
            return args[i + 1]
    return None


def main(argv):
    if len(argv) < 2 or argv[1] not in ("status", "path", "list"):
        print(__doc__)
        return 2
    cmd, args = argv[1], argv[2:]
    as_json = "--json" in args
    if cmd == "list":
        rows = []
        for p in sorted(ROOT.glob(f"*/*/{FILE}")):
            b = built_date(p)
            rows.append({"industry": p.parent.parent.name, "domain": p.parent.name,
                         "built": b.isoformat() if b else None, "path": str(p.relative_to(ROOT.parent))})
        if as_json:
            print(json.dumps(rows, indent=2))
        else:
            for r in rows:
                print(f"{r['industry']}/{r['domain']}  built {r['built'] or 'UNDATED'}  {r['path']}")
        return 0
    pos = [a for i, a in enumerate(args) if not a.startswith("--") and (i == 0 or args[i - 1] != "--today")]
    if len(pos) < 2:
        print(__doc__)
        return 2
    try:
        industry, domain = slug(pos[0]), slug(pos[1])
    except ValueError as e:
        print(f"industry_research: {e}", file=sys.stderr)
        return 2
    if cmd == "path":
        print(research_path(industry, domain).relative_to(ROOT.parent))
        return 0
    t = _opt(args, "--today")
    try:
        today = date.fromisoformat(t) if t else date.today()
    except ValueError:
        print(f"industry_research: --today {t!r} is not YYYY-MM-DD", file=sys.stderr)
        return 2
    st, p, b = status(industry, domain, today)
    rel = str(p.relative_to(ROOT.parent))
    if as_json:
        print(json.dumps({"status": st, "path": rel, "built": b.isoformat() if b else None,
                          "industry": industry, "domain": domain}))
    else:
        print(f"{st} {rel}" + (f" (built {b.isoformat()})" if b else ""))
    return CODES[st]


if __name__ == "__main__":
    sys.exit(main(sys.argv))
