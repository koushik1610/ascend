"""Ascend 2.0 M5: finder (five public ATS APIs) and prefilter, against a fake ATS server.

Run: python3 -m unittest tests/test_v2_finder.py -v
"""

import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(REPO / "tests"))
from test_v2_pipeline import make_ws  # noqa: E402


def gh_job(i, title, loc="Remote - US", html="<p>Own <b>AWS</b> IAM guardrails</p>"):
    return {"id": i, "title": title, "location": {"name": loc}, "absolute_url": f"https://boards.example/gh/{i}",
            "content": html.replace("<", "&lt;").replace(">", "&gt;"), "updated_at": "2026-10-10T00:00:00Z"}



class Override(unittest.TestCase):
    def test_board_override_only_points_at_this_machine(self):
        import finder
        try:
            os.environ["ASCEND_ATS_BASE"] = "https://evil.example"
            self.assertTrue(finder._url("lever", "acme").startswith("https://api.lever.co/"))
            os.environ["ASCEND_ATS_BASE"] = "http://127.0.0.1:9"
            self.assertTrue(finder._url("lever", "acme").startswith("http://127.0.0.1:9/"))
        finally:
            os.environ.pop("ASCEND_ATS_BASE", None)

class FakeATS:
    def __init__(self):
        self.boards = {}     # path -> payload, None for a 500, an int status, or a callable(query, body)
        self.calls = []
        fake = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):
                u = urlparse(self.path)
                path = u.path
                n = int(self.headers.get("Content-Length") or 0)
                body = json.loads(self.rfile.read(n) or b"{}") if n else None
                fake.calls.append((self.command, self.path, body))
                if path not in fake.boards:
                    self.send_response(404)
                    self.end_headers()
                    return
                payload = fake.boards[path]
                if callable(payload):       # (query, body) -> payload, or an int status
                    payload = payload(u.query, body)
                if isinstance(payload, int):
                    self.send_response(payload)
                    self.send_header("Retry-After", "3600")
                    self.end_headers()
                    return
                if payload is None:
                    self.send_response(500)
                    self.end_headers()
                    return
                b = json.dumps(payload).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(b)))
                self.end_headers()
                self.wfile.write(b)

            do_POST = do_GET

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def close(self):
        self.server.shutdown()


