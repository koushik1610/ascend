"""Ascend 2.0 M4: engine A Gmail sync against a fake Google server. No real account is ever touched.

Run: python3 -m unittest tests/test_v2_gmail.py -v
"""

import base64
import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(REPO / "tests"))
from test_v2_pipeline import make_ws  # noqa: E402


def b64(s):
    return base64.urlsafe_b64encode(s.encode()).decode().rstrip("=")


def gmsg(mid, subject, frm, body, labels=("INBOX",), html=False, epoch_ms=1791900000000):
    part = {"mimeType": "text/html" if html else "text/plain", "body": {"data": b64(body)}}
    return {"id": mid, "threadId": "t" + mid, "labelIds": list(labels), "snippet": body[:60],
            "internalDate": str(epoch_ms),
            "payload": {"mimeType": "multipart/alternative",
                        "headers": [{"name": "From", "value": frm}, {"name": "Subject", "value": subject}],
                        "parts": [part]}}


class FakeGoogle:
    """Token endpoint + the four Gmail endpoints sync uses, with switches for failure modes."""

    def __init__(self):
        self.messages = {}
        self.history = []          # list of (history_id, message_id)
        self.history_id = 100
        self.history_expired = False
        self.revoked = False
        self.token_error = "invalid_grant"
        self.history_page = 0      # >0: history answers in pages of this many records
        self.deleted = set()       # message IDs listed by history but gone when fetched
        self.on_profile = None     # called before profile answers: mail arriving mid-sync
        self.requests = []
        fake = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _json(self, code, obj):
                b = json.dumps(obj).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(b)))
                self.end_headers()
                self.wfile.write(b)

            def do_POST(self):
                n = int(self.headers.get("Content-Length", 0))
                form = parse_qs(self.rfile.read(n).decode())
                fake.requests.append(("POST", self.path, form))
                if fake.revoked:
                    return self._json(400, {"error": fake.token_error})
                return self._json(200, {"access_token": "at-123", "expires_in": 3600})

            def do_GET(self):
                u = urlparse(self.path)
                q = parse_qs(u.query)
                fake.requests.append(("GET", u.path, q))
                if self.headers.get("Authorization") != "Bearer at-123":
                    return self._json(401, {"error": "unauthorized"})
                base = "/gmail/v1/users/me/"
                p = u.path[len(base):]
                if p == "profile":
                    if fake.on_profile:
                        fake.on_profile()
                    return self._json(200, {"emailAddress": "user@example.com", "historyId": str(fake.history_id)})
                if p == "messages":
                    return self._json(200, {"messages": [{"id": m} for m in fake.messages]})
                if p.startswith("messages/"):
                    mid = p.split("/", 1)[1]
                    if mid in fake.deleted or mid not in fake.messages:
                        return self._json(404, {"error": {"code": 404}})
                    return self._json(200, fake.messages[mid])
                if p == "history":
                    if fake.history_expired:
                        return self._json(404, {"error": {"code": 404, "message": "Requested entity was not found."}})
                    start = int(q["startHistoryId"][0])
                    added = [{"messagesAdded": [{"message": {"id": mid}}]} for hid, mid in fake.history if hid > start]
                    hid = str(fake.history_id)
                    if fake.history_page:
                        at = int(q.get("pageToken", ["0"])[0])
                        page = added[at:at + fake.history_page]
                        more = at + fake.history_page < len(added)
                        return self._json(200, dict({"history": page, "historyId": hid},
                                                    **({"nextPageToken": str(at + fake.history_page)} if more else {})))
                    return self._json(200, {"history": added, "historyId": hid})
                return self._json(404, {})

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def add(self, m):
        self.messages[m["id"]] = m
        self.history_id += 1
        self.history.append((self.history_id, m["id"]))

    def close(self):
        self.server.shutdown()


class Overrides(unittest.TestCase):
    def test_endpoint_overrides_only_point_at_this_machine(self):
        env = dict(os.environ, ASCEND_GMAIL_API_BASE="https://evil.example", ASCEND_GOOGLE_OAUTH_BASE="http://127.0.0.1:9")
        r = subprocess.run([sys.executable, "-c", "import sys; sys.path.insert(0, 'tools'); import gmail_sync as g; "
                            "print(g.API_BASE, g.OAUTH_BASE)"], capture_output=True, text=True, env=env, cwd=str(REPO))
        self.assertEqual(r.stdout.split(), ["https://gmail.googleapis.com", "http://127.0.0.1:9"])


