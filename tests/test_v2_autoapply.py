"""Ascend 2.0 automatic apply: auto.json, the gates, and the runner with a stub form filler.

Run: python3 -m unittest tests/test_v2_autoapply.py -v
The real form filler (Playwright) is tested in tests/test_v2_autoapply_forms.py.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(REPO / "tests"))
from test_v2_apply import PROFILE, job_ws  # noqa: E402

TODAY = date.today().isoformat()
BOARD = {"company": "Acme Robotics", "ats": "greenhouse", "slug": "acme"}
ANSWERS = {"work_authorization": "Yes", "sponsorship": "No", "salary_expectation": "240000",
           "start_date": "Two weeks after an offer"}


class KeyEnv(unittest.TestCase):
    """Every test signs with a key in its own temp folder, never the user's real one."""

    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self._key = os.environ.get("ASCEND_AUTO_KEY")
        os.environ["ASCEND_AUTO_KEY"] = str(Path(self.td.name) / "auto.key")

    def tearDown(self):
        if self._key is None:
            os.environ.pop("ASCEND_AUTO_KEY", None)
        else:
            os.environ["ASCEND_AUTO_KEY"] = self._key
        self.td.cleanup()

    def ws(self, state="matched", fit=82, passed=True, board=BOARD, answers=ANSWERS, pid="greenhouse:acme:1"):
        import _v2data as d
        ws = job_ws(self.td.name)
        d.write_json_atomic(ws / "data" / "profile.json", PROFILE)
        if answers is not None:
            d.write_json_atomic(ws / "data" / "apply-answers.json", answers)
        d.write_json_atomic(ws / "data" / "sources.json", {"boards": [board] if board else [], "filters": {}})
        d.write_json_atomic(ws / "data" / "queue.json", {"jobs": [{
            "posting_id": pid, "company": "Acme Robotics", "title": "Staff Security Engineer",
            "nn": "05", "fit": fit, "state": state, "apply_url": "https://evil.example/acme"}]})
        d.append_jsonl(ws / "data" / "postings.jsonl", {"id": pid, "company": "Acme Robotics",
                                                        "title": "Staff Security Engineer"})
        d.append_jsonl(ws / "data" / "candidates.jsonl", {"posting_id": pid, "passed": passed})
        return ws

    def enable(self, ws, supervised_ok=True, **settings):
        import autoapply
        autoapply.enable(ws, "apply for me")
        if supervised_ok:          # most tests run past the first supervised send
            autoapply._change(ws, lambda cfg: cfg.update(first_send_ok=True))
        if settings:
            autoapply.settings(ws, **settings)

    def entry(self, ws, pid="greenhouse:acme:1"):
        import _v2data as d
        return next(j for j in d.read_json(ws / "data" / "queue.json", {})["jobs"] if j["posting_id"] == pid)

    def log(self, ws):
        import _v2data as d
        return d.read_jsonl(ws / "data" / "apply-log.jsonl")


