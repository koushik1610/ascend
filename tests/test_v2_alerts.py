"""Ascend 2.0 M6: job-alert emails and recruiter inbound. Run: python3 -m unittest tests/test_v2_alerts.py -v"""

import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(REPO / "tests"))
from test_v2_pipeline import make_ws  # noqa: E402

FILTERS = {"title_include": [r"\bsecurity\b"], "seniority": [r"\b(staff|principal|architect|manager)\b"],
           "remote_only": True, "locations": ["remote", "united states", "us"], "comp_floor": 200000}

WELLFOUND = {"msg_id": "w1", "from": "team@hi.wellfound.com", "subject": "New jobs: Staff Security Engineer at Litware and 1 more",
             "date": "2026-10-12T19:00:00Z",
             "body_excerpt": "Hi Jordan! I've found 2 new jobs that might interest you! Ready to Interview Open to offers "
                             "Staff Security Engineer, Cloud Litware / 5000+ Employees $219–301k | Remote only, United States "
                             "Principal Security Architect Contoso / 51-200 Employees $150k – $180k | Remote only"}
LINKEDIN = {"msg_id": "l1", "from": "jobalerts-noreply@linkedin.com", "subject": "Staff Security Engineer: 2 new jobs",
            "date": "2026-10-12T07:00:00Z",
            "body_excerpt": "Your job alert for Staff Security Engineer\nStaff Security Engineer · Acme Robotics · Remote (United States)\n"
                            "Principal Cloud Security Engineer · Northwind · New York, NY"}
MONSTER = {"msg_id": "mo1", "from": "monster@notifications.monster.com",
           "subject": "Your job alert for: Cloud Security Architect, Remote", "date": "2026-10-16T13:00:00Z",
           "body_excerpt": "Celigo is hiring."}
INBOUND_GOOD = {"msg_id": "r1", "from": "Priya <priya@tailspin.example>", "subject": "Staff Cloud Security Engineer (remote) at Tailspin",
                "date": "2026-10-12T09:00:00Z",
                "body_excerpt": "I came across your profile. This role is fully remote in the US. Interested?"}
INBOUND_HYBRID = {"msg_id": "r2", "from": "nitin@staffingco.example", "subject": "Urgent need: Security Architect - Phoenix, AZ",
                  "date": "2026-10-15T20:00:00Z",
                  "body_excerpt": "Location: Hybrid 3 days in office in Phoenix. Contract Length: 6-12 months. Rate: $67/hr W2."}


class Parse(unittest.TestCase):
    def test_wellfound(self):
        import alerts
        leads = alerts.parse_alert(WELLFOUND)
        self.assertEqual([(l["title"], l["company"]) for l in leads],
                         [("Staff Security Engineer, Cloud", "Litware"), ("Principal Security Architect", "Contoso")])
        self.assertEqual((leads[0]["comp_min"], leads[0]["comp_max"], leads[1]["comp_max"]), (219000, 301000, 180000))
        self.assertIn("Remote", leads[0]["location"])

    def test_linkedin(self):
        import alerts
        leads = alerts.parse_alert(LINKEDIN)
        self.assertEqual([(l["title"], l["company"], l["location"]) for l in leads],
                         [("Staff Security Engineer", "Acme Robotics", "Remote (United States)"),
                          ("Principal Cloud Security Engineer", "Northwind", "New York, NY")])

    def test_board_that_names_no_job(self):
        import alerts
        self.assertEqual(alerts.parse_alert(MONSTER), [])


class Inbound(unittest.TestCase):
    def test_remote_recruiter_mail_needs_you(self):
        import alerts
        e = alerts.inbound_entry(INBOUND_GOOD, FILTERS)
        self.assertEqual((e["posting_id"], e["company"], e["state"], e["source"]),
                         ("inbound:r1", "Tailspin", "needs-you", "recruiter"))

    def test_hybrid_contract_is_filtered_with_reasons(self):
        import alerts
        e = alerts.inbound_entry(INBOUND_HYBRID, FILTERS)
        self.assertEqual(e["state"], "inbound-filtered")
        self.assertTrue(any("not remote" in r for r in e["reasons"]), e["reasons"])

    def test_location_stops_at_the_next_field(self):
        import alerts
        mail = dict(INBOUND_HYBRID, body_excerpt="Location: Hybrid 3 days in office in Phoenix - Need Local Only "
                                                 "Contract Length: 6-12 months Visa: USC Rate: $67/hr W2")
        reason = next(r for r in alerts.inbound_entry(mail, FILTERS)["reasons"] if "not remote" in r)
        self.assertNotIn("Contract", reason)
        self.assertNotIn("Visa", reason)


class Run(unittest.TestCase):
    def setUp(self):
        import _v2data as d
        self.td = tempfile.TemporaryDirectory()
        self.ws = make_ws(self.td.name, [])
        dd = self.ws / "data"
        d.write_json_atomic(dd / "sources.json", {"boards": [], "filters": FILTERS})
        d.write_json_atomic(dd / "queue.json", {"jobs": [{"posting_id": "inbound:r1", "company": "Tailspin",
                                                          "title": "kept as the user edited it", "state": "approved"}]})
        for m, cat in [(WELLFOUND, "job-alert"), (LINKEDIN, "job-alert"), (MONSTER, "job-alert"),
                       (INBOUND_GOOD, "recruiter-inbound"), (INBOUND_HYBRID, "recruiter-inbound")]:
            d.append_jsonl(dd / "mail.jsonl", m)
            d.append_jsonl(dd / "events.jsonl", {"msg_id": m["msg_id"], "category": cat, "date": m["date"]})

    def tearDown(self):
        self.td.cleanup()

    def test_run_is_incremental_and_never_overwrites(self):
        import _v2data as d
        import alerts
        out = alerts.run(self.ws)
        self.assertEqual(out, {"alert_leads": 4, "inbound": 1, "inbound_matching": 0})
        jobs = {j["posting_id"]: j for j in d.read_json(self.ws / "data" / "queue.json", {})["jobs"]}
        self.assertEqual(jobs["inbound:r1"]["title"], "kept as the user edited it")
        self.assertEqual(jobs["inbound:r2"]["state"], "inbound-filtered")
        posts = d.read_jsonl(self.ws / "data" / "postings.jsonl")
        self.assertEqual(sorted(p["id"] for p in posts), ["alert:l1:0", "alert:l1:1", "alert:w1:0", "alert:w1:1"])
        self.assertTrue(all(p["source"] == "alert" and p["url"] is None for p in posts))
        self.assertEqual(alerts.run(self.ws), {"alert_leads": 0, "inbound": 0, "inbound_matching": 0})

    def test_alert_leads_go_through_the_prefilter(self):
        import _v2data as d
        import alerts
        import prefilter
        alerts.run(self.ws)
        prefilter.run(self.ws)
        verdict = {c["posting_id"]: c["passed"] for c in d.read_jsonl(self.ws / "data" / "candidates.jsonl")}
        self.assertEqual(verdict, {"alert:w1:0": True, "alert:w1:1": False, "alert:l1:0": True, "alert:l1:1": False})


if __name__ == "__main__":
    unittest.main()
