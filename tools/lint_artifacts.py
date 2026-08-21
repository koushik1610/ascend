#!/usr/bin/env python3
"""lint_artifacts.py — the Ascend honesty + language gate (stdlib only).

Scans generated sendable artifacts (résumés, outreach, signals, answer sheets) for the
language rules in `.claude/banned-words.md` / `reference/resume-writing-rules.md`, plus an
optional per-user forbidden-number / retracted-claim list. Replaces the ad-hoc greps that
real runs relied on (2026-07-01 run council, P0-1).

Checks:
  dash        em dashes anywhere; en dashes used as a sentence break (digit–digit ranges OK)
  vocab       banned vocabulary parsed live from .claude/banned-words.md (stem-matched)
  semicolon   clause-joining semicolons in prose ("...x; y..." between lowercase letters)
  colon       dramatic-reveal colons ("The result: ...")
  opener      bullets opening with Successfully/Effectively/Proactively
  numbers     the user's forbidden exact internals (from --config, never shipped in the repo)
  retracted   the user's retracted claims (from --config)
  provenance  a per-job resume.md must carry a DELTA LOG whose cited master entry IDs actually
              EXIST in master-resume.md (auto-located, or --master PATH). A cited ID the master
              never declares is the signature of an invented bullet.

Skipped automatically: fenced code blocks, HTML comments, DELTA LOG blocks, MASTER GAP notes,
FICTIONAL SAMPLE banners — those are meta, not sendable prose.

Usage:
  python3 tools/lint_artifacts.py FILE_OR_DIR [...] [--config lint-config.json]
                                  [--master master-resume.md] [--list]
  Config JSON shape: {"forbidden_patterns": ["regex", ...], "retracted_patterns": ["regex", ...],
                      "allow_vocab": ["ecosystem", ...]}

Vocabulary waivers: several banned words are conditional in .claude/banned-words.md ("ecosystem
*(unless literally a technical system)*"). Waive one per run via "allow_vocab", or per file with an
inline `<!-- lint-allow: ecosystem, dynamic -->`. Waivers are explicit and greppable by design.

Exit codes: 0 clean · 1 findings · 2 usage/config error.
The gate FLAGS for a human; it never rewrites (run council DA-3).
"""

import json
import re
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BANNED_WORDS_FILE = REPO / ".claude" / "banned-words.md"

# Sendable artifacts only. The internal master-resume.md library is deliberately NOT here
# (its annotation/protocol sections aren't sendable prose); its bullets are gated when they
# are selected into a per-job resume.md, and the public master-resume.json IS gated.
SENDABLE_NAMES = re.compile(
    r"^(resume\.md|outreach\.md|signal\.md|answer-bank\.md|"
    r"answer-sheet\.md|resume\.json|master-resume\.json)$"
)

DRAMATIC_COLON = re.compile(
    r"\b(the\s+)?(result|results|outcome|impact|payoff|bottom\s+line|takeaway)\s*:", re.I
)
BAD_OPENER = re.compile(r"^\s*[-*•]\s*(successfully|effectively|proactively)\b[, ]", re.I)
# A clause-joining semicolon. Digits count as a clause end ("...NPS from 22 to 41; mentors...") and
# the second clause may wrap to the next line, so also flag a trailing semicolon at end of line.
# Both forms shipped undetected in examples/sample-run (2026-08-20 council).
CLAUSE_SEMICOLON = re.compile(r"[a-z0-9)%]\s*;(\s+[a-z]|\s*$)")
EM_DASH = re.compile(r"—")
# an en dash is fine in ranges ("10–12pt", "Mar 2021 – Present"); flag it only when used
# as a sentence break between two non-date words
_DATEISH = re.compile(
    r"^(\d[\d,.]*\w*|Jan\w*|Feb\w*|Mar\w*|Apr\w*|May|Jun\w*|Jul\w*|Aug\w*|Sep\w*|Oct\w*|"
    r"Nov\w*|Dec\w*|Present|Now|Current|Today)$", re.I
)


