#!/usr/bin/env python3
"""
S.P.I.D.E.R. local control server.

A tiny, dependency-free (Python 3 standard library only) server that powers the /spiderui graphical
console. It binds to 127.0.0.1 ONLY — it is a local tool, never exposed to the network. It does the
things a browser can't do on its own: open a native folder/file picker, write your intake, install the
daily-brief schedule, report pipeline progress, and serve your private dashboard over http so links work.

It never sends your data anywhere. Everything it writes lives under workspace/<you>/ (gitignored).

Run directly:  python3 ui/server.py [--port 8765] [--no-browser]
The /spiderui Claude Code command launches it for you.
"""
import argparse, json, os, platform, re, shlex, shutil, subprocess, sys, threading, webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

REPO = Path(__file__).resolve().parent.parent          # spider/
UIDIR = REPO / "ui"
WORKSPACE = REPO / "workspace"


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


def native_pick(kind: str):
    """Open the OS's native folder/file dialog and return the chosen absolute path (or None)."""
    sysname = platform.system()
    try:
        if sysname == "Darwin":
            prompt = "Select your UNZIPPED LinkedIn export folder" if kind == "folder" else "Select your resume file"
            verb = "choose folder" if kind == "folder" else "choose file"
            script = f'POSIX path of ({verb} with prompt "{prompt}")'
            out = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=600)
            return (out.stdout.strip() or None)
        if sysname == "Linux":
            home = os.path.expanduser("~")
            if shutil.which("zenity"):
                args = ["zenity", "--file-selection"] + (["--directory"] if kind == "folder" else [])
            elif shutil.which("kdialog"):
                args = ["kdialog", "--getexistingdirectory", home] if kind == "folder" \
                    else ["kdialog", "--getopenfilename", home]
            else:
                return None
            out = subprocess.run(args, capture_output=True, text=True, timeout=600)
            return (out.stdout.strip() or None)
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
            return (out.stdout.strip() or None)
    except Exception:
        return None
    return None


def write_intake(data: dict):
    """Persist the wizard answers as workspace/<slug>/intake.md + a ready flag for the pipeline."""
    slug = slugify(data.get("name", ""))
    wdir = WORKSPACE / slug
    (wdir / "inputs").mkdir(parents=True, exist_ok=True)
    md = f"""# Intake — {data.get('name','')}

> Captured by the SPIDER console ({data.get('asOf','')}). The pipeline reads this first.

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
            f"{shlex.quote(agent)} >> {shlex.quote(str(logp))} 2>&1 # SPIDER-DAILY-BRIEF-{slug}")
    try:
        existing = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout.splitlines()
        kept = [l for l in existing if f"SPIDER-DAILY-BRIEF-{slug}" not in l]
        new = "\n".join(kept + [line]) + "\n"
        subprocess.run(["crontab", "-"], input=new, text=True, check=True)
        return {"ok": True, "time": hhmm}
    except Exception as e:
        return {"ok": False, "error": str(e), "manual": True,
                "note": f"Could not set cron automatically. Add this line via `crontab -e`:\n{line}"}


def read_status(slug: str):
    """Surface pipeline progress for the UI to poll (from the resumability manifest)."""
    statef = WORKSPACE / slug / ".spider-state.json"
    out = {"slug": slug, "phases": {}, "phase": None,
           "hasDashboard": (WORKSPACE / slug / "start-here.html").exists()}
    if statef.exists():
        try:
            out.update(json.loads(statef.read_text(encoding="utf-8")))
        except Exception:
            pass
    return out


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode()
        elif isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
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

    def do_GET(self):
        u = urlparse(self.path)
        if u.path in ("/", "/index.html"):
            return self._send(200, (UIDIR / "index.html").read_text(encoding="utf-8"), "text/html; charset=utf-8")
        if u.path == "/api/agents":
            return self._send(200, {"agents": detect_agents(), "platform": platform.system()})
        if u.path == "/api/status":
            slug = parse_qs(u.query).get("slug", [""])[0]
            return self._send(200, read_status(slugify(slug)))
        if u.path.startswith("/workspace/"):
            return self._serve_workspace(u.path)
        return self._send(404, {"error": "not found"})

    def do_POST(self):
        u = urlparse(self.path)
        if u.path == "/api/pick":
            kind = parse_qs(u.query).get("type", ["folder"])[0]
            return self._send(200, {"path": native_pick("file" if kind == "file" else "folder")})
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

    def _serve_workspace(self, path):
        # Serve the user's generated dashboard files over http (so relative links work). Path-traversal guarded.
        rel = path[len("/workspace/"):]
        target = (WORKSPACE / rel).resolve()
        if not str(target).startswith(str(WORKSPACE.resolve())) or not target.is_file():
            return self._send(404, {"error": "not found"})
        ctype = {"html": "text/html; charset=utf-8", "md": "text/plain; charset=utf-8",
                 "json": "application/json", "css": "text/css", "js": "text/javascript",
                 "svg": "image/svg+xml"}.get(target.suffix.lstrip("."), "application/octet-stream")
        return self._send(200, target.read_bytes(), ctype)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-browser", action="store_true")
    args = ap.parse_args()
    port = args.port
    for _ in range(20):                                  # find a free port
        try:
            httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
            break
        except OSError:
            port += 1
    else:
        print("Could not bind a local port.", file=sys.stderr); sys.exit(1)
    url = f"http://127.0.0.1:{port}/"
    (UIDIR / ".port").write_text(str(port), encoding="utf-8")
    print(f"SPIDER console → {url}")
    if not args.no_browser:
        try: webbrowser.open(url)
        except Exception: pass
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
