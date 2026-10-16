"""Ascend 2.0 tracker tests (stdlib unittest). Run: python3 -m unittest tests/test_v2_tracker.py -v

Fixtures under tests/fixtures/v2/ are synthetic. No real mail ever lives in this repo.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FIX = REPO / "tests/fixtures/v2"
sys.path.insert(0, str(REPO / "tools"))


class DataIO(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.ws = Path(self.td.name) / "ws"

    def tearDown(self):
        self.td.cleanup()

    def test_append_and_read_roundtrip(self):
        import _v2data as d
        p = d.data_dir(self.ws) / "events.jsonl"
        d.append_jsonl(p, {"a": 1})
        d.append_jsonl(p, {"a": 2})
        self.assertEqual([r["a"] for r in d.read_jsonl(p)], [1, 2])

    def test_read_missing_and_corrupt(self):
        import _v2data as d
        p = d.data_dir(self.ws) / "x.jsonl"
        self.assertEqual(d.read_jsonl(p), [])
        p.write_text('{"ok": 1}\n{broken\n\n{"ok": 2}\n', encoding="utf-8")
        self.assertEqual([r["ok"] for r in d.read_jsonl(p)], [1, 2])

    def test_atomic_json(self):
        import _v2data as d
        p = d.data_dir(self.ws) / "q.json"
        d.write_json_atomic(p, {"jobs": [1]})
        self.assertEqual(d.read_json(p, {}), {"jobs": [1]})
        self.assertEqual(d.read_json(p.with_name("none.json"), {"d": 1}), {"d": 1})
        self.assertFalse(list(p.parent.glob("*.tmp")))

    def test_refuses_outside_allowed_roots(self):
        import _v2data as d
        with self.assertRaises(Exception):
            d.append_jsonl(Path("/etc/ascend-should-not-write.jsonl"), {"x": 1})


class Classifier(unittest.TestCase):
    def mailbox(self):
        import _v2data as d
        return d.read_jsonl(FIX / "mailbox.jsonl")

    def test_fixture_covers_every_category_three_times(self):
        import classify
        counts = {}
        for m in self.mailbox():
            counts[m["_expect"]] = counts.get(m["_expect"], 0) + 1
        thin = {c: counts.get(c, 0) for c in classify.CATEGORIES if counts.get(c, 0) < 3}
        self.assertEqual(thin, {})

    def test_accuracy_at_least_95_percent(self):
        import classify
        msgs = self.mailbox()
        wrong = [(m["msg_id"], m["_expect"], classify.classify_message(m)["category"])
                 for m in msgs if classify.classify_message(m)["category"] != m["_expect"]]
        self.assertLessEqual(len(wrong) / len(msgs), 0.05, wrong)

    def test_conditional_interview_wording_is_acknowledgement(self):
        import classify
        m = {"from": "no-reply@ashbyhq.com", "subject": "Thanks for applying to Acme",
             "body_excerpt": "We received your application. If your background is a match, we will reach out "
                             "to schedule an interview.", "date": "2026-10-01T10:00:00Z"}
        self.assertEqual(classify.classify_message(m)["category"], "acknowledgement")

    def test_polite_rejection_is_rejection(self):
        import classify
        m = {"from": "acme@myworkday.com", "subject": "Your application to Acme",
             "body_excerpt": "Thank you for applying. Unfortunately we have decided to move forward with other "
                             "candidates.", "date": "2026-10-01T10:00:00Z"}
        self.assertEqual(classify.classify_message(m)["category"], "rejection")

    def test_unfortunately_in_a_reschedule_is_not_a_rejection(self):
        import classify
        m = {"from": "Christine <christine@acme-robotics.example>", "subject": "Rescheduling",
             "body_excerpt": "Unfortunately the slot we offered no longer works. Could you share your "
                             "availability for Thursday?", "date": "2026-10-01T00:00:00Z"}
        self.assertEqual(classify.classify_message(m)["category"], "interview-invite")

    def test_unfortunately_alone_still_reads_as_rejection(self):
        import classify
        m = {"from": "careers@contoso.example", "subject": "Your application",
             "body_excerpt": "Unfortunately, we won't be able to offer you a position.", "date": "2026-10-01T00:00:00Z"}
        self.assertEqual(classify.classify_message(m)["category"], "rejection")

    def test_unrelated_mail_never_goes_to_llm(self):
        import classify
        m = {"from": "receipts@coffee.example", "subject": "Your receipt", "body_excerpt": "Total $4.50",
             "date": "2026-10-01T10:00:00Z"}
        r = classify.classify_message(m)
        self.assertEqual((r["category"], r["needs_llm"]), ("other", False))

    def test_unclear_ats_mail_goes_to_llm(self):
        import classify
        m = {"from": "no-reply@ashbyhq.com", "subject": "Your candidate portal",
             "body_excerpt": "You can now log in to view your documents.", "date": "2026-10-01T10:00:00Z"}
        r = classify.classify_message(m)
        self.assertEqual((r["category"], r["needs_llm"]), ("other", True))

    def test_result_shape(self):
        import classify
        r = classify.classify_message(self.mailbox()[0])
        self.assertEqual(set(r), {"category", "confidence", "rule", "needs_llm"})
        self.assertIn(r["category"], classify.CATEGORIES)
        self.assertTrue(0 < r["confidence"] <= 1)


class Matching(unittest.TestCase):
    JOBS = [{"posting_id": "gh:acme:1", "company": "Acme Robotics, Inc.", "title": "Staff Security Engineer", "nn": "03"},
            {"posting_id": "wd:nvidia:9", "company": "NVIDIA", "title": "Principal Cloud Security Engineer"}]

    def msg(self, frm, subject="", body=""):
        return {"from": frm, "subject": subject, "body_excerpt": body, "date": "2026-10-01T00:00:00Z"}

    def test_workday_local_part_matches_company(self):
        import classify
        self.assertEqual(classify.match_job(self.msg("nvidia@myworkday.com", "Application update"), self.JOBS),
                         "wd:nvidia:9")

    def test_company_name_in_subject_prefers_nn(self):
        import classify
        m = self.msg("no-reply@ashbyhq.com", "Thanks for applying to Acme Robotics")
        self.assertEqual(classify.match_job(m, self.JOBS), "03")

    def test_company_domain_matches(self):
        import classify
        self.assertEqual(classify.match_job(self.msg("christine@acme-robotics.example", "Next steps"), self.JOBS), "03")

    def test_no_match(self):
        import classify
        self.assertIsNone(classify.match_job(self.msg("x@y.example", "Hello"), self.JOBS))

    def test_short_company_name_needs_word_boundary(self):
        import classify
        jobs = [{"posting_id": "gh:hp:1", "company": "HP", "title": "Security Engineer"}]
        self.assertIsNone(classify.match_job(self.msg("a@b.example", "Champion of the month"), jobs))
        self.assertEqual(classify.match_job(self.msg("hp@myworkday.com", "Your application"), jobs), "gh:hp:1")


class DueDates(unittest.TestCase):
    def msg(self, body):
        return {"subject": "", "body_excerpt": body, "date": "2026-10-01T09:00:00Z"}

    def test_within_days(self):
        import classify
        self.assertEqual(classify.due_date(self.msg("Please complete it within 5 days."), "assessment"), "2026-10-06")

    def test_within_hours_rounds_up_to_a_day(self):
        import classify
        self.assertEqual(classify.due_date(self.msg("Respond within 48 hours."), "info-request"), "2026-10-03")

    def test_by_month_day(self):
        import classify
        self.assertEqual(classify.due_date(self.msg("Please submit it by October 12."), "assessment"), "2026-10-12")

    def test_by_month_day_rolls_to_next_year(self):
        import classify
        m = {"subject": "", "body_excerpt": "Reply by January 5.", "date": "2026-12-20T09:00:00Z"}
        self.assertEqual(classify.due_date(m, "info-request"), "2027-01-05")

    def test_default_three_days_and_none_for_other_categories(self):
        import classify
        m = self.msg("Please answer a few questions.")
        self.assertEqual(classify.due_date(m, "info-request"), "2026-10-04")
        self.assertIsNone(classify.due_date(m, "rejection"))


class RunCommand(unittest.TestCase):
    TOOL = [sys.executable, str(REPO / "tools/classify.py")]

    def seed(self, ws):
        import _v2data as d
        dd = d.data_dir(ws)
        for m in d.read_jsonl(FIX / "mailbox.jsonl"):
            d.append_jsonl(dd / "mail.jsonl", {k: v for k, v in m.items() if k != "_expect"})
        d.write_json_atomic(dd / "queue.json", d.read_json(FIX / "queue.json", {}))
        return dd

    def test_run_is_incremental_and_complete(self):
        import _v2data as d
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td) / "ws"
            dd = self.seed(ws)
            r1 = subprocess.run(self.TOOL + ["run", str(ws), "--json"], capture_output=True, text=True)
            self.assertEqual(r1.returncode, 0, r1.stderr)
            out1 = json.loads(r1.stdout)
            events = d.read_jsonl(dd / "events.jsonl")
            self.assertEqual(out1["new"], len(events))
            self.assertEqual(len(events), len(d.read_jsonl(dd / "mail.jsonl")))
            r2 = subprocess.run(self.TOOL + ["run", str(ws), "--json"], capture_output=True, text=True)
            self.assertEqual(json.loads(r2.stdout)["new"], 0)
            self.assertEqual(len(d.read_jsonl(dd / "events.jsonl")), len(events))

    def test_events_carry_match_due_and_pending(self):
        import _v2data as d
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td) / "ws"
            dd = self.seed(ws)
            subprocess.run(self.TOOL + ["run", str(ws)], capture_output=True, text=True, check=True)
            ev = {e["msg_id"]: e for e in d.read_jsonl(dd / "events.jsonl")}
            self.assertEqual(ev["m03"]["match"], "wd:nvidia:3")
            self.assertEqual(ev["m13"]["match"], "01")
            self.assertEqual(ev["m10"]["due"], "2026-10-12")
            self.assertIsNone(ev["m30"]["match"])
            self.assertEqual({p["msg_id"] for p in d.read_jsonl(dd / "classify-pending.jsonl")}, {"m33"})

    def test_run_without_queue_still_classifies(self):
        import _v2data as d
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td) / "ws"
            dd = self.seed(ws)
            (dd / "queue.json").unlink()
            r = subprocess.run(self.TOOL + ["run", str(ws), "--json"], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            events = d.read_jsonl(dd / "events.jsonl")
            self.assertEqual(len(events), len(d.read_jsonl(dd / "mail.jsonl")))
            self.assertTrue(all(e["match"] is None for e in events))

    def test_one_command(self):
        r = subprocess.run(self.TOOL + ["one", "--from", "no-reply@greenhouse.io", "--subject", "Coding challenge",
                                        "--body", "Please complete the HackerRank assessment within 7 days.",
                                        "--date", "2026-10-01T00:00:00Z"], capture_output=True, text=True)
        out = json.loads(r.stdout)
        self.assertEqual((out["category"], out["due"]), ("assessment", "2026-10-08"))

    def test_usage_error_exits_2(self):
        self.assertEqual(subprocess.run(self.TOOL + ["nope"], capture_output=True).returncode, 2)

    def test_refuses_workspace_outside_allowed_roots(self):
        r = subprocess.run(self.TOOL + ["run", "/etc/ascend-ws"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main()
