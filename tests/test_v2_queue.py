"""Ascend 2.0 M7: usage metering, the scored queue, run planning, and the served hub's write channel.

Run: python3 -m unittest tests/test_v2_queue.py -v
"""

import http.client
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(REPO / "tests"))
from test_v2_pipeline import make_ws  # noqa: E402


def seed_candidates(ws):
    import _v2data as d
    dd = ws / "data"
    posts = [("greenhouse:a:1", "Acme", "Staff Security Engineer", 0.4, True),
             ("greenhouse:b:2", "Bravo", "Principal Security Engineer", 0.8, True),
             ("greenhouse:c:3", "Charlie", "Security Engineer II", 0.9, False),
             ("greenhouse:d:4", "Delta", "Staff Cloud Security Engineer", 0.6, True)]
    for pid, co, title, ov, ok in posts:
        d.append_jsonl(dd / "postings.jsonl", {"id": pid, "company": co, "title": title, "location": "Remote - US",
                                               "comp_min": None, "comp_max": None, "url": f"https://x.example/{pid}",
                                               "text": "word " * 1000})
        d.append_jsonl(dd / "candidates.jsonl", {"posting_id": pid, "passed": ok, "keyword_overlap": ov,
                                                 "reasons": [], "filters_hash": "h"})
    d.write_json_atomic(dd / "queue.json", {"jobs": [{"posting_id": "greenhouse:d:4", "company": "Delta",
                                                      "title": "Staff Cloud Security Engineer", "state": "matched", "fit": 70}]})