class Config(KeyEnv):
    def test_missing_config_is_off(self):
        import autoapply
        cfg = autoapply.load_config(self.ws())
        self.assertFalse(cfg["enabled"])

    def test_enable_needs_the_typed_phrase(self):
        import autoapply
        ws = self.ws()
        for phrase in ("", "yes", "Apply for me please", None):
            with self.assertRaises(ValueError):
                autoapply.enable(ws, phrase)
        self.assertFalse(autoapply.load_config(ws)["enabled"])
        autoapply.enable(ws, "  Apply for me ")
        self.assertTrue(autoapply.load_config(ws)["enabled"])

    def test_hand_edited_config_reads_as_off(self):
        import autoapply
        ws = self.ws()
        autoapply.enable(ws, "apply for me")
        autoapply.pause(ws, "testing")
        raw = json.loads((ws / "data" / "auto.json").read_text())
        raw["config"]["paused"] = False
        (ws / "data" / "auto.json").write_text(json.dumps(raw))
        cfg = autoapply.load_config(ws)
        self.assertFalse(cfg["enabled"])
        self.assertTrue(cfg["tampered"])

    def test_config_from_another_workspace_does_not_carry_over(self):
        import autoapply
        a = self.ws()
        autoapply.enable(a, "apply for me")
        b = Path(self.td.name) / "workspace" / "other" / "data"
        b.mkdir(parents=True)
        (b / "auto.json").write_text((a / "data" / "auto.json").read_text())
        self.assertFalse(autoapply.load_config(b.parent)["enabled"])

    def test_first_week_cap_is_five(self):
        import autoapply
        ws = self.ws()
        autoapply.enable(ws, "apply for me")
        cfg = autoapply.load_config(ws)
        self.assertEqual(autoapply.cap_today(cfg, date.today()), 5)
        self.assertEqual(autoapply.cap_today(cfg, date.today() + timedelta(days=8)), 25)

    def test_settings_are_bounded(self):
        import autoapply
        ws = self.ws()
        with self.assertRaises(ValueError):
            autoapply.settings(ws, daily_cap=500)
        with self.assertRaises(ValueError):
            autoapply.settings(ws, fit_threshold=10)
        autoapply.settings(ws, daily_cap=10, fit_threshold=80)
        cfg = autoapply.load_config(ws)
        self.assertEqual((cfg["daily_cap"], cfg["fit_threshold"], cfg["enabled"]), (10, 80, False))

    def test_command_line_cannot_turn_it_on_or_resume(self):
        ws = self.ws()
        env = dict(os.environ)
        for cmd in ("enable", "resume", "settings"):
            r = subprocess.run([sys.executable, str(REPO / "tools/autoapply.py"), cmd, str(ws)],
                               capture_output=True, text=True, env=env)
            self.assertEqual(r.returncode, 2, cmd)
            self.assertIn("hub", r.stderr)

    def test_command_line_can_pause(self):
        import autoapply
        ws = self.ws()
        autoapply.enable(ws, "apply for me")
        r = subprocess.run([sys.executable, str(REPO / "tools/autoapply.py"), "pause", str(ws), "--reason", "away"],
                           capture_output=True, text=True, env=dict(os.environ))
        self.assertEqual(r.returncode, 0, r.stderr)
        cfg = autoapply.load_config(ws)
        self.assertEqual((cfg["paused"], cfg["paused_reason"]), (True, "away"))


