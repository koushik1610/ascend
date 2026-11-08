#!/usr/bin/env python3
"""render_resume.py — resume.json → LaTeX → ATS-safe PDF (stdlib only).

The LaTeX path is Ascend's default résumé renderer. It produces two artifacts:

  <name>.tex   always, with no toolchain required. Compilable in Overleaf.
  <name>.pdf   when a TeX engine is installed locally.

Layout lives entirely in `templates/resume-latex.template.tex`. This script only
populates it: it emits calls to the template's macros and never raw formatting,
so filling a résumé cannot reintroduce a parsing hazard (the failure mode the
whole exercise exists to avoid).

Falling back: with no TeX engine, the .tex is still written and the caller is
told to either install one or use the HTML builder path
(`python3 ui/server.py --render <builder.html> --out <pdf>`). The pipeline never
hard-fails for want of LaTeX.

Usage:
  python3 tools/render_resume.py RESUME.json [--out OUT.pdf] [--tex OUT.tex]
                                 [--max-pages N] [--engine BIN] [--check]

  --check   validate and write the .tex, skip compilation (no engine needed).

Exit codes: 0 ok · 1 render/validation problem · 2 usage error.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _paths  # noqa: E402  (local helper; see tools/_paths.py for why it is not a command)

REPO = Path(__file__).resolve().parent.parent
TEMPLATE = REPO / "templates" / "resume-latex.template.tex"
MARKER = "%%ASCEND-CONTENT%%"

# Engines in preference order. tectonic is self-contained and needs no format
# files; the latex* family is what a normal TeX Live install provides.
ENGINES = ("tectonic", "latexmk", "pdflatex", "xelatex", "lualatex")

# LaTeX specials. Backslash must be substituted first or it re-escapes the
# replacements that follow it.
_ESCAPES = (
    ("\\", r"\textbackslash{}"),
    ("&", r"\&"),
    ("%", r"\%"),
    ("$", r"\$"),
    ("#", r"\#"),
    ("_", r"\_"),
    ("{", r"\{"),
    ("}", r"\}"),
    ("~", r"\textasciitilde{}"),
    ("^", r"\textasciicircum{}"),
)
# Invisible code points (Cf: zero-width space/joiners, soft hyphen, BOM, the U+E0000 tag block)
# are REMOVED, not escaped. They reached the .tex untouched before, so a résumé could ship text that
# renders as nothing and still extracts — hidden keywords inside a submitted PDF. The linter now
# fails them upstream (`scan`); this is the belt to that braces, because the renderer is also
# reachable from the builder and from a hand-edited resume.json.
_INVISIBLE = re.compile(r"[\u00ad\u200b-\u200f\u2028-\u202e\u2060-\u2064\ufeff"
                        r"\U000e0000-\U000e007f\U000e0100-\U000e01ef]")

# Characters a résumé picks up from smart editors and from our own templates.
_UNICODE = (
    ("\u2014", "---"), ("\u2013", "--"), ("\u2018", "`"), ("\u2019", "'"),
    ("\u201c", "``"), ("\u201d", "''"), ("\u2026", r"\ldots{}"),
    ("\u00b7", r"\textbar{}"), ("\u2022", r"\textbullet{}"), ("\u00a0", "~"),
    # No math mode anywhere. A math glyph carries no ToUnicode entry, so "0->1"
    # would extract as "01" and silently lose meaning. Text-mode only.
    ("\u2192", "->"), ("\u00d7", "x"), ("\u2212", "-"), ("\u2264", "<="),
    ("\u2265", ">="), ("\u00b1", "+/-"), ("\u00bd", "1/2"),
)


def tex_escape(s) -> str:
    """Make an arbitrary string safe to drop into LaTeX body text."""
    if s is None:
        return ""
    out = _INVISIBLE.sub("", str(s))
    for a, b in _ESCAPES:
        out = out.replace(a, b)
    for a, b in _UNICODE:
        out = out.replace(a, b)
    return out.strip()


def find_engine(preferred: str | None = None) -> str | None:
    if preferred:
        # Only the known engines. `--engine` used to spawn any binary shutil.which() could resolve,
        # which is an arbitrary-executable primitive inside an allow-listed command.
        if preferred not in ENGINES:
            print(f"render_resume: unknown engine {preferred!r}. "
                  f"Choose one of: {', '.join(ENGINES)}", file=sys.stderr)
            return None
        return preferred if shutil.which(preferred) else None
    for e in ENGINES:
        if shutil.which(e):
            return e
    return None


def build_body(d: dict) -> str:
    """resume.json → the macro calls that fill the template's content marker."""
    L: list[str] = []
    head = L
    b = d.get("basics") or {}

    L.append(r"\resumename{%s}" % tex_escape(b.get("name", "")))
    if b.get("label"):
        L.append(r"\resumelabel{%s}" % tex_escape(b["label"]))

    contact = [b.get(k) for k in ("email", "phone", "location", "url")]
    contact = [tex_escape(c) for c in contact if c]
    if contact:
        L.append(r"\resumecontact{%s}" % r" \textbar{} ".join(contact))
    L.append(r"\resumerule")

    if b.get("summary"):
        # The executive variant replaces "Summary" with a "Leadership Profile", per
        # reference/resume-writing-rules.md -> Resume variants. The heading was hardcoded, so the
        # sanctioned export path silently shipped an executive resume headed "Summary". The template
        # already parameterises \resumesection, so one optional key is the whole fix. Anything but a
        # short plain label is ignored rather than injected into the .tex.
        label = str(b.get("summaryLabel") or "Summary").strip()
        if not re.fullmatch(r"[A-Za-z][A-Za-z &-]{0,38}", label):
            label = "Summary"
        L.append("")
        L.append(r"\resumesection{%s}" % tex_escape(label))
        L.append(r"\resumeline{%s}" % tex_escape(b["summary"]))

    # Sections are built as blocks, then emitted in the order the master's `§0 Section order` chose
    # (reference/resume-writing-rules.md -> Section order). "early-career" leads with Skills and
    # Education; anything else, including a missing key, is the default Experience-first order.
    S = {}

    S["experience"] = L = []
    work = d.get("work") or []
    if work:
        L.append("")
        L.append(r"\resumesection{Experience}")
        for w in work:
            L.append(r"\resumeentry{%s}{%s}{%s}" % (
                tex_escape(w.get("position", "")),
                tex_escape(w.get("company", "")),
                tex_escape(w.get("dates", "")),
            ))
            if w.get("location"):
                L.append(r"\resumesub{%s}" % tex_escape(w["location"]))
            highlights = [h for h in (w.get("highlights") or []) if str(h).strip()]
            if highlights:
                L.append(r"\begin{resumebullets}")
                L += [r"  \item %s" % tex_escape(h) for h in highlights]
                L.append(r"\end{resumebullets}")

    S["projects"] = L = []
    projects = [p for p in (d.get("projects") or []) if (p.get("name") or p.get("description"))]
    if projects:
        L.append("")
        L.append(r"\resumesection{Projects}")
        for p in projects:
            L.append(r"\resumeproject{%s}{%s}" % (
                tex_escape(p.get("name", "")), tex_escape(p.get("dates", ""))))
            desc = " ".join(x for x in (p.get("role"), p.get("description")) if x)
            if desc:
                L.append(r"\resumeline{%s}" % tex_escape(desc))

    S["skills"] = L = []
    skills = [s for s in (d.get("skills") or []) if str(s).strip()]
    if skills:
        L.append("")
        L.append(r"\resumesection{Skills}")
        L.append(r"\resumeline{%s}" % r" \textbar{} ".join(tex_escape(s) for s in skills))

    S["education"] = L = []
    education = d.get("education") or []
    if education:
        L.append("")
        L.append(r"\resumesection{Education}")
        for e in education:
            parts = [e.get("studyType"), e.get("institution"), e.get("location"), e.get("dates")]
            line = ", ".join(tex_escape(p) for p in parts if p)
            if line:
                L.append(r"\resumeline{%s}" % line)

    S["certifications"] = L = []
    certs = d.get("certifications") or []
    if certs:
        L.append("")
        L.append(r"\resumesection{Certifications}")
        if isinstance(certs, str):
            certs = [certs]
        L.append(r"\resumeline{%s}" % r" \textbar{} ".join(tex_escape(c) for c in certs))


    order = (["skills", "education", "experience", "projects", "certifications"]
             if str(d.get("sectionOrder") or "").strip().lower() == "early-career"
             else ["experience", "projects", "skills", "education", "certifications"])
    L = head
    for key in order:
        L += S[key]
    return "\n".join(L)


