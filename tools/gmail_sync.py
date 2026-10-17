#!/usr/bin/env python3
"""gmail_sync.py: engine A's Gmail sync. Read-only, your own OAuth client, zero tokens (Ascend 2.0, M4).

  python3 tools/gmail_sync.py connect WS                 # once: sign in with Google in your browser
  python3 tools/gmail_sync.py sync WS [--days N] [--json] [--then-classify]
  python3 tools/gmail_sync.py status WS
  python3 tools/gmail_sync.py query WS                   # engines B and C: the Gmail search to run
  python3 tools/gmail_sync.py add WS --file workspace/<name>/data/connector-rows.json   # what it returned

Setup is in docs/GMAIL-SETUP.md: you create a Desktop OAuth client in your own Google Cloud project and
save its JSON as workspace/<name>/gmail-client.json. Nobody else's app ever touches your mail.

What it keeps: sender, subject, date, labels and the first 2,000 characters of the body, in
workspace/<name>/data/mail.jsonl. Never attachments. Your own sent mail, drafts, spam and trash are
skipped, and so are the promotions, social and forums tabs unless the sender is an ATS or a job board. The refresh token lives in the macOS Keychain (service "ascend-gmail"), not on disk.

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
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import _v2data as d  # noqa: E402
from _paths import PathOutsideWorkspace, resolve_out  # noqa: E402

SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"


def _local_override(var, default):
    """Test-only endpoint overrides, honoured only for this machine, so a stray environment variable can
    never send the refresh token or client secret to another host."""
    v = os.environ.get(var, "")
    return v.rstrip("/") if urlparse(v).hostname in ("127.0.0.1", "localhost") else default


OAUTH_BASE = _local_override("ASCEND_GOOGLE_OAUTH_BASE", "https://oauth2.googleapis.com")
API_BASE = _local_override("ASCEND_GMAIL_API_BASE", "https://gmail.googleapis.com")
# Ascend reads job mail (spec §8: collect only what tracking needs). Sent mail, drafts, spam and trash are
# never stored. Gmail's promotions, social and forums tabs are stored only from job senders (ATS systems
# and job boards), because Gmail often files LinkedIn and board alerts there.
SKIP_LABELS = {"SENT", "DRAFT", "SPAM", "TRASH"}
CATEGORY_LABELS = {"CATEGORY_PROMOTIONS", "CATEGORY_SOCIAL", "CATEGORY_FORUMS"}
QUERY_EXCLUDE = "-category:promotions -category:social -category:forums"
JOB_SUBJECTS = ("application", "applying", "applied", "interview", "recruiter", "recruiting", "position", "role",
                "opportunity", "assessment", "offer", '"next steps"', "candidate", "hiring", '"job alert"')


def _job_sender(sender_text):
    import classify
    m = re.search(r"[\w.+-]+@([\w.-]+)", sender_text or "")
    addr, dom = (m.group(0).lower(), m.group(1).lower()) if m else ("", "")
    return addr in classify.ALERT_SENDERS or any(dom == x or dom.endswith("." + x)
                                                  for x in classify.ATS_DOMAINS | classify.ALERT_DOMAINS)


def _skip(labels, sender_text):
    labels = set(labels or [])
    return bool(SKIP_LABELS & labels) or (bool(CATEGORY_LABELS & labels) and not _job_sender(sender_text))


def _iso_date(s):
    """An ISO 8601 date for anything Gmail or the connector writes, or None when it cannot be read."""
    try:
        return datetime.fromisoformat((s or "").replace("Z", "+00:00")).isoformat()
    except ValueError:
        pass
    try:
        return parsedate_to_datetime(s).isoformat()
    except (TypeError, ValueError, IndexError):
        return None


def connector_query(ws, today=None):
    """The Gmail search engines B and C run through the connector: from the day before the last read (so a
    gap of days is never skipped), job senders or job subjects only, never the promotions/social/forums tabs
    except from job senders. Keeps 2FA codes, bank and personal mail out of Claude's context."""
    import classify
    last = d.read_json(d.data_dir(ws) / "sync-state.json", {}).get("connector_last_read")
    if last:
        window = "after:" + (date.fromisoformat(last[:10]) - timedelta(days=1)).strftime("%Y/%m/%d")
    else:
        window = "newer_than:2d"
    senders = " OR ".join(sorted(classify.ATS_DOMAINS | classify.ALERT_DOMAINS))
    subjects = " OR ".join(JOB_SUBJECTS)
    return f"{window} (from:({senders}) OR (subject:({subjects}) {QUERY_EXCLUDE}))"
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
        try:
            err = json.loads(e.read().decode() or "{}").get("error")
        except (ValueError, OSError):
            err = None
        if err == "invalid_grant":          # revoked or expired; anything else may be transient
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
    payload = msg.get("payload", {}) or {}
    headers = {h["name"].lower(): h["value"] for h in payload.get("headers", [])}
    if _skip(labels, headers.get("from", "")):
        return None
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
    ids, mode, cursor = None, "query", None
    if state.get("history_id"):
        try:
            ids, page = [], None
            while True:
                params = {"startHistoryId": state["history_id"], "historyTypes": "messageAdded"}
                if page:
                    params["pageToken"] = page
                h = _get(token, "history", params)
                ids += [a["message"]["id"] for rec in h.get("history", []) for a in rec.get("messagesAdded", [])]
                cursor = cursor or h.get("historyId")      # where this read started, not where Gmail is now
                page = h.get("nextPageToken")
                if not page:
                    break
            mode = "history"
        except HTTPError as e:
            if e.code != 404:       # 404 = cursor expired; anything else is a real failure
                raise
            ids = None
    if ids is None:
        cursor = _get(token, "profile").get("historyId")   # taken before listing, so nothing slips between
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
        try:
            row = message_to_mail(_get(token, f"messages/{mid}", {"format": "full"}))
        except HTTPError as e:
            if e.code != 404:       # deleted between the listing and the fetch: skip it, keep going
                raise
            row = None
        known.add(mid)
        if row:
            d.append_jsonl(dd / "mail.jsonl", row)
            new += 1
    profile = _get(token, "profile")
    cursor = cursor or profile.get("historyId")
    _save_state(ws, {"connected": True, "history_id": cursor, "account": profile.get("emailAddress"),
                     "last_sync": datetime.now(timezone.utc).isoformat(timespec="seconds")})
    return {"new": new, "mode": mode, "history_id": cursor}