class Gates(KeyEnv):
    def test_apply_url_is_rebuilt_from_the_board(self):
        import apply
        ws = self.ws(board=None)
        import _v2data as d
        d.write_json_atomic(ws / "data" / "sources.json", {"boards": [
            BOARD, {"ats": "ashby", "slug": "north"}, {"ats": "lever", "slug": "lev"}, {"ats": "workday", "slug": "z",
                                                                                  "pod": "wd5", "site": "S"}]})
        self.assertEqual(apply.apply_url_for(ws, "greenhouse:acme:1"),
                         "https://job-boards.greenhouse.io/embed/job_app?for=acme&token=1")
        self.assertEqual(apply.apply_url_for(ws, "ashby:north:3f2a1b4c-0000-4000-8000-000000000001"),
                         "https://jobs.ashbyhq.com/north/3f2a1b4c-0000-4000-8000-000000000001/application")
        self.assertEqual(apply.apply_url_for(ws, "lever:lev:3f2a1b4c-0000-4000-8000-000000000001"),
                         "https://jobs.lever.co/lev/3f2a1b4c-0000-4000-8000-000000000001/apply")
        for pid in ("workday:z:P1", "greenhouse:other:1", "web:abc", "greenhouse:acme:1/../x", "lever:lev:x?y=1"):
            self.assertIsNone(apply.apply_url_for(ws, pid), pid)

    def test_allowed_hosts_are_exact(self):
        import apply
        ok = ["https://job-boards.greenhouse.io/acme/jobs/1", "https://boards.greenhouse.io/acme/jobs/1",
              "https://jobs.ashbyhq.com/n/1/application", "https://jobs.lever.co/l/1/apply"]
        bad = ["http://job-boards.greenhouse.io/acme/jobs/1", "https://job-boards.greenhouse.io.evil.com/a",
               "https://evil.com/job-boards.greenhouse.io/", "https://user@job-boards.greenhouse.io/a",
               "https://job-boards.greenhouse.io:8443/a", "https://job-boards.greenhouse.io\\@evil.com/",
               "https://xn--jobs-lever-co.evil/a", "https://jobs.lever.co%2f@evil.com/", "https://greenhouse.io/a",
               "https://evil.greenhouse.io/a", "https://jobs.lever.co /a", "javascript:alert(1)", ""]
        for u in ok:
            self.assertTrue(apply.allowed(u), u)
        for u in bad:
            self.assertFalse(apply.allowed(u), u)

    def test_a_ready_job(self):
        import apply
        import autoapply
        ws = self.ws()
        self.assertEqual(apply.ready(ws, self.entry(ws), autoapply.load_config(ws)), [])

    def test_each_gate_says_why(self):
        import apply
        import autoapply
        cases = [(dict(fit=60), "fit 60 is below 75"), (dict(fit=None), "not scored"),
                 (dict(state="rejected"), "rejected"), (dict(passed=False), "rule filter"),
                 (dict(board=None), "not on a board in your sources"),
                 (dict(board={"ats": "workday", "slug": "acme", "pod": "wd5", "site": "S"}, pid="workday:acme:P1"),
                  "only Greenhouse, Ashby and Lever")]
        for kw, why in cases:
            with self.subTest(why=why):
                self.td.cleanup()
                self.td = tempfile.TemporaryDirectory()
                os.environ["ASCEND_AUTO_KEY"] = str(Path(self.td.name) / "auto.key")
                ws = self.ws(**kw)
                reasons = apply.ready(ws, self.entry(ws, kw.get("pid", "greenhouse:acme:1")), autoapply.load_config(ws))
                self.assertTrue(any(why in r for r in reasons), reasons)

    def test_a_folder_from_an_earlier_run_needs_the_users_approval(self):
        # Run 4 (2026-10-22): the user's v1 folders sit in the queue as matched with fits up to 86 and tailored
        # résumés. Turning automatic apply on must not send the jobs they chose not to send.
        import _v2data as d
        import apply
        import autoapply
        ws = self.ws()
        d.update_json(ws / "data" / "queue.json", {}, lambda q: q["jobs"][0].update(source="v1"))
        reasons = apply.ready(ws, self.entry(ws), autoapply.load_config(ws))
        self.assertTrue(any("earlier run" in r for r in reasons), reasons)
        d.update_json(ws / "data" / "queue.json", {}, lambda q: q["jobs"][0].update(state="approved"))
        self.assertEqual(apply.ready(ws, self.entry(ws), autoapply.load_config(ws)), [])

    def test_company_cap(self):
        import _v2data as d
        import apply
        import autoapply
        ws = self.ws()
        for i in range(2):
            d.append_jsonl(ws / "data" / "apply-log.jsonl", {"posting_id": f"greenhouse:acme:{90 + i}", "result": "submitted",
                                                             "company": "Acme Robotics", "at": f"{TODAY}T09:00:00"})
        reasons = apply.ready(ws, self.entry(ws), autoapply.load_config(ws))
        self.assertTrue(any("2 applications to Acme Robotics" in r for r in reasons), reasons)

    def test_answers_merge_profile_and_the_users_own_answers(self):
        import apply
        ws = self.ws()
        a = apply.answers(ws)
        self.assertEqual((a["email"], a["sponsorship"], a["salary_expectation"]), ("jordan@example.com", "No", "240000"))
        (ws / "data" / "apply-answers.json").unlink()
        self.assertEqual(apply.answers(ws).get("sponsorship"), None)


def stub(result="submitted", reason=None, unfilled=()):
    calls = []

    def fill(url, answers, resume, submit, shots):
        calls.append({"url": url, "submit": submit, "resume": resume, "answers": answers})
        return {"result": result if submit or result != "submitted" else "filled", "reason": reason,
                "unfilled": list(unfilled), "shots": []}
    fill.calls = calls
    return fill