def en_dash_break(line):
    for m in re.finditer(r"(\S+) – (\S+)", line):
        left = m.group(1).strip("\"'()[]*_,.")
        right = m.group(2).strip("\"'()[]*_,.")
        if not (_DATEISH.match(left) or _DATEISH.match(right)):
            return True
    return False
# A master entry ID as the master résumé declares and cites them: E1/E12a (experience bullets),
# P1 (projects), M7 (metrics bank), S3/D2 (packet stories). Deliberately NARROW: the old
# r"\b[A-Z]{1,4}-?\d{1,3}\b" matched S3, EC2, K8, GPT-4 and SOC-2, so essentially every technical
# résumé satisfied the provenance check incidentally (2026-08-20 council).
MASTER_ID = re.compile(r"\b([EPMSD]\d{1,3}[a-z]?)\b")
# How the master DECLARES an entry: "#### E1, label" / "### P1 — name" / "| M7 | ... |".
MASTER_DECL_HEAD = re.compile(r"^#{2,4}\s+([EPMSD]\d{1,3}[a-z]?)\b")
MASTER_DECL_ROW = re.compile(r"^\|\s*([EPMSD]\d{1,3}[a-z]?)\s*\|")


# A Delta Log entry: a bullet, a numbered item, or an indented continuation of one.
DELTA_ENTRY = re.compile(r"^(\s{2,}\S|\s*[-*•]\s|\s*\d+[.)]\s|\s*[A-Za-z][\w /&-]{0,40}:\s)")


def parse_master_ids(path):
    """Collect the entry IDs a master résumé actually declares."""
    ids = set()
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    for line in text.splitlines():
        for rx in (MASTER_DECL_HEAD, MASTER_DECL_ROW):
            m = rx.match(line.strip() if rx is MASTER_DECL_ROW else line)
            if m:
                ids.add(m.group(1))
    return ids


def find_master(resume_path):
    """A per-job résumé lives at workspace/<name>/jobs/<NN>-slug/resume.md."""
    for up in (resume_path.parent.parent.parent, resume_path.parent.parent):
        cand = up / "master-resume.md"
        if cand.is_file():
            return cand
    return None


def delta_block(text):
    """The Delta Log block only. IDs cited elsewhere in the file don't count as provenance."""
    out, inside = [], False
    for line in text.splitlines():
        s = line.strip()
        m = re.search(r"\bDELTA LOG\b", s, re.I)
        if m:
            inside = True
            # A one-line Delta Log ("<!-- DELTA LOG: selected E1, E2 -->") carries its IDs on this
            # same line, so keep the remainder rather than only the lines below.
            out.append(s[m.end():])
            continue
        if inside:
            if not s or s.startswith("---") or s.startswith("#") or s.startswith("-->"):
                if s.startswith("-->") or s.startswith("---") or s.startswith("#"):
                    break
                continue
            out.append(s)
    return "\n".join(out)


def parse_banned_words(path=BANNED_WORDS_FILE):
    """Pull the banned single words and multi-word phrases out of banned-words.md."""
    words, phrases = set(), set()
    if not path.exists():
        return words, phrases
    section = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("##"):
            head = line.lower()
            if any(k in head for k in ("verbs", "adjectives", "nouns", "transitions", "clichés", "cliches")):
                section = head
            else:
                section = None
            continue
        if not section or not line.strip():
            continue
        for item in line.split("·"):
            item = re.sub(r"\*\(.*?\)\*", "", item)          # drop *(unless …)* notes
            item = re.sub(r"\(.*?\)", "", item)               # drop plain parentheticals
            item = item.strip().strip("\"“”'.").strip()
            if not item or item.startswith("#"):
                continue
            token = item.lower()
            if " " in token:
                phrases.add(token)
            elif re.fullmatch(r"[a-z][a-z\-]+", token):
                words.add(token)
    return words, phrases


