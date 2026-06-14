#!/usr/bin/env python3
"""
S.P.I.D.E.R. smoke tests — dependency-free (Python 3 stdlib + git). Run:  python3 tests/smoke.py

Covers the regressions a human won't catch by eye, all fast:
  1. The hardened /spiderui server: token + Host allowlist + Origin + path-traversal (the security fix).
  2. Every HTML dashboard's embedded JSON block parses (a bad block blanks the dashboard).
  3. The gitignore privacy matrix: personal data ignored, system + the committed sample tracked.
  4. Repo cross-references resolve (catches prompt/template drift + dead links).
  5. The UI shell scripts pass `bash -n`, and server.py compiles.
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
        return subprocess.run(["git", "check-ignore", "-q", p], cwd=REPO).returncode == 0
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

# ── 5. Scripts compile / lint ────────────────────────────────────────────────
def test_scripts():
    print("scripts & config")
    check("server.py compiles",
          subprocess.run([sys.executable, "-m", "py_compile", str(REPO / "ui/server.py")]).returncode == 0)
    settings = REPO / ".claude/settings.json"
    if settings.exists():
        try:
            json.loads(settings.read_text(encoding="utf-8")); check(".claude/settings.json is valid JSON", True)
        except Exception as e:
            check(".claude/settings.json is valid JSON", False, str(e))
    if shutil.which("bash"):
        check("run-daily-brief.sh passes bash -n",
              subprocess.run(["bash", "-n", str(REPO / "ui/run-daily-brief.sh")]).returncode == 0)
    else:
        print("  – bash not found, skipping shell lint")

if __name__ == "__main__":
    for t in (test_server, test_html_json, test_gitignore, test_crossrefs, test_scripts):
        try: t()
        except Exception as e:
            check(f"{t.__name__} raised", False, repr(e))
    print()
    if FAILS:
        print(f"FAILED ({len(FAILS)}): " + ", ".join(FAILS)); sys.exit(1)
    print("All smoke tests passed ✓")