class Placeholders(KeyEnv):
    def test_template_placeholders_are_never_sent(self):
        import _v2data as d
        import apply
        ws = self.ws(answers={"salary_expectation": "your number", "current_company": "Your current employer",
                              "sponsorship": "No"})
        d.write_json_atomic(ws / "data" / "answer-bank.json", [
            {"question": "Why are you interested in this role", "answer": "Your own two or three sentences."},
            {"question": "Have you ever worked here", "answer": "No"}])
        a = apply.answers(ws)
        self.assertNotIn("salary_expectation", a)
        self.assertNotIn("current_company", a)
        self.assertEqual(a["sponsorship"], "No")
        self.assertEqual([b["question"] for b in a["_bank"]], ["Have you ever worked here"])

    def test_shipped_templates_are_all_placeholders_or_safe_defaults(self):
        import json as j
        bank = j.loads((REPO / "templates/answer-bank.example.json").read_text())
        own = [b for b in bank if b.get("question") and not str(b.get("answer")).lower().startswith(("yes", "no"))]
        self.assertTrue(all(str(b["answer"]).lower().startswith("your ") for b in own), own)


class Runner(KeyEnv):
    def test_off_does_nothing(self):
        import autoapply
        ws = self.ws()
        f = stub()
        out = autoapply.run(ws, filler=f)
        self.assertEqual(f.calls, [])
        self.assertIn("off", out["skipped"])

    def test_submitted_is_applied_and_logged(self):
        import autoapply
        ws = self.ws()
        self.enable(ws)
        f = stub()
        out = autoapply.run(ws, filler=f)
        self.assertEqual(out["submitted"], 1)
        self.assertEqual(f.calls[0]["url"], "https://job-boards.greenhouse.io/embed/job_app?for=acme&token=1")   # not the stored link
        self.assertTrue(f.calls[0]["submit"])
        self.assertTrue(f.calls[0]["resume"].endswith(".pdf"))
        e = self.entry(ws)
        self.assertEqual((e["state"], e.get("approved_by")), ("applied", "auto"))
        row = self.log(ws)[-1]
        self.assertEqual((row["result"], row["mode"], row["company"]), ("submitted", "auto", "Acme Robotics"))

    def test_unclear_goes_to_needs_you_never_applied(self):
        import autoapply
        ws = self.ws()
        self.enable(ws)
        autoapply.run(ws, filler=stub("unclear", "no confirmation within 30 seconds"))
        e = self.entry(ws)
        self.assertEqual(e["state"], "applied?")
        self.assertIn("no confirmation", e["stop_reason"])
        self.assertIn("check", e["stop_reason"])

    def test_stopped_goes_to_needs_you_with_reason(self):
        import autoapply
        ws = self.ws()
        self.enable(ws)
        autoapply.run(ws, filler=stub("stopped", "CAPTCHA"))
        e = self.entry(ws)
        self.assertEqual((e["state"], e["stop_reason"]), ("needs-you", "CAPTCHA"))

    def test_dry_run_never_submits_and_changes_nothing(self):
        import autoapply
        ws = self.ws()
        f = stub()
        out = autoapply.run(ws, dry_run=True, filler=f)       # works while auto-apply is off
        self.assertFalse(f.calls[0]["submit"])
        self.assertEqual(self.entry(ws)["state"], "matched")
        self.assertEqual(out["filled"], 1)
        self.assertEqual(self.log(ws)[-1]["result"], "filled")
        self.assertTrue(self.log(ws)[-1]["dry_run"])

    def test_paused_does_nothing(self):
        import autoapply
        ws = self.ws()
        self.enable(ws)
        autoapply.pause(ws, "away")
        f = stub()
        self.assertIn("paused", autoapply.run(ws, filler=f)["skipped"])
        self.assertEqual(f.calls, [])

    def test_daily_cap(self):
        import _v2data as d
        import autoapply
        ws = self.ws()
        self.enable(ws)
        for i in range(5):
            d.append_jsonl(ws / "data" / "apply-log.jsonl", {"posting_id": f"greenhouse:zz:{i}", "result": "submitted",
                                                             "mode": "auto", "company": "Zed", "at": f"{TODAY}T08:00:00"})
        f = stub()
        out = autoapply.run(ws, filler=f)
        self.assertEqual(f.calls, [])
        self.assertIn("cap", out["skipped"])

    def test_lint_failure_is_a_stop_and_missing_pack_waits(self):
        import autoapply
        ws = self.ws()
        self.enable(ws)
        (ws / "jobs/05-acme-staff/resume.md").write_text("# Jordan\n\n- Own the 9,999 baseline.\n")
        f = stub()
        autoapply.run(ws, filler=f)
        self.assertEqual(f.calls, [])
        e = self.entry(ws)
        self.assertEqual(e["state"], "needs-you")
        self.assertIn("lint", e["stop_reason"])

        self.td.cleanup()
        self.td = tempfile.TemporaryDirectory()
        os.environ["ASCEND_AUTO_KEY"] = str(Path(self.td.name) / "auto.key")
        ws = self.ws()
        self.enable(ws)
        for pdf in (ws / "jobs/05-acme-staff").glob("*.pdf"):
            pdf.unlink()
        out = autoapply.run(ws, filler=stub())
        self.assertEqual(self.entry(ws)["state"], "matched")      # waits for its résumé, no stop
        self.assertIn("waiting for a tailored résumé", " ".join(out["waiting"]))

    def test_interrupted_attempt_is_handed_to_the_user(self):
        import _v2data as d
        import autoapply
        ws = self.ws()
        self.enable(ws)
        old = (datetime.now() - timedelta(hours=2)).isoformat(timespec="seconds")
        d.update_json(ws / "data" / "queue.json", {}, lambda q: q["jobs"][0].update(state="applying", attempt_at=old))
        f = stub()
        autoapply.run(ws, filler=f)
        e = self.entry(ws)
        self.assertEqual(e["state"], "applied?")
        self.assertIn("interrupted", e["stop_reason"])
        self.assertEqual(f.calls, [])             # never retried on its own

    def test_three_unclear_in_a_day_pauses(self):
        import _v2data as d
        import autoapply
        ws = self.ws()
        self.enable(ws)
        for i in range(3):
            d.append_jsonl(ws / "data" / "apply-log.jsonl", {"posting_id": f"greenhouse:zz:{i}", "result": "unclear",
                                                             "mode": "auto", "company": "Zed", "at": f"{TODAY}T08:00:00"})
        out = autoapply.run(ws, filler=stub())
        self.assertIn("paused", out["skipped"])
        self.assertIn("unclear", autoapply.load_config(ws)["paused_reason"])

    def test_low_reply_rate_pauses_after_fifty(self):
        import _v2data as d
        import autoapply
        ws = self.ws()
        self.enable(ws)
        for i in range(50):
            d.append_jsonl(ws / "data" / "apply-log.jsonl", {"posting_id": f"greenhouse:zz:{i}", "result": "submitted",
                                                             "mode": "auto", "company": f"Zed{i}", "at": "2026-09-01T08:00:00"})
        d.append_jsonl(ws / "data" / "events.jsonl", {"msg_id": "m1", "category": "rejection", "match": "greenhouse:zz:3"})
        out = autoapply.run(ws, filler=stub())
        self.assertIn("paused", out["skipped"])
        self.assertIn("1 of the last 50", autoapply.load_config(ws)["paused_reason"])

    def test_without_playwright_it_says_how_to_install(self):
        import autoapply
        ws = self.ws()
        self.enable(ws)
        saved = sys.modules.get("autoapply_forms")
        sys.modules["autoapply_forms"] = None
        try:
            out = autoapply.run(ws)
        finally:
            if saved is None:
                sys.modules.pop("autoapply_forms", None)
            else:
                sys.modules["autoapply_forms"] = saved
        self.assertIn("pip install playwright", out["error"])
        self.assertEqual(self.entry(ws)["state"], "matched")

    def test_command_line_cannot_mark_applied(self):
        import jobqueue
        ws = self.ws()
        for state in ("applying", "applied"):
            with self.assertRaises(ValueError):
                jobqueue.set_state(ws, "greenhouse:acme:1", state)


