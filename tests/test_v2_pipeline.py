"""Ascend 2.0 M2: ingest classified mail into the ledger, and the duplicate-apply guard.

Run: python3 -m unittest tests/test_v2_pipeline.py -v
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
TOOL = [sys.executable, str(REPO / "tools/pipeline.py")]


def make_ws(root, jobs):
    """A workspace with job folders. pipeline.py refuses paths without a `workspace` component."""
    ws = Path(root) / "workspace" / "tester"
    for slug, company, role, status in jobs:
        d = ws / "jobs" / slug
        d.mkdir(parents=True)
        log = f"# Application Log: {company}, {role}\n\nNotes the user wrote.\n"
        if status:
            log += f"\n```ascend-state\nstatus: {status}\napplied_on: 2026-09-01\n```\n"
        (d / "application-log.md").write_text(log, encoding="utf-8")
    (ws / "data").mkdir(parents=True, exist_ok=True)
    return ws


def add_events(ws, events):
    import _v2data as d
    for e in events:
        d.append_jsonl(ws / "data" / "events.jsonl", e)


def state(ws, slug):
    import pipeline
    return pipeline.parse_state(ws / "jobs" / slug / "application-log.md")


def ingest(ws):
    r = subprocess.run(TOOL + ["ingest", str(ws), "--json"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def ev(msg_id, category, match, date="2026-10-05T10:00:00Z", due=None):
    return {"msg_id": msg_id, "category": category, "match": match, "date": date, "due": due}


class Ingest(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.ws = make_ws(self.td.name, [
            ("01-acme-staff", "Acme Robotics", "Staff Security Engineer", None),
            ("02-northwind-principal", "Northwind", "Principal Cloud Security Engineer", "applied"),
            ("03-litware-staff", "Litware", "Staff Detection Engineer", "screen"),
        ])

    def tearDown(self):
        self.td.cleanup()

    def test_acknowledgement_moves_queued_to_applied(self):
        add_events(self.ws, [ev("a1", "acknowledgement", "01")])
        out = ingest(self.ws)
        self.assertEqual(out["applied"], 1)
        st = state(self.ws, "01-acme-staff")
        self.assertEqual((st["status"], st["applied_on"]), ("applied", "2026-10-05"))

    def test_interview_invite_moves_applied_to_screen(self):
        add_events(self.ws, [ev("a2", "interview-invite", "02")])
        ingest(self.ws)
        self.assertEqual(state(self.ws, "02-northwind-principal")["status"], "screen")

    def test_rejection_after_screen(self):
        add_events(self.ws, [ev("a3", "rejection", "03")])
        ingest(self.ws)
        self.assertEqual(state(self.ws, "03-litware-staff")["status"], "rejected")

    def test_a_body_only_match_never_closes_a_job(self):
        add_events(self.ws, [dict(ev("a6", "rejection", "02"), match_by="body")])
        out = ingest(self.ws)
        self.assertEqual(state(self.ws, "02-northwind-principal")["status"], "applied")
        self.assertEqual(out["applied"], 0)

    def test_never_moves_backwards(self):
        add_events(self.ws, [ev("a4", "acknowledgement", "03")])
        out = ingest(self.ws)
        self.assertEqual(out["applied"], 0)
        self.assertEqual(state(self.ws, "03-litware-staff")["status"], "screen")

    def test_assessment_sets_due_date(self):
        add_events(self.ws, [ev("a5", "assessment", "02", due="2026-10-12")])
        ingest(self.ws)
        st = state(self.ws, "02-northwind-principal")
        self.assertEqual((st["status"], st["next_followup_due"]), ("responded", "2026-10-12"))

    def test_posting_id_resolves_through_queue(self):
        import _v2data as d
        d.write_json_atomic(self.ws / "data" / "queue.json",
                            {"jobs": [{"posting_id": "gh:northwind:2", "company": "Northwind", "nn": "02"}]})
        add_events(self.ws, [ev("a6", "interview-invite", "gh:northwind:2")])
        ingest(self.ws)
        self.assertEqual(state(self.ws, "02-northwind-principal")["status"], "screen")

    def test_unmatched_and_informational_events_are_counted_not_applied(self):
        add_events(self.ws, [ev("a7", "rejection", None), ev("a8", "status-update", "02"),
                             ev("a9", "job-alert", None)])
        out = ingest(self.ws)
        self.assertEqual((out["applied"], out["unmatched"], out["skipped"]), (0, 1, 2))
        self.assertEqual(state(self.ws, "02-northwind-principal")["status"], "applied")

    def test_idempotent(self):
        add_events(self.ws, [ev("b1", "acknowledgement", "01"), ev("b2", "interview-invite", "01",
                                                                      date="2026-10-07T10:00:00Z")])
        first = ingest(self.ws)
        second = ingest(self.ws)
        self.assertEqual(first["applied"], 2)
        self.assertEqual(second["applied"] + second["skipped"] + second["unmatched"], 0)

    def test_ledger_rows_are_sourced_gmail_and_prose_survives(self):
        import pipeline
        add_events(self.ws, [ev("c1", "acknowledgement", "01")])
        ingest(self.ws)
        rows = pipeline.read_ledger(self.ws)
        self.assertEqual([(r["slug"], r["from"], r["to"], r["source"]) for r in rows],
                         [("01-acme-staff", "queued", "applied", "gmail")])
        text = (self.ws / "jobs/01-acme-staff/application-log.md").read_text()
        self.assertIn("Notes the user wrote.", text)


class Guard(unittest.TestCase):
    def setUp(self):
        import _v2data as d
        self.td = tempfile.TemporaryDirectory()
        self.ws = make_ws(self.td.name, [
            ("01-acme-staff", "Acme Robotics", "Staff Security Engineer", "applied"),
            ("02-litware-queued", "Litware", "Staff Detection Engineer", None),
        ])
        d.write_json_atomic(self.ws / "data" / "queue.json", {"jobs": [
            {"posting_id": "gh:northwind:2", "company": "Northwind", "title": "Sr. Staff Security Engineer",
             "state": "applied", "applied_on": "2026-10-01"},
            {"posting_id": "gh:contoso:4", "company": "Contoso", "title": "Security Engineer", "state": "matched"}]})

    def tearDown(self):
        self.td.cleanup()

    def guard(self, *args):
        return subprocess.run(TOOL + ["guard", str(self.ws), *args], capture_output=True, text=True)

    def test_same_posting_id_blocks(self):
        r = self.guard("--company", "Northwind", "--title", "Anything", "--posting-id", "gh:northwind:2",
                       "--today", "2026-10-10")
        self.assertEqual(r.returncode, 3)
        self.assertIn("DUPLICATE", r.stdout)

    def test_same_company_and_normalized_title_within_60_days_blocks(self):
        r = self.guard("--company", "Northwind, Inc.", "--title", "Senior Staff Security Engineer",
                       "--today", "2026-11-29")
        self.assertEqual(r.returncode, 3)

    def test_same_pair_after_60_days_is_allowed(self):
        r = self.guard("--company", "Northwind", "--title", "Senior Staff Security Engineer",
                       "--today", "2026-12-01")
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "OK"))

    def test_different_title_same_company_is_allowed(self):
        r = self.guard("--company", "Northwind", "--title", "Security Engineering Manager", "--today", "2026-10-10")
        self.assertEqual(r.returncode, 0)

    def test_applied_job_folder_blocks_same_title(self):
        r = self.guard("--company", "Acme Robotics", "--title", "Staff Security Engineer", "--today", "2026-10-10")
        self.assertEqual(r.returncode, 3)

    def test_board_slug_matches_the_company_name(self):
        r = self.guard("--company", "acmeroboticshq", "--title", "Staff Security Engineer", "--today", "2026-10-10")
        self.assertEqual(r.returncode, 3, r.stdout)
        self.assertEqual(self.guard("--company", "Acme", "--title", "Staff Security Engineer",
                                    "--today", "2026-10-10").returncode, 0)

    def test_queued_folder_and_matched_queue_entry_never_block(self):
        self.assertEqual(self.guard("--company", "Litware", "--title", "Staff Detection Engineer",
                                    "--today", "2026-10-10").returncode, 0)
        self.assertEqual(self.guard("--company", "Contoso", "--title", "Security Engineer",
                                    "--posting-id", "gh:contoso:4", "--today", "2026-10-10").returncode, 0)

    def test_missing_args_exit_2(self):
        r = self.guard("--company", "Acme")
        self.assertEqual(r.returncode, 2)
        self.assertIn("usage: guard", r.stderr)

    def test_unknown_application_date_says_so(self):
        import _v2data as d
        ws = make_ws(self.td.name + "/b", [("05-grove-staff", "Grove Health", "Staff Engineer", None)])
        log = ws / "jobs/05-grove-staff/application-log.md"
        log.write_text(log.read_text() + "\n```ascend-state\nstatus: screen\n```\n")
        r = subprocess.run(TOOL + ["guard", str(ws), "--company", "Grove Health", "--title", "Staff Engineer"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 3)
        self.assertIn("date unknown", r.stdout)
        self.assertNotIn("0 day(s) ago", r.stdout)

    def test_normalize_title(self):
        import pipeline
        self.assertEqual(pipeline.normalize_title("Sr. Staff Security Eng (Remote)"),
                         pipeline.normalize_title("Senior Staff Security Engineer"))


if __name__ == "__main__":
    unittest.main()
