#!/usr/bin/env python3
"""
Ascend local control server.

A tiny, dependency-free (Python 3 standard library only) server that powers the /ascendui graphical
console. It binds to 127.0.0.1 ONLY — it is a local tool, never exposed to the network. It does the
things a browser can't do on its own: open a native folder/file picker, write your intake, install the
daily-brief schedule, report pipeline progress, and serve your private dashboard over http so links work.

It never sends your data anywhere. Everything it writes lives under workspace/<you>/ (gitignored).

Run directly:  python3 ui/server.py [--port 8765] [--no-browser]
The /ascendui Claude Code command launches it for you.
"""
import argparse, json, os, platform, re, secrets, shlex, shutil, subprocess, sys, threading, webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

REPO = Path(__file__).resolve().parent.parent          # ascend/
UIDIR = REPO / "ui"
TEMPLATES = REPO / "templates"
WORKSPACE = REPO / "workspace"

# Set in main(). The server is local-only, but a localhost port is still reachable by any site you
# visit while it runs, so we defend against CSRF and DNS-rebinding:
#   • Host-header allowlist → a rebound hostname (attacker.com → 127.0.0.1) is rejected.
#   • Per-session TOKEN injected into the served page and required on /api/* → a cross-site fetch can't
#     read the token (CORS hides the page body), so it can't call the API.
#   • No CORS headers → the browser blocks cross-origin reads of /workspace files anyway.
TOKEN = ""
PORT = 0


def slugify(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", (name or "").strip().lower()).strip("-")
    return s or "me"


def detect_agents():
    """Which agentic CLIs are installed (the engine that runs the analysis)."""
    found = []
    for cli, label in [("claude", "Claude Code"), ("gemini", "Gemini CLI"), ("codex", "Codex CLI")]:
        if shutil.which(cli):
            found.append({"cli": cli, "label": label})
    return found


def find_chrome():
    """Locate a Chrome-class engine (Chrome/Chromium/Edge/Brave) for headless PDF rendering.

    Returns an absolute path string, or None if nothing usable is installed. Render is the one feature
    that needs a real browser engine; everything else here is stdlib-only.
    """
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
                 "microsoft-edge", "brave-browser", "chrome"):
        hit = shutil.which(name)
        if hit:
            return hit
    sysname = platform.system()
    candidates = []
    if sysname == "Darwin":
        candidates = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        ]
    elif sysname == "Windows":
        candidates = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        ]
    for c in candidates:
        if Path(c).exists():
            return c
    return None


def render_pdf(input_html: str, out_pdf: str):
    """Render a local résumé-builder HTML file to an ATS-safe PDF via headless Chrome.

    The HTML is loaded as a file:// URL (no network) and printed with the page's own print CSS, which
    shows only the résumé. Returns (ok: bool, message: str). On a missing engine it returns ok=False
    with the manual fallback instructions rather than raising — the caller tells the user to open the
    file and press Cmd/Ctrl-P.
    """
    src = Path(input_html).resolve()
    if not src.is_file():
        return False, f"input HTML not found: {src}"
    out = Path(out_pdf).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    chrome = find_chrome()
    if not chrome:
        return False, ("No Chrome-class engine found. Open this file in your browser and press "
                       f"Cmd/Ctrl-P -> Save as PDF (Background graphics off):\n  {src}")
    cmd = [chrome, "--headless", "--disable-gpu", "--no-pdf-header-footer",
           f"--print-to-pdf={out}", src.as_uri()]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except Exception as e:
        return False, f"render failed to launch ({e}). Fallback: open {src} and print to PDF."
    if r.returncode != 0 or not out.is_file():
        return False, (f"render returned {r.returncode}; {r.stderr.strip()[:200]}\n"
                       f"Fallback: open {src} and print to PDF.")
    return True, str(out)


