"""Ascend 2.0 M9: validated add commands for Claude-sourced rows (engines B and C, LinkedIn search).

Run: python3 -m unittest tests/test_v2_engines.py -v
"""

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


class FinderAdd(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.ws = make_ws(self.td.name, [])

    def tearDown(self):
        self.td.cleanup()

    def test_add_normalizes_dedupes_and_validates(self):
        import _v2data as d
        import finder
        rows = [{"company": "Acme", "title": "Staff Security Engineer", "url": "https://jobs.example/1",
                 "location": "Remote - US", "text": "<p>AWS</p>" + "x" * 9000},
                {"company": "Acme", "title": "Staff Security Engineer", "url": "https://jobs.example/1"},
                {"company": "NoUrl", "title": "Principal"}]
        out = finder.add(self.ws, rows, "linkedin")
        self.assertEqual(out, {"added": 1, "skipped": 2})
        p = d.read_jsonl(self.ws / "data" / "postings.jsonl")[0]
        self.assertTrue(p["id"].startswith("linkedin:"))
        self.assertEqual((p["remote"], p["source"], len(p["text"])), (True, "linkedin", 6000))
        self.assertTrue(p["text"].startswith("AWS"))

    def test_ats_url_maps_to_the_board_id_closed_or_duplicate(self):
        import _v2data as d
        import finder
        dd = self.ws / "data"
        d.write_json_atomic(dd / "sources.json", {"boards": [{"ats": "greenhouse", "slug": "acme", "company": "Acme"}]})
        d.write_json_atomic(dd / "postings-state.json", {"greenhouse:acme:1": {"closed": False, "last_seen": "2026-10-16"}})
        d.append_jsonl(dd / "postings.jsonl", {"id": "greenhouse:acme:1", "url": "https://boards.example/gh/1"})
        rows = [{"company": "Acme", "title": "Staff Security Engineer", "url": "https://job-boards.greenhouse.io/acme/jobs/1"},
                {"company": "Acme", "title": "Old Role", "url": "https://job-boards.greenhouse.io/acme/jobs/2"},
                {"company": "Other", "title": "Staff", "url": "https://jobs.lever.co/other/a7f70c18-72a9-4708-ac49-c0ab9acdf537"}]
        self.assertEqual(finder.add(self.ws, rows, "web"), {"added": 2, "skipped": 1})
        state = d.read_json(dd / "postings-state.json", {})
        self.assertTrue(state["greenhouse:acme:2"]["closed"])
        self.assertFalse(state["lever:other:a7f70c18-72a9-4708-ac49-c0ab9acdf537"]["closed"])

    def test_alert_leads_without_urls_do_not_block_adds(self):
        import _v2data as d
        import finder
        d.append_jsonl(self.ws / "data" / "postings.jsonl", {"id": "alert:w1:0", "url": None, "source": "alert"})
        rows = [{"company": "MongoDB", "title": "Principal Security Engineer", "url": "https://www.linkedin.com/jobs/view/1"}]
        self.assertEqual(finder.add(self.ws, rows, "linkedin"), {"added": 1, "skipped": 0})

    def test_cli(self):
        rows = json.dumps([{"company": "Bravo", "title": "Principal Security Engineer", "url": "https://jobs.example/2"}])
        r = subprocess.run([sys.executable, str(REPO / "tools/finder.py"), "add", str(self.ws), "--source", "web",
                            "--json", rows], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["added"], 1)


class GmailAdd(unittest.TestCase):
    def setUp(self):
        import _v2data as d
        self.td = tempfile.TemporaryDirectory()
        self.ws = make_ws(self.td.name, [])
        d.write_json_atomic(self.ws / "data" / "profile.json", {"email": "me@example.com"})

    def tearDown(self):
        self.td.cleanup()

    def test_add_caps_skips_own_and_dupes(self):
        import _v2data as d
        import gmail_sync as g
        rows = [{"msg_id": "a", "from": "Recruiter <r@co.example>", "subject": "Hi", "date": "2026-10-16T10:00:00Z",
                 "body_excerpt": "y" * 5000},
                {"msg_id": "a", "from": "r@co.example", "subject": "dup", "date": "2026-10-16T10:00:00Z"},
                {"msg_id": "b", "from": "Me <me@example.com>", "subject": "my note", "date": "2026-10-16T10:00:00Z"},
                {"msg_id": "c", "from": "x@co.example", "subject": "draft", "date": "2026-10-16T10:00:00Z",
                 "labels": ["DRAFT"]},
                {"msg_id": "d", "subject": "no sender"}]
        self.assertEqual(g.add(self.ws, rows), {"added": 1, "skipped": 4})
        self.assertEqual(len(d.read_jsonl(self.ws / "data" / "mail.jsonl")[0]["body_excerpt"]), 2000)

    def test_added_mail_classifies(self):
        import _v2data as d
        import gmail_sync as g
        g.add(self.ws, [{"msg_id": "z", "from": "no-reply@ashbyhq.com", "subject": "Thanks for applying",
                         "date": "2026-10-16T10:00:00Z", "body_excerpt": "We received your application."}])
        subprocess.run([sys.executable, str(REPO / "tools/classify.py"), "run", str(self.ws)], check=True,
                       capture_output=True)
        self.assertEqual(d.read_jsonl(self.ws / "data" / "events.jsonl")[0]["category"], "acknowledgement")


class Steps(unittest.TestCase):
    def test_engine_sources(self):
        import run
        self.assertTrue(run.steps("B")[0].startswith("CLAUDE: read new Gmail"))
        self.assertIn("gmail_sync.py add", " ".join(run.steps("C")))
        self.assertIn("finder.py add", " ".join(run.steps("B")))


class Resolve(unittest.TestCase):
    """The model's verdict on mail the rules could not place: an append-only correction that ingest,
    the hub and the pending count all honour."""

    def setUp(self):
        import _v2data as d
        self.td = tempfile.TemporaryDirectory()
        self.ws = make_ws(self.td.name, [("01-streamco", "StreamCo", "Security Engineer", "applied")])
        d.write_json_atomic(self.ws / "data" / "queue.json", {"jobs": [{"posting_id": "x1", "company": "StreamCo",
                                                                        "title": "Security Engineer", "nn": "01"}]})
        d.append_jsonl(self.ws / "data" / "mail.jsonl", {"msg_id": "n1", "from": "recruiter@jobs.streamco.example",
                                                         "subject": "Next steps w/ StreamCo", "date": "2026-10-16T21:00:00Z",
                                                         "body_excerpt": "Thanks again for taking the time to chat. After connecting with the team, we"})
        subprocess.run([sys.executable, str(REPO / "tools/classify.py"), "run", str(self.ws)], check=True, capture_output=True)
        subprocess.run([sys.executable, str(REPO / "tools/pipeline.py"), "ingest", str(self.ws)], check=True, capture_output=True)

    def tearDown(self):
        self.td.cleanup()

    def test_resolve_moves_the_job_and_clears_pending(self):
        import classify
        import hub
        import pipeline
        self.assertEqual(classify.pending(self.ws), ["n1"])
        classify.resolve(self.ws, "n1", "interview-invite")
        subprocess.run([sys.executable, str(REPO / "tools/pipeline.py"), "ingest", str(self.ws)], check=True, capture_output=True)
        self.assertEqual(pipeline.parse_state(self.ws / "jobs/01-streamco/application-log.md")["status"], "screen")
        self.assertEqual(classify.pending(self.ws), [])
        inbox = hub.compute(self.ws)["inbox"]
        self.assertEqual([(i["msg_id"], i["category"]) for i in inbox], [("n1", "interview-invite")])

    def test_resolve_only_touches_mail_waiting_for_a_model(self):
        import _v2data as d
        import classify
        d.append_jsonl(self.ws / "data" / "mail.jsonl", {"msg_id": "r1", "from": "no-reply@greenhouse.io",
                                                         "subject": "Update on your application", "date": "2026-10-16T22:00:00Z",
                                                         "body_excerpt": "Unfortunately we have decided not to move forward."})
        subprocess.run([sys.executable, str(REPO / "tools/classify.py"), "run", str(self.ws)], check=True, capture_output=True)
        with self.assertRaises(ValueError):
            classify.resolve(self.ws, "r1", "interview-invite")

    def test_resolve_rejects_unknown_category_and_message(self):
        import classify
        with self.assertRaises(ValueError):
            classify.resolve(self.ws, "n1", "teleport")
        with self.assertRaises(KeyError):
            classify.resolve(self.ws, "nope", "rejection")


if __name__ == "__main__":
    unittest.main()
