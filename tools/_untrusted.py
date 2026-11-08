#!/usr/bin/env python3
"""_untrusted.py — de-smuggle untrusted text before anything reads it (stdlib only).

NOT an allow-listed command, deliberately. Like `_paths.py`, the leading underscore marks it as a
module the tools import, never a `python3 tools/<x>.py` form. Two reasons:

  1. `.claude/settings.json` pins a Bash entry by **path prefix and places no constraint on the
     arguments** (the weakness `_paths.py` was written to contain). A scanner invoked as a command,
     with untrusted text or — worse — a URL on argv, turns an allow-listed entry into a primitive
     that attacker-influenced content can aim.
  2. A scanner the model is *told* to run is itself an instruction-level control, which is the exact
     class of defence it exists to replace. Called from inside the tools, it needs no cooperation.

## What was actually wrong

`reference/untrusted-content-policy.md` says a posting is data, never instructions, and CLAUDE.md is
honest that this is "constrained by judgment + the quarantine, not capability". Meanwhile the two
deterministic ingest paths **laundered** hidden content into clean-looking prose. `finder.clean()` and
`gmail_sync._strip_html()` both did, in effect:

    s = html.unescape(s)                    # &#8203; becomes a real zero-width space
    s = re.sub(r"<[^>]+>", " ", s)          # removes the wrapper, KEEPS the hidden text

So a `<div style="display:none">` payload came out indistinguishable from the visible job text: the
only thing removed was the evidence that it was hidden. The ordering is the bug — hidden-CSS
detection has to happen *before* tag removal.

## The candidate cost, which is not hypothetical

`prefilter.keyword_overlap` matches by literal substring. `"Pyt​hon"` does not contain
`"python"`, and `re.sub(r"\s+", " ")` does not strip U+200B because Python's `\s` does not match it.
A posting the user is well matched to therefore scores a lower overlap, sorts lower, and never gets
scored. The commonest source of these characters is not an attacker at all — it is a JD drafted in
Word and pasted into a portal, which arrives full of `&#8203;` and soft hyphens.

## Scope, and what is deliberately NOT here

Removal is the defence: an invisible code point has no legitimate use in a job posting, so stripping
it has no false-positive cost. Heuristic *flagging* does, so this module does not do it:

  - **No instruction-shaped-line detection.** A posting for an SSH administrator legitimately says
    "SSH", and almost every posting says "Please submit your resume as a PDF". A classifier in the
    hot path would fire on both.
  - **No Latin/Cyrillic look-alike detection.** "Яндекс" and Greek-market roles are not attacks.

Both remain the quarantine's job, where a human reads the quoted text. What this module guarantees is
narrower and absolute: the model is never handed bytes it cannot see.

Honest limit: this covers the **tool-mediated** ingest paths. Where a prompt has the model WebFetch a
posting directly (Phase 4, engine B), the content is in context before any Python could run. No tool
can sit in front of a WebFetch result. That is a reason to route ingestion through the tools, not a
reason to skip this.
"""

import re
import unicodedata

# U+E0000-E007F: the Unicode tag block, one invisible code point per ASCII character. A sentence
# written in it renders as nothing, survives copy-paste, and reads to a model as the ASCII it
# mirrors ("ASCII smuggling"). Decoded before removal so an anomaly row can quote what it said.
TAG_RUN = re.compile("[\U000E0000-\U000E007F]{3,}")
# Variation selectors pick a glyph variant and render as nothing alone; a RUN of them carries one
# byte each and is a payload. A lone one (the VS16 in an emoji) is ordinary encoding noise.
VARIATION_RUN = re.compile("[︀-️\U000E0100-\U000E01EF]{2,}")

# Read the way a browser reads it, after entity decoding. Only inline `style=` and <style> rules —
# class-based hiding needs a CSS cascade this deliberately does not implement.
HIDDEN_STYLE = re.compile(
    r"display\s*:\s*none"
    r"|visibility\s*:\s*hidden"
    r"|opacity\s*:\s*0(?![.\d]*[1-9])"
    r"|font-size\s*:\s*0(?:\.0+)?(?:px|pt|em|rem|%)?(?![\d.])"
    r"|color\s*:\s*transparent"
    r"|clip-path\s*:\s*inset\(\s*100%"
    r"|(?:left|top|text-indent)\s*:\s*-\d{4,}px",
    re.I,
)
# An element carrying a hidden style, plus its content, up to the matching close of the SAME tag
# name. Nested same-name tags are rare in a posting and cost only over-removal of hidden content.
HIDDEN_EL = re.compile(
    r"<(?P<t>[a-zA-Z][\w:-]*)\b[^>]*?(?:style\s*=\s*(?P<q>[\"'])(?P<s>[^\"']*)(?P=q)|\bhidden\b)"
    r"[^>]*>(?P<body>.*?)</(?P=t)\s*>",
    re.I | re.S,
)
DROP_BLOCKS = re.compile(r"<(script|style|noscript|svg|template)\b[^>]*>.*?(?:</\1\s*>|\Z)", re.I | re.S)
COMMENT = re.compile(r"<!--.*?(?:-->|\Z)", re.S)


