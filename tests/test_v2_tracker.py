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


if __name__ == "__main__":
    unittest.main()
