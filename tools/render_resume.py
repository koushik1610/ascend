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
    out = str(s)
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
        L.append("")
        L.append(r"\resumesection{Summary}")
        L.append(r"\resumeline{%s}" % tex_escape(b["summary"]))

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

    skills = [s for s in (d.get("skills") or []) if str(s).strip()]
    if skills:
        L.append("")
        L.append(r"\resumesection{Skills}")
        L.append(r"\resumeline{%s}" % r" \textbar{} ".join(tex_escape(s) for s in skills))

    education = d.get("education") or []
    if education:
        L.append("")
        L.append(r"\resumesection{Education}")
        for e in education:
            parts = [e.get("studyType"), e.get("institution"), e.get("location"), e.get("dates")]
            line = ", ".join(tex_escape(p) for p in parts if p)
            if line:
                L.append(r"\resumeline{%s}" % line)

    certs = d.get("certifications") or []
    if certs:
        L.append("")
        L.append(r"\resumesection{Certifications}")
        if isinstance(certs, str):
            certs = [certs]
        L.append(r"\resumeline{%s}" % r" \textbar{} ".join(tex_escape(c) for c in certs))

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
    a = ap.parse_args()

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
    return 0


if __name__ == "__main__":
    sys.exit(main())
