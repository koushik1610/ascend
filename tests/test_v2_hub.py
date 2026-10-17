"""Ascend 2.0 M3: the hub dashboard. Run: python3 -m unittest tests/test_v2_hub.py -v"""

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

TODAY = "2026-10-16"


def ledger(ws, rows):
    p = ws / "data" / "status-log.tsv"
    lines = ["# slug\tdate\tfrom\tto\tsource\tnote"] + ["\t".join(r) for r in rows]
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def seed(root):
    import _v2data as d
    ws = make_ws(root, [
        ("01-acme-staff", "Acme Robotics", "Staff Security Engineer", "applied"),
        ("02-northwind-principal", "Northwind", "Principal Cloud Security Engineer", "screen"),
        ("03-litware-staff", "Litware", "Staff Detection Engineer", None),
    ])
    dd = ws / "data"
    for i in range(5):
        d.append_jsonl(dd / "postings.jsonl", {"id": f"p{i}", "company": "X", "title": "Y"})
    for i in range(5):
        d.append_jsonl(dd / "candidates.jsonl", {"posting_id": f"p{i}", "passed": i < 3})
    d.write_json_atomic(dd / "queue.json", {"jobs": [
        {"posting_id": "a1", "company": "Acme Robotics", "title": "Staff Security Engineer", "nn": "01", "fit": 84},
        {"posting_id": "n2", "company": "Northwind", "title": "Principal Cloud Security Engineer", "nn": "02", "fit": 79},
        {"posting_id": "l3", "company": "Litware", "title": "Staff Detection Engineer", "nn": "03", "fit": 71}]})
    ledger(ws, [("01-acme-staff", "2026-10-10", "queued", "applied", "gmail", "-"),
                ("02-northwind-principal", "2026-09-01", "queued", "applied", "log", "-"),
                ("02-northwind-principal", "2026-09-20", "applied", "screen", "gmail", "-")])
    for e in [
        {"msg_id": "e1", "category": "acknowledgement", "match": "01", "date": "2026-10-10T09:00:00Z",
         "subject": "Thanks for applying", "from": "no-reply@ashbyhq.com"},
        {"msg_id": "e2", "category": "info-request", "match": "01", "date": "2026-10-12T09:00:00Z", "due": "2026-10-18",
         "subject": "Please answer a few questions", "from": "acme@myworkday.com"},
        {"msg_id": "e3", "category": "interview-invite", "match": "02", "date": "2026-09-20T09:00:00Z",
         "subject": "Interview invitation", "from": "recruiter@northwind.example"},
        {"msg_id": "e4", "category": "other", "match": None, "date": "2026-10-15T09:00:00Z",
         "subject": "Weekly digest", "from": "news@digest.example"},
    ]:
        d.append_jsonl(dd / "events.jsonl", e)
    return ws