def build_vocab_regexes(words, phrases):
    regs = []
    if words:
        # stem-match common inflections: leverage → leverages/leveraged/leveraging
        alts = "|".join(sorted(re.escape(w) for w in words))
        regs.append(re.compile(rf"\b({alts})(s|es|ed|d|ing)?\b", re.I))
    for p in sorted(phrases):
        regs.append(re.compile(re.escape(p), re.I))
    return regs


def iter_prose_lines(text):
    """Yield (lineno, line) for sendable prose, skipping meta blocks."""
    in_code = in_delta = in_comment = False
    for i, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if s.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if "<!--" in line:
            in_comment = "-->" not in line
            continue
        if in_comment:
            in_comment = "-->" not in line
            continue
        if re.search(r"\bDELTA LOG\b", line, re.I):
            in_delta = True
            continue
        if in_delta:
            # The template puts the Delta Log inside an HTML comment (handled above), so this branch
            # only sees an UNCOMMENTED one. It used to skip everything until a `---` or a heading,
            # which meant a résumé whose Delta Log wasn't comment-wrapped had its entire body
            # exempted: invented content, an em dash and five banned words all linted CLEAN
            # (2026-08-20 council, reproducer in tests/smoke.py).
            #
            # A Delta Log is a list. Skip its entries (bullets, numbered items, indented
            # continuations, blank spacer lines) and end the block at the first line that is none of
            # those, re-processing that line as ordinary prose.
            if not s or DELTA_ENTRY.match(line):
                continue
            in_delta = False
        if "FICTIONAL SAMPLE" in line or "MASTER GAP" in line:
            continue
        yield i, line


LINT_ALLOW = re.compile(r"<!--\s*lint-allow:\s*([^>]*?)\s*-->", re.I)


def collect_allowed_vocab(text, config_allow):
    """Words this file may legitimately use, despite the banned list.

    `.claude/banned-words.md` marks several words conditional ("ecosystem *(unless literally a
    technical system)*"), but parse_banned_words strips the parenthetical, so "Kafka ecosystem
    migration" and "dynamic programming" were flagged as slop with no way to say otherwise
    (2026-08-20 council). Two escape hatches, both explicit and both auditable:
      - "allow_vocab": ["ecosystem", ...] in the run's lint-config.json
      - <!-- lint-allow: ecosystem, dynamic --> anywhere in the file
    """
    allowed = {w.strip().lower() for w in config_allow if w.strip()}
    for m in LINT_ALLOW.finditer(text):
        allowed |= {w.strip().lower() for w in m.group(1).split(",") if w.strip()}
    return allowed


def lint_text(text, fname, vocab_regexes, forbidden, retracted, allowed_vocab=frozenset()):
    findings = []
    # Never-publish values and retracted claims are checked over EVERY line, including the meta
    # blocks the prose scanner skips. A forbidden internal number must not sit in a Delta Log or a
    # MASTER GAP note inside a file that gets sent (2026-08-20 council).
    for i, raw in enumerate(text.splitlines(), 1):
        for rx in forbidden:
            if rx.search(raw):
                findings.append((fname, i, "numbers", f"forbidden internal value: {rx.pattern!r}"))
        for rx in retracted:
            if rx.search(raw):
                findings.append((fname, i, "retracted", f"retracted claim: {rx.pattern!r}"))
    for i, line in iter_prose_lines(text):
        if EM_DASH.search(line):
            findings.append((fname, i, "dash", "em dash (use period/comma/colon)"))
        if en_dash_break(line):
            findings.append((fname, i, "dash", "en dash as sentence break"))
        if CLAUSE_SEMICOLON.search(line):
            findings.append((fname, i, "semicolon", "clause-joining semicolon"))
        m = DRAMATIC_COLON.search(line)
        if m:
            findings.append((fname, i, "colon", f"dramatic-reveal colon: {m.group(0)!r}"))
        if BAD_OPENER.search(line):
            findings.append((fname, i, "opener", "bullet opens with Successfully/Effectively/Proactively"))
        for rx in vocab_regexes:
            for m in rx.finditer(line):
                # group(1) is the uninflected stem for the word alternation ("optimized" → "optimize"
                # is not captured, but "optimized" matches stem "optimized"/"optimize" per the
                # banned list's own spelling); phrase regexes have no groups, so fall back to the
                # whole match. Waiving a stem waives its inflections.
                stem = (m.group(1) if m.re.groups else m.group(0)).lower()
                if stem in allowed_vocab or m.group(0).lower() in allowed_vocab:
                    continue
                findings.append((fname, i, "vocab", f"banned word: {m.group(0)!r}"))
    return findings