def native_pick(kind: str):
    """Open the OS's native folder/file dialog.

    Returns {"path": <abs path or None>, "status": ...} so the UI can tell the cases apart:
      "ok"          — a path was chosen
      "cancelled"   — a picker opened but the user dismissed it (just re-prompt)
      "unavailable" — no native picker on this system (UI should point at the paste-path field)
      "error"       — the picker invocation blew up
    """
    sysname = platform.system()
    try:
        if sysname == "Darwin":
            prompt = "Select your UNZIPPED LinkedIn export folder" if kind == "folder" else "Select your resume file"
            verb = "choose folder" if kind == "folder" else "choose file"
            script = f'POSIX path of ({verb} with prompt "{prompt}")'
            out = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=600)
            path = out.stdout.strip() or None
            return {"path": path, "status": "ok" if path else "cancelled"}
        if sysname == "Linux":
            home = os.path.expanduser("~")
            if shutil.which("zenity"):
                args = ["zenity", "--file-selection"] + (["--directory"] if kind == "folder" else [])
            elif shutil.which("kdialog"):
                args = ["kdialog", "--getexistingdirectory", home] if kind == "folder" \
                    else ["kdialog", "--getopenfilename", home]
            else:
                return {"path": None, "status": "unavailable"}
            out = subprocess.run(args, capture_output=True, text=True, timeout=600)
            path = out.stdout.strip() or None
            return {"path": path, "status": "ok" if path else "cancelled"}
        if sysname == "Windows":
            if kind == "folder":
                ps = ("Add-Type -AssemblyName System.Windows.Forms;"
                      "$d=New-Object System.Windows.Forms.FolderBrowserDialog;"
                      "if($d.ShowDialog() -eq 'OK'){$d.SelectedPath}")
            else:
                ps = ("Add-Type -AssemblyName System.Windows.Forms;"
                      "$d=New-Object System.Windows.Forms.OpenFileDialog;"
                      "if($d.ShowDialog() -eq 'OK'){$d.FileName}")
            out = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=600)
            path = out.stdout.strip() or None
            return {"path": path, "status": "ok" if path else "cancelled"}
    except Exception:
        return {"path": None, "status": "error"}
    return {"path": None, "status": "unavailable"}


def write_intake(data: dict):
    """Persist the wizard answers as workspace/<slug>/intake.md + a ready flag for the pipeline."""
    slug = slugify(data.get("name", ""))
    wdir = WORKSPACE / slug
    (wdir / "inputs").mkdir(parents=True, exist_ok=True)
    md = f"""# Intake — {data.get('name','')}

> Captured by the Ascend console ({data.get('asOf','')}). The pipeline reads this first.

- **Name:** {data.get('name','')}
- **LinkedIn export folder:** {data.get('linkedinPath') or '(not provided yet — see how-to)'}
- **Resume:** {data.get('resumePath') or '(none — build from LinkedIn + interview)'}
- **Target roles:** {data.get('roles','')}
- **Seniority:** {data.get('seniority','')}
- **Target companies / industries:** {data.get('companies','')}
- **Location / work mode:** {data.get('location','')}
- **Compensation target:** {data.get('comp','')}
- **Differentiators:** {data.get('differentiators','')}
- **Honest gaps:** {data.get('gaps','')}
- **Sanitization needs:** {data.get('sanitization','')}
- **Daily brief time:** {data.get('dailyBrief') or '(off)'}
- **Agent CLI:** {data.get('agent','')}
"""
    (wdir / "intake.md").write_text(md, encoding="utf-8")
    for old in WORKSPACE.glob("*/.ui-ready"):    # clear stale flags so the bridge can't mis-route a run
        try: old.unlink()
        except Exception: pass
    (wdir / ".ui-ready").write_text("ready\n", encoding="utf-8")   # the pipeline polls for this
    return slug


def install_daily_brief(slug: str, hhmm: str, agent: str = ""):
    """Install a daily-brief schedule. cron on macOS/Linux; Task Scheduler note on Windows."""
    try:
        h, m = [int(x) for x in hhmm.split(":")]
    except Exception:
        return {"ok": False, "error": "bad time"}
    logp = WORKSPACE / slug / "briefing.log"
    wrapper = UIDIR / "run-daily-brief.sh"
    if platform.system() == "Windows":
        return {"ok": False, "manual": True,
                "note": f"On Windows, schedule Task Scheduler to run: bash {wrapper} {slug} daily at {hhmm}."}
    line = (f"{m} {h} * * * /bin/bash {shlex.quote(str(wrapper))} {shlex.quote(slug)} "
            f"{shlex.quote(agent)} >> {shlex.quote(str(logp))} 2>&1 # Ascend-DAILY-BRIEF-{slug}")
    try:
        existing = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout.splitlines()
        kept = [l for l in existing if f"Ascend-DAILY-BRIEF-{slug}" not in l]
        new = "\n".join(kept + [line]) + "\n"
        subprocess.run(["crontab", "-"], input=new, text=True, check=True)
        return {"ok": True, "time": hhmm}
    except Exception as e:
        return {"ok": False, "error": str(e), "manual": True,
                "note": f"Could not set cron automatically. Add this line via `crontab -e`:\n{line}"}


