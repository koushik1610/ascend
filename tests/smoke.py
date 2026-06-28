#!/usr/bin/env python3
"""
S.P.I.D.E.R. smoke tests — dependency-free (Python 3 stdlib + git). Run:  python3 tests/smoke.py

Covers the regressions a human won't catch by eye, all fast:
  1. The hardened /spiderui server: token + Host allowlist + Origin + path-traversal (the security fix).
  2. Every HTML dashboard's embedded JSON block parses (a bad block blanks the dashboard).
  3. The gitignore privacy matrix: personal data ignored, system + the committed sample tracked.
  4. Repo cross-references resolve (catches prompt/template drift + dead links).
  5. The UI shell scripts pass `bash -n`, server.py compiles, the daily-brief `--check` self-test runs.
  6. The /view reader's scheme allow-list (SEC-CRIT-2) is present and its strict CSP is served.
  7. The phase run-order stays single-sourced (00-orchestrator == CLAUDE.md == spiderui.md).
  8. On-demand ops stay discoverable on both surfaces (command file ⇄ 00-orchestrator).
  9. The résumé builder is self-contained + `server.py --render` makes a selectable-text PDF (or fails clean).
Exits non-zero if anything fails — wired into CI (.github/workflows/ci.yml).
"""
import http.client, json, re, shutil, subprocess, sys, time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FAILS = []
def check(name, ok, detail=""):
    print(f"  {'✓' if ok else '✗'} {name}" + (f"  — {detail}" if detail and not ok else ""))
    if not ok:
        FAILS.append(name)