def decode_tag_chars(s):
    """U+E0000-block run -> the ASCII it mirrors, so a finding can quote the attacker's sentence."""
    return "".join(chr(ord(c) - 0xE0000) for c in s if 0xE0000 <= ord(c) <= 0xE007F)


def strip_invisible(text):
    """Remove every code point a human cannot see. Returns (clean_text, findings).

    `findings` is a list of {kind, count, text?} — data for an `## Anomalies & ignored directives`
    row, never a reason to block. Blocking on anomalies would hand an attacker a denial of service
    over the queue: one crafted posting and the run stops.
    """
    findings, out = [], text or ""

    for m in TAG_RUN.finditer(out):
        decoded = decode_tag_chars(m.group(0))
        if decoded.strip():
            findings.append({"kind": "ascii_smuggling", "count": len(m.group(0)),
                             "text": decoded[:200]})
    n = len(VARIATION_RUN.findall(out))
    if n:
        findings.append({"kind": "variation_selector_run", "count": n})

    # Strip every Cf (format) code point: zero-width space/joiners, soft hyphen, bidi controls,
    # BOM, and the whole tag block. unicodedata rather than a hand-kept list, so a code point added
    # to the category in a later Unicode version is covered without an edit here.
    kept, removed = [], 0
    for ch in out:
        cat = unicodedata.category(ch)
        if cat == "Cf" or VARIATION_RUN.fullmatch(ch * 2):
            removed += 1
            continue
        kept.append(ch)
    out = "".join(kept)
    if removed:
        findings.append({"kind": "invisible_chars", "count": removed})

    # NFKC folds look-alike compatibility forms (a fullwidth 'Ｐ' to 'P'), so keyword matching
    # downstream sees one spelling. It does not touch distinct scripts, which is correct — a
    # Cyrillic 'а' stays a Cyrillic 'а' rather than being silently rewritten into Latin.
    return unicodedata.normalize("NFKC", out), findings


def strip_hidden_html(html_text):
    """Remove hidden elements and their CONTENT, before tags are flattened. Returns (html, findings).

    Call this *before* any `re.sub(r"<[^>]+>", " ", ...)`. Reversed, the tag removal deletes the
    `style="display:none"` wrapper and promotes the payload to ordinary visible text, which is
    precisely the laundering this fixes.
    """
    findings, out = [], html_text or ""
    out = DROP_BLOCKS.sub(" ", out)   # script/style/noscript/svg/template: every page has them
    out = COMMENT.sub(" ", out)

    def _drop(m):
        style = m.group("s") or ""
        if m.group("s") is not None and not HIDDEN_STYLE.search(style):
            return m.group(0)
        body = re.sub(r"<[^>]+>", " ", m.group("body"))
        body = re.sub(r"\s+", " ", body).strip()
        if body:
            findings.append({"kind": "hidden_html", "count": len(body), "text": body[:200]})
        return " "

    for _ in range(3):      # a few passes so nested hidden elements collapse
        new = HIDDEN_EL.sub(_drop, out)
        if new == out:
            break
        out = new
    return out, findings


def clean_untrusted(raw, is_html=True):
    """The one call the ingest tools make: hidden HTML out, invisibles out, findings reported.

    Run this BEFORE any character budget is applied. A smuggled payload is one invisible code point
    per character, so ~1,500 of them can eat the entire text allowance the scorer was given — trim
    first and the crowd-out survives the fix.
    """
    findings = []
    text = raw or ""
    if is_html:
        text, f = strip_hidden_html(text)
        findings += f
    text, f = strip_invisible(text)
    return text, findings + f


def summarize(findings):
    """One line for a tool's stdout, or '' when clean. Keeps a run's output honest about what ran."""
    if not findings:
        return ""
    by = {}
    for f in findings:
        by[f["kind"]] = by.get(f["kind"], 0) + f.get("count", 1)
    return "untrusted text: " + ", ".join(f"{k}={v}" for k, v in sorted(by.items()))
