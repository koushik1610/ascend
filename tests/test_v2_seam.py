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
        post(self.ws, "greenhouse:doordashusa:8154315", "doordashusa", "Staff Security Engineer, Proactive Security - AI")
        jobqueue.score(self.ws, "greenhouse:doordashusa:8154315", 70, "why", [])
        post(self.ws, "greenhouse:doordashusa:999", "doordashusa", "Staff Security Engineer, Proactive Security - AI")
        jobqueue.score(self.ws, "greenhouse:doordashusa:999", 70, "why", [])
        jobqueue.sync_folders(self.ws)
        dd = {j["posting_id"]: j.get("nn") for j in queue(self.ws) if j.get("company", "").lower().startswith("doordash")}
        # The folder joins its own posting; a different requisition with the same title stays its own role.
        self.assertEqual(dd, {"greenhouse:doordashusa:8154315": "10", "greenhouse:doordashusa:999": None})


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


class Round2(unittest.TestCase):
    """Council rerun 2: regressions in late matching and the name matcher, and two misfiled kinds of mail."""

    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.ws = seed(self.td.name)

    def tearDown(self):
        self.td.cleanup()

    def ingest(self):
        r = subprocess.run([sys.executable, str(REPO / "tools" / "pipeline.py"), "ingest", str(self.ws), "--json"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)

    def classify(self):
        subprocess.run([sys.executable, str(REPO / "tools" / "classify.py"), "run", str(self.ws)], capture_output=True)

    def test_old_mail_never_moves_a_job_queued_later(self):
        # An acknowledgement for an application made outside Ascend must not land on a folder added later.
        import _v2data as d
        dd = self.ws / "data"
        d.append_jsonl(dd / "mail.jsonl", {"msg_id": "nv", "from": "nvidia@myworkday.com",
                                           "subject": "Thank you for your interest in NVIDIA", "date": "2026-09-24T21:11:02Z",
                                           "body_excerpt": "your application for the Principal Engineer, Security "
                                                           "Architecture role has been received"})
        self.classify()
        self.assertEqual(self.ingest()["unmatched"], 1)
        f = self.ws / "jobs" / "21-nvidia-senior-security"
        f.mkdir()
        (f / "application-log.md").write_text("# Application Log: NVIDIA, Senior Security Engineer\n")
        self.ingest()
        self.assertEqual(state(self.ws, "21-nvidia-senior-security").get("status", "queued"), "queued")

    def test_mail_matched_on_arrival_still_needs_a_sent_application_or_the_title(self):
        # Round 3: an acknowledgement for a role applied to elsewhere matched a scored, never-sent posting when it
        # was classified, then moved that job's new folder to applied and blocked its sheet.
        import _v2data as d
        import jobqueue
        dd = self.ws / "data"
        post(self.ws, "ashby:linear:1", "Linear", "Senior / Staff Security Engineer")
        jobqueue.score(self.ws, "ashby:linear:1", 50, "why", [])
        d.append_jsonl(dd / "mail.jsonl", {"msg_id": "ln", "from": "no-reply@ashbyhq.com",
                                           "subject": "Thank you for applying to Linear", "date": "2026-10-10T10:00:00Z",
                                           "body_excerpt": "Thank you for applying for the Product Designer role."})
        self.classify()
        jobqueue.set_state(self.ws, "ashby:linear:1", "approved", via_hub=True)
        f = self.ws / "jobs" / "16-linear-senior-staff-security-engineer"
        f.mkdir()
        (f / "application-log.md").write_text("# Application Log: Linear, Senior / Staff Security Engineer\n")
        jobqueue.link(self.ws, "ashby:linear:1", "16")
        self.ingest()
        self.assertEqual(state(self.ws, "16-linear-senior-staff-security-engineer").get("status", "queued"), "queued")

    def test_mail_naming_the_role_still_moves_a_job_not_yet_sent(self):
        import _v2data as d
        import jobqueue
        dd = self.ws / "data"
        post(self.ws, "ashby:linear:1", "Linear", "Senior / Staff Security Engineer")
        jobqueue.score(self.ws, "ashby:linear:1", 50, "why", [])
        f = self.ws / "jobs" / "16-linear-senior-staff-security-engineer"
        f.mkdir()
        (f / "application-log.md").write_text("# Application Log: Linear, Senior / Staff Security Engineer\n")
        jobqueue.link(self.ws, "ashby:linear:1", "16")
        d.append_jsonl(dd / "mail.jsonl", {"msg_id": "ln2", "from": "no-reply@ashbyhq.com",
                                           "subject": "Thank you for applying to Linear", "date": "2026-10-10T10:00:00Z",
                                           "body_excerpt": "Thank you for applying for the Senior / Staff Security Engineer role."})
        self.classify()
        self.ingest()
        self.assertEqual(state(self.ws, "16-linear-senior-staff-security-engineer").get("status"), "applied")

    def test_unmatched_mail_stops_retrying_after_thirty_days(self):
        import _v2data as d
        dd = self.ws / "data"
        d.append_jsonl(dd / "mail.jsonl", {"msg_id": "old", "from": "no-reply@ashbyhq.com",
                                           "subject": "Thanks for applying to Nobodyco", "date": "2026-01-01T00:00:00Z",
                                           "body_excerpt": "Thank you for applying."})
        self.classify()
        self.ingest()
        self.assertEqual(self.ingest()["unmatched"], 0)

    def test_a_suffix_never_turns_a_name_into_a_common_word(self):
        import classify
        jobs = [{"posting_id": "s", "company": "Scale AI", "title": "Staff Security Engineer"},
                {"posting_id": "d", "company": "doordashusa", "title": "Staff Security Engineer"}]
        self.assertIsNone(classify.match_job({"from": "x@news.example", "subject": "Security leadership at scale"}, jobs))
        self.assertEqual(classify.match_job({"from": "no-reply@ashbyhq.com",
                                             "subject": "Your application to DoorDash"}, jobs), "d")

    def test_a_hiring_address_scheduling_an_interview_is_an_interview(self):
        import classify
        msg = {"from": "paixc@jobs.netflix.com", "subject": "Next steps w/ Netflix",
               "body_excerpt": "Thanks again for taking the time to chat. After connecting with the team, we'd love to "
                               "schedule a 45-minute video conversation with the team's hiring manager. Please send "
                               "at least three options for days and times you're available. This opportunity"}
        self.assertEqual(classify.classify_message(msg)["category"], "interview-invite")

    def test_a_newsletter_is_never_an_assessment(self):
        import classify
        msg = {"from": "no-reply@substack.com", "subject": "Coding Challenge #140 - Bluetooth Proximity Finder",
               "body_excerpt": "From John Crickett and Substack"}
        self.assertEqual(classify.classify_message(msg)["category"], "other")

    def test_recruiter_mail_about_a_known_job_is_not_a_new_lead(self):
        import _v2data as d
        import alerts
        import jobqueue
        jobqueue.sync_folders(self.ws)
        dd = self.ws / "data"
        for mid, sender, subj in (("c1", "eric@growtherapy.com", "Your background and Grow Therapy"),
                                  ("m1", "donotreply@match.indeed.com", "Sr Security Architect @ MoneyGram"),
                                  ("m2", "donotreply@match.indeed.com", "Sr Security Architect @ MoneyGram")):
            d.append_jsonl(dd / "mail.jsonl", {"msg_id": mid, "from": sender, "subject": subj, "date": "2026-10-16T10:00:00Z",
                                               "body_excerpt": "I came across your profile. $235,000 - $305,000 a year."})
        self.classify()
        alerts.run(self.ws)
        inbound = [j for j in queue(self.ws) if j.get("source") == "recruiter"]
        self.assertEqual([(j["company"], j["title"]) for j in inbound], [("MoneyGram", "Sr Security Architect")])

    def test_inbound_reads_pay_remote_and_hybrid_from_what_is_written(self):
        import alerts
        filters = {"title_include": [r"\bsecurity\b"], "seniority": [r"\b(staff|principal|architect)\b"],
                   "remote_only": True, "locations": ["remote", "united states", "us"], "comp_floor": 200000}
        e = alerts.inbound_entry({"msg_id": "q", "from": "donotreply@match.indeed.com",
                                  "subject": "Staff Security Engineer [Remote-US] @ Quanata",
                                  "body_excerpt": "$235,000 - $305,000 a year. Hi"}, filters)
        self.assertEqual(e["state"], "needs-you", e["reasons"])
        self.assertFalse(any("comp unknown" in r or "location not stated" in r for r in e["reasons"]), e["reasons"])
        h = alerts.inbound_entry({"msg_id": "p", "from": "x@staffingco.example",
                                  "subject": "Hiring for Security Architect | Phoenix, AZ - Hybrid",
                                  "body_excerpt": "I am reaching out on an opportunity with one of our clients."}, filters)
        self.assertEqual(h["state"], "inbound-filtered", h["reasons"])

    def test_hub_counts_only_mail_still_waiting_for_a_job(self):
        import _v2data as d
        import hub
        dd = self.ws / "data"
        d.append_jsonl(dd / "mail.jsonl", {"msg_id": "g", "from": "recruiter@growtherapy.com",
                                           "subject": "Grow Therapy: Availability Request", "body_excerpt": "",
                                           "date": "2026-10-15T22:24:05Z"})
        self.classify()
        self.assertIsNotNone(hub.compute(self.ws)["health"]["mail"])
        self.ingest()                                   # matched to folder 00 on ingest's second look
        self.assertIsNone(hub.compute(self.ws)["health"]["mail"])


class Names(unittest.TestCase):
    def test_the_boards_current_name_wins_over_the_stored_slug(self):
        import _v2data as d
        import jobqueue
        with tempfile.TemporaryDirectory() as td:
            ws = seed(td)
            d.write_json_atomic(ws / "data" / "sources.json", {"boards": [{"ats": "greenhouse", "slug": "acmeusa",
                                                                            "company": "Acme"}], "filters": {}})
            post(ws, "greenhouse:acmeusa:9", "acmeusa", "Principal Security Engineer")
            self.assertEqual(jobqueue.candidates(ws)[0]["company"], "Acme")
            jobqueue.score(ws, "greenhouse:acmeusa:9", 60, "why", [])
            self.assertEqual(next(j for j in queue(ws) if j["posting_id"] == "greenhouse:acmeusa:9")["company"], "Acme")

    def test_show_gives_phase_5_the_whole_posting(self):
        import jobqueue
        with tempfile.TemporaryDirectory() as td:
            ws = seed(td)
            post(ws, "greenhouse:a:1", "Acme", "Staff Security Engineer")
            jobqueue.score(ws, "greenhouse:a:1", 60, "why", [])
            out = jobqueue.show(ws, "greenhouse:a:1")
            self.assertEqual((out["company"], out["title"], out["text"]), ("Acme", "Staff Security Engineer", "role text"))
            self.assertIn("next_nn", out)

    def test_two_postings_with_their_own_ids_are_two_roles(self):
        import jobqueue
        self.assertFalse(jobqueue._same_role("Elastic", "Principal Security Engineer (Java)", "Elastic",
                                             "Principal Security Engineer (Go)", "greenhouse:elastic:1",
                                             "greenhouse:elastic:2"))
        self.assertTrue(jobqueue._same_role("Elastic", "Principal Security Engineer", "Elastic",
                                            "Principal Security Engineer", "greenhouse:elastic:1", "v1:04"))


class SiblingRoles(unittest.TestCase):
    def test_link_and_sheet_refuse_a_sibling_requisition(self):
        import apply
        import jobqueue
        with tempfile.TemporaryDirectory() as td:
            ws = seed(td)
            post(ws, "greenhouse:elastic:2", "Elastic", "Principal Security Engineer (Go)")
            jobqueue.score(ws, "greenhouse:elastic:2", 60, "why", [])
            f = ws / "jobs" / "17-elastic-principal"
            f.mkdir()
            (f / "application-log.md").write_text("# Application Log: Elastic, Principal Security Engineer (Java)\n\n"
                                                  "| JD | https://boards.greenhouse.io/elastic/jobs/1 |\n")
            with self.assertRaises(ValueError):
                jobqueue.link(ws, "greenhouse:elastic:2", "17")


class ScoreFile(unittest.TestCase):
    def test_score_file_checks_every_row_before_writing_and_caps_text(self):
        import jobqueue
        with tempfile.TemporaryDirectory() as td:
            ws = seed(td)
            post(ws, "greenhouse:a:1", "Acme", "Staff Security Engineer")
            rows = Path(td) / "workspace" / "tester" / "data" / "scores.json"
            rows.write_text(json.dumps([{"posting_id": "greenhouse:a:1", "fit": 70, "why": "w" * 5000, "gaps": ["g"] * 30},
                                        {"posting_id": "nope", "fit": 50, "why": "x"}]))
            r = subprocess.run([sys.executable, str(REPO / "tools" / "jobqueue.py"), "score", str(ws), "--file", str(rows)],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 2)
            self.assertFalse([j for j in queue(ws) if j["posting_id"] == "greenhouse:a:1"])   # nothing half-written
            rows.write_text(json.dumps([{"posting_id": "greenhouse:a:1", "fit": 70, "why": "w" * 5000, "gaps": ["g"] * 30}]))
            subprocess.run([sys.executable, str(REPO / "tools" / "jobqueue.py"), "score", str(ws), "--file", str(rows)])
            e = next(j for j in queue(ws) if j["posting_id"] == "greenhouse:a:1")
            self.assertLessEqual(len(e["why"]), jobqueue.WHY_MAX)
            self.assertLessEqual(len(e["gaps"]), jobqueue.GAPS_MAX)
            for bad in ({"posting_id": "greenhouse:a:1", "fit": None}, {"posting_id": "greenhouse:a:1", "fit": 5, "gaps": "abc"}):
                rows.write_text(json.dumps([bad]))
                r = subprocess.run([sys.executable, str(REPO / "tools" / "jobqueue.py"), "score", str(ws), "--file", str(rows)],
                                   capture_output=True, text=True)
                self.assertEqual(r.returncode, 2, r.stderr)
            rows.write_text(json.dumps([{"posting_id": "greenhouse:a:1", "fit": 5, "why": "$(touch pwned)"}]))
            subprocess.run([sys.executable, str(REPO / "tools" / "jobqueue.py"), "score", str(ws), "--file", str(rows)],
                           cwd=td)
            self.assertFalse((Path(td) / "pwned").exists())
            self.assertEqual(next(j for j in queue(ws) if j["posting_id"] == "greenhouse:a:1")["why"], "$(touch pwned)")


class Privacy(unittest.TestCase):
    def test_data_is_readable_by_the_user_only(self):
        import _v2data as d
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td) / "workspace" / "tester"
            dd = d.data_dir(ws)
            d.append_jsonl(dd / "mail.jsonl", {"msg_id": "a"})
            self.assertEqual(dd.stat().st_mode & 0o777, 0o700)
            self.assertEqual((dd / "mail.jsonl").stat().st_mode & 0o777, 0o600)


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