def lint_provenance(text, fname, master_ids=None):
    """A per-job resume.md must be selection, not invention: DELTA LOG + REAL master IDs.

    When the master résumé is found, every ID the Delta Log cites is checked against the IDs the
    master actually declares. A cited ID that does not exist in the master is the exact signature of
    an invented bullet, and it used to pass (see MASTER_ID above).
    """
    findings = []
    if not re.search(r"\bDELTA LOG\b", text, re.I):
        findings.append((fname, 1, "provenance", "no DELTA LOG (selection record) found"))
        return findings
    cited = set(MASTER_ID.findall(delta_block(text)))
    if not cited:
        findings.append((fname, 1, "provenance", "DELTA LOG cites no master entry IDs"))
        return findings
    if master_ids is None:
        findings.append((fname, 1, "provenance",
                         f"master-resume.md not found, {len(cited)} cited ID(s) UNVERIFIED"))
    elif not master_ids:
        findings.append((fname, 1, "provenance", "master-resume.md declares no entry IDs to check against"))
    else:
        for cid in sorted(cited - master_ids):
            findings.append((fname, 1, "provenance",
                             f"DELTA LOG cites {cid!r}, which the master résumé does not declare "
                             "(invention, or a stale ID)"))
    return findings


MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
DATE_RANGE_START = re.compile(r"([A-Za-z]{3,9})?\.?\s*(\d{4})")
YEARS_CLAIM = re.compile(r"\b(\d{1,2})\+?\s*(?:years|yrs)\b", re.I)
# A keyword written only as a glyph is invisible to ATS keyword search and to a recruiter's Boolean
# query, and can break PDF text extraction. Each pair is (glyph form, the ASCII form that must also
# appear somewhere in the document).
GLYPH_KEYWORDS = [("0→1", ("0 to 1", "zero to one", "zero-to-one", "0-to-1"))]


def _start_key(dates):
    """Sort key for a 'Mar 2021 – Present' style range: (year, month) of the START date."""
    m = DATE_RANGE_START.search(dates or "")
    if not m:
        return None
    mon = MONTHS.get((m.group(1) or "")[:3].lower(), 1)
    return (int(m.group(2)), mon)