class Auth(unittest.TestCase):
    def test_auth_url_is_read_only_pkce_and_local(self):
        import gmail_sync as g
        verifier, challenge = g.pkce_pair()
        url = g.auth_url("cid", "http://127.0.0.1:5555/callback", "st8", challenge)
        q = parse_qs(urlparse(url).query)
        self.assertEqual(q["scope"], ["https://www.googleapis.com/auth/gmail.readonly"])
        self.assertEqual((q["code_challenge_method"], q["state"], q["access_type"]), (["S256"], ["st8"], ["offline"]))
        self.assertTrue(q["redirect_uri"][0].startswith("http://127.0.0.1:"))
        expect = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
        self.assertEqual(q["code_challenge"], [expect])

    def test_callback_rejects_wrong_state_and_errors(self):
        import gmail_sync as g
        self.assertEqual(g.check_callback({"state": ["ok"], "code": ["c1"]}, "ok"), "c1")
        with self.assertRaises(ValueError):
            g.check_callback({"state": ["evil"], "code": ["c1"]}, "ok")
        with self.assertRaises(ValueError):
            g.check_callback({"state": ["ok"], "error": ["access_denied"]}, "ok")


class MessageShape(unittest.TestCase):
    def test_plain_text_trimmed(self):
        import gmail_sync as g
        row = g.message_to_mail(gmsg("m1", "Hello", "Ann <a@co.example>", "x" * 5000))
        self.assertEqual((row["msg_id"], row["from"], row["subject"]), ("m1", "Ann <a@co.example>", "Hello"))
        self.assertEqual(len(row["body_excerpt"]), 2000)
        self.assertTrue(row["date"].startswith("2026-"))

    def test_html_is_stripped(self):
        import gmail_sync as g
        row = g.message_to_mail(gmsg("m2", "Hi", "a@co.example", "<p>Thanks for <b>applying</b></p>", html=True))
        self.assertEqual(row["body_excerpt"], "Thanks for applying")

    def test_own_and_junk_mail_skipped(self):
        import gmail_sync as g
        for labels in (["SENT"], ["DRAFT"], ["SPAM"], ["TRASH"]):
            self.assertIsNone(g.message_to_mail(gmsg("m", "s", "a@b.example", "b", labels=labels)))