# ── 1. Hardened server ───────────────────────────────────────────────────────
def test_server():
    print("server (security)")
    port = 8911
    proc = subprocess.Popen([sys.executable, str(REPO / "ui/server.py"), "--port", str(port), "--no-browser"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(1.4)
        def req(method, path, headers=None, host=None):
            c = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            h = dict(headers or {});  h["Host"] = host or f"127.0.0.1:{port}"
            c.request(method, path, headers=h); r = c.getresponse(); b = r.read().decode("utf-8", "replace"); c.close()
            return r.status, b
        s, body = req("GET", "/")
        m = re.search(r'const TOKEN = "([^"]+)"', body)
        tok = m.group(1) if m else ""
        check("GET / serves page with a real token", s == 200 and tok and tok != "__SPIDER_TOKEN__")
        check("GET /api/agents WITHOUT token → 403", req("GET", "/api/agents")[0] == 403)
        check("GET /api/agents WITH token → 200", req("GET", "/api/agents", {"X-SPIDER-Token": tok})[0] == 200)
        check("forged Host (DNS-rebind) → 403", req("GET", "/api/agents", {"X-SPIDER-Token": tok}, host="evil.com")[0] == 403)
        check("path traversal → 404", req("GET", "/workspace/../../../../etc/passwd")[0] == 404)
        check("forged Origin POST → 403 (no side effect)",
              req("POST", "/api/shutdown", {"X-SPIDER-Token": tok, "Origin": "http://evil.com"})[0] == 403)
        check("server still alive after forged shutdown", req("GET", "/api/agents", {"X-SPIDER-Token": tok})[0] == 200)
        # SEC-CRIT-2: the /view markdown reader. Link sanitization is client-side, but guard the
        # defense-in-depth CSP server-side and the scheme allow-list statically.
        smoke_md = REPO / "workspace/_sec_smoke/x.md"
        smoke_md.parent.mkdir(parents=True, exist_ok=True)
        smoke_md.write_text("[evil](javascript:alert(1)) and [ok](https://example.com)\n", encoding="utf-8")
        try:
            def reqh(path):  # like req() but also return headers
                c = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
                c.request("GET", path, headers={"X-SPIDER-Token": tok, "Host": f"127.0.0.1:{port}"})
                r = c.getresponse(); b = r.read().decode("utf-8", "replace"); h = dict(r.getheaders()); c.close()
                return r.status, b, h
            st, body2, hdrs = reqh("/view/_sec_smoke/x.md")
            csp = hdrs.get("Content-Security-Policy", "")
            check("/view served", st == 200)
            check("/view sets strict CSP (nonce script-src + connect-src none)",
                  "script-src 'nonce-" in csp and "connect-src 'none'" in csp)
            check("/view template placeholders fully substituted", "__NONCE__" not in body2 and "__MD__" not in body2)
        finally:
            shutil.rmtree(REPO / "workspace/_sec_smoke", ignore_errors=True)
    finally:
        proc.terminate()
        try: proc.wait(timeout=5)
        except Exception: proc.kill()
        (REPO / "ui/.port").unlink(missing_ok=True)

# ── 2. HTML JSON blocks parse ────────────────────────────────────────────────
def test_html_json():
    print("dashboards (JSON data blocks)")
    htmls = list((REPO / "templates").glob("*.html")) + list((REPO / "examples").rglob("*.html"))
    pat = re.compile(r'<script type="application/json"[^>]*>(.*?)</script>', re.S)
    found = False
    for f in htmls:
        for block in pat.findall(f.read_text(encoding="utf-8")):
            found = True
            try:
                json.loads(block); ok = True
            except Exception as e:
                ok = False; check(f"{f.relative_to(REPO)} JSON parses", False, str(e))
            if ok: check(f"{f.relative_to(REPO)} JSON parses", True)
    check("found at least one JSON dashboard", found)

# ── 3. gitignore privacy matrix ──────────────────────────────────────────────
def test_gitignore():
    print("gitignore (privacy matrix)")
    def ignored(p):
        # Force case-sensitive matching so macOS (core.ignorecase=true) catches gaps that would only
        # bite on a case-sensitive Linux box — e.g. `Resume.pdf` vs a lowercase-only pattern.
        return subprocess.run(["git", "-c", "core.ignorecase=false", "check-ignore", "-q", p],
                              cwd=REPO).returncode == 0
    must_ignore = ["workspace/jane/master-resume.md", "workspace/jane/jobs/01-acme/resume.md",
                   "workspace/jane/inputs/linkedin-export/Connections.csv", "workspace/jane/start-here.html",
                   "examples/realperson/master-resume.md", "examples/realperson/inputs/Connections.csv",
                   "Resume.pdf", "cover-letter.md", "ui/.port", "images/spider_gold.jpg"]
    must_track = ["README.md", "ui/server.py", "prompts/00-orchestrator.md",
                  "examples/sample-run/master-resume.md", "examples/sample-run/start-here.html",
                  "images/spider_unsplash.jpg", "images/spider_unsplash2.jpg"]
    for p in must_ignore: check(f"ignored: {p}", ignored(p))
    for p in must_track:  check(f"tracked: {p}", not ignored(p))

# ── 4. Repo cross-references resolve ─────────────────────────────────────────
def test_crossrefs():
    print("cross-references (drift)")
    files = list((REPO / "prompts").glob("*.md")) + [REPO / "templates/job-folder/_TEMPLATE.md",
            REPO / "CLAUDE.md", REPO / "README.md", REPO / "START-HERE.md"]
    ref = re.compile(r'(?:\.\./)*(?:prompts|templates|reference|docs|ui|assets)/[A-Za-z0-9_./-]+\.(?:md|html|css|svg|py|sh)')
    missing = []
    for f in files:
        for raw in ref.findall(f.read_text(encoding="utf-8")):
            rel = re.sub(r'^(\.\./)+', '', raw)
            if not (REPO / rel).exists():
                missing.append(f"{f.name} → {raw}")
    check("all repo cross-references resolve", not missing, "; ".join(missing[:6]))
    # SEC-CRIT-1: every prompt that ingests web/file content must carry the injection quarantine.
    ingesting = ["01-linkedin-analysis", "04-job-search", "09-maintenance", "10-deep-prep",
                 "11-network-map", "13-daily-briefing"]
    no_quarantine = [p for p in ingesting
                     if "untrusted-content-policy" not in (REPO / f"prompts/{p}.md").read_text(encoding="utf-8")]
    check("ingesting prompts cite the injection quarantine (SEC-CRIT-1)", not no_quarantine,
          "missing in: " + ", ".join(no_quarantine))

# ── 4b. Phase run-order stays single-sourced ─────────────────────────────────
def test_phase_order():
    print("phase run-order (single-source)")
    canon = (REPO / "prompts/00-orchestrator.md").read_text(encoding="utf-8")
    m = re.search(r"Default run order:\s*([0-9 →>-]+?)\.", canon)
    order = re.sub(r"\s+", "", m.group(1)) if m else ""
    check("canonical run order found in 00-orchestrator.md", bool(order),
          "no 'Default run order:' line")
    for f in ["CLAUDE.md", ".claude/commands/spiderui.md"]:
        txt = re.sub(r"\s+", "", (REPO / f).read_text(encoding="utf-8"))
        check(f"{f} matches the canonical run order", bool(order) and order in txt,
              f"expected {order!r}")

# ── 4c. On-demand ops stay discoverable on every surface ─────────────────────
def test_op_parity():
    # Every documented `/spider <op>` must appear in BOTH the command file (canonical op list) and
    # the orchestrator (so a user reading either surface can find it). Catches the kind of menu drift
    # where an op exists in one place but not the other. Case-insensitive substring match.
    print("op parity (command ⇄ orchestrator)")
    OPS = ["resume", "job add", "prep", "network", "answers", "today",
           "score", "export", "maintenance", "job rebuild", "build-resume"]
    cmd = (REPO / ".claude/commands/spider.md").read_text(encoding="utf-8").lower()
    orch = (REPO / "prompts/00-orchestrator.md").read_text(encoding="utf-8").lower()
    for op in OPS:
        check(f"op '{op}' documented in spider.md", op in cmd)
        check(f"op '{op}' documented in 00-orchestrator.md", op in orch)

# ── 4d. Résumé builder + render path ─────────────────────────────────────────
def test_resume_builder():
    print("résumé builder (template + render)")
    import tempfile, os
    tpl = REPO / "templates/resume-builder.template.html"
    check("builder template exists", tpl.is_file())
    if not tpl.is_file():
        return
    html = tpl.read_text(encoding="utf-8")
    # data island present and parses (empty object at rest)
    m = re.search(r'<script type="application/json" id="resume-data">(.*?)</script>', html, re.S)
    check("builder has a resume-data island", bool(m))
    if m:
        try:
            json.loads(m.group(1).strip()); check("data island parses as JSON", True)
        except Exception as e:
            check("data island parses as JSON", False, str(e))
    # self-contained: no external script/style/asset references
    ext = re.findall(r'(?:src|href)\s*=\s*"(https?:|//)', html)
    check("builder is self-contained (no external assets)", not ext, "; ".join(set(ext)))
    # print CSS hides the builder chrome (prints only the résumé)
    check("print CSS hides the editor chrome",
          bool(re.search(r'@media print[^}]*\{[^@]*\.editor', html, re.S)) or
          ".editor, .pagewarn" in html or "display: none !important" in html)
    check("locked résumé layout present (single-column scope)", '.resume-page' in html and '.resume ' in html)

    # render path through the trusted server (the allowed `python3 ui/server.py*` form)
    sample = {"basics": {"name": "Test User", "label": "Engineer", "email": "t@example.com",
                         "location": "Remote", "summary": "One line summary."},
              "work": [{"company": "Acme", "position": "Engineer", "dates": "2020 - Present",
                        "highlights": ["Did a measurable thing that improved a number by 20%."]}],
              "projects": [], "education": [], "skills": ["Python", "Testing"]}
    d = Path(tempfile.mkdtemp(prefix="spider-resume-"))
    try:
        filled = re.sub(r'(<script type="application/json" id="resume-data">)\s*\{\}\s*(</script>)',
                        lambda mm: mm.group(1) + "\n" + json.dumps(sample) + "\n" + mm.group(2), html, count=1)
        check("data island is fillable", filled != html)
        fin = d / "filled.html"; fin.write_text(filled, encoding="utf-8")
        out = d / "out.pdf"
        r = subprocess.run([sys.executable, str(REPO / "ui/server.py"), "--render", str(fin), "--out", str(out)],
                           capture_output=True, text=True, timeout=130)
        if r.returncode == 0:
            raw = out.read_bytes() if out.is_file() else b""
            check("render produced a PDF", out.is_file() and raw[:4] == b"%PDF")
            check("rendered PDF has selectable text (ATS parse)", b"/Font" in raw and re.search(rb"\b(Tj|TJ)\b", raw) is not None)
        else:
            # no Chrome-class engine on this box: must fail gracefully with the manual fallback
            check("no-engine render fails gracefully with fallback message",
                  ("Save as PDF" in r.stderr or "print to PDF" in r.stderr), r.stderr.strip()[:120])
    finally:
        shutil.rmtree(d, ignore_errors=True)

# ── 5. Scripts compile / lint ────────────────────────────────────────────────
def test_scripts():
    print("scripts & config")
    check("server.py compiles",
          subprocess.run([sys.executable, "-m", "py_compile", str(REPO / "ui/server.py")]).returncode == 0)
    src = (REPO / "ui/server.py").read_text(encoding="utf-8")
    check("reader has a link scheme allow-list (SEC-CRIT-2)",
          "blocked non-http link" in src and "https?:" in src)
    settings = REPO / ".claude/settings.json"
    try:
        perms = json.loads(settings.read_text(encoding="utf-8")).get("permissions", {})
        allow, deny = perms.get("allow", []), perms.get("deny", [])
        check("no RCE interpreter pre-approved in allow (SEC-HIGH-3)",
              not any(a.startswith(("Bash(node", "Bash(deno", "Bash(bun", "Bash(ruby",
                                    "Bash(perl", "Bash(php", "Bash(osascript")) for a in allow))
        check("RCE interpreters + exfil tools denied (SEC-HIGH-3)",
              "Bash(node *)" in deny and "Bash(nc *)" in deny and "Bash(ssh *)" in deny)
    except Exception as e:
        check("settings.json permissions parse", False, str(e))
    if settings.exists():
        try:
            json.loads(settings.read_text(encoding="utf-8")); check(".claude/settings.json is valid JSON", True)
        except Exception as e:
            check(".claude/settings.json is valid JSON", False, str(e))
    if shutil.which("bash"):
        check("run-daily-brief.sh passes bash -n",
              subprocess.run(["bash", "-n", str(REPO / "ui/run-daily-brief.sh")]).returncode == 0)
        # --check self-test must run cleanly (0 = a CLI is present, 2 = none found) — never crash.
        rc = subprocess.run(["bash", str(REPO / "ui/run-daily-brief.sh"), "--check"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode
        check("run-daily-brief.sh --check exits cleanly (0 or 2)", rc in (0, 2), f"rc={rc}")
    else:
        print("  – bash not found, skipping shell lint")

if __name__ == "__main__":
    for t in (test_server, test_html_json, test_gitignore, test_crossrefs, test_phase_order, test_op_parity, test_resume_builder, test_scripts):
        try: t()
        except Exception as e:
            check(f"{t.__name__} raised", False, repr(e))
    print()
    if FAILS:
        print(f"FAILED ({len(FAILS)}): " + ", ".join(FAILS)); sys.exit(1)
    print("All smoke tests passed ✓")
