#!/usr/bin/env python3
"""grade_run.py — the v1.0 run rubric, executable (stdlib only).

`docs/ROADMAP.md` gates the 1.0 tag on real end-to-end runs graded against a four-part rubric:
honesty, grounding, completeness, privacy. That rubric was prose, so grading it meant a human
re-reading a whole workspace and deciding — which is exactly how the 2026-07-01 run got signed off
as passing an honesty check that (as the 2026-08-20 council found) could not actually have run.

This makes the rubric mechanical. It grades a real workspace, and CI grades the committed sample with
the same code, so the fixture and the gate can never drift apart.

  python3 tools/grade_run.py workspace/<name>          # grade a real run
  python3 tools/grade_run.py examples/sample-run       # what CI does
  python3 tools/grade_run.py <dir> --json

What it can and cannot see, stated plainly so nobody over-trusts a PASS:
  - It CAN verify that every cited master ID exists, that sendables pass the language and
    never-publish gates, that MASTER GAPs are declared rather than silently filled, that the expected
    artifacts exist, and that nothing personal is git-tracked.
  - It CANNOT verify that a claim is TRUE. "Selection, not invention" is checkable; "this metric is
    real" is not. A PASS means no detectable fiction, never "verified honest".

Exit: 0 all sections pass · 1 any FAIL · 2 usage error.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MASTER_ID = re.compile(r"\b([EPMSD]\d{1,3}[a-z]?)\b")
DECL_HEAD = re.compile(r"^#{2,4}\s+([EPMSD]\d{1,3}[a-z]?)\b")
DECL_ROW = re.compile(r"^\|\s*([EPMSD]\d{1,3}[a-z]?)\s*\|")
FICTION = re.compile(r"\b(TODO|FIXME|TBD|XXX|made[- ]up|fabricat\w*|lorem ipsum|placeholder bullet)\b", re.I)
SENDABLE = re.compile(r"^(resume\.md|outreach\.md|signal\.md|answer-bank\.md|answer-sheet\.md|"
                      r"resume\.json|master-resume\.json)$")


class Grade:
    def __init__(self):
        self.rows = []

    def add(self, section, name, ok, detail="", fatal=True):
        self.rows.append({"section": section, "check": name, "ok": bool(ok),
                          "detail": detail, "fatal": fatal})

    def failed(self):
        return [r for r in self.rows if not r["ok"] and r["fatal"]]

    def report(self, as_json=False):
        if as_json:
            print(json.dumps({"rows": self.rows, "pass": not self.failed()}, indent=2))
            return
        cur = None
        for r in self.rows:
            if r["section"] != cur:
                cur = r["section"]
                print(f"\n{cur}")
            mark = "PASS" if r["ok"] else ("FAIL" if r["fatal"] else "warn")
            line = f"  [{mark}] {r['check']}"
            if r["detail"] and not r["ok"]:
                line += f"\n         {r['detail']}"
            print(line)
        bad = self.failed()
        print("\n" + ("GRADE: PASS (no detectable fiction; not a claim that content is true)"
                      if not bad else f"GRADE: FAIL ({len(bad)} blocking)"))


def parse_master_ids(ws):
    m = ws / "master-resume.md"
    if not m.is_file():
        return set()
    ids = set()
    for line in m.read_text(encoding="utf-8").splitlines():
        for rx, target in ((DECL_HEAD, line), (DECL_ROW, line.strip())):
            hit = rx.match(target)
            if hit:
                ids.add(hit.group(1))
    return ids


def delta_block(text):
    out, inside = [], False
    for line in text.splitlines():
        s = line.strip()
        m = re.search(r"\bDELTA LOG\b", s, re.I)
        if m:
            inside, _ = True, out.append(s[m.end():])
            continue
        if inside:
            if s.startswith("-->") or s.startswith("---") or s.startswith("#"):
                break
            out.append(s)
    return "\n".join(out)


def grade(ws, g):
    jobs = sorted((ws / "jobs").glob("*/")) if (ws / "jobs").is_dir() else []
    master_ids = parse_master_ids(ws)

    # ── HONESTY: selection, not invention ───────────────────────────────────
    S = "HONESTY — selection, not invention"
    g.add(S, "master-resume.md exists and declares entry IDs", bool(master_ids),
          "no master résumé, or it declares no E#/P#/M# entries to select from")
    for job in jobs:
        r = job / "resume.md"
        if not r.is_file():
            continue
        txt = r.read_text(encoding="utf-8")
        name = job.name
        has_delta = bool(re.search(r"\bDELTA LOG\b", txt, re.I))
        g.add(S, f"{name}: carries a DELTA LOG", has_delta)
        if has_delta and master_ids:
            cited = set(MASTER_ID.findall(delta_block(txt)))
            g.add(S, f"{name}: DELTA LOG cites master IDs", bool(cited))
            unknown = sorted(cited - master_ids)
            g.add(S, f"{name}: every cited ID exists in the master", not unknown,
                  f"cites {', '.join(unknown)}, which the master never declares "
                  "(the signature of an invented bullet)")
        body = re.sub(r"<!--.*?-->", "", txt, flags=re.S)
        g.add(S, f"{name}: no fiction marker in the body", not FICTION.search(body))

    # ── GROUNDING: gaps are declared, never quietly filled ──────────────────
    S = "GROUNDING — gaps declared, not filled"
    for job in jobs:
        r = job / "resume.md"
        if r.is_file():
            g.add(S, f"{job.name}: declares MASTER GAP handling",
                  "MASTER GAP" in r.read_text(encoding="utf-8").upper(),
                  "a résumé with no MASTER GAPS line has not stated whether any needed bullet "
                  "was missing. Silence is not the same as 'none'.")

    # ── LANGUAGE + NEVER-PUBLISH: reuse the real gate, don't reimplement it ──
    S = "SENDABLES — language + never-publish gate"
    sendables = [p for p in ws.rglob("*") if p.is_file() and SENDABLE.match(p.name)]
    g.add(S, "found sendable artifacts to grade", bool(sendables))
    if sendables:
        cfg = ws / "lint-config.json"
        cmd = [sys.executable, str(REPO / "tools/lint_artifacts.py")] + [str(p) for p in sendables]
        if cfg.is_file():
            cmd += ["--config", str(cfg)]
        res = subprocess.run(cmd, capture_output=True, text=True)
        findings = [l for l in res.stdout.splitlines() if re.search(r":\d+: \[", l)]
        g.add(S, f"lint_artifacts is clean over {len(sendables)} sendable(s)", res.returncode == 0,
              "\n         ".join(findings[:6]) or res.stdout.strip()[-200:])
        g.add(S, "a lint-config.json exists (user's never-publish list)", cfg.is_file(),
              "without it the forbidden-number and retracted-claim checks have nothing to enforce",
              fatal=False)

    # ── COMPLETENESS: the run produced what it claims to ────────────────────
    S = "COMPLETENESS"
    g.add(S, "job queue exists", (ws / "job-queue.md").is_file())
    g.add(S, "interview packet exists", (ws / "interview-packet").is_dir())
    g.add(S, "at least one CORE apply pack", bool(jobs))
    for job in jobs:
        missing = [f for f in ("resume.md", "outreach.md", "application-log.md")
                   if not (job / f).is_file()]
        g.add(S, f"{job.name}: CORE pack complete", not missing, "missing: " + ", ".join(missing))
    g.add(S, "a rendered résumé PDF exists",
          any(ws.rglob("*.pdf")), "the pack ships markdown but nothing submittable", fatal=False)

    # ── PRIVACY: nothing personal is tracked ────────────────────────────────
    S = "PRIVACY"
    if ws.resolve().is_relative_to((REPO / "workspace").resolve()):
        probe = ws / "master-resume.md"
        ignored = subprocess.run(["git", "-c", "core.ignorecase=false", "check-ignore", "-q",
                                  str(probe.relative_to(REPO))], cwd=REPO).returncode == 0
        g.add(S, "the workspace is gitignored", ignored,
              "personal output is NOT ignored by git. Nothing may be committed from here.")
    else:
        g.add(S, "committed fixture is deliberately tracked (not a real workspace)", True)
        txt = " ".join(p.read_text(encoding="utf-8", errors="ignore")
                       for p in ws.rglob("*.md") if p.is_file())
        g.add(S, "committed fixture is labelled fictional", "FICTIONAL SAMPLE" in txt,
              "a tracked example must say it is invented, or a reader will take it for a real person")


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 2
    ws = Path(args[0]).resolve()
    if not ws.is_dir():
        print(f"grade_run: not a directory: {ws}", file=sys.stderr)
        return 2
    g = Grade()
    print(f"Grading {ws.relative_to(REPO) if ws.is_relative_to(REPO) else ws} "
          "against the v1.0 run rubric")
    grade(ws, g)
    g.report(as_json="--json" in argv)
    return 1 if g.failed() else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