def lint_scan_gate(data, fname):
    """The seven-second recruiter scan + ATS parse gate over a structured résumé.

    These are the defects a recruiter rejects on without ever giving feedback, so the candidate never
    learns why. All three were live in examples/sample-run when this was written (2026-08-20 council).
    """
    findings = []
    basics = data.get("basics") or {}
    work = [w for w in (data.get("work") or []) if isinstance(w, dict)]

    # 1. Reverse-chronological order. A current role listed below an older one reads as concealment
    #    and is the single fastest reject in a résumé screen.
    keys = [(w, _start_key(w.get("dates"))) for w in work]
    dated = [(w, k) for w, k in keys if k]
    for (w1, k1), (w2, k2) in zip(dated, dated[1:]):
        if k1 < k2:
            findings.append((fname, 1, "scan",
                             f"work history is not reverse-chronological: "
                             f"{w1.get('company')!r} ({w1.get('dates')}) is listed above "
                             f"{w2.get('company')!r} ({w2.get('dates')})"))
            break

    # 2. A stated years-of-experience claim that contradicts the dates on the same page.
    text = " ".join(str(basics.get(k) or "") for k in ("label", "summary"))
    earliest = min((k for _, k in dated), default=None)
    if earliest:
        span = date.today().year - earliest[0]
        for m in YEARS_CLAIM.finditer(text):
            claimed = int(m.group(1))
            if abs(claimed - span) >= 2:
                findings.append((fname, 1, "scan",
                                 f"summary claims {claimed} years but the earliest role starts "
                                 f"{earliest[0]} (~{span} years). Reconcile, or the page "
                                 "contradicts itself"))
                break

    # 3. A load-bearing keyword that exists only as a glyph.
    whole = json.dumps(data, ensure_ascii=False)
    for glyph, ascii_forms in GLYPH_KEYWORDS:
        if glyph in whole and not any(a in whole.lower() for a in ascii_forms):
            findings.append((fname, 1, "scan",
                             f"{glyph!r} appears only as a glyph. It is not keyword-searchable and "
                             f"can break PDF text extraction. Also write it once as one of: "
                             + ", ".join(repr(a) for a in ascii_forms)))
    return findings


def collect_files(args):
    files = []
    for a in args:
        p = Path(a)
        if p.is_dir():
            for f in sorted(p.rglob("*")):
                if f.is_file() and SENDABLE_NAMES.match(f.name):
                    files.append(f)
        elif p.is_file():
            files.append(p)
        else:
            print(f"lint_artifacts: not found: {a}", file=sys.stderr)
            sys.exit(2)
    return files


def main(argv):
    argv = argv[1:]
    config_path, list_only, paths, master_path = None, False, [], None
    it = iter(argv)
    for a in it:
        if a == "--config":
            config_path = next(it, None)
        elif a == "--master":
            master_path = next(it, None)
        elif a == "--list":
            list_only = True
        elif a in ("-h", "--help"):
            print(__doc__)
            return 0
        else:
            paths.append(a)
    if not paths:
        print(__doc__)
        return 2

    forbidden, retracted, config_allow = [], [], []
    if config_path:
        try:
            cfg = json.loads(Path(config_path).read_text(encoding="utf-8"))
            forbidden = [re.compile(p) for p in cfg.get("forbidden_patterns", [])]
            retracted = [re.compile(p, re.I) for p in cfg.get("retracted_patterns", [])]
            config_allow = list(cfg.get("allow_vocab", []))
        except (OSError, ValueError, re.error) as e:
            print(f"lint_artifacts: bad config {config_path}: {e}", file=sys.stderr)
            return 2

    words, phrases = parse_banned_words()
    vocab = build_vocab_regexes(words, phrases)

    files = collect_files(paths)
    if list_only:
        for f in files:
            print(f)
        return 0

    all_findings = []
    for f in files:
        try:
            text = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            all_findings.append((str(f), 0, "io", str(e)))
            continue
        allowed = collect_allowed_vocab(text, config_allow)
        all_findings += lint_text(text, str(f), vocab, forbidden, retracted, allowed)
        if f.suffix == ".json":
            try:
                all_findings += lint_scan_gate(json.loads(text), str(f))
            except ValueError as e:
                all_findings.append((str(f), 0, "scan", f"not valid JSON: {e}"))
        if f.name == "resume.md" and f.parent.parent.name == "jobs":
            mp = Path(master_path) if master_path else find_master(f)
            all_findings += lint_provenance(text, str(f),
                                            parse_master_ids(mp) if mp else None)

    for fname, line, cat, msg in all_findings:
        print(f"{fname}:{line}: [{cat}] {msg}")
    n = len(all_findings)
    print(f"\nlint_artifacts: {len(files)} file(s), {n} finding(s) — "
          + ("CLEAN ✓" if n == 0 else "REVIEW REQUIRED (the gate flags; a human decides)"))
    return 0 if n == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
