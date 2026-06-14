# Contributing to S.P.I.D.E.R.

Thanks for wanting to make this better. S.P.I.D.E.R. is a prompt-and-template system, not a codebase —
contributions are mostly Markdown (prompts, templates, reference rules) and the occasional HTML/JS in
the two dashboard templates.

## The one hard rule: never commit personal data
This is a privacy-first project. **No real resumes, LinkedIn exports, names, or generated runs go into
git — ever.** All of that lives in `workspace/` (gitignored). If you add an example, it must be **100%
fictional** and go under `examples/`. Before any PR, run:

```bash
git status --porcelain     # nothing personal should be staged
git check-ignore workspace/you/master-resume.md   # should print the path (ignored)
```

If you change `.gitignore`, prove it still ignores personal data AND still tracks the system files
(`git check-ignore` on a few of each). The gitignore is load-bearing — test it.

## Good first contributions
- **Field packs:** the system is field-agnostic but examples lean tech. A worked sample or
  reference notes for design, PM, marketing, healthcare, finance, trades, academia, etc.
- **ATS / interview intel:** keep `reference/ats-and-keywords.md` and
  `reference/interview-prep-framework.md` current as the market shifts.
- **Dashboard polish:** improve `templates/linkedin-analysis.template.html` /
  `templates/start-here.template.html` (keep them self-contained, offline, no CDN, accessible).
- **Non-tech onboarding:** improve `docs/SETUP.md`, especially Windows.
- **Bug fixes:** prompts that are ambiguous or produce inconsistent results.

## Principles to preserve (don't regress these)
1. **Honesty gates** — nothing fabricated; conviction essays stay outlines (`reference/number-and-honesty-policy.md`).
2. **Selection, not invention** — resumes are selected from the master; missing bullet = MASTER GAP note.
3. **Self-contained dashboards** — no external/CDN calls; they must open offline.
4. **Field-agnostic** — don't hard-code software-engineering assumptions into shared files.
5. **Person-agnostic** — no real person's details in committed files.

## Workflow
1. Fork, branch, make the change.
2. **Run the smoke tests:** `python3 tests/smoke.py` (no installs — stdlib + git). They cover the server
   security, dashboard JSON, the gitignore privacy matrix, and repo cross-references; CI runs the same.
3. If you touched a dashboard template, also `node --check` its render `<script>`.
4. Update `CHANGELOG.md` under "Unreleased."
4. Open a PR describing what changed and which principle(s) it touches. Use the PR template.

## Reporting issues
Use the issue templates. For prompt bugs, include the phase, what you asked, and what it produced
(with any personal data removed).
