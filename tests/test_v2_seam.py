"""Ascend 2.0: the seam between v1 job folders and the v2 queue, found by a from-scratch run.

No test here writes `nn` by hand: every link comes from the tools.

Run: python3 -m unittest tests/test_v2_seam.py -v
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
from test_v2_pipeline import make_ws, state  # noqa: E402

FOLDERS = [("05-affirm-staff-security-enterprise-ai", "Affirm", "Staff Security Engineer, Enterprise AI", None),
           ("00-grow-therapy-staff-cloud-infra-security", "Grow Therapy",
            "Senior/Staff Engineer, Cloud & Infrastructure Security", "screen"),
           ("10-doordash-staff-proactive-security-ai", "DoorDash", "Staff Security Engineer, Proactive Security - AI", None)]
JD = {"05-affirm-staff-security-enterprise-ai": "https://job-boards.greenhouse.io/affirm/jobs/7994553003",
      "00-grow-therapy-staff-cloud-infra-security": "https://jobs.ashbyhq.com/grow-therapy/40326d35-cf61-4b93-bc39-2679c07b4332",
      "10-doordash-staff-proactive-security-ai": "https://boards.greenhouse.io/doordashusa/jobs/8154315"}


def seed(root):
    ws = make_ws(root, FOLDERS)
    for slug, url in JD.items():
        log = ws / "jobs" / slug / "application-log.md"
        log.write_text(log.read_text().replace("\nNotes the user wrote.\n",
                                               f"\n| Fit Score | 84/100 |\n| JD | {url} |\n\nNotes.\n"))
    return ws


def post(ws, pid, company, title, passed=True):
    import _v2data as d
    d.append_jsonl(ws / "data" / "postings.jsonl", {"id": pid, "company": company, "title": title, "location": "Remote",
                                                    "url": f"https://x.example/{pid}", "text": "role text"})
    d.append_jsonl(ws / "data" / "candidates.jsonl", {"posting_id": pid, "passed": passed, "keyword_overlap": 0.5,
                                                      "reasons": [], "filters_hash": "h"})


def queue(ws):
    import _v2data as d
    return d.read_json(ws / "data" / "queue.json", {"jobs": []})["jobs"]


class Sync(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.ws = seed(self.td.name)

    def tearDown(self):
        self.td.cleanup()

    def test_folders_enter_the_queue_linked_with_their_posting_id(self):
        import jobqueue
        out = jobqueue.sync_folders(self.ws)
        self.assertEqual(out["added"], 3)
        by_nn = {j["nn"]: j for j in queue(self.ws)}
        self.assertEqual(by_nn["05"]["posting_id"], "greenhouse:affirm:7994553003")
        self.assertEqual(by_nn["05"]["state"], "matched")
        self.assertEqual(by_nn["00"]["state"], "applied")      # a folder past queued was sent
        self.assertEqual(by_nn["05"]["source"], "v1")
        self.assertEqual(jobqueue.sync_folders(self.ws)["added"], 0)   # idempotent

    def test_finder_posting_for_a_folder_is_never_a_candidate(self):
        import jobqueue
        post(self.ws, "greenhouse:affirm:7994553003", "affirm", "Staff Security Engineer, Enterprise AI")
        post(self.ws, "greenhouse:doordashusa:8154315", "doordashusa", "Staff Security Engineer, Proactive Security - AI")
        post(self.ws, "greenhouse:affirm:1", "affirm", "Security Risk Management Lead")
        ids = [c["posting_id"] for c in jobqueue.candidates(self.ws)]
        self.assertEqual(ids, ["greenhouse:affirm:1"])

    def test_scored_entry_links_to_an_existing_folder(self):
        import jobqueue
        post(self.ws, "greenhouse:doordashusa:999", "doordashusa", "Staff Security Engineer, Proactive Security - AI")
        jobqueue.score(self.ws, "greenhouse:doordashusa:999", 70, "why", [])
        jobqueue.sync_folders(self.ws)
        dd = [j for j in queue(self.ws) if j.get("company", "").lower().startswith("doordash")]
        self.assertEqual(len(dd), 1, dd)       # the folder's entry, not a second one
        self.assertEqual(dd[0]["nn"], "10")


class Link(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.ws = seed(self.td.name)
        import jobqueue
        post(self.ws, "greenhouse:affirm:1", "affirm", "Security Risk Management Lead")
        jobqueue.score(self.ws, "greenhouse:affirm:1", 40, "why", [])

    def tearDown(self):
        self.td.cleanup()

    def test_link_refuses_a_folder_for_a_different_role(self):
        import jobqueue
        with self.assertRaises(ValueError):
            jobqueue.link(self.ws, "greenhouse:affirm:1", "05")

    def test_link_refuses_a_substring(self):
        import jobqueue
        with self.assertRaises(ValueError):
            jobqueue.link(self.ws, "greenhouse:affirm:1", "affirm")

    def test_link_and_sheet_for_a_new_pack(self):
        import apply
        import jobqueue
        d = self.ws / "jobs" / "15-affirm-security-risk-management-lead"
        d.mkdir()
        (d / "application-log.md").write_text("# Application Log: Affirm, Security Risk Management Lead\n")
        jobqueue.link(self.ws, "greenhouse:affirm:1", "15")
        self.assertEqual(next(j for j in queue(self.ws) if j["posting_id"] == "greenhouse:affirm:1")["nn"], "15")
        jobqueue.set_state(self.ws, "greenhouse:affirm:1", "approved", via_hub=True)
        with self.assertRaises(apply.Refused) as cm:        # linked, but no résumé yet
            apply.sheet(self.ws, "greenhouse:affirm:1")
        self.assertIn("no résumé PDF in 15-affirm", str(cm.exception))

    def test_sheet_refuses_a_folder_for_another_role(self):
        import _v2data as d
        import apply
        import jobqueue
        jobqueue.set_state(self.ws, "greenhouse:affirm:1", "approved", via_hub=True)

        def bad(q):
            next(j for j in q["jobs"] if j["posting_id"] == "greenhouse:affirm:1")["nn"] = "05"
        d.update_json(self.ws / "data" / "queue.json", {"jobs": []}, bad)
        with self.assertRaises(apply.Refused) as cm:
            apply.sheet(self.ws, "greenhouse:affirm:1")
        self.assertIn("different role", str(cm.exception))

    def test_hub_only_states_need_the_hub(self):
        import jobqueue
        with self.assertRaises(ValueError):
            jobqueue.set_state(self.ws, "greenhouse:affirm:1", "approved")

    def test_unapproved_refusal_names_link_when_no_folder(self):
        import apply
        import jobqueue
        jobqueue.set_state(self.ws, "greenhouse:affirm:1", "approved", via_hub=True)
        with self.assertRaises(apply.Refused) as cm:
            apply.sheet(self.ws, "greenhouse:affirm:1")
        self.assertIn("jobqueue.py link", str(cm.exception))


class Mail(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.ws = seed(self.td.name)

    def tearDown(self):
        self.td.cleanup()

    def test_slug_company_matches_the_real_name(self):
        import classify
        jobs = [{"posting_id": "p1", "company": "doordashusa", "title": "Staff Security Engineer"},
                {"posting_id": "p2", "company": "andurilindustries", "title": "Staff Security Engineer"}]
        self.assertEqual(classify.match_job({"from": "no-reply@ashbyhq.com",
                                             "subject": "Your application to DoorDash"}, jobs), "p1")
        self.assertEqual(classify.match_job({"from": "x@gmail.com",
                                             "subject": "Interview with Anduril Industries"}, jobs), "p2")

    def test_two_roles_at_one_company_need_the_title(self):
        import classify
        jobs = [{"posting_id": "p1", "company": "Affirm", "title": "Staff Security Engineer, Enterprise AI", "nn": "05"},
                {"posting_id": "p2", "company": "Affirm", "title": "Security Risk Management Lead"}]
        msg = {"from": "no-reply@greenhouse.io", "subject": "Your application to Affirm",
               "body_excerpt": "Thank you for applying for the Security Risk Management Lead role. Unfortunately"}
        self.assertEqual(classify.match_job(msg, jobs), "p2")
        msg["body_excerpt"] = "Thank you for applying. Unfortunately we will not move forward."
        self.assertIsNone(classify.match_job(msg, jobs))

    def test_unmatched_mail_matches_once_the_folder_is_known(self):
        import _v2data as d
        dd = self.ws / "data"
        d.append_jsonl(dd / "mail.jsonl", {"msg_id": "m1", "from": "recruiter@growtherapy.com",
                                           "subject": "Grow Therapy: Availability Request",
                                           "body_excerpt": "", "date": "2026-10-15T22:24:05Z"})
        run = lambda *a: subprocess.run([sys.executable, str(REPO / "tools" / a[0])] + list(a[1:]),  # noqa: E731
                                        capture_output=True, text=True)
        self.assertEqual(run("classify.py", "run", str(self.ws)).returncode, 0)
        ev = d.read_jsonl(dd / "events.jsonl")[-1]
        self.assertEqual(ev["category"], "interview-invite")
        r = run("pipeline.py", "ingest", str(self.ws), "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["unmatched"], 0)
        self.assertEqual(state(self.ws, "00-grow-therapy-staff-cloud-infra-security")["status"], "screen")
        # Matched to the folder, so it is done: a second ingest has nothing to do.
        self.assertEqual(json.loads(run("pipeline.py", "ingest", str(self.ws), "--json").stdout)["unmatched"], 0)

    def test_unmatched_event_is_retried(self):
        import _v2data as d
        dd = self.ws / "data"
        d.append_jsonl(dd / "mail.jsonl", {"msg_id": "m2", "from": "talent@neweco.example",
                                           "subject": "Neweco: Availability Request", "body_excerpt": "",
                                           "date": "2026-10-16T10:00:00Z"})
        tool = [sys.executable, str(REPO / "tools" / "pipeline.py"), "ingest", str(self.ws), "--json"]
        subprocess.run([sys.executable, str(REPO / "tools" / "classify.py"), "run", str(self.ws)], capture_output=True)
        self.assertEqual(json.loads(subprocess.run(tool, capture_output=True, text=True).stdout)["unmatched"], 1)
        d.append_jsonl(dd / "postings.jsonl", {"id": "greenhouse:neweco:1", "company": "Neweco", "title": "Staff Eng"})
        import jobqueue
        jobqueue.score(self.ws, "greenhouse:neweco:1", 60, "why", [])
        f = self.ws / "jobs" / "20-neweco-staff-eng"
        f.mkdir()
        (f / "application-log.md").write_text("# Application Log: Neweco, Staff Eng\n\n```ascend-state\nstatus: applied\n```\n")
        jobqueue.link(self.ws, "greenhouse:neweco:1", "20")
        out = json.loads(subprocess.run(tool, capture_output=True, text=True).stdout)
        self.assertEqual((out["unmatched"], out["applied"]), (0, 1))


if __name__ == "__main__":
    unittest.main()