def validate(tex: str) -> list[str]:
    """Static checks that catch the breakages we can find without a compiler."""
    problems = []
    if MARKER in tex:
        problems.append("content marker was not replaced")
    if tex.count(r"\begin{document}") != 1 or tex.count(r"\end{document}") != 1:
        problems.append("document environment is not balanced")
    if tex.count(r"\begin{resumebullets}") != tex.count(r"\end{resumebullets}"):
        problems.append("resumebullets environment is not balanced")
    # Unescaped specials in body text. Ignore the preamble, where they are ours.
    body = tex.split(r"\begin{document}", 1)[-1]
    for line in body.splitlines():
        if line.lstrip().startswith("%"):
            continue
        stripped = re.sub(r"\\[a-zA-Z]+\{?|\\[&%$#_{}]|\$[^$]*\$", "", line)
        for ch in ("&", "%", "$", "#", "_"):
            if ch in stripped:
                problems.append(f"unescaped {ch!r} in body: {line.strip()[:70]}")
                break
    depth = 0
    for ch in body:
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        if depth < 0:
            problems.append("unbalanced closing brace in body")
            break
    if depth > 0:
        problems.append("unbalanced opening brace in body")
    return problems


def _safe_inflate(b):
    try:
        return zlib.decompressobj().decompress(b)
    except zlib.error:
        return b""


