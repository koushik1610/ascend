#!/usr/bin/env python3
"""gmail_sync.py: engine A's Gmail sync. Read-only, your own OAuth client, zero tokens (Ascend 2.0, M4).

  python3 tools/gmail_sync.py connect WS                 # once: sign in with Google in your browser
  python3 tools/gmail_sync.py sync WS [--days N] [--json] [--then-classify]
  python3 tools/gmail_sync.py status WS

Setup is in docs/GMAIL-SETUP.md: you create a Desktop OAuth client in your own Google Cloud project and
save its JSON as workspace/<name>/gmail-client.json. Nobody else's app ever touches your mail.

What it keeps: sender, subject, date, labels and the first 2,000 characters of the body, in
workspace/<name>/data/mail.jsonl. Never attachments. Your own sent mail, drafts, spam and trash are
skipped. The refresh token lives in the macOS Keychain (service "ascend-gmail"), not on disk.

Sync is incremental: the Gmail history API returns only what arrived since the last run. When that
cursor has expired (Gmail keeps about a week), it falls back to a date query and de-duplicates by
message ID.

Exit codes: 0 ok, 2 usage or path, 4 not connected or access revoked (run `connect` again).
Email content is untrusted data (reference/untrusted-content-policy.md). This tool stores it; it never
acts on it.
"""

import base64
import hashlib
import html
import json
import os
import re
import secrets
import subprocess
import sys
import webbrowser
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import _v2data as d  # noqa: E402
from _paths import PathOutsideWorkspace  # noqa: E402

SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
# Test-only overrides; production uses Google's endpoints.
OAUTH_BASE = os.environ.get("ASCEND_GOOGLE_OAUTH_BASE", "https://oauth2.googleapis.com")
API_BASE = os.environ.get("ASCEND_GMAIL_API_BASE", "https://gmail.googleapis.com")
SKIP_LABELS = {"SENT", "DRAFT", "SPAM", "TRASH"}
EXCERPT = 2000
KEYCHAIN_SERVICE = "ascend-gmail"


class NotConnected(Exception):
    pass


# ── token store: Keychain by default, a 0600 file when ASCEND_TOKEN_STORE=file:<path> ──
def _file_store():
    spec = os.environ.get("ASCEND_TOKEN_STORE", "")
    return Path(spec[5:]) if spec.startswith("file:") else None