class Usage(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.ws = make_ws(self.td.name, [])

    def tearDown(self):
        self.td.cleanup()

    def test_record_converts_characters_and_flags_estimate(self):
        import _v2data as d
        import usage
        usage.record(self.ws, "score", chars_in=4001, chars_out=800, engine="A", mode="assisted")
        row = d.read_jsonl(self.ws / "data" / "usage.jsonl")[0]
        self.assertEqual((row["input_tokens"], row["output_tokens"], row["estimated"]), (1001, 200, True))

    def test_estimate_defaults_then_measured(self):
        import usage
        e = usage.estimate(self.ws, "A", "assisted", jobs=20)
        self.assertEqual((e["basis"], e["per_job"], e["daily"]), ("default", 7500, 85000 + 20 * 7500))
        for _ in range(3):
            usage.record(self.ws, "score", chars_in=8000, chars_out=0, engine="A", mode="assisted")
            usage.record(self.ws, "tailor", chars_in=12000, chars_out=0, engine="A", mode="assisted")
        e = usage.estimate(self.ws, "A", "assisted", jobs=20)
        self.assertEqual((e["basis"], e["per_job"]), ("measured", 5000))


class Queue(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.ws = make_ws(self.td.name, [])
        seed_candidates(self.ws)

    def tearDown(self):
        self.td.cleanup()

    def test_candidates_exclude_queued_sort_and_trim(self):
        import jobqueue as qt
        c = qt.candidates(self.ws)
        self.assertEqual([x["posting_id"] for x in c], ["greenhouse:b:2", "greenhouse:a:1"])
        self.assertLessEqual(len(c[0]["text"]), 1500)

    def test_score_adds_then_updates(self):
        import _v2data as d
        import jobqueue as qt
        qt.score(self.ws, "greenhouse:b:2", 82, "AWS baselines match", ["Kubernetes in production"])
        qt.score(self.ws, "greenhouse:b:2", 85, "rescored", [])
        jobs = [j for j in d.read_json(self.ws / "data" / "queue.json", {})["jobs"] if j["posting_id"] == "greenhouse:b:2"]
        self.assertEqual(len(jobs), 1)
        self.assertEqual((jobs[0]["fit"], jobs[0]["state"], jobs[0]["company"]), (85, "matched", "Bravo"))

    def test_candidate_text_starts_at_the_role_not_the_boilerplate(self):
        import jobqueue as qt
        text = ("At Acme we exist for the moments that matter. " * 40 +
                "About the Role You will own AWS guardrails and detection for every account.")
        self.assertTrue(qt.role_text(text).startswith("About the Role You will own AWS"))
        self.assertEqual(qt.role_text("No markers here."), "No markers here.")

    def test_candidates_skip_a_role_already_queued_under_another_id(self):
        import _v2data as d
        import jobqueue as qt
        q = d.read_json(self.ws / "data" / "queue.json", {})
        q["jobs"].append({"posting_id": "https://boards.example/bravo/2", "company": "Bravo, Inc.",
                          "title": "Principal Security Engineer", "nn": "05", "state": "matched"})
        d.write_json_atomic(self.ws / "data" / "queue.json", q)
        self.assertEqual([x["posting_id"] for x in qt.candidates(self.ws)], ["greenhouse:a:1"])

    def test_board_slug_company_matches_the_proper_name(self):
        import _v2data as d
        import jobqueue as qt
        q = d.read_json(self.ws / "data" / "queue.json", {})
        q["jobs"].append({"posting_id": "https://x.example/a", "company": "acmehq", "title": "Staff Security Engineer",
                          "nn": "07", "state": "queued"})
        d.write_json_atomic(self.ws / "data" / "queue.json", q)
        self.assertNotIn("greenhouse:a:1", [x["posting_id"] for x in qt.candidates(self.ws)])
        self.assertTrue(qt.same_company("DoorDash", "doordashusa"))
        self.assertTrue(qt.same_company("Grow Therapy", "grow-therapy"))
        self.assertFalse(qt.same_company("Meta", "Metabase"))

    def test_set_state(self):
        import _v2data as d
        import jobqueue as qt
        qt.set_state(self.ws, "greenhouse:d:4", "approved")
        self.assertEqual(d.read_json(self.ws / "data" / "queue.json", {})["jobs"][0]["state"], "approved")
        with self.assertRaises(ValueError):
            qt.set_state(self.ws, "greenhouse:d:4", "teleported")
        with self.assertRaises(KeyError):
            qt.set_state(self.ws, "nope", "approved")

    def test_a_sent_job_never_moves_back(self):
        import jobqueue as qt
        qt.set_state(self.ws, "greenhouse:d:4", "approved")
        qt.set_state(self.ws, "greenhouse:d:4", "applied?")
        for back in ("approved", "matched", "rejected", "needs-you"):
            with self.assertRaises(ValueError):
                qt.set_state(self.ws, "greenhouse:d:4", back)
        self.assertEqual(qt.set_state(self.ws, "greenhouse:d:4", "applied")["state"], "applied")
        with self.assertRaises(ValueError):
            qt.set_state(self.ws, "greenhouse:d:4", "approved")

    def test_cli_cannot_approve_or_mark_applied(self):
        import _v2data as d
        for state in ("approved", "applied"):
            r = subprocess.run([sys.executable, str(REPO / "tools/jobqueue.py"), "set-state", str(self.ws),
                                "greenhouse:d:4", state], capture_output=True, text=True)
            self.assertEqual(r.returncode, 2, r.stdout)
            self.assertIn("hub", r.stderr)
        self.assertNotIn(d.read_json(self.ws / "data" / "queue.json", {})["jobs"][0]["state"], ("approved", "applied"))
        r = subprocess.run([sys.executable, str(REPO / "tools/jobqueue.py"), "set-state", str(self.ws),
                            "greenhouse:d:4", "rejected"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)


def ready_ws(ws):
    """The three files a v2 run needs before it can do anything useful."""
    import _v2data as d
    (ws / "master-resume.md").write_text("# Master\n", encoding="utf-8")
    d.write_json_atomic(ws / "data" / "sources.json", {"boards": [{"ats": "lever", "slug": "acme"}], "filters": {}})
    d.write_json_atomic(ws / "data" / "profile.json", {"name": "Jordan Rivera", "email": "jordan@example.com"})
    return ws


class Plan(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.ws = ready_ws(make_ws(self.td.name, []))

    def test_an_unready_workspace_is_refused_with_the_fix(self):
        import run
        out = run.plan(make_ws(self.td.name + "/fresh", []), "C")
        self.assertFalse(out["ok"])
        text = " ".join(out["problems"])
        for need in ("master-resume.md", "sources.json", "profile.json", "templates/"):
            self.assertIn(need, text)

    def tearDown(self):
        self.td.cleanup()

    def test_engine_a_needs_client_and_token(self):
        import run
        p = run.plan(self.ws, "A", "assisted")
        self.assertFalse(p["ok"])
        self.assertTrue(any("gmail-client.json" in x for x in p["problems"]))

    def test_agent_and_automatic_are_not_in_this_release(self):
        import run
        for mode in ("agent", "automatic"):
            out = run.plan(self.ws, "B", mode)
            self.assertFalse(out["ok"])
            self.assertIn("not in this release", " ".join(out["problems"]))

    def test_assisted_warns_about_tokens_and_ok_saves_defaults(self):
        import _v2data as d
        import run
        out = run.plan(self.ws, "B", "assisted")
        self.assertTrue(out["ok"], out)
        self.assertIn("tokens", out["warning"])
        state = d.read_json(Path(self.ws) / ".ascend-state.json", {})
        self.assertEqual(state["run_defaults"], {"engine": "B", "mode": "assisted"})

    def test_every_engine_states_the_permissions_it_uses(self):
        import run
        for engine in ("A", "B", "C"):
            perms = " ".join(run.plan(self.ws, engine)["permissions"])
            self.assertIn("never submits", perms)
            self.assertIn("LinkedIn", perms)
        self.assertIn("gmail.readonly", " ".join(run.plan(self.ws, "A")["permissions"]))
        for engine in ("B", "C"):
            perms = " ".join(run.plan(self.ws, engine)["permissions"])
            self.assertIn("claude.ai Gmail connector", perms)
            self.assertIn("denies", perms)

    def test_steps(self):
        import run
        a = run.steps("A")
        self.assertIn("gmail_sync.py sync", a[0])
        self.assertTrue(any(s.startswith("CLAUDE:") for s in a))
        self.assertTrue(all("gmail_sync.py sync" not in s for s in run.steps("C")))   # C never uses the OAuth sync


class Server(unittest.TestCase):
    SLUG = "v2-queue-test"

    @classmethod
    def setUpClass(cls):
        cls.ws = REPO / "workspace" / cls.SLUG
        shutil.rmtree(cls.ws, ignore_errors=True)
        (cls.ws / "data").mkdir(parents=True)
        seed_candidates(cls.ws)
        cls.port = 8957
        cls.proc = subprocess.Popen([sys.executable, str(REPO / "ui/server.py"), "--port", str(cls.port), "--no-browser"],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1.4)
        _, body = cls.req("GET", "/")
        cls.token = re.search(r'const TOKEN = "([^"]+)"', body).group(1)

    @classmethod
    def tearDownClass(cls):
        cls.proc.terminate()
        cls.proc.wait(timeout=5)
        shutil.rmtree(cls.ws, ignore_errors=True)
        (REPO / "ui/.port").unlink(missing_ok=True)

    @classmethod
    def req(cls, method, path, body=None, token=None):
        c = http.client.HTTPConnection("127.0.0.1", cls.port, timeout=5)
        h = {"Host": f"127.0.0.1:{cls.port}"}
        if token:
            h["X-Ascend-Token"] = token
        if body is not None:
            h["Content-Type"] = "application/json"
            h["Origin"] = f"http://127.0.0.1:{cls.port}"
        c.request(method, path, body=json.dumps(body) if body is not None else None, headers=h)
        r = c.getresponse()
        out = (r.status, r.read().decode("utf-8", "replace"), dict(r.getheaders()))
        c.close()
        return out[:2] if method == "GET" and path == "/" else out

    def test_hub_route_injects_token_and_allows_self_only(self):
        status, body, headers = self.req("GET", f"/hub?slug={self.SLUG}")
        self.assertEqual(status, 200)
        self.assertIn(self.token, body)
        self.assertIn("connect-src 'self'", body)
        self.assertNotIn("connect-src 'none'", body)

    def test_apply_sheet_endpoint_refuses_unapproved_with_reason(self):
        status, body, _ = self.req("POST", "/api/apply", {"slug": self.SLUG, "posting_id": "greenhouse:d:4"},
                                   token=self.token)
        self.assertEqual(status, 409, body)
        self.assertIn("not approved", json.loads(body)["error"])

    def test_no_apply_control_endpoint(self):
        status, _, _ = self.req("POST", "/api/apply-control", {"slug": self.SLUG, "paused": True}, token=self.token)
        self.assertEqual(status, 404)

    def test_i_submitted_it_logs_the_send(self):
        import _v2data as d
        q = d.read_json(self.ws / "data" / "queue.json", {})
        q["jobs"].append({"posting_id": "greenhouse:e:5", "company": "Echo", "title": "Staff Engineer", "state": "approved"})
        d.write_json_atomic(self.ws / "data" / "queue.json", q)
        status, body, _ = self.req("POST", "/api/queue", {"slug": self.SLUG, "posting_id": "greenhouse:e:5",
                                                          "action": "applied"}, token=self.token)
        self.assertEqual(status, 200, body)
        log = d.read_jsonl(self.ws / "data" / "apply-log.jsonl")
        self.assertEqual([(r["posting_id"], r["result"]) for r in log], [("greenhouse:e:5", "submitted")])

    def test_queue_action_needs_token(self):
        status, _, _ = self.req("POST", "/api/queue", {"slug": self.SLUG, "posting_id": "greenhouse:d:4", "action": "approved"})
        self.assertEqual(status, 403)
        status, body, _ = self.req("POST", "/api/queue", {"slug": self.SLUG, "posting_id": "greenhouse:d:4",
                                                          "action": "approved"}, token=self.token)
        self.assertEqual(status, 200, body)
        import _v2data as d
        self.assertEqual(d.read_json(self.ws / "data" / "queue.json", {})["jobs"][0]["state"], "approved")
        status, _, _ = self.req("POST", "/api/queue", {"slug": self.SLUG, "posting_id": "greenhouse:d:4",
                                                       "action": "teleported"}, token=self.token)
        self.assertEqual(status, 400)


if __name__ == "__main__":
    unittest.main()