def read_status(slug: str):
    """Surface pipeline progress for the UI to poll (from the resumability manifest)."""
    statef = WORKSPACE / slug / ".ascend-state.json"
    sh = WORKSPACE / slug / "start-here.html"
    intake = WORKSPACE / slug / "intake.md"
    # "Done" = the dashboard exists AND was (re)generated AFTER the current intake — so a re-run with a
    # fresh intake shows live progress instead of instantly surfacing a stale report from an old run.
    done = sh.exists() and (not intake.exists() or sh.stat().st_mtime >= intake.stat().st_mtime)
    out = {"slug": slug, "phases": {}, "phase": None, "current": "", "log": [],
           "hasDashboard": done}
    if statef.exists():
        try:
            out.update(json.loads(statef.read_text(encoding="utf-8")))   # carries current + log for the live feed
        except Exception:
            out["error"] = "state file unreadable"   # surface it so the console doesn't hang silently
    return out


def build_results(slug: str):
    """The output tree the console's in-app results browser navigates (only files that exist)."""
    w = WORKSPACE / slug
    def it(name, rel):
        p = w / rel
        return {"name": name, "path": rel, "type": "html" if rel.endswith(".html") else "md"} if p.is_file() else None
    groups = []
    overview = [x for x in (it("Start here", "start-here.html"),
                            it("LinkedIn analysis", "linkedin-analysis.html"),
                            it("Master résumé", "master-resume.md"),
                            it("Job queue", "job-queue.md")) if x]
    if overview:
        groups.append({"label": "Overview", "items": overview})
    pk = w / "interview-packet"
    if pk.is_dir():
        items = [{"name": f.stem.replace("-", " ").capitalize(), "path": f"interview-packet/{f.name}", "type": "md"}
                 for f in sorted(pk.glob("*.md"))]
        if items:
            groups.append({"label": "Interview packet", "items": items})
    jobs = w / "jobs"
    if jobs.is_dir():
        items = []
        for jd in sorted(p for p in jobs.iterdir() if p.is_dir()):
            for fn, nm in (("resume.md", "résumé"), ("prep-doc.md", "prep"), ("application-log.md", "log")):
                if (jd / fn).is_file():
                    items.append({"name": f"{jd.name} · {nm}", "path": f"jobs/{jd.name}/{fn}", "type": "md"})
        if items:
            groups.append({"label": "Apply packs", "items": items})
    return {"slug": slug, "groups": groups}