class Sync(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.ws = make_ws(self.td.name, [])
        self.fake = FakeGoogle()
        self.store = Path(self.td.name) / "secrets" / "tokens.json"
        self.env = dict(os.environ, ASCEND_GOOGLE_OAUTH_BASE=self.fake.base, ASCEND_GMAIL_API_BASE=self.fake.base,
                        ASCEND_TOKEN_STORE=f"file:{self.store}")
        (self.ws / "gmail-client.json").write_text(json.dumps({"client_id": "cid", "client_secret": "cs"}))

    def tearDown(self):
        self.fake.close()
        self.td.cleanup()

    def run_tool(self, *args):
        return subprocess.run([sys.executable, str(REPO / "tools/gmail_sync.py"), *args], capture_output=True,
                              text=True, env=self.env)

    def connected(self):
        os.environ.update({k: v for k, v in self.env.items() if k.startswith("ASCEND_")})
        import gmail_sync as g
        g.put_refresh("tester", "rt-1")

    def mail(self):
        import _v2data as d
        return d.read_jsonl(self.ws / "data" / "mail.jsonl")

    def test_not_connected_exits_4(self):
        r = self.run_tool("sync", str(self.ws))
        self.assertEqual(r.returncode, 4)
        self.assertIn("gmail_sync.py connect", r.stderr)

    def test_first_sync_then_history(self):
        self.connected()
        self.fake.add(gmsg("a1", "Thanks for applying", "no-reply@ashbyhq.com", "We received your application."))
        self.fake.add(gmsg("a2", "Re: my note", "me@example.com", "sent by me", labels=["SENT"]))
        r = self.run_tool("sync", str(self.ws), "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual((out["mode"], out["new"]), ("query", 1))
        self.assertEqual([m["msg_id"] for m in self.mail()], ["a1"])
        self.fake.add(gmsg("a3", "Interview invitation", "talent@co.example", "Please share your availability."))
        out = json.loads(self.run_tool("sync", str(self.ws), "--json").stdout)
        self.assertEqual((out["mode"], out["new"]), ("history", 1))
        self.assertEqual([m["msg_id"] for m in self.mail()], ["a1", "a3"])

    def test_expired_cursor_falls_back_without_duplicates(self):
        self.connected()
        self.fake.add(gmsg("b1", "One", "a@co.example", "one"))
        self.run_tool("sync", str(self.ws))
        self.fake.add(gmsg("b2", "Two", "a@co.example", "two"))
        self.fake.history_expired = True
        out = json.loads(self.run_tool("sync", str(self.ws), "--json").stdout)
        self.assertEqual((out["mode"], out["new"]), ("query", 1))
        self.assertEqual(sorted(m["msg_id"] for m in self.mail()), ["b1", "b2"])

    def test_revoked_token_disconnects(self):
        self.connected()
        self.fake.revoked = True
        r = self.run_tool("sync", str(self.ws))
        self.assertEqual(r.returncode, 4)
        import gmail_sync as g
        self.assertIsNone(g.get_refresh("tester"))
        state = json.loads((self.ws / "data" / "sync-state.json").read_text())
        self.assertFalse(state["connected"])

    def test_history_is_read_to_the_last_page(self):
        self.connected()
        self.fake.add(gmsg("p0", "Zero", "a@co.example", "zero"))
        self.run_tool("sync", str(self.ws))
        for i in range(1, 6):
            self.fake.add(gmsg(f"p{i}", f"N{i}", "a@co.example", "x"))
        self.fake.history_page = 2
        out = json.loads(self.run_tool("sync", str(self.ws), "--json").stdout)
        self.assertEqual((out["mode"], out["new"]), ("history", 5))

    def test_mail_arriving_during_a_sync_is_picked_up_next_time(self):
        self.connected()
        self.fake.add(gmsg("r1", "One", "a@co.example", "one"))
        late = gmsg("r2", "Arrived mid-sync", "talent@co.example", "Can you share availability?")
        self.fake.on_profile = lambda: (self.fake.add(late), setattr(self.fake, "on_profile", None))
        self.run_tool("sync", str(self.ws))
        self.run_tool("sync", str(self.ws))
        self.assertIn("r2", [m["msg_id"] for m in self.mail()])

    def test_a_deleted_message_does_not_stall_the_sync(self):
        self.connected()
        self.fake.add(gmsg("d0", "Zero", "a@co.example", "zero"))
        self.run_tool("sync", str(self.ws))
        self.fake.add(gmsg("d1", "Gone", "a@co.example", "deleted before fetch"))
        self.fake.add(gmsg("d2", "Kept", "a@co.example", "kept"))
        self.fake.deleted.add("d1")
        r = self.run_tool("sync", str(self.ws), "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["new"], 1)
        self.fake.add(gmsg("d3", "Next", "a@co.example", "next"))
        self.assertEqual(json.loads(self.run_tool("sync", str(self.ws), "--json").stdout)["new"], 1)

    def test_promotions_social_and_forums_are_not_stored_except_job_senders(self):
        self.connected()
        self.fake.add(gmsg("e1", "Sale", "shop@store.example", "50% off", labels=["INBOX", "CATEGORY_PROMOTIONS"]))
        self.fake.add(gmsg("e2", "Friend", "x@social.example", "tagged you", labels=["INBOX", "CATEGORY_SOCIAL"]))
        self.fake.add(gmsg("e3", "Thanks for applying", "no-reply@ashbyhq.com", "received", labels=["INBOX", "CATEGORY_UPDATES"]))
        self.fake.add(gmsg("e4", "New jobs for you", "jobalerts-noreply@linkedin.com", "Staff Engineer at Acme",
                           labels=["INBOX", "CATEGORY_SOCIAL"]))
        self.fake.add(gmsg("e5", "Your application", "no-reply@greenhouse.io", "received", labels=["INBOX", "CATEGORY_PROMOTIONS"]))
        self.run_tool("sync", str(self.ws))
        self.assertEqual(sorted(m["msg_id"] for m in self.mail()), ["e3", "e4", "e5"])

    def test_a_transient_token_error_keeps_the_sign_in(self):
        self.connected()
        self.fake.revoked, self.fake.token_error = True, "invalid_request"
        r = self.run_tool("sync", str(self.ws))
        self.assertNotEqual(r.returncode, 0)
        import gmail_sync as g
        self.assertEqual(g.get_refresh("tester"), "rt-1")

    def test_file_store_is_private_and_outside_data(self):
        self.connected()
        mode = stat.S_IMODE(self.store.stat().st_mode)
        self.assertEqual(mode, 0o600)
        self.assertFalse(any("rt-1" in p.read_text() for p in (self.ws / "data").glob("*") if p.is_file()))

    def test_then_classify_runs_the_zero_token_chain(self):
        self.connected()
        self.fake.add(gmsg("c1", "Thanks for applying to Acme", "no-reply@ashbyhq.com", "We received your application."))
        r = self.run_tool("sync", str(self.ws), "--then-classify")
        self.assertEqual(r.returncode, 0, r.stderr)
        import _v2data as d
        self.assertEqual(d.read_jsonl(self.ws / "data" / "events.jsonl")[0]["category"], "acknowledgement")
        self.assertTrue((self.ws / "hub.html").is_file())


if __name__ == "__main__":
    unittest.main()