def add_job(ws, n, fit=82, state="matched", company=None):
    """A second ready job: its own board posting, folder and résumé."""
    import shutil
    import _v2data as d
    pid = f"greenhouse:acme:{100 + n}"
    word = ["Alpha", "Bravo", "Charlie", "Delta", "Echo"][n]
    company = company or ["Globex", "Initech", "Umbrella", "Hooli", "Vandelay"][n]
    src = ws / "jobs" / "05-acme-staff"
    dst = ws / "jobs" / f"{20 + n:02d}-acme-staff-{n}"
    shutil.copytree(src, dst)
    log = (dst / "application-log.md").read_text().replace("Acme Robotics, Staff Security Engineer", f"{company}, Staff Security Engineer {word}")
    (dst / "application-log.md").write_text(log)
    d.update_json(ws / "data" / "queue.json", {}, lambda q: q["jobs"].append({
        "posting_id": pid, "company": company, "title": f"Staff Security Engineer {word}",
        "nn": f"{20 + n:02d}", "fit": fit, "state": state}))
    d.append_jsonl(ws / "data" / "candidates.jsonl", {"posting_id": pid, "passed": True})
    return pid


class Release1(KeyEnv):
    """Council release round 1: the runner's guards had to hold inside a run, not only before it."""

    def ws(self, **kw):
        ws = super().ws(**kw)
        import _v2data as d
        d.write_json_atomic(ws / "data" / "sources.json", {"boards": [BOARD], "filters": {}})
        return ws

    def state(self, ws, pid):
        return self.entry(ws, pid)["state"]

    def test_three_unclear_in_one_run_pause_it_mid_run(self):          # B2
        import autoapply
        ws = self.ws()
        for n in range(4):
            add_job(ws, n)
        self.enable(ws, daily_cap=10)
        autoapply._change(ws, lambda c: c.update(enabled_at="2026-01-01"))
        f = stub("unclear", "no confirmation within 30 seconds")
        autoapply.run(ws, filler=f)
        self.assertEqual(len(f.calls), 3)
        self.assertTrue(autoapply.load_config(ws)["paused"])

    def test_a_job_rejected_during_the_run_is_not_sent(self):           # B3
        import jobqueue
        import autoapply
        ws = self.ws()
        pid = add_job(ws, 1, fit=70)
        self.enable(ws)
        calls = []

        def fill(url, answers, resume, submit, shots):
            calls.append(url)
            jobqueue.set_state(ws, pid, "rejected", via_hub=True)      # the user clicks Reject meanwhile
            return {"result": "submitted", "shots": []}
        autoapply.settings(ws, fit_threshold=60)
        autoapply.run(ws, filler=fill)
        self.assertEqual(len(calls), 1)
        self.assertEqual(self.state(ws, pid), "rejected")

    def test_resume_after_a_low_reply_pause_holds(self):                # B4
        import _v2data as d
        import autoapply
        ws = self.ws()
        self.enable(ws)
        for i in range(50):
            d.append_jsonl(ws / "data" / "apply-log.jsonl", {"posting_id": f"greenhouse:zz:{i}", "result": "submitted",
                                                             "mode": "auto", "company": f"Z{i}", "at": "2026-08-01T08:00:00"})
        out = autoapply.run(ws, filler=stub())
        self.assertIn("paused", out["skipped"])
        autoapply.resume(ws)
        f = stub()
        autoapply.run(ws, filler=f)
        self.assertEqual(len(f.calls), 1)          # the user's resume holds until 10 more sends mature

    def test_recent_sends_do_not_count_as_unanswered(self):              # B4
        import _v2data as d
        import autoapply
        ws = self.ws()
        self.enable(ws)
        for i in range(50):
            d.append_jsonl(ws / "data" / "apply-log.jsonl", {"posting_id": f"greenhouse:zz:{i}", "result": "submitted",
                                                             "mode": "auto", "company": f"Z{i}",
                                                             "at": datetime.now().isoformat(timespec="seconds")})
        self.assertIsNone(autoapply.pause_reason(ws))

    def test_unclear_is_applied_maybe_and_blocks_a_second_send(self):    # D2
        import autoapply
        import pipeline
        ws = self.ws()
        self.enable(ws)
        autoapply.run(ws, filler=stub("unclear", "no confirmation within 30 seconds"))
        e = self.entry(ws)
        self.assertEqual(e["state"], "applied?")
        self.assertTrue(pipeline.check_duplicate(ws, e["company"], e["title"], e["posting_id"]))

    def test_user_settles_an_unclear_send_in_the_hub(self):              # D2
        import apply
        import autoapply
        import jobqueue
        ws = self.ws()
        self.enable(ws)
        autoapply.run(ws, filler=stub("unclear", "x"))
        jobqueue.set_state(ws, "greenhouse:acme:1", "needs-you", via_hub=True, not_sent=True, stop_reason="not sent")
        self.assertEqual(self.entry(ws)["state"], "needs-you")
        jobqueue.set_state(ws, "greenhouse:acme:1", "applied?", via_runner=True)
        apply.record(ws, "greenhouse:acme:1")
        self.assertEqual(self.entry(ws)["state"], "applied")

    def test_retry_puts_a_stopped_job_back_for_the_runner(self):         # D5
        import autoapply
        import jobqueue
        ws = self.ws()
        self.enable(ws)
        autoapply.run(ws, filler=stub("stopped", "questions your saved answers do not cover: City"))
        jobqueue.set_state(ws, "greenhouse:acme:1", "matched", via_hub=True, stop_reason=None)
        f = stub()
        autoapply.run(ws, filler=f)
        self.assertEqual(self.entry(ws)["state"], "applied")

    def test_a_click_on_submitted_mid_run_does_not_abort_the_rest(self):  # B6
        import apply
        import jobqueue
        import autoapply
        ws = self.ws()
        pid = add_job(ws, 1)
        self.enable(ws)
        seen = []

        def fill(url, answers, resume, submit, shots):
            seen.append(url)
            if len(seen) == 1:
                jobqueue.set_state(ws, pid, "approved", via_hub=True)
                apply.record(ws, pid)                                    # the user sent the other one by hand
            return {"result": "submitted", "shots": []}
        autoapply.run(ws, filler=fill)
        self.assertEqual(len(seen), 1)
        self.assertEqual(self.state(ws, "greenhouse:acme:1"), "applied")

    def test_dry_run_changes_no_state_even_for_an_old_attempt(self):     # B13
        import _v2data as d
        import autoapply
        ws = self.ws()
        old = (datetime.now() - timedelta(hours=2)).isoformat(timespec="seconds")
        d.update_json(ws / "data" / "queue.json", {}, lambda q: q["jobs"][0].update(state="applying", attempt_at=old))
        autoapply.run(ws, dry_run=True, filler=stub())
        self.assertEqual(self.entry(ws)["state"], "applying")

    def test_nothing_goes_unattended_before_the_first_supervised_send(self):
        import autoapply
        ws = self.ws()
        self.enable(ws, supervised_ok=False)
        f = stub()
        out = autoapply.run(ws, filler=f)
        self.assertEqual(f.calls, [])
        self.assertIn("supervised", out["skipped"])
        out = autoapply.run(ws, filler=f, supervised=True)
        self.assertEqual(out["submitted"], 1)
        self.assertEqual(self.log(ws)[-1]["supervised"], True)
        autoapply.confirm_first(ws)
        self.assertTrue(autoapply.load_config(ws)["first_send_ok"])

    def test_first_send_cannot_be_confirmed_without_one(self):
        import autoapply
        ws = self.ws()
        self.enable(ws, supervised_ok=False)
        with self.assertRaises(ValueError):
            autoapply.confirm_first(ws)

    def test_a_supervised_send_is_one_job(self):
        import autoapply
        ws = self.ws()
        add_job(ws, 1)
        self.enable(ws, supervised_ok=False)
        f = stub()
        autoapply.run(ws, filler=f, supervised=True)
        self.assertEqual(len(f.calls), 1)

    def test_an_old_signed_auto_json_cannot_be_restored(self):           # S9
        import autoapply
        ws = self.ws()
        autoapply.enable(ws, "apply for me")
        saved = (ws / "data" / "auto.json").read_text()
        autoapply.disable(ws)
        (ws / "data" / "auto.json").write_text(saved)
        cfg = autoapply.load_config(ws)
        self.assertFalse(cfg["enabled"])
        self.assertTrue(cfg["tampered"])


if __name__ == "__main__":
    unittest.main()
