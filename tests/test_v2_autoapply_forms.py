"""The real form filler (tools/autoapply_forms.py) against local fake Greenhouse, Ashby and Lever forms.

Run: python3 -m unittest tests/test_v2_autoapply_forms.py -v
Needs Playwright with Chromium (pip install playwright && playwright install chromium). Without it every
test here is skipped and says why; the runner's own logic is covered by tests/test_v2_autoapply.py.
"""

import json
import os
import sys
import tempfile
import threading
import unittest
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
FORMS = REPO / "tests" / "fixtures" / "forms"

try:
    import playwright.sync_api  # noqa: F401
    HAVE_PW = True
except ImportError:
    HAVE_PW = False
    if os.environ.get("ASCEND_REQUIRE_PLAYWRIGHT"):        # CI: a skip here would hide a broken filler
        raise

ANSWERS = {"name": "Jordan Rivera", "email": "jordan@example.com", "phone": "555-0100",
           "linkedin": "https://www.linkedin.com/in/example", "location": "Remote, US",
           "work_authorization": "Yes", "sponsorship": "No", "current_company": "Example Corp",
           "gender": "Decline to self-identify", "_bank": []}


class Fake:
    def __init__(self):
        self.records = []
        fake = self

        class H(SimpleHTTPRequestHandler):
            def __init__(self, *a, **kw):
                super().__init__(*a, directory=str(FORMS), **kw)

            def log_message(self, *a):
                pass

            def do_POST(self):
                n = int(self.headers.get("Content-Length") or 0)
                fake.records.append(json.loads(self.rfile.read(n) or b"{}"))
                self.send_response(200)
                self.send_header("Content-Length", "2")
                self.end_headers()
                self.wfile.write(b"{}")

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def close(self):
        self.server.shutdown()


