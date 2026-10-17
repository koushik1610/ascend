"""Ascend 2.0 M8: applying. Run: python3 -m unittest tests/test_v2_apply.py -v"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(REPO / "tests"))
from test_v2_pipeline import make_ws  # noqa: E402

LINT = [sys.executable, str(REPO / "tools/lint_artifacts.py")]
MASTER = "# Master\n\n## Bullets\n- **PR1** [x] (src: A1): Own the baseline.\n- **Y4** [x] (src: C2): Designed enforcement.\n"
RESUME = ("# Jordan Rivera\n\n- Own the baseline.\n\n<!-- DELTA LOG (selection only)\n  YahooP: PR1 (A1)\n"
          "  Yahoo: Y4 (C2)\n-->\n")


def job_ws(root, resume=RESUME, cfg=None, status=None):
    ws = make_ws(root, [("05-acme-staff", "Acme Robotics", "Staff Security Engineer", status)])
    (ws / "master-resume.md").write_text(MASTER, encoding="utf-8")
    job = ws / "jobs/05-acme-staff"
    (job / "resume.md").write_text(resume, encoding="utf-8")
    (job / "Jordan-Rivera-Resume-Acme.pdf").write_bytes(b"%PDF-1.4 fake")
    (ws / "lint-config.json").write_text(json.dumps(cfg if cfg is not None else
                                                    {"id_prefixes": ["PR", "Y", "C"], "forbidden_patterns": ["9,999"]}))
    return ws


class LintPrefixes(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.td.cleanup()

    def lint(self, ws):
        return subprocess.run(LINT + ["--config", str(ws / "lint-config.json"), str(ws / "jobs/05-acme-staff/resume.md")],
                              capture_output=True, text=True)

    def test_user_prefixes_and_bullet_declarations_pass(self):
        r = self.lint(job_ws(self.td.name))
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_cited_id_missing_from_master_still_fails(self):
        r = self.lint(job_ws(self.td.name, resume=RESUME.replace("Y4 (C2)", "Y99 (C2)")))
        self.assertEqual(r.returncode, 1)
        self.assertIn("'Y99'", r.stdout)

    def test_default_grammar_unchanged_without_prefixes(self):
        r = self.lint(job_ws(self.td.name, cfg={}))
        self.assertEqual(r.returncode, 1)
        self.assertIn("cites no master entry IDs", r.stdout)


PROFILE = {"name": "Jordan Rivera", "email": "jordan@example.com", "phone": "555-0100", "location": "Remote, US",
           "linkedin": "https://www.linkedin.com/in/example", "website": "https://jordan.example",
           "work_authorization": None, "sponsorship": None, "salary_expectation": None, "start_date": None}


def apply_ws(root, state="approved", fit=82, status=None, cfg=None):
    import _v2data as d
    ws = job_ws(root, cfg=cfg, status=status)
    d.write_json_atomic(ws / "data" / "profile.json", PROFILE)
    d.write_json_atomic(ws / "data" / "queue.json", {"jobs": [{
        "posting_id": "greenhouse:acme:1", "company": "Acme Robotics", "title": "Staff Security Engineer",
        "nn": "05", "fit": fit, "state": state, "apply_url": "https://boards.greenhouse.io/acme/jobs/1"}]})
    return ws


class Sheet(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.td.cleanup()

    def test_sheet_for_an_approved_job(self):
        import apply
        ws = apply_ws(self.td.name)
        s = apply.sheet(ws, "greenhouse:acme:1")
        self.assertTrue(s["resume_pdf"].endswith("Jordan-Rivera-Resume-Acme.pdf"))
        self.assertEqual((s["answers"]["email"], s["apply_url"]), ("jordan@example.com", "https://boards.greenhouse.io/acme/jobs/1"))
        self.assertIn("work_authorization", s["ask_user"])
        self.assertNotIn("work_authorization", s["answers"])
        self.assertTrue((ws / "data" / "apply-sheets").is_dir())

    def test_refuses_unapproved(self):
        import apply
        with self.assertRaises(apply.Refused):
            apply.sheet(apply_ws(self.td.name, state="matched"), "greenhouse:acme:1")

    def test_automatic_mode_takes_matched_at_threshold(self):
        import apply
        ws = apply_ws(self.td.name, state="matched", fit=80)
        self.assertEqual(apply.sheet(ws, "greenhouse:acme:1", mode="automatic")["company"], "Acme Robotics")
        with self.assertRaises(apply.Refused):
            apply.sheet(apply_ws(self.td.name + "/b", state="matched", fit=60), "greenhouse:acme:1", mode="automatic")

    def test_refuses_a_duplicate(self):
        import apply
        ws = apply_ws(self.td.name, status="applied")
        with self.assertRaises(apply.Refused) as c:
            apply.sheet(ws, "greenhouse:acme:1")
        self.assertIn("DUPLICATE", str(c.exception))

    def test_refuses_a_resume_that_fails_lint(self):
        import apply
        ws = apply_ws(self.td.name)
        r = ws / "jobs/05-acme-staff/resume.md"
        r.write_text(r.read_text().replace("Own the baseline.", "Own 9,999 accounts."))
        with self.assertRaises(apply.Refused) as c:
            apply.sheet(ws, "greenhouse:acme:1")
        self.assertIn("lint", str(c.exception))


class Allowed(unittest.TestCase):
    def test_allow_list(self):
        import apply
        for u in ["https://boards.greenhouse.io/acme/jobs/1", "https://jobs.lever.co/acme/x/apply",
                  "https://jobs.ashbyhq.com/acme/u1/application", "https://acme.wd5.myworkdayjobs.com/x"]:
            self.assertTrue(apply.allowed(u), u)
        for u in ["http://boards.greenhouse.io/acme/jobs/1", "https://greenhouse.io.evil.example/x",
                  "https://tracking.us.nylas.com/l/abc", "javascript:alert(1)"]:
            self.assertFalse(apply.allowed(u), u)


class NextAndRecord(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.td.cleanup()

    def test_pause_and_cap(self):
        import apply
        ws = apply_ws(self.td.name)
        self.assertEqual(apply.next(ws, "agent")["posting_id"], "greenhouse:acme:1")
        apply.pause(ws, "taking a break")
        out = apply.next(ws, "agent")
        self.assertIsNone(out["job"])
        self.assertIn("paused", out["reason"])
        apply.resume(ws)
        self.assertIsNone(apply.next(ws, "agent", cap=0)["job"])

    def test_reply_rate_auto_pause_only_in_automatic(self):
        import _v2data as d
        import apply
        ws = apply_ws(self.td.name, state="matched", fit=90)
        for i in range(50):
            d.append_jsonl(ws / "data" / "apply-log.jsonl", {"posting_id": f"p{i}", "result": "submitted",
                                                              "at": "2026-09-01T00:00:00"})
        out = apply.next(ws, "automatic")
        self.assertIsNone(out["job"])
        self.assertIn("reply rate", out["reason"])

    def test_record_submitted_moves_queue_and_folder(self):
        import _v2data as d
        import apply
        import pipeline
        ws = apply_ws(self.td.name)
        apply.record(ws, "greenhouse:acme:1", "submitted")
        self.assertEqual(d.read_json(ws / "data" / "queue.json", {})["jobs"][0]["state"], "applied")
        self.assertEqual(pipeline.parse_state(ws / "jobs/05-acme-staff/application-log.md")["status"], "applied")

    def test_record_unclear_and_stopped(self):
        import _v2data as d
        import apply
        ws = apply_ws(self.td.name)
        apply.record(ws, "greenhouse:acme:1", "stopped", "CAPTCHA on the form")
        job = d.read_json(ws / "data" / "queue.json", {})["jobs"][0]
        self.assertEqual((job["state"], job["stop_reason"]), ("needs-you", "CAPTCHA on the form"))
        apply.record(ws, "greenhouse:acme:1", "unclear")
        self.assertEqual(d.read_json(ws / "data" / "queue.json", {})["jobs"][0]["state"], "applied?")

    def test_marking_applied_from_the_hub_moves_the_folder(self):
        import jobqueue
        import pipeline
        ws = apply_ws(self.td.name)
        jobqueue.set_state(ws, "greenhouse:acme:1", "applied")
        self.assertEqual(pipeline.parse_state(ws / "jobs/05-acme-staff/application-log.md")["status"], "applied")


class FakeForm(unittest.TestCase):
    def test_records_submissions_and_serves_variants(self):
        import http.client
        import time
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "submissions.jsonl"
            proc = subprocess.Popen([sys.executable, str(REPO / "tools/fakeform.py"), "serve", "--port", "8963",
                                     "--log", str(log)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                time.sleep(1.0)
                def get(path):
                    c = http.client.HTTPConnection("127.0.0.1", 8963, timeout=5)
                    c.request("GET", path); r = c.getresponse(); b = r.read().decode(); c.close(); return r.status, b
                self.assertIn('name="first_name"', get("/apply/plain")[1])
                self.assertIn("captcha", get("/apply/captcha")[1].lower())
                self.assertIn("authorized to work", get("/apply/workauth")[1])
                c = http.client.HTTPConnection("127.0.0.1", 8963, timeout=5)
                c.request("POST", "/apply/plain", body="first_name=Jordan&email=j%40example.com",
                          headers={"Content-Type": "application/x-www-form-urlencoded"})
                r = c.getresponse(); body = r.read().decode(); c.close()
                self.assertIn("Application received", body)
                self.assertEqual(json.loads(log.read_text().splitlines()[0])["fields"]["first_name"], "Jordan")
            finally:
                proc.terminate(); proc.wait(timeout=5)


if __name__ == "__main__":
    unittest.main()