def add(ws, rows, today=None):
    """Mail read by Claude through the claude.ai connector (engines B and C), held to the same rules as
    engine A's sync: required headers, a 2,000-character excerpt, no sent mail or drafts, no mail from
    the user's own address, no duplicates."""
    dd = d.data_dir(ws)
    own = (d.read_json(dd / "profile.json", {}).get("email") or "").lower()
    known = {m.get("msg_id") for m in d.read_jsonl(dd / "mail.jsonl")}
    out = {"added": 0, "skipped": 0}
    for r in rows:
        sender = (r.get("from") or "").lower()
        when = _iso_date(r.get("date"))
        if (not all(r.get(k) for k in ("msg_id", "from", "subject")) or not when or r["msg_id"] in known
                or _skip(r.get("labels"), r.get("from")) or (own and own in sender)):
            out["skipped"] += 1
            continue
        d.append_jsonl(dd / "mail.jsonl", {"msg_id": r["msg_id"], "thread_id": r.get("thread_id"), "from": r["from"],
                                           "subject": r["subject"], "date": when, "labels": r.get("labels") or [],
                                           "body_excerpt": re.sub(r"\s+", " ", r.get("body_excerpt") or "").strip()[:EXCERPT]})
        known.add(r["msg_id"])
        out["added"] += 1
    _save_state(ws, {"connector_last_read": today or date.today().isoformat()})
    return out


def _then_classify(ws):
    for cmd in (["classify.py", "run", str(ws)], ["pipeline.py", "ingest", str(ws)], ["hub.py", "build", str(ws)]):
        subprocess.run([sys.executable, str(TOOLS / cmd[0]), *cmd[1:]], check=True, stdout=subprocess.DEVNULL)


def main(argv):
    if len(argv) >= 3 and argv[1] == "query" and not argv[2].startswith("--"):
        print(connector_query(argv[2]))
        return 0
    if len(argv) >= 3 and argv[1] == "add" and not argv[2].startswith("--"):
        try:
            if "--file" in argv:        # rows Claude wrote under the workspace: no email text on the command line
                rows = json.loads(resolve_out(argv[argv.index("--file") + 1]).read_text(encoding="utf-8"))
            elif "--json" in argv:
                rows = json.loads(argv[argv.index("--json") + 1])
            else:
                rows = json.load(sys.stdin)
            print(json.dumps(add(argv[2], rows)))
        except PathOutsideWorkspace as e:
            print(f"gmail_sync: {e}", file=sys.stderr)
            return 2
        return 0
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
