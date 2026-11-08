"""Ascend 2.0 M10: shared cron helper, the scheduled zero-token sync, release wiring.

Run: python3 -m unittest tests/test_v2_release.py -v
Never touches the real crontab: ASCEND_CRONTAB_FILE points the helper at a temp file.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(REPO / "tests"))
from test_v2_pipeline import make_ws  # noqa: E402


class Cron(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.tab = Path(self.td.name) / "crontab"
        self.tab.write_text("0 7 * * * /usr/bin/backup.sh # mine\n")
        os.environ["ASCEND_CRONTAB_FILE"] = str(self.tab)

    def tearDown(self):
        os.environ.pop("ASCEND_CRONTAB_FILE", None)
        self.td.cleanup()

    def test_install_replace_remove(self):
        import _cron
        out = _cron.install("Ascend-V2-SYNC-x", "5 6 * * * run-a", Path(self.td.name))
        self.assertTrue(out["ok"])
        _cron.install("Ascend-V2-SYNC-x", "9 6 * * * run-b", Path(self.td.name))
        lines = self.tab.read_text().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertIn("/usr/bin/backup.sh", lines[0])
        self.assertTrue(lines[1].startswith("9 6 * * * run-b") and lines[1].endswith("# Ascend-V2-SYNC-x"))
        self.assertTrue((Path(self.td.name) / "crontab.bak").is_file())
        _cron.remove("Ascend-V2-SYNC-x")
        self.assertEqual(self.tab.read_text().splitlines(), ["0 7 * * * /usr/bin/backup.sh # mine"])

    def test_unreadable_crontab_is_refused(self):
        import _cron
        self.tab.unlink()
        self.tab.mkdir()                     # a directory cannot be read as a crontab
        out = _cron.install("Ascend-V2-SYNC-x", "5 6 * * * run", Path(self.td.name))
        self.assertFalse(out["ok"])
        self.assertIn("crontab -e", out["note"])

    def test_schedule_install_line(self):
        import schedule
        ws = make_ws(self.td.name, [])
        out = schedule.install(ws, "06:30")
        self.assertTrue(out["ok"])
        line = self.tab.read_text().splitlines()[-1]
        self.assertTrue(line.startswith("30 6 * * * "))
        self.assertIn("tools/daily.py", line)
        self.assertIn("Ascend-V2-SYNC-tester", line)
        self.assertFalse(schedule.install(ws, "25:99")["ok"])

    def test_a_line_break_or_percent_never_reaches_the_crontab(self):
        import _cron
        before = self.tab.read_text()
        for bad in ("5 6 * * * run\n* * * * * touch /tmp/pwned", "5 6 * * * run\r* * * * * x", "5 6 * * * date +%s"):
            self.assertFalse(_cron.install("Ascend-V2-SYNC-x", bad, Path(self.td.name))["ok"], bad)
        self.assertEqual(self.tab.read_text(), before)

    def test_tags_match_exactly_and_remove_needs_a_name(self):
        import _cron
        import schedule
        _cron.install("Ascend-V2-SYNC-ab", "5 6 * * * run-ab", Path(self.td.name))
        _cron.install("Ascend-V2-SYNC-a", "5 7 * * * run-a", Path(self.td.name))
        self.assertIn("run-ab", self.tab.read_text())
        _cron.remove("Ascend-V2-SYNC-a")
        self.assertIn("run-ab", self.tab.read_text())
        self.assertFalse(schedule.remove("")["ok"])
        self.assertIn("run-ab", self.tab.read_text())

    def test_show_matches_its_own_workspace_only(self):
        import _cron
        import schedule
        _cron.install("Ascend-V2-SYNC-ab", "5 6 * * * run-ab", Path(self.td.name))
        self.assertIsNone(schedule.show("workspace/a")["line"])

    def test_schedule_refuses_a_workspace_path_it_cannot_trust(self):
        import schedule
        before = self.tab.read_text()
        evil = Path(self.td.name) / "ws\n* * * * * touch /tmp/pwned #"
        self.assertFalse(schedule.install(evil, "06:30")["ok"])
        self.assertFalse(evil.exists())
        self.assertFalse(schedule.install(REPO.parent / "not-a-workspace", "06:30")["ok"])
        self.assertEqual(self.tab.read_text(), before)


class Daily(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.ws = make_ws(self.td.name, [])

    def tearDown(self):
        self.td.cleanup()

    def test_runs_every_stage_and_isolates_failures(self):
        import _v2data as d
        import daily
        d.write_json_atomic(self.ws / "data" / "sources.json",
                            {"boards": [{"ats": "greenhouse", "slug": "nope", "company": "Nope"}], "filters": {}})
        os.environ["ASCEND_ATS_BASE"] = "http://127.0.0.1:9"     # nothing listens: the board fails
        try:
            out = daily.run(self.ws)
        finally:
            os.environ.pop("ASCEND_ATS_BASE", None)
        stages = {s["stage"]: s for s in out["stages"]}
        self.assertFalse(stages["gmail"]["ok"])            # no run settings yet: say so, never pass silently
        self.assertIn("run-v2", stages["gmail"]["detail"])
        self.assertFalse(stages["finder"]["ok"])           # its only board is unreachable: say so
        self.assertIn("unreachable", stages["finder"]["detail"])
        self.assertTrue(stages["hub"]["ok"])               # and every later stage still runs
        self.assertTrue((self.ws / "hub.html").is_file())
        self.assertEqual(len(d.read_jsonl(self.ws / "data" / "run-log.jsonl")), 1)


    def stages(self):
        import daily
        return {s["stage"]: s for s in daily.run(self.ws)["stages"]}

    def test_engine_a_signed_out_is_a_failed_stage_with_the_fix(self):
        import _v2data as d
        d.write_json_atomic(self.ws / ".ascend-state.json", {"run_defaults": {"engine": "A", "mode": "assisted"}})
        (self.ws / "gmail-client.json").write_text('{"client_id": "cid"}')
        os.environ["ASCEND_TOKEN_STORE"] = f"file:{self.td.name}/tokens.json"     # never the real Keychain
        try:
            g = self.stages()["gmail"]
        finally:
            os.environ.pop("ASCEND_TOKEN_STORE", None)
        self.assertFalse(g["ok"])
        self.assertIn("gmail_sync.py connect", g["detail"])

    def test_engine_c_skips_gmail_and_no_boards_fails_the_finder(self):
        import _v2data as d
        d.write_json_atomic(self.ws / ".ascend-state.json", {"run_defaults": {"engine": "C", "mode": "assisted"}})
        st = self.stages()
        self.assertTrue(st["gmail"]["ok"])
        self.assertFalse(st["finder"]["ok"])
        self.assertIn("sources.json", st["finder"]["detail"])

    def test_help_prints_usage_and_runs_nothing(self):
        r = subprocess.run([sys.executable, str(REPO / "tools/daily.py"), "--help"], capture_output=True, text=True,
                           cwd=self.td.name)
        self.assertEqual(r.returncode, 2)
        self.assertFalse((Path(self.td.name) / "--help").exists())

    def test_every_board_unreachable_fails_the_finder(self):
        import _v2data as d
        d.write_json_atomic(self.ws / ".ascend-state.json", {"run_defaults": {"engine": "C", "mode": "assisted"}})
        d.write_json_atomic(self.ws / "data" / "sources.json", {"boards": [{"ats": "greenhouse", "slug": "nope"}]})
        os.environ["ASCEND_ATS_BASE"] = "http://127.0.0.1:9"
        try:
            f = self.stages()["finder"]
        finally:
            os.environ.pop("ASCEND_ATS_BASE", None)
        self.assertFalse(f["ok"])
        self.assertIn("unreachable", f["detail"])

    def test_retention_only_runs_without_the_other_stages(self):
        import _v2data as d
        dd = self.ws / "data"
        d.write_json_atomic(dd / "sources.json", {"boards": [], "retention_days": 180})
        d.append_jsonl(dd / "mail.jsonl", {"msg_id": "old", "from": "a@b.example", "subject": "s",
                                           "date": "2020-01-01T00:00:00+00:00", "body_excerpt": "x"})
        r = subprocess.run([sys.executable, str(REPO / "tools/daily.py"), str(self.ws), "--retention-only"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertIn('"dropped": 1', r.stdout)
        self.assertEqual(d.read_jsonl(dd / "mail.jsonl"), [])

    def test_retention_drops_old_mail_and_keeps_only_headers_of_non_job_mail(self):
        import _v2data as d
        import daily
        dd = self.ws / "data"
        d.write_json_atomic(dd / "sources.json", {"boards": [], "retention_days": 180})
        for mid, when, thread in (("old", "2026-01-01T00:00:00+00:00", "t1"), ("job", "2026-09-10T00:00:00+00:00", "t2"),
                                  ("news", "2026-09-11T00:00:00+00:00", "t3"), ("unsure", "2026-09-12T00:00:00+00:00", "t4"),
                                  ("followup", "2026-09-13T00:00:00+00:00", "t2"), ("fresh", "2026-10-15T00:00:00+00:00", "t5")):
            d.append_jsonl(dd / "mail.jsonl", {"msg_id": mid, "thread_id": thread, "from": "a@b.example", "subject": mid,
                                               "date": when, "body_excerpt": f"body of {mid}"})
        for mid, cat, llm in (("job", "acknowledgement", False), ("news", "other", False), ("unsure", "other", True),
                              ("followup", "other", False), ("fresh", "other", False)):
            d.append_jsonl(dd / "events.jsonl", {"msg_id": mid, "category": cat, "needs_llm": llm})
        (dd / "connector-rows.json").write_text("[]")
        d.append_jsonl(dd / "mail.jsonl", {"msg_id": "home", "thread_id": "t9", "from": "do-not-reply@customer.homeservices.example",
                                           "subject": "Did you hire a pro?", "date": "2026-10-16T00:00:00+00:00",
                                           "body_excerpt": "body of home"})
        d.append_jsonl(dd / "events.jsonl", {"msg_id": "home", "category": "other", "needs_llm": False})
        out = daily.prune(self.ws, today="2026-10-17")
        mail = {m["msg_id"]: m["body_excerpt"] for m in d.read_jsonl(dd / "mail.jsonl")}
        # Personal mail a broad first read pulled in keeps headers only from day one.
        self.assertEqual(mail.pop("home"), "")
        self.assertEqual(sorted(mail), ["followup", "fresh", "job", "news", "unsure"])
        # Trimmed: non-job mail older than two weeks. Kept: a follow-up in a job thread, mail still fresh enough
        # for a model pass or a second look, and mail waiting for a model.
        self.assertEqual(mail, {"job": "body of job", "news": "", "unsure": "body of unsure",
                                "followup": "body of followup", "fresh": "body of fresh"})
        self.assertEqual(out["dropped"], 1)
        self.assertEqual(out["trimmed"], 2)
        self.assertFalse((dd / "connector-rows.json").exists())     # a staging copy left behind is removed


class Registry(unittest.TestCase):
    def test_v2_ops_and_phases_registered(self):
        reg = json.loads((REPO / "ops.json").read_text())
        ops = {o["op"] for o in reg["ops"]}
        self.assertTrue({"run-v2", "apply", "linkedin-search", "hub", "schedule"} <= ops, ops)
        state = (REPO / "tools/state.py").read_text()
        for ph in ('"27"', '"28"', '"29"'):
            self.assertIn(ph, state)


class Permissions(unittest.TestCase):
    """Engines B and C read Gmail through the claude.ai connector. Read-only has to hold in settings, not only in prose."""

    GMAIL_WRITES = ["send_message", "reply", "forward", "create_draft", "update_draft", "delete_draft", "trash_message",
                    "trash_thread", "untrash_message", "untrash_thread", "mark_message_spam", "mark_thread_spam",
                    "unmark_message_spam", "unmark_thread_spam", "label_message", "label_thread", "unlabel_message",
                    "unlabel_thread", "update_message_labels", "create_label", "update_label", "delete_label",
                    "apply_sensitive_message_label", "apply_sensitive_thread_label"]
    DRIVE_WRITES = ["share_file", "create_file", "update_file", "copy_file", "trash_file"]

    def test_connector_write_tools_are_denied(self):
        perms = json.loads((REPO / ".claude/settings.json").read_text())["permissions"]
        for t in self.GMAIL_WRITES:
            self.assertIn(f"mcp__claude_ai_Gmail__{t}", perms["deny"])
        for t in self.DRIVE_WRITES:
            self.assertIn(f"mcp__claude_ai_Google_Drive__{t}", perms["deny"])

    def test_web_fetch_asks_and_nothing_can_click_for_the_user(self):
        # Rerun 1 council: mail, postings and an any-domain WebFetch shared one session; approval and sends
        # were guarded only by the CLI. The user chose: WebFetch asks, Chrome form tools and direct edits of
        # the queue and logs are denied.
        perms = json.loads((REPO / ".claude/settings.json").read_text())["permissions"]
        self.assertNotIn("WebFetch", perms["allow"])
        self.assertIn("WebFetch", perms.get("ask", []))
        # browser_batch can run a denied tool inside a batch; upload_image fills a file input; no prompt uses either.
        for t in ("form_input", "file_upload", "javascript_tool", "browser_batch", "upload_image", "shortcuts_execute"):
            self.assertIn(f"mcp__claude-in-chrome__{t}", perms["deny"])
        for f in ("queue.json", "apply-log.jsonl", "events.jsonl", "ingested.jsonl"):
            for tool in ("Edit", "Write"):
                self.assertIn(f"{tool}(workspace/*/data/{f})", perms["deny"])
                self.assertIn(f"{tool}(**/workspace/*/data/{f})", perms["deny"])     # whatever the launch folder

    def test_no_text_claims_more_than_the_settings_hold(self):
        for f in ("README.md", "prompts/29-run-v2.md", "tools/run.py", "CLAUDE.md"):
            text = (REPO / f).read_text()
            self.assertNotIn("never your sent mail", text, f)
            self.assertNotIn("never for the user's sent mail", text, f)
            self.assertNotIn("denies Claude in Chrome's form filling, file upload and page scripting,", text, f)

    def test_claude_md_permissions_match_settings(self):
        text = (REPO / "CLAUDE.md").read_text()
        self.assertNotIn("domain-allowlist", text)       # a local allow cannot narrow the project's rules
        self.assertNotIn("a few pinned forms", text)
        self.assertIn('"ask"', text)

    def test_no_agent_submit_tool_is_allowed(self):
        allow = json.loads((REPO / ".claude/settings.json").read_text())["permissions"]["allow"]
        self.assertFalse([a for a in allow if "fakeform" in a])


if __name__ == "__main__":
    unittest.main()
