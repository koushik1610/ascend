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
        self.assertEqual(stages["gmail"]["detail"], "skipped: engine A is not connected")
        self.assertTrue(stages["finder"]["ok"])            # an unreachable board is data, not a crash
        self.assertIn("unreachable", stages["finder"]["detail"])
        self.assertTrue(stages["hub"]["ok"])
        self.assertTrue((self.ws / "hub.html").is_file())
        self.assertEqual(len(d.read_jsonl(self.ws / "data" / "run-log.jsonl")), 1)


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

    def test_no_agent_submit_tool_is_allowed(self):
        allow = json.loads((REPO / ".claude/settings.json").read_text())["permissions"]["allow"]
        self.assertFalse([a for a in allow if "fakeform" in a])


if __name__ == "__main__":
    unittest.main()
