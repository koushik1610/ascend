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

    def test_a_link_off_the_known_application_systems_is_flagged(self):
        import _v2data as d
        import apply
        ws = apply_ws(self.td.name)
        self.assertIsNone(apply.sheet(ws, "greenhouse:acme:1")["link_note"])
        for bad in ("https://greenhouse.io.evil.example/x", "https://evil.com\\@boards.greenhouse.io/x",
                    "https://u:p@boards.greenhouse.io/x"):
            q = d.read_json(ws / "data" / "queue.json", {})
            q["jobs"][0]["apply_url"] = bad
            d.write_json_atomic(ws / "data" / "queue.json", q)
            self.assertIn("Check the address", apply.sheet(ws, "greenhouse:acme:1")["link_note"], bad)

    def test_refuses_unapproved(self):
        import apply
        with self.assertRaises(apply.Refused):
            apply.sheet(apply_ws(self.td.name, state="matched"), "greenhouse:acme:1")

    def test_sensitive_answers_are_always_asked_never_filled(self):
        import _v2data as d
        import apply
        ws = apply_ws(self.td.name)
        d.write_json_atomic(ws / "data" / "profile.json", dict(PROFILE, salary_expectation="200k", sponsorship="no"))
        s = apply.sheet(ws, "greenhouse:acme:1")
        for k in ("work_authorization", "sponsorship", "salary_expectation", "start_date"):
            self.assertIn(k, s["ask_user"])
            self.assertNotIn(k, s["answers"])

    def test_refuses_a_duplicate(self):
        import apply
        ws = apply_ws(self.td.name, status="applied")
        with self.assertRaises(apply.Refused) as c:
            apply.sheet(ws, "greenhouse:acme:1")
        self.assertIn("DUPLICATE", str(c.exception))

    def test_sheet_checks_the_posting_id_even_with_a_folder(self):
        import _v2data as d
        import apply
        ws = apply_ws(self.td.name)
        q = d.read_json(ws / "data" / "queue.json", {})
        q["jobs"].append({"posting_id": "greenhouse:acme:1", "company": "Other Name", "title": "Other Title",
                          "state": "applied", "applied_on": "2026-10-01"})
        d.write_json_atomic(ws / "data" / "queue.json", q)
        with self.assertRaises(apply.Refused) as c:
            apply.sheet(ws, "greenhouse:acme:1")
        self.assertIn("posting", str(c.exception))

    def test_attaches_the_resume_pdf_not_another_pdf(self):
        import apply
        ws = apply_ws(self.td.name)
        (ws / "jobs/05-acme-staff/A-job-description.pdf").write_bytes(b"%PDF-1.4 jd")
        self.assertTrue(apply.sheet(ws, "greenhouse:acme:1")["resume_pdf"].endswith("Jordan-Rivera-Resume-Acme.pdf"))

    def test_a_pdf_built_in_the_same_run_as_its_resume_passes(self):
        import os
        import apply
        ws = apply_ws(self.td.name)
        job = ws / "jobs/05-acme-staff"
        t = (job / "resume.md").stat().st_mtime
        os.utime(job / "Jordan-Rivera-Resume-Acme.pdf", (t - 0.5, t - 0.5))     # the builder writes the PDF first
        self.assertEqual(apply.sheet(ws, "greenhouse:acme:1")["company"], "Acme Robotics")

    def test_refuses_a_pdf_older_than_its_resume(self):
        import os
        import apply
        ws = apply_ws(self.td.name)
        pdf = ws / "jobs/05-acme-staff/Jordan-Rivera-Resume-Acme.pdf"
        os.utime(pdf, (1, 1))
        with self.assertRaises(apply.Refused) as c:
            apply.sheet(ws, "greenhouse:acme:1")
        self.assertIn("older", str(c.exception))

    def test_refuses_a_resume_that_fails_lint(self):
        import apply
        ws = apply_ws(self.td.name)
        r = ws / "jobs/05-acme-staff/resume.md"
        r.write_text(r.read_text().replace("Own the baseline.", "Own 9,999 accounts."))
        with self.assertRaises(apply.Refused) as c:
            apply.sheet(ws, "greenhouse:acme:1")
        self.assertIn("lint", str(c.exception))


class AssistedOnly(unittest.TestCase):
    """Agent-submit and fully automatic live on the ascend-v2-agent-modes branch, not in this release."""

    def test_no_agent_submit_surface(self):
        import apply
        for name in ("next", "allowed", "pause", "resume"):
            self.assertFalse(hasattr(apply, name), name)
        self.assertFalse((REPO / "tools" / "fakeform.py").exists())
        r = subprocess.run([sys.executable, str(REPO / "tools/apply.py"), "next", "workspace/x", "--mode", "agent"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)


class Record(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.td.cleanup()

    def test_record_submitted_moves_queue_and_folder(self):
        import _v2data as d
        import apply
        import pipeline
        ws = apply_ws(self.td.name)
        apply.record(ws, "greenhouse:acme:1", "submitted")
        self.assertEqual(d.read_json(ws / "data" / "queue.json", {})["jobs"][0]["state"], "applied")
        self.assertEqual(pipeline.parse_state(ws / "jobs/05-acme-staff/application-log.md")["status"], "applied")

    def test_record_needs_an_approved_job_and_counts_a_send_once(self):
        import _v2data as d
        import apply
        with self.assertRaises(apply.Refused):
            apply.record(apply_ws(self.td.name + "/m", state="matched"), "greenhouse:acme:1", "submitted")
        ws = apply_ws(self.td.name)
        apply.record(ws, "greenhouse:acme:1", "submitted")
        apply.record(ws, "greenhouse:acme:1", "submitted")      # a double-click
        self.assertEqual(len(d.read_jsonl(ws / "data" / "apply-log.jsonl")), 1)

    def test_record_is_not_a_command(self):
        ws = apply_ws(self.td.name)
        r = subprocess.run([sys.executable, str(REPO / "tools/apply.py"), "record", str(ws), "greenhouse:acme:1",
                            "submitted"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        self.assertIn("hub", r.stderr)

    def test_only_a_submission_is_recorded_in_this_release(self):
        import apply
        ws = apply_ws(self.td.name)
        for result in ("unclear", "stopped"):
            with self.assertRaises(ValueError):
                apply.record(ws, "greenhouse:acme:1", result)

    def test_marking_applied_from_the_hub_moves_the_folder(self):
        import jobqueue
        import pipeline
        ws = apply_ws(self.td.name)
        jobqueue.set_state(ws, "greenhouse:acme:1", "applied")
        self.assertEqual(pipeline.parse_state(ws / "jobs/05-acme-staff/application-log.md")["status"], "applied")


if __name__ == "__main__":
    unittest.main()