class Base(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.ws = make_ws(self.td.name, [])
        self.fake = FakeATS()
        os.environ["ASCEND_ATS_BASE"] = self.fake.base

    def tearDown(self):
        os.environ.pop("ASCEND_ATS_BASE", None)
        self.fake.close()
        self.td.cleanup()

    def sources(self, boards, **filters):
        import _v2data as d
        d.write_json_atomic(self.ws / "data" / "sources.json", {"boards": boards, "filters": filters})

    def postings(self):
        import _v2data as d
        return d.read_jsonl(self.ws / "data" / "postings.jsonl")


class Adapters(Base):
    def test_greenhouse(self):
        import finder
        self.fake.boards["/v1/boards/acme/jobs"] = {"jobs": [gh_job(7, "Staff Security Engineer")]}
        p = finder.normalize("greenhouse", "acme", "Acme", finder.fetch_board("greenhouse", "acme")[0])
        self.assertEqual((p["id"], p["title"], p["remote"], p["url"]),
                         ("greenhouse:acme:7", "Staff Security Engineer", True, "https://boards.example/gh/7"))
        self.assertEqual(p["text"], "Own AWS IAM guardrails")

    def test_ashby_with_compensation(self):
        import finder
        self.fake.boards["/posting-api/job-board/northwind"] = {"jobs": [{
            "id": "u1", "title": "Principal Security Engineer", "location": "New York", "isRemote": False,
            "jobUrl": "https://jobs.example/u1", "applyUrl": "https://jobs.example/u1/apply",
            "descriptionPlain": "Cloud security", "compensation": {"summaryComponents": [
                {"compensationType": "Salary", "minValue": 210000, "maxValue": 260000}]}}]}
        p = finder.normalize("ashby", "northwind", "Northwind", finder.fetch_board("ashby", "northwind")[0])
        self.assertEqual((p["remote"], p["comp_min"], p["comp_max"], p["apply_url"]),
                         (False, 210000, 260000, "https://jobs.example/u1/apply"))

    def test_greenhouse_apply_link_is_greenhouses_own(self):
        # Companies with their own careers site give Greenhouse an absolute_url there; the apply sheet then
        # warns "not a known application system". Greenhouse's own job page works for every board.
        import finder
        j = gh_job(7, "Staff Security Engineer")
        j["absolute_url"] = "https://databricks.com/company/careers/open-positions/job?gh_jid=7"
        p = finder.normalize("greenhouse", "databricks", "Databricks", j)
        self.assertEqual(p["apply_url"], "https://job-boards.greenhouse.io/databricks/jobs/7")
        self.assertEqual(p["url"], j["absolute_url"])

    def test_ashby_hybrid_is_not_remote(self):
        # Ashby sets isRemote on hybrid jobs: Harvey's San Francisco hybrid roles came through remote_only.
        import finder
        base = {"title": "Staff Security Engineer", "location": "San Francisco", "jobUrl": "https://jobs.example/h",
                "descriptionPlain": "x"}
        for wp, is_remote, want in [("Hybrid", True, False), ("OnSite", True, False), ("Remote", False, True),
                                    (None, True, True)]:
            j = dict(base, id=f"h-{wp}", workplaceType=wp, isRemote=is_remote)
            self.assertEqual(finder.normalize("ashby", "h", "H", j)["remote"], want, wp)

    def test_stored_text_starts_at_the_role_and_keeps_requirements(self):
        import finder
        body = ("About Us. " + "Company boilerplate. " * 300 + "As the Staff Security Engineer at Acme, you will own "
                "cloud guardrails. " + "Detail. " * 200 + "Requirements: active clearance required.")
        p = finder.normalize("greenhouse", "acme", "Acme", {"id": 9, "title": "Staff Security Engineer",
                                                            "location": {"name": "Remote"}, "content": body})
        self.assertTrue(p["text"].startswith("As the Staff Security Engineer"), p["text"][:60])
        self.assertIn("clearance required", p["text"])

    def test_lever(self):
        import finder
        self.fake.boards["/v0/postings/streamco"] = [{
            "id": "L1", "text": "Senior Staff Cloud Security Engineer", "categories": {"location": "Remote"},
            "hostedUrl": "https://jobs.example/L1", "applyUrl": "https://jobs.example/L1/apply",
            "descriptionPlain": "Detection", "lists": [{"content": "<li>Terraform</li>"}],
            "workplaceType": "remote", "salaryRange": {"min": 180000, "max": 220000}}]
        p = finder.normalize("lever", "streamco", "StreamCo", finder.fetch_board("lever", "streamco")[0])
        self.assertEqual((p["remote"], p["comp_min"], p["text"]), (True, 180000, "Detection Terraform"))

    def test_workable(self):
        import finder
        self.fake.boards["/api/v1/widget/accounts/litware"] = {"jobs": [{
            "shortcode": "AB12", "title": "Security Architect", "city": "Austin", "country": "United States",
            "telecommuting": True, "url": "https://apply.example/AB12", "application_url": "https://apply.example/AB12/apply",
            "description": "<p>Zero trust</p>"}]}
        p = finder.normalize("workable", "litware", "Litware", finder.fetch_board("workable", "litware")[0])
        self.assertEqual((p["id"], p["remote"], p["location"], p["text"]),
                         ("workable:litware:AB12", True, "Austin, United States", "Zero trust"))

    def test_smartrecruiters(self):
        import finder
        self.fake.boards["/v1/companies/contoso/postings"] = {"content": [{
            "id": "999", "name": "Cloud Security Manager",
            "location": {"city": "Remote", "country": "us", "remote": True}}]}
        p = finder.normalize("smartrecruiters", "contoso", "Contoso",
                             finder.fetch_board("smartrecruiters", "contoso")[0])
        self.assertEqual((p["id"], p["remote"], p["url"]),
                         ("smartrecruiters:contoso:999", True, "https://jobs.smartrecruiters.com/contoso/999"))


class Run(Base):
    def test_dedupe_last_seen_and_closing(self):
        import _v2data as d
        import finder
        self.sources([{"ats": "greenhouse", "slug": "acme", "company": "Acme"},
                      {"ats": "greenhouse", "slug": "flaky", "company": "Flaky"}])
        self.fake.boards["/v1/boards/acme/jobs"] = {"jobs": [gh_job(1, "Staff Security Engineer"),
                                                              gh_job(2, "Principal Security Engineer")]}
        self.fake.boards["/v1/boards/flaky/jobs"] = {"jobs": [gh_job(9, "Staff Security Engineer")]}
        first = finder.run(self.ws, today="2026-10-10")
        self.assertEqual((first["new"], first["failed"]), (3, []))
        self.fake.boards["/v1/boards/acme/jobs"] = {"jobs": [gh_job(1, "Staff Security Engineer")]}
        self.fake.boards["/v1/boards/flaky/jobs"] = None
        second = finder.run(self.ws, today="2026-10-11")
        self.assertEqual((second["new"], second["closed"], second["failed"]), (0, 1, ["greenhouse:flaky"]))
        self.assertEqual(len(self.postings()), 3)
        state = d.read_json(self.ws / "data" / "postings-state.json", {})
        self.assertEqual(state["greenhouse:acme:1"]["last_seen"], "2026-10-11")
        self.assertTrue(state["greenhouse:acme:2"]["closed"])
        self.assertFalse(state["greenhouse:flaky:9"]["closed"])

    def test_a_board_whose_jobs_all_fail_to_read_is_not_emptied(self):
        import _v2data as d
        import finder
        self.sources([{"ats": "greenhouse", "slug": "acme", "company": "Acme"}])
        self.fake.boards["/v1/boards/acme/jobs"] = {"jobs": [gh_job(1, "Staff Security Engineer")]}
        finder.run(self.ws, today="2026-10-10")
        self.fake.boards["/v1/boards/acme/jobs"] = {"jobs": [{"renamed_id": 1}, {"renamed_id": 2}]}
        out = finder.run(self.ws, today="2026-10-11")
        self.assertEqual((out["closed"], out["failed"]), (0, ["greenhouse:acme"]))
        self.assertFalse(d.read_json(self.ws / "data" / "postings-state.json", {})["greenhouse:acme:1"]["closed"])

    def test_an_odd_answer_never_closes_a_board_or_stops_the_run(self):
        import _v2data as d
        import finder
        self.sources([{"ats": "greenhouse", "slug": "acme", "company": "Acme"},
                      {"ats": "greenhouse", "slug": "weird", "company": "Weird"}])
        self.fake.boards["/v1/boards/acme/jobs"] = {"jobs": [gh_job(1, "Staff Security Engineer")]}
        self.fake.boards["/v1/boards/weird/jobs"] = {"jobs": [gh_job(5, "Staff Security Engineer")]}
        finder.run(self.ws, today="2026-10-10")
        self.fake.boards["/v1/boards/acme/jobs"] = ["not", "an", "object"]
        self.fake.boards["/v1/boards/weird/jobs"] = {"error": "maintenance"}
        out = finder.run(self.ws, today="2026-10-11")
        self.assertEqual((out["closed"], sorted(out["failed"])), (0, ["greenhouse:acme", "greenhouse:weird"]))
        state = d.read_json(self.ws / "data" / "postings-state.json", {})
        self.assertFalse(state["greenhouse:weird:5"]["closed"])

    def test_board_health_names_the_ats_and_counts_empty_boards(self):
        import _v2data as d
        import finder
        self.fake.boards["/v1/boards/acme/jobs"] = {"jobs": [gh_job(1, "Staff Security Engineer")]}
        self.fake.boards["/v1/boards/quiet/jobs"] = {"jobs": []}
        self.sources([{"ats": "greenhouse", "slug": "acme"}, {"ats": "greenhouse", "slug": "quiet"},
                      {"ats": "lever", "slug": "acme"}])
        out = finder.run(self.ws, today="2026-10-17")
        self.assertEqual((out["failed"], out["empty"]), (["lever:acme"], ["greenhouse:quiet"]))
        health = d.read_json(self.ws / "data" / "board-health.json", {})
        self.assertEqual((health["failed"], health["empty"], health["checked"]), (["lever:acme"], ["greenhouse:quiet"], "2026-10-17"))

    def test_probe_finds_the_board_and_its_name(self):
        import finder
        self.fake.boards["/v1/boards/acmehq/jobs"] = {"jobs": [gh_job(1, "Staff Security Engineer")]}
        self.fake.boards["/v1/boards/acmehq"] = {"name": "Acme Robotics"}
        self.fake.boards["/posting-api/job-board/acme-robotics"] = {"jobs": [{"id": "x"}, {"id": "y"}]}
        self.fake.boards["/v1/companies/acmerobotics/postings"] = {"content": []}     # answers for any name
        hits = finder.probe("Acme Robotics")
        self.assertFalse([h for h in hits if h["jobs"] == 0], hits)
        self.assertIn({"ats": "greenhouse", "slug": "acmehq", "jobs": 1, "name": "Acme Robotics"}, hits)
        self.assertIn({"ats": "ashby", "slug": "acme-robotics", "jobs": 2, "name": None}, hits)

    def test_cli(self):
        self.sources([{"ats": "greenhouse", "slug": "acme", "company": "Acme"}])
        self.fake.boards["/v1/boards/acme/jobs"] = {"jobs": [gh_job(1, "Staff Security Engineer")]}
        env = dict(os.environ)
        r = subprocess.run([sys.executable, str(REPO / "tools/finder.py"), "run", str(self.ws), "--json"],
                           capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["new"], 1)


FILTERS = {"title_include": [r"secur"], "title_exclude": [r"\bintern\b", r"\bsales\b"],
           "seniority": [r"\b(staff|principal|senior staff|manager)\b"], "remote_only": True,
           "locations": ["united states", "us", "remote"], "comp_floor": 200000,
           "exclude_keywords": ["clearance required"], "blocklist": ["Badco"],
           "keywords": ["aws", "iam", "terraform", "detection"]}


def posting(**kw):
    base = {"id": "greenhouse:acme:1", "company": "Acme", "title": "Staff Security Engineer",
            "location": "Remote - US", "remote": True, "comp_min": None, "comp_max": None,
            "text": "AWS IAM guardrails with Terraform"}
    base.update(kw)
    return base


class Evaluate(unittest.TestCase):
    def check(self, expect_pass, reason_part=None, applied=(), **kw):
        import prefilter
        r = prefilter.evaluate(posting(**kw), FILTERS, list(applied))
        self.assertEqual(r["passed"], expect_pass, r)
        if reason_part:
            self.assertTrue(any(reason_part in x for x in r["reasons"]), r["reasons"])
        return r

    def test_numbered_levels_five_and_up_count_as_senior(self):
        # Run 4 (2026-10-22): Netflix titles its levels "Security Engineer 5" and "(L6)", so the user's seniority
        # filter rejected every Netflix role, the one they were interviewing for among them.
        for title in ("Security Engineer 5 - IAM", "Security Software Engineer (L6), Platform Security",
                      "Security Engineer L5", "Security Engineer, Level 6", "IC6 Security Engineer"):
            self.check(True, title=title)
        for title in ("Security Engineer 3", "Security Engineer (L4)", "Security Engineer 2 - AU",
                      "Security Engineer - Windows 11 hardening"):
            self.check(False, "seniority", title=title)

    def test_passes_and_scores_overlap(self):
        r = self.check(True)
        self.assertEqual(r["keyword_overlap"], 0.75)

    def test_title_rules(self):
        self.check(False, "title", title="Software Engineer")
        self.check(False, "excluded title", title="Security Sales Staff")
        self.check(False, "seniority", title="Security Engineer II")

    def test_remote_and_location(self):
        self.check(False, "not remote", remote=False, location="New York")
        self.check(True, remote=None, location="Remote (United States)")

    def test_comp_floor(self):
        self.check(False, "below", comp_max=180000)
        self.check(True, "comp unknown")

    def test_location_matches_whole_words(self):
        self.check(False, "location", remote=True, location="Remote - Australia")

    def test_us_geography_counts_as_us(self):
        import prefilter
        us = ["remote", "united states", "us"]
        for loc in ["remote - california", "remote u.s.", "remote - seattle", "remote - nyc",
                    "remote-friendly (travel-required) | san francisco, ca", "remote - washington d.c."]:
            self.assertTrue(prefilter.location_ok(loc, us), loc)
        for loc in ["remote - india", "remote - denmark; remote - united kingdom", "london, uk",
                    "remote - latin america", "south america"]:
            self.assertFalse(prefilter.location_ok(loc, us), loc)

    def test_remote_stated_only_in_description(self):
        r = self.check(True, "description", remote=None, location="United States",
                       text="AWS IAM guardrails. This role is remote within the US.")
        self.check(False, "not remote", remote=None, location="United States", text="AWS IAM. Onsite in Austin.")

    def test_keywords_blocklist_and_applied(self):
        self.check(False, "excluded keyword", text="Clearance required. AWS.")
        self.check(False, "blocklist", company="Badco")
        self.check(False, "already applied", applied=[("acme", "staff security engineer")],
                   title="Staff Security Eng (Remote)")
        # A board slug ("acmeusa") is the same company as the folder's "Acme".
        self.check(False, "already applied", applied=[("acme", "staff security engineer")], company="acmeusa")
        self.check(False, "blocklist", company="badcousa")


class PrefilterRun(Base):
    def seed_postings(self):
        import _v2data as d
        for p in [posting(), posting(id="greenhouse:acme:2", title="Software Engineer")]:
            d.append_jsonl(self.ws / "data" / "postings.jsonl", p)

    def test_incremental_and_refilter_on_change(self):
        import _v2data as d
        import prefilter
        self.sources([], **FILTERS)
        self.seed_postings()
        self.assertEqual(prefilter.run(self.ws), {"evaluated": 2, "passed": 1})
        self.assertEqual(prefilter.run(self.ws), {"evaluated": 0, "passed": 0})
        self.sources([], **dict(FILTERS, title_include=[r"engineer"]))
        self.assertEqual(prefilter.run(self.ws), {"evaluated": 2, "passed": 1})
        self.assertEqual(len(d.read_jsonl(self.ws / "data" / "candidates.jsonl")), 4)

    def test_same_role_in_several_locations_counts_once(self):
        import _v2data as d
        import prefilter
        self.sources([], **FILTERS)
        for i, loc in enumerate(["Remote - US", "Remote - United States", "Remote, USA"]):
            d.append_jsonl(self.ws / "data" / "postings.jsonl", posting(id=f"greenhouse:acme:{i}", location=loc))
        self.assertEqual(prefilter.run(self.ws), {"evaluated": 3, "passed": 1})
        rows = d.read_jsonl(self.ws / "data" / "candidates.jsonl")
        self.assertTrue(any("same role as greenhouse:acme:0" in r["reasons"][0] for r in rows if not r["passed"]))

    def test_rules_version_change_rejudges(self):
        import prefilter
        self.sources([], **FILTERS)
        self.seed_postings()
        prefilter.run(self.ws)
        prefilter.RULES_VERSION += 1
        try:
            self.assertEqual(prefilter.run(self.ws)["evaluated"], 2)
        finally:
            prefilter.RULES_VERSION -= 1

    def test_closed_postings_fail(self):
        import _v2data as d
        import prefilter
        self.sources([], **FILTERS)
        self.seed_postings()
        d.write_json_atomic(self.ws / "data" / "postings-state.json", {"greenhouse:acme:1": {"closed": True}})
        prefilter.run(self.ws)
        rows = {r["posting_id"]: r for r in d.read_jsonl(self.ws / "data" / "candidates.jsonl")}
        self.assertFalse(rows["greenhouse:acme:1"]["passed"])
        self.assertIn("closed", rows["greenhouse:acme:1"]["reasons"][0])


WD = {"company": "Zillow", "ats": "workday", "slug": "zillow", "pod": "wd5", "site": "Zillow_Group_External"}
EF = {"company": "Netflix", "ats": "eightfold", "slug": "netflix", "host": "explore.jobs.netflix.net",
      "domain": "netflix.com"}


def wd_row(i, title, loc="Remote-USA"):
    return {"title": title, "externalPath": f"/job/{loc}/Role_P{i}", "locationsText": loc,
            "postedOn": "Posted Today", "bulletFields": [f"P{i}"]}


def wd_detail(i, title, remote="Remote", loc="Remote-USA"):
    return {"jobPostingInfo": {"title": title, "jobDescription": "<p>About the role: own <b>cloud</b> guardrails</p>",
                               "location": loc, "jobReqId": f"P{i}", "remoteType": remote}}


def ef_pos(i, title, loc="Remote, United States", wlo="onsite"):
    return {"id": i, "name": title, "location": loc, "locations": [loc], "work_location_option": wlo,
            "canonicalPositionUrl": f"https://evil.example/{i}", "job_description": ""}


class NewSources(Base):
    WD_BASE = "/wday/cxs/zillow/Zillow_Group_External"

    def setUp(self):
        super().setUp()
        import finder
        self._spacing, finder.EF_SPACING = finder.EF_SPACING, 0

    def tearDown(self):
        import finder
        finder.EF_SPACING = self._spacing
        super().tearDown()

    def wd_board(self, rows, details):
        def jobs(query, body):
            off = body["offset"]
            return {"total": len(rows) if off == 0 else 0, "jobPostings": rows[off:off + 20]}
        self.fake.boards[self.WD_BASE + "/jobs"] = jobs
        for r in rows:
            i = r["bulletFields"][0][1:]
            self.fake.boards[self.WD_BASE + r["externalPath"]] = details.get(i, 404)

    def test_workday_pages_and_reads_detail_only_for_wanted_titles(self):
        import finder
        rows = [wd_row(i, "Staff Security Engineer" if i < 3 else "Account Executive") for i in range(25)]
        self.wd_board(rows, {str(i): wd_detail(i, "Staff Security Engineer") for i in range(3)})
        self.sources([WD], title_include=[r"\bsecurity\b"])
        out = finder.run(self.ws)
        self.assertEqual(out["new"], 25)
        posts = {p["id"]: p for p in self.postings()}
        p = posts["workday:zillow:P1"]
        self.assertEqual((p["company"], p["remote"], p["ats"]), ("Zillow", True, "workday"))
        self.assertIn("cloud guardrails", p["text"])
        self.assertEqual(p["url"], "https://zillow.wd5.myworkdayjobs.com/Zillow_Group_External/job/Remote-USA/Role_P1")
        self.assertEqual(p["apply_url"], p["url"] + "/apply")
        self.assertEqual(posts["workday:zillow:P10"]["text"], "")
        details = [c for c in self.fake.calls if c[0] == "GET"]
        self.assertEqual(len(details), 3)       # only the three security titles were opened
        posted = [c[2] for c in self.fake.calls if c[0] == "POST"]
        self.assertEqual([b["offset"] for b in posted], [0, 20])
        self.assertEqual(posted[0]["searchText"], "security")

    def test_workday_hybrid_is_not_remote(self):
        import finder
        self.wd_board([wd_row(1, "Security Engineer", "Seattle")], {"1": wd_detail(1, "Security Engineer", "Hybrid", "Seattle")})
        self.sources([WD], title_include=["security"])
        finder.run(self.ws)
        self.assertIs(self.postings()[0]["remote"], False)

    def test_workday_path_that_leaves_the_site_is_dropped(self):
        import finder
        rows = [wd_row(1, "Security Engineer"), dict(wd_row(2, "Security Engineer"), externalPath="//evil.example/job/x"),
                dict(wd_row(3, "Security Engineer"), externalPath="/job/../../x")]
        self.wd_board(rows, {"1": wd_detail(1, "Security Engineer")})
        self.sources([WD], title_include=["security"])
        finder.run(self.ws)
        self.assertEqual([p["id"] for p in self.postings()], ["workday:zillow:P1"])

    def test_workday_bad_board_settings_fail_the_board(self):
        import finder
        self.sources([dict(WD, pod="wd5.evil.example/")], title_include=["security"])
        out = finder.run(self.ws)
        self.assertEqual(out["failed"], ["workday:zillow"])

    def test_eightfold_lists_reads_detail_and_builds_its_own_link(self):
        import finder
        pos = [ef_pos(100 + i, "Security Engineer 5" if i < 2 else "Content Producer") for i in range(12)]

        def jobs(query, body):
            from urllib.parse import parse_qs
            q = parse_qs(query)
            assert q["domain"] == ["netflix.com"]
            st = int(q["start"][0])
            return {"count": len(pos), "positions": pos[st:st + 10]}
        self.fake.boards["/api/apply/v2/jobs"] = jobs
        for i in range(2):
            self.fake.boards[f"/api/apply/v2/jobs/{100 + i}"] = dict(pos[i], job_description="<p>The role: detection</p>")
        self.sources([EF], title_include=["security"])
        out = finder.run(self.ws)
        self.assertEqual(out["new"], 12)
        p = {x["id"]: x for x in self.postings()}["eightfold:netflix:100"]
        self.assertEqual((p["remote"], p["company"]), (True, "Netflix"))
        self.assertIn("detection", p["text"])
        self.assertEqual(p["url"], "https://explore.jobs.netflix.net/careers/job/100")
        self.assertEqual(p["apply_url"], p["url"])

    def test_throttled_board_closes_nothing_and_is_reported(self):
        import finder
        import _v2data as d
        self.fake.boards["/api/apply/v2/jobs"] = {"count": 1, "positions": [ef_pos(1, "Security Engineer")]}
        self.fake.boards["/api/apply/v2/jobs/1"] = dict(ef_pos(1, "Security Engineer"), job_description="x")
        self.sources([EF], title_include=["security"])
        finder.run(self.ws, today="2026-10-20")
        self.fake.boards["/api/apply/v2/jobs"] = 429
        out = finder.run(self.ws, today="2026-10-21")
        self.assertEqual((out["throttled"], out["failed"], out["closed"]), (["eightfold:netflix"], [], 0))
        self.assertFalse(d.read_json(self.ws / "data" / "postings-state.json", {})["eightfold:netflix:1"]["closed"])
        self.assertEqual(d.read_json(self.ws / "data" / "board-health.json", {})["throttled"], ["eightfold:netflix"])


class ProbeCareers(unittest.TestCase):
    def test_reads_workday_eightfold_and_greenhouse_links(self):
        import finder
        html = ('<a href="https://zillow.wd5.myworkdayjobs.com/en-US/Zillow_Group_External/job/x">x</a>'
                '<a href="https://arcticwolf.wd1.myworkdayjobs.com/External">y</a>'
                '<script src="https://static.eightfold.ai/x.js"></script><script>{"domain": "netflix.com"}</script>'
                '<a href="https://boards.greenhouse.io/cerebral/jobs/1">z</a>')
        got = finder.boards_from_page(html, "https://explore.jobs.netflix.net/careers", "Acme")
        self.assertIn({"company": "Acme", "ats": "workday", "slug": "zillow", "pod": "wd5", "site": "Zillow_Group_External"}, got)
        self.assertIn({"company": "Acme", "ats": "workday", "slug": "arcticwolf", "pod": "wd1", "site": "External"}, got)
        self.assertIn({"company": "Acme", "ats": "greenhouse", "slug": "cerebral"}, got)
        self.assertIn({"company": "Acme", "ats": "eightfold", "slug": "netflix", "host": "explore.jobs.netflix.net",
                       "domain": "netflix.com"}, got)

    def test_eightfold_needs_the_eightfold_api_shape(self):
        import finder
        self.assertEqual(finder.boards_from_page('{"domain": "x.com"}', "https://www.example.com/careers", "X"), [])


if __name__ == "__main__":
    unittest.main()