@unittest.skipUnless(HAVE_PW, "Playwright is not installed: pip install playwright && playwright install chromium")
class Forms(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fake = Fake()

    @classmethod
    def tearDownClass(cls):
        cls.fake.close()

    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.resume = Path(self.td.name) / "Jordan-Rivera-Resume-Acme.pdf"
        self.resume.write_bytes(b"%PDF-1.4 fake")
        self.fake.records.clear()

    def tearDown(self):
        self.td.cleanup()

    def fill(self, page, submit=True, answers=None, hosts=("127.0.0.1",), timeout=5):
        import autoapply_forms
        return autoapply_forms.fill(f"{self.fake.base}/{page}", answers or ANSWERS, str(self.resume), submit,
                                    self.td.name, hosts=set(hosts), timeout=timeout)

    def test_greenhouse_is_filled_and_submitted(self):
        out = self.fill("greenhouse.html")
        self.assertEqual(out["result"], "submitted", out)
        v = self.fake.records[-1]["values"]
        self.assertEqual((v["first_name"], v["last_name"], v["email"]), ("Jordan", "Rivera", "jordan@example.com"))
        self.assertEqual((v["question_2"], v["question_3"]), ("No", "Yes"))     # sponsorship, authorization
        self.assertEqual(v["resume"], self.resume.name)
        self.assertEqual(v["gender"], "Decline To Self Identify")
        self.assertEqual(v["question_4"], "")       # no answer for an optional question: left empty
        self.assertTrue(any(s.endswith("filled.png") for s in out["shots"]))
        self.assertTrue(any(s.endswith("confirmation.png") for s in out["shots"]))

    def test_dry_run_fills_and_never_submits(self):
        out = self.fill("greenhouse.html", submit=False)
        self.assertEqual(out["result"], "filled", out)
        self.assertEqual(self.fake.records, [])

    def test_dry_run_never_uploads_the_resume(self):
        # Attaching a file can send it to the ATS before any submit (Ashby parses uploads for autofill).
        out = self.fill("ashby.html", submit=False)
        self.assertEqual(out["result"], "filled", out)
        self.assertFalse(out["uploaded"])
        self.assertTrue(self.fill("ashby.html")["uploaded"])

    def test_visible_captcha_stops_before_anything_is_typed(self):
        out = self.fill("greenhouse.html?variant=captcha")
        self.assertEqual(out["result"], "stopped")
        self.assertIn("CAPTCHA", out["reason"])
        self.assertEqual(self.fake.records, [])

    def test_sign_in_page_stops(self):
        out = self.fill("greenhouse.html?variant=login")
        self.assertEqual(out["result"], "stopped")
        self.assertIn("sign in", out["reason"])

    def test_a_question_the_answers_do_not_cover_stops(self):
        out = self.fill("greenhouse.html?variant=essay")
        self.assertEqual(out["result"], "stopped")
        self.assertIn("Why Acme?", out["unfilled"])
        self.assertEqual(self.fake.records, [])

    def test_the_users_own_banked_answer_fills_it(self):
        bank = dict(ANSWERS, _bank=[{"question": "Why Acme?", "answer": "Your detection team's work on IAM drift."}])
        out = self.fill("greenhouse.html?variant=essay", answers=bank)
        self.assertEqual(out["result"], "submitted", out)
        self.assertEqual(self.fake.records[-1]["values"]["question_9"], "Your detection team's work on IAM drift.")

    def test_no_confirmation_is_unclear(self):
        out = self.fill("greenhouse.html?variant=noconfirm", timeout=2)
        self.assertEqual(out["result"], "unclear")
        self.assertIn("no confirmation", out["reason"])

    def test_browser_blocking_the_submit_is_a_stop_not_unclear(self):
        # The browser's own "Please fill out this field" bubble is not page text: nothing was sent.
        out = self.fill("greenhouse.html?variant=stuck", timeout=2)
        self.assertEqual(out["result"], "stopped", out)
        self.assertIn("required", out["reason"])
        self.assertEqual(self.fake.records, [])

    def test_page_off_the_allowed_hosts_is_never_filled(self):
        out = self.fill("greenhouse.html", hosts=("job-boards.greenhouse.io",))
        self.assertEqual(out["result"], "stopped")
        self.assertIn("127.0.0.1", out["reason"])
        self.assertEqual(self.fake.records, [])

    def test_ashby_yes_no_buttons(self):
        out = self.fill("ashby.html")
        self.assertEqual(out["result"], "submitted", out)
        v = self.fake.records[-1]["values"]
        self.assertEqual((v["a1"], v["a2"], v["auth"], v["sponsor"]), ("Jordan", "Rivera", "Yes", "No"))
        self.assertEqual(v["_systemfield_resume"], self.resume.name)

    def test_required_marked_by_css_still_stops(self):
        # Ashby draws the asterisk with CSS: the label text has none. A real Snyk form was reported filled
        # with "work in the office three days per week?*" unanswered.
        out = self.fill("ashby.html?variant=office")
        self.assertEqual(out["result"], "stopped", out)
        self.assertIn("Are you able to work in the office three days per week?", out["unfilled"])
        self.assertEqual(self.fake.records, [])

    def test_lever_radios_and_selects(self):
        out = self.fill("lever.html")
        self.assertEqual(out["result"], "submitted", out)
        v = self.fake.records[-1]["values"]
        self.assertEqual((v["name"], v["org"], v["cards[c1][field0]"], v["eeo[gender]"]),
                         ("Jordan Rivera", "Example Corp", "Yes", "Decline to self-identify"))
        self.assertEqual(v["resume"], self.resume.name)

    def test_missing_current_company_stops_on_lever(self):
        out = self.fill("lever.html", answers={k: v for k, v in ANSWERS.items() if k != "current_company"})
        self.assertEqual(out["result"], "stopped")
        self.assertIn("Current company", out["unfilled"])


class Rules(unittest.TestCase):
    """Label to answer: plain Python, runs without Playwright."""

    def test_labels_map_to_the_users_answers(self):
        import autoapply_forms as f
        cases = {"First Name*": "Jordan", "Legal Last Name": "Rivera", "Email": "jordan@example.com",
                 "Will you now or in the future require employment visa sponsorship to work in the US?": "No",
                 "Are you legally authorised to work full-time in the country where this job is based?*": "Yes",
                 "Current company ✱": "Example Corp", "LinkedIn Profile": "https://www.linkedin.com/in/example",
                 "Why Anthropic?*": None, "Agreement to Arbitrate*": None, "Have you ever interviewed at Acme before?": None}
        for label, want in cases.items():
            self.assertEqual(f.answer_for(label, ANSWERS), want, label)
        # Toast's live form (run 4): a city field and a postal code, answered from the user's own file.
        a = dict(ANSWERS, city="Salt Lake City", postal_code="84101")
        self.assertEqual(f.answer_for("Location (City)*", a), "Salt Lake City")
        self.assertEqual(f.answer_for("What's your postal code?*", a), "84101")
        self.assertIsNone(f.answer_for("What's your postal code?*", ANSWERS))

    def test_authorized_without_sponsorship_combines_both_answers(self):
        # Council release round 1 (B1): this question got the sponsorship answer ("No") and would have
        # knocked out a candidate who needs no sponsorship.
        import autoapply_forms as f
        q = "Are you legally authorized to work in the United States without the need for employer sponsorship?*"
        self.assertEqual(f.answer_for(q, dict(ANSWERS, work_authorization="Yes", sponsorship="No")), "Yes")
        self.assertEqual(f.answer_for(q, dict(ANSWERS, work_authorization="Yes", sponsorship="Yes")), "No")
        self.assertEqual(f.answer_for(q, dict(ANSWERS, work_authorization="No", sponsorship="Yes")), "No")
        self.assertIsNone(f.answer_for(q, {k: v for k, v in ANSWERS.items() if k != "sponsorship"}))
        self.assertIsNone(f.answer_for(q, dict(ANSWERS, sponsorship="Maybe later")))
        self.assertEqual(f.answer_for("Will you now or in the future require sponsorship?*", ANSWERS), "No")

    def test_bank_entry_wins_and_must_be_the_users_wording(self):
        import autoapply_forms as f
        a = dict(ANSWERS, _bank=[{"question": "Have you ever interviewed at Acme before?", "answer": "No"}])
        self.assertEqual(f.answer_for("Have you ever interviewed at Acme before?*", a), "No")
        self.assertIsNone(f.answer_for("Have you ever interviewed at Globex before?*", a))

    def test_option_choice(self):
        import autoapply_forms as f
        self.assertEqual(f.pick("No", ["Yes", "No, I will not require sponsorship"]), "No, I will not require sponsorship")
        self.assertEqual(f.pick("Decline to self-identify", ["Male", "Decline To Self Identify"]), "Decline To Self Identify")
        self.assertIsNone(f.pick("Maybe", ["Yes", "No"]))
        self.assertIsNone(f.pick("No", ["Not sure", "Nope"]))


if __name__ == "__main__":
    unittest.main()