class Compute(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.td.cleanup()

    def test_empty_workspace(self):
        import hub
        ws = make_ws(self.td.name, [])
        out = hub.compute(ws, today=TODAY)
        self.assertTrue(all(s["count"] == 0 for s in out["funnel"]))
        self.assertEqual((out["inbox"], out["pinned"], out["tokens"]), ([], [], None))

    def test_gmail_status_tells_the_user_when_tracking_stopped(self):
        import _v2data as d
        import hub
        ws = make_ws(self.td.name, [])
        d.write_json_atomic(ws / ".ascend-state.json", {"run_defaults": {"engine": "A", "mode": "assisted"}})
        d.write_json_atomic(ws / "data" / "sync-state.json", {"connected": False})
        self.assertIn("gmail_sync.py connect", hub.compute(ws, today=TODAY)["gmail"]["warning"])
        d.write_json_atomic(ws / "data" / "sync-state.json", {"connected": True, "last_sync": "2026-10-13T06:30:00+00:00"})
        self.assertIn("2026-10-13", hub.compute(ws, today=TODAY)["gmail"]["warning"])
        d.write_json_atomic(ws / "data" / "sync-state.json", {"connected": True, "last_sync": "2026-10-16T06:30:00+00:00"})
        self.assertIsNone(hub.compute(ws, today=TODAY)["gmail"]["warning"])
        self.assertIn('id="gmailStatus"', hub.render(ws, today=TODAY))

    def test_funnel(self):
        import hub
        out = hub.compute(seed(self.td.name), today=TODAY)
        self.assertEqual([(s["stage"], s["count"]) for s in out["funnel"]],
                         [("found", 5), ("screened", 3), ("matched", 3), ("applied", 2), ("replied", 2),
                          ("interviewing", 1), ("offer", 0)])

    def test_week(self):
        import hub
        out = hub.compute(seed(self.td.name), today=TODAY)
        self.assertEqual(out["week"], {"applied": 1, "replies": 1, "interviews": 0})

    def test_rates_withheld_below_ten_applications(self):
        import hub
        out = hub.compute(seed(self.td.name), today=TODAY)
        self.assertEqual(out["rates"], {"reply": None, "ghost": None})
        self.assertIsNone(out["warning"])

    def test_rates_ghosting_and_warning_at_ten_or_more(self):
        import hub
        ws = make_ws(self.td.name, [(f"{i:02d}-co{i}", f"Co{i}", "Engineer", "applied") for i in range(12)])
        ledger(ws, [(f"{i:02d}-co{i}", "2026-08-01", "queued", "applied", "log", "-") for i in range(12)])
        out = hub.compute(ws, today=TODAY)
        self.assertEqual(out["rates"], {"reply": 0.0, "ghost": 1.0})
        self.assertIn("reply rate", out["warning"])

    def test_inbox_newest_first_with_job_names(self):
        import hub
        out = hub.compute(seed(self.td.name), today=TODAY)
        self.assertEqual([i["msg_id"] for i in out["inbox"]], ["e4", "e2", "e1", "e3"])
        self.assertEqual(out["inbox"][1]["job"], "01 Acme Robotics")
        self.assertIsNone(out["inbox"][0]["job"])
        self.assertTrue(out["inbox"][1]["gmail_url"].endswith("e2"))

    def test_pinned_info_request_until_job_moves_on(self):
        import hub
        ws = seed(self.td.name)
        out = hub.compute(ws, today=TODAY)
        self.assertEqual([(p["msg_id"], p["due"]) for p in out["pinned"]], [("e2", "2026-10-18")])
        log = ws / "jobs/01-acme-staff/application-log.md"
        log.write_text(log.read_text().replace("status: applied", "status: screen"))
        self.assertEqual(hub.compute(ws, today=TODAY)["pinned"], [])

    def test_week_counts_jobs_not_emails(self):
        import _v2data as d
        import hub
        ws = seed(self.td.name)
        for i, day in enumerate(["2026-10-14", "2026-10-15"]):
            d.append_jsonl(ws / "data" / "events.jsonl",
                           {"msg_id": f"g{i}", "category": "interview-invite", "match": "03",
                            "date": f"{day}T09:00:00Z", "subject": "Interview", "from": "x@litware.example"})
        self.assertEqual(hub.compute(ws, today=TODAY)["week"]["interviews"], 1)

    def test_inbox_takes_subject_and_sender_from_mail(self):
        import _v2data as d
        import hub
        ws = make_ws(self.td.name, [])
        d.append_jsonl(ws / "data" / "mail.jsonl", {"msg_id": "z1", "from": "talent@co.example",
                                                     "subject": "Interview invitation", "date": "2026-10-15T09:00:00Z"})
        d.append_jsonl(ws / "data" / "events.jsonl", {"msg_id": "z1", "category": "interview-invite", "match": None,
                                                       "date": "2026-10-15T09:00:00Z"})
        row = hub.compute(ws, today=TODAY)["inbox"][0]
        self.assertEqual((row["subject"], row["from"]), ("Interview invitation", "talent@co.example"))

    def test_screened_uses_latest_verdict_per_posting(self):
        import _v2data as d
        import hub
        ws = make_ws(self.td.name, [])
        for row in [{"posting_id": "p1", "passed": True, "filters_hash": "old"},
                    {"posting_id": "p1", "passed": False, "filters_hash": "new"},
                    {"posting_id": "p2", "passed": True, "filters_hash": "new"}]:
            d.append_jsonl(ws / "data" / "candidates.jsonl", row)
        funnel = dict((s["stage"], s["count"]) for s in hub.compute(ws, today=TODAY)["funnel"])
        self.assertEqual(funnel["screened"], 1)

    def test_queue_puts_open_decisions_first_by_fit(self):
        import _v2data as d
        import hub
        ws = seed(self.td.name)
        q = d.read_json(ws / "data" / "queue.json", {})
        q["jobs"] += [{"posting_id": "x9", "company": "Zeta", "title": "Staff", "fit": 90, "state": "matched"},
                      {"posting_id": "x8", "company": "Eta", "title": "Staff", "fit": 60, "state": "needs-you"}]
        d.write_json_atomic(ws / "data" / "queue.json", q)
        rows = hub.compute(ws, today=TODAY)["queue"]
        self.assertEqual([r["company"] for r in rows[:3]], ["Zeta", "Litware", "Eta"])

    def test_queue_decision_shows_over_an_untouched_folder(self):
        import _v2data as d
        import hub
        ws = seed(self.td.name)
        q = d.read_json(ws / "data" / "queue.json", {})
        q["jobs"][2]["state"] = "approved"          # job 03's folder still says queued
        d.write_json_atomic(ws / "data" / "queue.json", q)
        rows = {r["nn"]: r["status"] for r in hub.compute(ws, today=TODAY)["queue"]}
        self.assertEqual((rows["03"], rows["01"]), ("approved", "applied"))

    def test_queue_rows(self):
        import hub
        q = hub.compute(seed(self.td.name), today=TODAY)["queue"]
        self.assertEqual([(r["nn"], r["status"], r["fit"]) for r in q],
                         [("03", "queued", 71), ("01", "applied", 84), ("02", "screen", 79)])

    def test_tokens_by_stage(self):
        import _v2data as d
        import hub
        ws = seed(self.td.name)
        for row in [{"stage": "score", "input_tokens": 1000, "output_tokens": 200},
                    {"stage": "score", "input_tokens": 500, "output_tokens": 100},
                    {"stage": "tailor", "input_tokens": 3000, "output_tokens": 900}]:
            d.append_jsonl(ws / "data" / "usage.jsonl", row)
        t = hub.compute(ws, today=TODAY)["tokens"]
        self.assertEqual((t["by_stage"], t["total"]), ({"score": 1800, "tailor": 3900}, 5700))


class Build(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.ws = seed(self.td.name)

    def tearDown(self):
        self.td.cleanup()

    def test_writes_page_with_embedded_data(self):
        import hub
        out = hub.build(self.ws, today=TODAY)
        html = out.read_text()
        self.assertEqual(out, (self.ws / "hub.html").resolve())
        m = __import__("re").search(r'<script type="application/json" id="hub-data">(.*?)</script>', html, 16)
        self.assertEqual(json.loads(m.group(1))["funnel"][0], {"stage": "found", "count": 5})
        self.assertNotIn("__hub_data__", html)

    def test_hostile_subject_cannot_close_the_script(self):
        import _v2data as d
        import hub
        d.append_jsonl(self.ws / "data" / "events.jsonl",
                       {"msg_id": "x1", "category": "other", "match": None, "date": "2026-10-16T09:00:00Z",
                        "subject": "</script><img src=x onerror=alert(1)>", "from": "a@b.example"})
        html = hub.build(self.ws, today=TODAY).read_text()
        self.assertEqual(html.lower().count("</script"), html.lower().count("<script"))
        self.assertNotIn("<img src=x", html)

    def test_page_cannot_call_out(self):
        import hub
        html = hub.build(self.ws, today=TODAY).read_text()
        self.assertIn("connect-src 'none'", html)
        self.assertNotIn("connect-src 'self'", html)
        m = __import__("re").search(r'<script type="application/json" id="hub-data">(.*?)</script>', html, 16)
        self.assertNotIn("server", json.loads(m.group(1)))     # no token, so no write channel

    def test_cli(self):
        r = subprocess.run([sys.executable, str(REPO / "tools/hub.py"), "build", str(self.ws), "--today", TODAY],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((self.ws / "hub.html").is_file())
        r = subprocess.run([sys.executable, str(REPO / "tools/hub.py"), "build", str(self.ws), "--json",
                            "--today", TODAY], capture_output=True, text=True)
        self.assertEqual(json.loads(r.stdout)["week"]["applied"], 1)

    def test_template_declares_no_browser_global_names(self):
        # `const top = ...` at script top level throws "Identifier 'top' has already been declared"
        # in a browser (window.top), which silently blanks the whole page. Caught on the real hub.
        import re
        html = (REPO / "templates/hub.template.html").read_text()
        script = html.split('<script>', 1)[1]
        clash = {"top", "name", "length", "status", "parent", "self", "location", "history", "event",
                 "origin", "frames", "opener", "closed", "screen", "navigator", "document", "window"}
        declared = set(re.findall(r"^(?:const|let|var|function)\s+([A-Za-z_$][\w$]*)", script, re.M))
        self.assertEqual(declared & clash, set())

    def test_refuses_outside_allowed_roots(self):
        r = subprocess.run([sys.executable, str(REPO / "tools/hub.py"), "build", "/etc/ascend-ws"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main()
