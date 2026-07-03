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
  provenance  a per-job resume.md must carry a DELTA LOG citing master entry IDs

Skipped automatically: fenced code blocks, HTML comments, DELTA LOG blocks, MASTER GAP notes,
FICTIONAL SAMPLE banners — those are meta, not sendable prose.

Usage:
  python3 tools/lint_artifacts.py FILE_OR_DIR [...] [--config lint-config.json] [--list]
  Config JSON shape: {"forbidden_patterns": ["regex", ...], "retracted_patterns": ["regex", ...]}

Exit codes: 0 clean · 1 findings · 2 usage/config error.
The gate FLAGS for a human; it never rewrites (run council DA-3).
"""

import json
import re
import sys
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
CLAUSE_SEMICOLON = re.compile(r"[a-z)]\s*;\s+[a-z]")
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
MASTER_ID = re.compile(r"\b[A-Z]{1,4}-?\d{1,3}\b")


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
            # a delta block ends at a rule line or a markdown heading
            if s.startswith("---") or s.startswith("#"):
                in_delta = False
            continue
        if "FICTIONAL SAMPLE" in line or "MASTER GAP" in line:
            continue
        yield i, line


def lint_text(text, fname, vocab_regexes, forbidden, retracted):
    findings = []
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
                findings.append((fname, i, "vocab", f"banned word: {m.group(0)!r}"))
        for rx in forbidden:
            if rx.search(line):
                findings.append((fname, i, "numbers", f"forbidden internal value: {rx.pattern!r}"))
        for rx in retracted:
            if rx.search(line):
                findings.append((fname, i, "retracted", f"retracted claim: {rx.pattern!r}"))
    return findings


def lint_provenance(text, fname):
    """A per-job resume.md must be selection, not invention: DELTA LOG + master IDs."""
    findings = []
    if not re.search(r"\bDELTA LOG\b", text, re.I):
        findings.append((fname, 1, "provenance", "no DELTA LOG (selection record) found"))
    elif not MASTER_ID.search(text):
        findings.append((fname, 1, "provenance", "DELTA LOG cites no master entry IDs"))
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
    config_path, list_only, paths = None, False, []
    it = iter(argv)
    for a in it:
        if a == "--config":
            config_path = next(it, None)
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

    forbidden, retracted = [], []
    if config_path:
        try:
            cfg = json.loads(Path(config_path).read_text(encoding="utf-8"))
            forbidden = [re.compile(p) for p in cfg.get("forbidden_patterns", [])]
            retracted = [re.compile(p, re.I) for p in cfg.get("retracted_patterns", [])]
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
        all_findings += lint_text(text, str(f), vocab, forbidden, retracted)
        if f.name == "resume.md" and f.parent.parent.name == "jobs":
            all_findings += lint_provenance(text, str(f))

    for fname, line, cat, msg in all_findings:
        print(f"{fname}:{line}: [{cat}] {msg}")
    n = len(all_findings)
    print(f"\nlint_artifacts: {len(files)} file(s), {n} finding(s) — "
          + ("CLEAN ✓" if n == 0 else "REVIEW REQUIRED (the gate flags; a human decides)"))
    return 0 if n == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