def _read_file_store(p):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _write_file_store(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(p), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.chmod(p, 0o600)


def get_refresh(slug):
    p = _file_store()
    if p:
        return _read_file_store(p).get(slug)
    r = subprocess.run(["security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-a", slug, "-w"],
                       capture_output=True, text=True)
    return r.stdout.strip() or None if r.returncode == 0 else None


def put_refresh(slug, token):
    p = _file_store()
    if p:
        data = _read_file_store(p)
        data[slug] = token
        return _write_file_store(p, data)
    subprocess.run(["security", "add-generic-password", "-U", "-s", KEYCHAIN_SERVICE, "-a", slug, "-w", token],
                   check=True, capture_output=True)


def delete_refresh(slug):
    p = _file_store()
    if p:
        data = _read_file_store(p)
        data.pop(slug, None)
        return _write_file_store(p, data)
    subprocess.run(["security", "delete-generic-password", "-s", KEYCHAIN_SERVICE, "-a", slug], capture_output=True)


# ── OAuth (installed-app loopback flow with PKCE) ────────────────────────────
def pkce_pair():
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    return verifier, challenge


def auth_url(client_id, redirect_uri, state, challenge):
    return AUTH_URL + "?" + urlencode({
        "client_id": client_id, "redirect_uri": redirect_uri, "response_type": "code", "scope": SCOPE,
        "state": state, "code_challenge": challenge, "code_challenge_method": "S256",
        "access_type": "offline", "prompt": "consent"})


def check_callback(query, expected_state):
    if query.get("state", [""])[0] != expected_state:
        raise ValueError("OAuth state mismatch: ignoring a callback this run did not start")
    if "error" in query:
        raise ValueError(f"Google returned an error: {query['error'][0]}")
    code = query.get("code", [""])[0]
    if not code:
        raise ValueError("no authorization code in the callback")
    return code


def _post_form(url, form):
    req = Request(url, data=urlencode(form).encode(), headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def _client(ws):
    p = Path(ws) / "gmail-client.json"
    if not p.is_file():
        raise NotConnected(f"no OAuth client at {p}. See docs/GMAIL-SETUP.md")
    c = json.loads(p.read_text(encoding="utf-8"))
    c = c.get("installed", c)        # Google's download wraps the fields in "installed"
    return c["client_id"], c.get("client_secret", "")


def connect(ws):
    client_id, client_secret = _client(ws)
    verifier, challenge = pkce_pair()
    state = secrets.token_urlsafe(24)
    result = {}

    class Callback(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            u = urlparse(self.path)
            if u.path != "/callback":
                self.send_response(404)
                self.end_headers()
                return
            try:
                result["code"] = check_callback(parse_qs(u.query), state)
                msg = "Ascend is connected to Gmail (read-only). You can close this tab."
            except ValueError as e:
                result["error"] = str(e)
                msg = f"Not connected: {e}"
            body = f"<!doctype html><meta charset=utf-8><p>{html.escape(msg)}</p>".encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)

    server = HTTPServer(("127.0.0.1", 0), Callback)
    redirect = f"http://127.0.0.1:{server.server_address[1]}/callback"
    url = auth_url(client_id, redirect, state, challenge)
    print(f"Opening Google sign-in. If no browser opens, visit:\n{url}")
    webbrowser.open(url)
    while not result:
        server.handle_request()
    server.server_close()
    if "error" in result:
        raise NotConnected(result["error"])
    tok = _post_form(OAUTH_BASE + "/token", {
        "client_id": client_id, "client_secret": client_secret, "code": result["code"],
        "code_verifier": verifier, "grant_type": "authorization_code", "redirect_uri": redirect})
    if "refresh_token" not in tok:
        raise NotConnected("Google returned no refresh token. Remove Ascend's access at "
                           "myaccount.google.com/permissions and run connect again.")
    put_refresh(Path(ws).name, tok["refresh_token"])
    _save_state(ws, {"connected": True})
    return True


# ── Gmail API ────────────────────────────────────────────────────────────────
def _access_token(ws):
    slug = Path(ws).name
    refresh = get_refresh(slug)
    if not refresh:
        raise NotConnected("Gmail is not connected")
    client_id, client_secret = _client(ws)
    try:
        tok = _post_form(OAUTH_BASE + "/token", {"client_id": client_id, "client_secret": client_secret,
                                                 "refresh_token": refresh, "grant_type": "refresh_token"})
    except HTTPError as e:
        if e.code in (400, 401):
            delete_refresh(slug)
            _save_state(ws, {"connected": False})
            raise NotConnected("Google revoked Ascend's access") from e
        raise
    return tok["access_token"]


def _get(token, path, params=None):
    url = API_BASE + "/gmail/v1/users/me/" + path + ("?" + urlencode(params, doseq=True) if params else "")
    with urlopen(Request(url, headers={"Authorization": f"Bearer {token}"}), timeout=30) as r:
        return json.loads(r.read().decode())


def _decode(data):
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("utf-8", "replace")


def _find_part(payload, mime):
    if payload.get("mimeType") == mime and payload.get("body", {}).get("data"):
        return _decode(payload["body"]["data"])
    for part in payload.get("parts", []) or []:
        found = _find_part(part, mime)
        if found:
            return found
    return None


def _strip_html(s):
    s = re.sub(r"(?is)<(script|style).*?</\1>", " ", s)
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s))).strip()