def _pdf_text(pdf: bytes) -> str:
    """Extract text through the PDF's own ToUnicode CMaps.

    This is what an ATS does. A glyph with no ToUnicode entry is invisible to it,
    which is why this reads the CMaps rather than just asserting Tj/TJ exist.
    """
    streams = [_safe_inflate(m.group(1))
               for m in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", pdf, re.S)]
    streams = [s for s in streams if s]
    cmap, width = {}, 1
    for st in streams:
        cs = re.search(rb"begincodespacerange\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", st)
        if cs:
            width = max(width, len(cs.group(1)) // 2)
        for blk in re.findall(rb"beginbfchar(.*?)endbfchar", st, re.S):
            for src, dst in re.findall(rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", blk):
                cmap[int(src, 16)] = bytes.fromhex(dst.decode()).decode("utf-16-be", "replace")
        for blk in re.findall(rb"beginbfrange(.*?)endbfrange", st, re.S):
            for lo, hi, dst in re.findall(
                    rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", blk):
                lo, hi = int(lo, 16), int(hi, 16)
                base = bytes.fromhex(dst.decode()).decode("utf-16-be", "replace")
                for i in range(lo, hi + 1):
                    cmap[i] = chr(ord(base[0]) + i - lo) if base else "?"
    out = []
    for st in streams:
        if not re.search(rb"\b(Tj|TJ)\b", st):
            continue
        for t in re.finditer(rb"<([0-9A-Fa-f]+)>|\((?:[^()\\]|\\.)*\)", st):
            g = t.group(0)
            raw = (bytes.fromhex(g[1:-1].decode()) if g.startswith(b"<")
                   else re.sub(rb"\\([()\\])", rb"\1", g[1:-1]))
            codes = ([int.from_bytes(raw[i:i + 2], "big") for i in range(0, len(raw) - 1, 2)]
                     if width == 2 else list(raw))
            out.append("".join(cmap.get(c, "�") for c in codes))
    return "".join(out)


def verify_text_layer(pdf: Path, must_contain=()) -> tuple[str, list[str]]:
    """Read the PDF the way an ATS does and report what a parser would actually see.

    Why this exists: the renderer enforced the PAGE BUDGET and nothing else, so "the PDF is
    ATS-safe" meant "the PDF exists and has one page". The failure modes that cost a candidate an
    application are all silent and all invisible to a page count:

      * the contact line rendered as icon-font glyphs, so the parsed record has a name, a work
        history and no email address — a shortlistable candidate with no reachable human attached;
      * ligatures or a missing ToUnicode map, so "fintech" extracts as "ntech" and the résumé
        misses the recruiter's Boolean search;
      * a scrambled reading order, so the database holds the wrong current employer.

    An extractor for exactly this already existed — in `tests/smoke.py`, pointed at one committed
    sample, skipped entirely when no TeX engine was installed, and therefore never run against the
    file a user submits. It now lives here and the test imports it, so there is one copy.

    Returns (extracted_text, problems). Tri-state on purpose: an empty `problems` list with little
    text means "could not read the text layer", which is reported rather than passed — a binary
    verdict would have to lie in that case. ToUnicode presence is context in the message, never the
    assertion: a PDF can carry a CMap per font and still extract as eight ligatures (demonstrated
    on the committed sample), and a wrong CMap entry maps cleanly to the wrong character.
    """
    raw = pdf.read_bytes()
    txt = _pdf_text(raw)
    flat = re.sub(r"\s+", "", txt)
    problems = []
    ligatures = [lig for lig in "\ufb00\ufb01\ufb02\ufb03\ufb04\ufb05\ufb06" if lig in txt]
    if ligatures:
        problems.append(
            "ligature glyphs survive into the text layer (" + " ".join(ligatures) + "): a word like "
            "'first' extracts as 'ﬁrst', so a recruiter's search for 'first' — or for 'fintech', "
            "'benefit', 'workflow' — does not match it. The LaTeX template disables these; a PDF "
            "produced any other way may not.")
    if "\ufffd" in txt:
        n = txt.count("\ufffd")
        i = txt.index("\ufffd")
        problems.append(f"{n} glyph(s) have no usable ToUnicode entry, so a parser reads them as "
                        f"garbage. First one here: {txt[max(0, i - 30):i + 30]!r}")
    for needle in must_contain:
        if needle and re.sub(r"\s+", "", str(needle)) not in flat:
            problems.append(f"not found in the text layer: {str(needle)[:60]!r} — a parser cannot "
                            "read it, whatever the page looks like")
    return txt, problems


def page_count(pdf: Path) -> int:
    """Count pages, including PDFs that pack page objects into object streams.

    tectonic/XeTeX compresses the object tree by default, so a raw scan finds
    nothing. Inflate every Flate stream and count there instead. Same approach
    the smoke harness uses for Chrome output.
    """
    data = pdf.read_bytes()
    n = len(re.findall(rb"/Type\s*/Page[^s]", data))
    if n:
        return n
    for sm in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", data, re.S):
        try:
            n += len(re.findall(rb"/Type\s*/Page[^s]",
                                zlib.decompressobj().decompress(sm.group(1))))
        except zlib.error:
            continue
    return n


def compile_pdf(tex_path: Path, out_pdf: Path, engine: str) -> tuple[bool, str]:
    """Compile with shell-escape OFF.

    Résumé content can trace back to a fetched job posting, and LaTeX's \\write18
    would turn a document into a command execution primitive. tex_escape() already
    neutralises backslashes so no macro can be injected through content, but the
    engine flag is the boundary that does not depend on that being perfect.
    tectonic disables shell escape by default and offers no way to enable it here.
    """
    with tempfile.TemporaryDirectory() as td:
        if engine == "tectonic":
            cmd = [engine, "-X", "compile", "--outdir", td, "--keep-logs",
                   "--print", str(tex_path)]
        elif engine == "latexmk":
            cmd = [engine, "-pdf", "-interaction=nonstopmode", "-no-shell-escape",
                   f"-outdir={td}", str(tex_path)]
        else:
            cmd = [engine, "-interaction=nonstopmode", "-halt-on-error", "-no-shell-escape",
                   "-output-directory", td, str(tex_path)]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        except FileNotFoundError:
            return False, f"engine {engine} disappeared from PATH"
        except subprocess.TimeoutExpired:
            return False, f"{engine} timed out after 180s"
        produced = Path(td) / (tex_path.stem + ".pdf")
        if not produced.exists():
            tail = (r.stderr or r.stdout or "").strip().splitlines()[-12:]
            return False, f"{engine} produced no PDF:\n" + "\n".join(tail)
        out_pdf.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(produced, out_pdf)
    return True, ""


def main() -> int:
    ap = argparse.ArgumentParser(description="Render a resume.json to an ATS-safe PDF via LaTeX.")
    ap.add_argument("resume_json")
    ap.add_argument("--out", help="output PDF path (default: alongside the JSON)")
    ap.add_argument("--tex", help="output .tex path (default: alongside the PDF)")
    ap.add_argument("--max-pages", type=int, default=1,
                    help="fail if the PDF exceeds this many pages (default 1; use 2 for the master)")
    ap.add_argument("--engine", help="force a specific TeX engine")
    ap.add_argument("--check", action="store_true",
                    help="write and validate the .tex, skip compilation")
    ap.add_argument("--verify-text", metavar="PDF",
                    help="read an EXISTING PDF's text layer the way an ATS does and report what a "
                         "parser sees, then exit. This is the Overleaf path: when no TeX engine is "
                         "installed the tool hands over a .tex and the PDF is compiled elsewhere, "
                         "so without this no mechanical check ever touches the file that gets "
                         "submitted — exactly the users most at risk.")
    ap.add_argument("--no-text-check", action="store_true",
                    help="skip the post-render text-layer report (it never blocks either way)")
    a = ap.parse_args()

    if a.verify_text:
        pdf = Path(a.verify_text)
        if not pdf.is_file():
            print(f"render_resume: no such PDF: {pdf}", file=sys.stderr)
            return 2
        want = []
        if Path(a.resume_json).is_file():
            b = (json.loads(Path(a.resume_json).read_text(encoding="utf-8")).get("basics") or {})
            # Contact details only. A headline legitimately differs between the master public
            # résumé and a per-job one, so asserting `label` across an arbitrary PDF/JSON pair
            # reports a mismatch that is not a defect.
            want = [b.get("email"), b.get("phone"), b.get("name")]
        txt, problems = verify_text_layer(pdf, [w for w in want if w])
        print(f"text layer: {len(txt)} characters extracted from {pdf}")
        if len(txt) < 200:
            print("render_resume: almost nothing extracted. Either the PDF has no text layer "
                  "(a scan or an image), or its fonts carry no usable ToUnicode map. An ATS would "
                  "read this as an empty résumé. Run the manual parse test in "
                  "prompts/08-export-pdf.md before submitting.", file=sys.stderr)
            return 1
        for pr in problems:
            print(f"  ! {pr}", file=sys.stderr)
        print("  text layer looks parseable" if not problems else
              "  fix the above, or verify by pasting the PDF into a text editor")
        return 1 if problems else 0

    src = Path(a.resume_json)
    if not src.exists():
        print(f"render_resume: no such file: {src}", file=sys.stderr)
        return 2
    try:
        data = json.loads(src.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"render_resume: {src} is not valid JSON: {e}", file=sys.stderr)
        return 2
    if not TEMPLATE.exists():
        print(f"render_resume: missing template {TEMPLATE}", file=sys.stderr)
        return 2

    # Confine both outputs. The Bash allow-list pins this tool by path prefix and constrains none of
    # its arguments, so before this an allow-listed `--tex /anywhere` wrote outside the repo and made
    # CLAUDE.md's "writes only under workspace/" claim false for tools.
    out_pdf = _paths.guard(a.out, default=src.with_suffix(".pdf"))
    tex_path = _paths.guard(a.tex, default=out_pdf.with_suffix(".tex"))

    raw = TEMPLATE.read_text(encoding="utf-8")
    # Replace the marker LINE, not every occurrence of the string. The marker must
    # appear exactly once and on a line of its own, or an injected body would land
    # in the preamble and fail with an undefined control sequence.
    lines = raw.splitlines()
    hits = [i for i, ln in enumerate(lines) if ln.strip() == MARKER]
    if len(hits) != 1:
        print(f"render_resume: template must contain exactly one {MARKER} line, found {len(hits)}",
              file=sys.stderr)
        return 2
    lines[hits[0]] = build_body(data)
    tex = "\n".join(lines) + "\n"
    problems = validate(tex)
    tex_path.parent.mkdir(parents=True, exist_ok=True)
    tex_path.write_text(tex, encoding="utf-8")
    if problems:
        print("render_resume: LaTeX validation failed:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        print(f"  (the .tex was still written to {tex_path} so you can inspect it)", file=sys.stderr)
        return 1
    print(f"TEX: {tex_path}")

    if a.check:
        print("checked only, compilation skipped (--check)")
        return 0

    engine = find_engine(a.engine)
    if not engine:
        print("render_resume: no TeX engine found (looked for: " + ", ".join(ENGINES) + ").")
        print(f"  The .tex is ready at {tex_path}. Two ways forward:")
        print("    1. Upload it to overleaf.com and compile there (no install).")
        print("    2. Install one locally: brew install tectonic")
        print("  Or use the HTML path: python3 ui/server.py --render <builder.html> --out <pdf>")
        return 1

    ok, err = compile_pdf(tex_path, out_pdf, engine)
    if not ok:
        print(f"render_resume: {err}", file=sys.stderr)
        print(f"  The .tex at {tex_path} is still valid input for Overleaf.", file=sys.stderr)
        return 1

    pages = page_count(out_pdf)
    print(f"PDF: {out_pdf}  ({engine}, {pages} page{'s' if pages != 1 else ''})")
    if a.max_pages and pages > a.max_pages:
        print(f"render_resume: {pages} pages exceeds the {a.max_pages}-page budget. "
              f"Cut CONTENT per reference/resume-writing-rules.md. Never shrink the type.",
              file=sys.stderr)
        return 1

    if not a.no_text_check:
        # The page budget says the PDF is the right SHAPE. This says a parser can read it.
        # Reported, never fatal — the budget is a rule the user chose, a garbled glyph is a
        # warning they need to see and act on with the deadline they actually have.
        b = data.get("basics") or {}
        want = [b.get("email"), b.get("phone"), b.get("name")]
        txt, problems = verify_text_layer(out_pdf, [w for w in want if w])
        if len(txt) < 200:
            print(f"  ! text layer: only {len(txt)} characters extracted — an ATS would read this "
                  "as nearly empty. Check the fonts, then the manual parse test in "
                  "prompts/08-export-pdf.md.", file=sys.stderr)
        elif problems:
            for pr in problems:
                print(f"  ! {pr}", file=sys.stderr)
        else:
            print(f"  text layer: {len(txt)} characters, contact details parse as literal text")
    return 0


if __name__ == "__main__":
    sys.exit(main())
