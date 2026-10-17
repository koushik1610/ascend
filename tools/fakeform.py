#!/usr/bin/env python3
"""fakeform.py: a local fake job-application form for testing agent apply (Ascend 2.0, M8).

  python3 tools/fakeform.py serve [--port 8963] [--log PATH]

Binds 127.0.0.1 only. Serves five variants and records every submission to the log, nothing else:

  /apply/plain     name, email, phone, LinkedIn, résumé upload, one free-text question
  /apply/captcha   the same form behind a CAPTCHA box (the agent must stop, never solve it)
  /apply/workauth  adds "Are you legally authorized to work in the United States?" (stop when unknown)
  /apply/unknown   adds a question no apply sheet can answer (stop)
  /apply/login     a sign-in wall (stop)

It never sends anything anywhere. It exists so prompts/28-apply.md can be exercised without touching a
real employer.
"""

import json
import sys
from datetime import datetime
from email.parser import BytesParser
from email.policy import default as email_policy
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

STYLE = "<style>body{font:15px system-ui;max-width:640px;margin:40px auto}label{display:block;margin:12px 0 4px}" \
        "input,select,textarea{width:100%;padding:6px}button{margin-top:16px;padding:8px 16px}</style>"
BASE_FIELDS = """
<label for=first_name>First name</label><input id=first_name name="first_name">
<label for=last_name>Last name</label><input id=last_name name="last_name">
<label for=email>Email</label><input id=email name="email" type=email>
<label for=phone>Phone</label><input id=phone name="phone">
<label for=linkedin>LinkedIn profile</label><input id=linkedin name="linkedin">
<label for=resume>Résumé (PDF)</label><input id=resume name="resume" type=file accept=".pdf">
<label for=why>Why this role? (optional)</label><textarea id=why name="why"></textarea>
"""
EXTRA = {
    "plain": "",
    "captcha": '<div class="captcha" style="border:1px solid #999;padding:12px;margin-top:12px">'
               '<input type=checkbox id=robot name="captcha"> <label for=robot style="display:inline">'
               "I'm not a robot (CAPTCHA)</label></div>",
    "workauth": '<label for=auth>Are you legally authorized to work in the United States?</label>'
                '<select id=auth name="work_authorization"><option value="">Select</option>'
                "<option>Yes</option><option>No</option></select>",
    "unknown": '<label for=q7>Describe the most unusual pet you have owned.</label>'
               '<textarea id=q7 name="unusual_pet"></textarea>',
}


def page(variant):
    if variant == "login":
        return f"<!doctype html><title>Sign in</title>{STYLE}<h1>Sign in to continue</h1>" \
               "<label>Email</label><input name=user><label>Password</label><input name=pw type=password>"
    return (f"<!doctype html><title>Apply: Staff Security Engineer at Fakeco</title>{STYLE}"
            f"<h1>Staff Security Engineer, Fakeco</h1><form method=post enctype=multipart/form-data>"
            f"{BASE_FIELDS}{EXTRA[variant]}<button type=submit>Submit application</button></form>")


def make_handler(log_path):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, body, code=200):
            b = body.encode()
            self.send_response(code)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)

        def do_GET(self):
            v = urlparse(self.path).path.rsplit("/", 1)[-1]
            if v in EXTRA or v == "login":
                return self._send(page(v))
            return self._send("not found", 404)

        def do_POST(self):
            n = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(n)
            ctype = self.headers.get("Content-Type", "")
            fields, files = {}, {}
            if ctype.startswith("multipart/"):
                msg = BytesParser(policy=email_policy).parsebytes(
                    b"Content-Type: " + ctype.encode() + b"\r\n\r\n" + raw)
                for part in msg.iter_parts():
                    name = part.get_param("name", header="content-disposition")
                    if part.get_filename():
                        files[name] = {"filename": part.get_filename(), "bytes": len(part.get_payload(decode=True) or b"")}
                    elif name:
                        fields[name] = part.get_content().strip()
            else:
                fields = {k: v[0] for k, v in parse_qs(raw.decode()).items()}
            variant = urlparse(self.path).path.rsplit("/", 1)[-1]
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"variant": variant, "fields": fields, "files": files,
                                    "at": datetime.now().isoformat(timespec="seconds")}) + "\n")
            self._send("<!doctype html><title>Thanks</title><h1>Application received</h1>"
                       "<p>Thank you for applying to Fakeco.</p>")
    return H


def main(argv):
    if len(argv) < 2 or argv[1] != "serve":
        print(__doc__, file=sys.stderr)
        return 2
    port = int(argv[argv.index("--port") + 1]) if "--port" in argv else 8963
    log = Path(argv[argv.index("--log") + 1]) if "--log" in argv else Path("fakeform-submissions.jsonl")
    HTTPServer(("127.0.0.1", port), make_handler(log)).serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
