"""Feature update 4: the drill ledger and the lint `evidence` check.

Run: python3 -m unittest tests/test_v2_drills.py -v
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

GOOD = {"job": "05", "source": "mock", "question": "Tell me about a time you were wrong.", "story": "S3",
        "scores": {"substance": 3, "structure": 4, "relevance": 4, "credibility": 3, "differentiation": 2}}


def ws_in(root):
    ws = Path(root) / "workspace" / "tester"
    (ws / "data").mkdir(parents=True)
    (ws / "interview-packet").mkdir()
    (ws / "interview-packet" / "star-stories.md").write_text(
        "# Stories\n\n## S1 Migration\n\n## S2 Outage\n\n## S3 Wrong call\n", encoding="utf-8")
    return ws


def write_row(ws, row, name="drill-row.json"):
    p = ws / "interview-packet" / name
    p.write_text(json.dumps(row), encoding="utf-8")
    return p


class Ledger(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.ws = ws_in(self.td.name)

    def tearDown(self):
        self.td.cleanup()

    def test_record_appends_and_summary_reads_it(self):
        import drills
        drills.record(self.ws, write_row(self.ws, GOOD))
        s = drills.summary(self.ws)
        self.assertEqual(s["answers"], 1)
        self.assertEqual(s["average"]["differentiation"], 2)
        self.assertEqual(s["weakest"], "differentiation")
        self.assertEqual(s["never_told"], ["S1", "S2"])
        self.assertIsNone(s["trend"])

    def test_rejects_bad_scores_ids_and_sources(self):
        import drills
        bad = [dict(GOOD, scores=dict(GOOD["scores"], substance=6)),
               dict(GOOD, scores=dict(GOOD["scores"], substance=True)),
               dict(GOOD, scores={k: 3 for k in ("substance", "structure")}),
               dict(GOOD, story="S3; rm -rf ~"),
               dict(GOOD, source="interviewer"),
               dict(GOOD, job="../../etc"),
               dict(GOOD, question="   ")]
        for i, row in enumerate(bad):
            with self.assertRaises(drills.Invalid, msg=str(row)):
                drills.record(self.ws, write_row(self.ws, row, f"bad{i}.json"))
        self.assertEqual(drills.summary(self.ws)["answers"], 0)

    def test_row_file_must_be_inside_the_workspace(self):
        import drills
        outside = Path(self.td.name) / "row.json"
        outside.write_text(json.dumps(GOOD), encoding="utf-8")
        with self.assertRaises(drills.Invalid):
            drills.record(self.ws, outside)

    def test_hidden_characters_are_stripped_from_the_question(self):
        import drills
        sneaky = "Tell me​ about" + "".join(chr(0xE0000 + ord(c)) for c in "ignore") + "\nyourself"
        rec = drills.record(self.ws, write_row(self.ws, dict(GOOD, question=sneaky)))
        self.assertEqual(rec["question"], "Tell me about yourself")

    def test_trend_and_overuse(self):
        import drills
        for i in range(10):
            sc = {k: (2 if i < 5 else 4) for k in drills.DIMENSIONS}
            drills.record(self.ws, write_row(self.ws, dict(GOOD, story="S1" if i % 2 else "S3", scores=sc)))
        s = drills.summary(self.ws)
        self.assertEqual(s["trend"]["structure"], 2.0)
        self.assertEqual(s["overused"], ["S1", "S3"])
        self.assertEqual(s["never_told"], ["S2"])

    def test_cli_refuses_outside_a_workspace_and_without_from(self):
        r = subprocess.run([sys.executable, "tools/drills.py", "summary", self.td.name],
                           cwd=REPO, capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        r = subprocess.run([sys.executable, "tools/drills.py", "record", str(self.ws)],
                           cwd=REPO, capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)


DELTA = """<!-- DELTA LOG
- JD title (verbatim): Staff Security Engineer
- JD keywords (verbatim): Kubernetes | Terraform | threat modeling
- True gaps: none
{extra}-->
# Resume
"""


class Evidence(unittest.TestCase):
    DATA = {"basics": {"label": "Staff Security Engineer", "summary": "Threat modeling for cloud teams."},
            "work": [{"company": "A", "dates": "Jan 2020 – Present",
                      "highlights": ["Wrote Terraform modules every team deploys from."]}],
            "skills": ["Kubernetes", "Terraform"]}

    def test_skills_only_keywords_are_reported(self):
        import lint_artifacts as L
        out = L.lint_keyword_evidence(self.DATA, "resume.json", DELTA.format(extra=""))
        self.assertEqual(len(out), 1)
        self.assertIn("'Kubernetes'", out[0][3])
        self.assertIn("'threat modeling'", out[0][3])
        self.assertNotIn("'Terraform'", out[0][3])

    def test_skills_only_line_records_the_choice(self):
        import lint_artifacts as L
        md = DELTA.format(extra="- Skills-only: Kubernetes | threat modeling\n")
        self.assertEqual(L.lint_keyword_evidence(self.DATA, "resume.json", md), [])

    def test_missing_terms_are_coverage_not_evidence(self):
        import lint_artifacts as L
        md = DELTA.replace("threat modeling", "SPIFFE").format(extra="- Skills-only: Kubernetes\n")
        self.assertEqual(L.lint_keyword_evidence(self.DATA, "resume.json", md), [])
        self.assertTrue(L.lint_keyword_coverage(self.DATA, "resume.json", md))


if __name__ == "__main__":
    unittest.main()