# A self-contained dark "reader" that renders a markdown file (the run's outputs) in the browser — no CDN,
# offline. The file's text is HTML-escaped into a hidden <textarea>; tiny JS reads .value (decoded back to
# the original) and renders it. Served by /view/<slug>/<path>.
READER_SHELL = """<!doctype html><html><head><meta charset="utf-8">
<title>__TITLE__</title><style>
:root{--bg:#0b0f14;--txt:#e6edf3;--muted:#8b97a7;--line:#1f2937;--accent:#5b9dff;--panel:#0f141c}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--txt);
font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;line-height:1.6}
.doc{max-width:820px;margin:0 auto;padding:30px 28px 80px}
h1{font-size:26px;letter-spacing:-.01em;margin:.2em 0 .4em}h2{font-size:13px;text-transform:uppercase;
letter-spacing:.12em;color:var(--muted);border-bottom:1px solid var(--line);padding-bottom:5px;margin:1.6em 0 .7em}
h3{font-size:16px;margin:1.1em 0 .3em}a{color:var(--accent)}
code{font-family:ui-monospace,Menlo,monospace;background:var(--panel);border:1px solid var(--line);
border-radius:5px;padding:1px 5px;font-size:.9em}
pre{background:var(--panel);border:1px solid var(--line);border-radius:9px;padding:12px 14px;overflow:auto}
pre code{background:none;border:0;padding:0}
table{border-collapse:collapse;width:100%;margin:.8em 0;font-size:14px}
th,td{border:1px solid var(--line);padding:7px 10px;text-align:left;vertical-align:top}
th{color:var(--muted);font-weight:600;background:var(--panel)}
blockquote{border-left:3px solid var(--accent);margin:.8em 0;padding:.2em 0 .2em 14px;color:var(--muted)}
hr{border:0;border-top:1px solid var(--line);margin:1.4em 0}ul,ol{padding-left:22px}li{margin:.2em 0}
strong{color:#fff}.blk{color:var(--muted);text-decoration:line-through;cursor:not-allowed}</style></head><body>
<textarea id="md" hidden>__MD__</textarea><div class="doc" id="out"></div>
<script nonce="__NONCE__">
function render(md){
  md = md.replace(/<!--[\\s\\S]*?-->/g,"");
  const esc=s=>s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
  const inl=s=>esc(s).replace(/`([^`]+)`/g,"<code>$1</code>")
    .replace(/\\*\\*([^*]+)\\*\\*/g,"<strong>$1</strong>")
    .replace(/(^|[^*])\\*([^*\\n]+)\\*/g,"$1<em>$2</em>")
    .replace(/\\[([^\\]]+)\\]\\(([^)]+)\\)/g,function(m,t,u){u=u.trim();
      var ok=/^(https?:\\/\\/|mailto:|#|\\/|\\.\\/|\\.\\.\\/)/i.test(u)||!/^[a-z][a-z0-9+.\\-]*:/i.test(u);
      return ok?'<a href="'+u.replace(/"/g,"&quot;")+'" target="_blank" rel="noopener">'+t+'</a>'
              :'<span class="blk" title="blocked non-http link">'+t+'</span>';});
  const L=md.replace(/\\r\\n/g,"\\n").split("\\n");let h="",i=0;
  const cells=r=>r.replace(/^\\s*\\|/,"").replace(/\\|\\s*$/,"").split("|").map(c=>c.trim());
  while(i<L.length){let l=L[i];
    if(/^```/.test(l)){let c="";i++;while(i<L.length&&!/^```/.test(L[i])){c+=L[i]+"\\n";i++}i++;h+="<pre><code>"+esc(c)+"</code></pre>";continue}
    let m=l.match(/^\\s*(#{1,6})\\s+(.*)$/);if(m){const n=m[1].length;h+="<h"+n+">"+inl(m[2])+"</h"+n+">";i++;continue}
    if(/^\\s*([-*_])\\1{2,}\\s*$/.test(l)){h+="<hr>";i++;continue}
    if(/\\|/.test(l)&&i+1<L.length&&/^[\\s|:\\-]+$/.test(L[i+1])&&/-/.test(L[i+1])){
      const hd=cells(l);i+=2;let b=[];while(i<L.length&&/\\|/.test(L[i])&&L[i].trim()){b.push(cells(L[i]));i++}
      h+="<table><thead><tr>"+hd.map(c=>"<th>"+inl(c)+"</th>").join("")+"</tr></thead><tbody>"+
        b.map(r=>"<tr>"+r.map(c=>"<td>"+inl(c)+"</td>").join("")+"</tr>").join("")+"</tbody></table>";continue}
    if(/^\\s*>\\s?/.test(l)){let q="";while(i<L.length&&/^\\s*>\\s?/.test(L[i])){q+=L[i].replace(/^\\s*>\\s?/,"")+" ";i++}h+="<blockquote>"+inl(q)+"</blockquote>";continue}
    if(/^\\s*[-*+]\\s+/.test(l)){let x="";while(i<L.length&&/^\\s*[-*+]\\s+/.test(L[i])){x+="<li>"+inl(L[i].replace(/^\\s*[-*+]\\s+/,""))+"</li>";i++}h+="<ul>"+x+"</ul>";continue}
    if(/^\\s*\\d+\\.\\s+/.test(l)){let x="";while(i<L.length&&/^\\s*\\d+\\.\\s+/.test(L[i])){x+="<li>"+inl(L[i].replace(/^\\s*\\d+\\.\\s+/,""))+"</li>";i++}h+="<ol>"+x+"</ol>";continue}
    if(!l.trim()){i++;continue}
    let p=l;i++;while(i<L.length&&L[i].trim()&&!/^\\s*(#{1,6}\\s|>|[-*+]\\s|\\d+\\.\\s|```)/.test(L[i])&&!/^\\s*([-*_])\\1{2,}\\s*$/.test(L[i])){p+=" "+L[i];i++}
    h+="<p>"+inl(p)+"</p>"}
  return h}
document.getElementById("out").innerHTML=render(document.getElementById("md").value);
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json", headers=None):
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode()
        elif isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):       # quiet
        pass

    def _body(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        if not n:
            return {}
        try:
            return json.loads(self.rfile.read(n).decode() or "{}")
        except Exception:
            return {}

    # --- request-origin defenses (see TOKEN/PORT note up top) ---
    def _host_ok(self):
        host = (self.headers.get("Host") or "").lower()
        return host in (f"127.0.0.1:{PORT}", f"localhost:{PORT}")

    def _origin_ok(self):
        o = self.headers.get("Origin")
        return (not o) or o.lower() in (f"http://127.0.0.1:{PORT}", f"http://localhost:{PORT}")

    def _token_ok(self):
        return bool(TOKEN) and self.headers.get("X-Ascend-Token") == TOKEN

    def do_GET(self):
        if not self._host_ok():
            return self._send(403, {"error": "bad host"})
        u = urlparse(self.path)
        if u.path in ("/", "/index.html"):
            html = (UIDIR / "index.html").read_text(encoding="utf-8").replace("__Ascend_TOKEN__", TOKEN)
            return self._send(200, html, "text/html; charset=utf-8")
        if u.path in ("/resume-builder", "/resume-builder.html"):     # standalone builder (blank)
            html = (TEMPLATES / "resume-builder.template.html").read_text(encoding="utf-8")
            # Same default-src 'none' posture as /view. The builder is dual-use (also opened straight
            # off disk as a file://), so it can't rely on a server-substituted nonce — its own inline
            # script/style run via 'unsafe-inline'. The load-bearing control is connect-src 'none':
            # a malicious résumé.json renders as DOM text and still can't phone home.
            csp = ("default-src 'none'; img-src 'self' data:; style-src 'unsafe-inline'; "
                   "script-src 'unsafe-inline'; connect-src 'none'; base-uri 'none'; form-action 'none'")
            return self._send(200, html, "text/html; charset=utf-8",
                              {"Content-Security-Policy": csp, "X-Content-Type-Options": "nosniff",
                               "Referrer-Policy": "no-referrer"})
        if u.path.startswith("/api/") and not self._token_ok():
            return self._send(403, {"error": "forbidden"})
        if u.path == "/api/agents":
            return self._send(200, {"agents": detect_agents(), "platform": platform.system()})
        if u.path == "/api/status":
            slug = parse_qs(u.query).get("slug", [""])[0]
            return self._send(200, read_status(slugify(slug)))
        if u.path == "/api/results":
            slug = parse_qs(u.query).get("slug", [""])[0]
            return self._send(200, build_results(slugify(slug)))
        if u.path == "/api/exists":     # does a finished report already exist for this name?
            slug = slugify(parse_qs(u.query).get("name", [""])[0])
            return self._send(200, {"slug": slug, "hasReport": (WORKSPACE / slug / "start-here.html").exists()})
        if u.path.startswith("/view/"):
            return self._serve_md_reader(u.path)
        if u.path.startswith("/workspace/"):
            return self._serve_dir(WORKSPACE, "/workspace/", u.path)
        if u.path.startswith("/images/"):
            return self._serve_dir(REPO / "images", "/images/", u.path)
        return self._send(404, {"error": "not found"})

    def do_POST(self):
        if not self._host_ok():
            return self._send(403, {"error": "bad host"})
        if not self._origin_ok():
            return self._send(403, {"error": "bad origin"})
        u = urlparse(self.path)
        if u.path.startswith("/api/") and not self._token_ok():
            return self._send(403, {"error": "forbidden"})
        if u.path == "/api/pick":
            kind = parse_qs(u.query).get("type", ["folder"])[0]
            return self._send(200, native_pick("file" if kind == "file" else "folder"))
        if u.path == "/api/intake":
            slug = write_intake(self._body())
            return self._send(200, {"ok": True, "slug": slug})
        if u.path == "/api/daily-brief":
            d = self._body()
            return self._send(200, install_daily_brief(slugify(d.get("slug", "")), d.get("time", ""), d.get("agent", "")))
        if u.path == "/api/shutdown":
            threading.Thread(target=self.server.shutdown, daemon=True).start()
            return self._send(200, {"ok": True})
        return self._send(404, {"error": "not found"})

    def _serve_dir(self, base, prefix, path):
        # Serve static files from `base` (dashboards from workspace/, art from images/). Traversal-guarded:
        # resolve() collapses ../ and follows symlinks, then relative_to() rejects anything outside base
        # (incl. sibling dirs like workspace-secrets that a string startswith would wrongly allow).
        target = (base / path[len(prefix):]).resolve()
        try:
            target.relative_to(base.resolve())
        except ValueError:
            return self._send(404, {"error": "not found"})
        if not target.is_file():
            return self._send(404, {"error": "not found"})
        ctype = {"html": "text/html; charset=utf-8", "md": "text/plain; charset=utf-8",
                 "json": "application/json", "css": "text/css", "js": "text/javascript",
                 "svg": "image/svg+xml", "jpg": "image/jpeg", "jpeg": "image/jpeg",
                 "png": "image/png", "webp": "image/webp", "gif": "image/gif"}.get(
                     target.suffix.lstrip("."), "application/octet-stream")
        return self._send(200, target.read_bytes(), ctype)

    def _serve_md_reader(self, path):
        # Render a workspace .md file as a styled, offline HTML page (the in-app results reader).
        target = (WORKSPACE / path[len("/view/"):]).resolve()
        try:
            target.relative_to(WORKSPACE.resolve())
        except ValueError:
            return self._send(404, {"error": "not found"})
        if not target.is_file() or target.suffix != ".md":
            return self._send(404, {"error": "not found"})
        md = target.read_text(encoding="utf-8", errors="replace")
        esc = md.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        nonce = secrets.token_urlsafe(16)
        html = (READER_SHELL.replace("__TITLE__", target.name)
                            .replace("__NONCE__", nonce)
                            .replace("__MD__", esc))
        # Defense-in-depth for the offline reader: a strict CSP. The lone inline script runs via its
        # nonce; everything else (network connections, other scripts, javascript: URLs) is denied, so a
        # malicious link/payload in a workspace .md can't execute or phone home even if it slips the
        # renderer's scheme allow-list.
        csp = ("default-src 'none'; img-src 'self' data:; style-src 'unsafe-inline'; "
               f"script-src 'nonce-{nonce}'; connect-src 'none'; base-uri 'none'; form-action 'none'")
        return self._send(200, html, "text/html; charset=utf-8",
                          {"Content-Security-Policy": csp, "X-Content-Type-Options": "nosniff",
                           "Referrer-Policy": "no-referrer"})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--render", metavar="INPUT.html", help="render a résumé-builder HTML file to PDF and exit")
    ap.add_argument("--out", metavar="OUTPUT.pdf", help="output PDF path (with --render)")
    args = ap.parse_args()

    if args.render:                                      # one-shot PDF render, no server
        if not args.out:
            print("--render requires --out OUTPUT.pdf", file=sys.stderr); sys.exit(2)
        ok, msg = render_pdf(args.render, args.out)
        print(("PDF: " + msg) if ok else msg, file=(sys.stdout if ok else sys.stderr))
        sys.exit(0 if ok else 1)

    port = args.port
    for _ in range(20):                                  # find a free port
        try:
            httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
            break
        except OSError:
            port += 1
    else:
        print("Could not bind a local port.", file=sys.stderr); sys.exit(1)
    global TOKEN, PORT
    PORT = port
    TOKEN = secrets.token_urlsafe(24)                    # per-session CSRF token
    url = f"http://127.0.0.1:{port}/"
    (UIDIR / ".port").write_text(str(port), encoding="utf-8")
    print(f"Ascend console → {url}")
    if not args.no_browser:
        try: webbrowser.open(url)
        except Exception: pass
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