def message_to_mail(msg):
    """One Gmail message → one mail.jsonl row, or None for mail Ascend never reads."""
    labels = msg.get("labelIds", []) or []
    if SKIP_LABELS & set(labels):
        return None
    payload = msg.get("payload", {}) or {}
    headers = {h["name"].lower(): h["value"] for h in payload.get("headers", [])}
    text = _find_part(payload, "text/plain")
    if text is None:
        h = _find_part(payload, "text/html")
        text = _strip_html(h) if h else html.unescape(msg.get("snippet", ""))
    text = re.sub(r"\s+", " ", text).strip()
    try:
        when = datetime.fromtimestamp(int(msg.get("internalDate", 0)) / 1000, tz=timezone.utc)
    except (TypeError, ValueError):
        when = None
    if when is None and headers.get("date"):
        try:
            when = parsedate_to_datetime(headers["date"])
        except (TypeError, ValueError):
            when = None
    return {"msg_id": msg["id"], "thread_id": msg.get("threadId"), "from": headers.get("from", ""),
            "subject": headers.get("subject", ""), "date": when.isoformat() if when else "",
            "labels": labels, "body_excerpt": text[:EXCERPT]}


def _state_path(ws):
    return d.data_dir(ws) / "sync-state.json"


def _save_state(ws, updates):
    p = _state_path(ws)
    state = d.read_json(p, {})
    state.update(updates)
    d.write_json_atomic(p, state)


def sync(ws, days=30):
    token = _access_token(ws)
    dd = d.data_dir(ws)
    state = d.read_json(_state_path(ws), {})
    known = {m.get("msg_id") for m in d.read_jsonl(dd / "mail.jsonl")}
    ids, mode = None, "query"
    if state.get("history_id"):
        try:
            h = _get(token, "history", {"startHistoryId": state["history_id"], "historyTypes": "messageAdded"})
            ids = [a["message"]["id"] for rec in h.get("history", []) for a in rec.get("messagesAdded", [])]
            mode = "history"
        except HTTPError as e:
            if e.code != 404:       # 404 = cursor expired; anything else is a real failure
                raise
    if ids is None:
        ids, page = [], None
        while True:
            params = {"q": f"newer_than:{days}d", "maxResults": 100}
            if page:
                params["pageToken"] = page
            r = _get(token, "messages", params)
            ids += [m["id"] for m in r.get("messages", [])]
            page = r.get("nextPageToken")
            if not page:
                break
    new = 0
    for mid in dict.fromkeys(ids):
        if mid in known:
            continue
        row = message_to_mail(_get(token, f"messages/{mid}", {"format": "full"}))
        known.add(mid)
        if row:
            d.append_jsonl(dd / "mail.jsonl", row)
            new += 1
    profile = _get(token, "profile")
    _save_state(ws, {"connected": True, "history_id": profile.get("historyId"), "account": profile.get("emailAddress"),
                     "last_sync": datetime.now(timezone.utc).isoformat(timespec="seconds")})
    return {"new": new, "mode": mode, "history_id": profile.get("historyId")}


def _then_classify(ws):
    for cmd in (["classify.py", "run", str(ws)], ["pipeline.py", "ingest", str(ws)], ["hub.py", "build", str(ws)]):
        subprocess.run([sys.executable, str(TOOLS / cmd[0]), *cmd[1:]], check=True, stdout=subprocess.DEVNULL)


def main(argv):
    if len(argv) < 3 or argv[1] not in ("connect", "sync", "status") or argv[2].startswith("--"):
        print(__doc__, file=sys.stderr)
        return 2
    cmd, ws, args = argv[1], Path(argv[2]), argv[3:]
    reconnect = f"Run: python3 tools/gmail_sync.py connect {ws}"
    try:
        d.data_dir(ws)
        if cmd == "status":
            print(json.dumps(d.read_json(_state_path(ws), {"connected": False})))
            return 0
        if cmd == "connect":
            connect(ws)
            print("Connected (read-only).")
            return 0
        days = int(args[args.index("--days") + 1]) if "--days" in args else 30
        out = sync(ws, days)
        if "--then-classify" in args:
            _then_classify(ws)
        print(json.dumps(out) if "--json" in args else f"synced {out['new']} new message(s) via {out['mode']}")
        return 0
    except PathOutsideWorkspace as e:
        print(f"gmail_sync: {e}", file=sys.stderr)
        return 2
    except NotConnected as e:
        print(f"gmail_sync: {e}. {reconnect}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    sys.exit(main(sys.argv))
