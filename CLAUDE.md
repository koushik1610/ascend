# CLAUDE.md — S.P.I.D.E.R. (project instructions)

You are running inside the **S.P.I.D.E.R.** repo (*Strategic Profile Intelligence & Direct Employment
Routing*) — a reusable, AI-driven job-search system that runs end-to-end in Claude Code for ONE user
at a time.

## When the user says "Run SPIDER" / `/spider` / "start the job search"
Follow **`prompts/00-orchestrator.md`** exactly. Begin with the intake interview — do not pre-explain
the whole system; ask the questions, then build the workspace and run the phases with checkpoints.

If they say "Run SPIDER Phase N" (or name a phase), jump to that phase's prompt in `prompts/`,
re-reading `workspace/<name>/intake.md` first for context.

## The pipeline
`prompts/00-orchestrator.md` drives phases 1–7 (`prompts/01…07`). Outputs go to
`workspace/<name>/`. The orchestrator pauses for review after each phase.

## Binding rules (always)
- **Person-agnostic.** Nothing about any previous user (the repo author included) carries into a run.
  Everything traces to THIS user's LinkedIn export, resume, or intake answers.
- **Honesty gates (absolute).** Never fabricate experience, metrics, titles, certs, skills, or referral
  contacts. Missing number → suggest what to measure, never invent. Conviction essays → honest outlines
  only; the user writes the prose. See `reference/number-and-honesty-policy.md`.
- **Selection, not invention.** Once `master-resume.md` exists, per-job resumes are *selected* from it.
  A missing bullet is a "MASTER GAP" note (fix the master), never fiction on the derivative.
- **Privacy.** All personal output goes under `workspace/<name>/` only. Never write personal data
  elsewhere; never suggest committing the workspace; never `git add` anything under `workspace/`.
- **Verify before "done."** Each phase has a verification step — show evidence (paths, counts, grep),
  don't just assert.
- **Field-aware.** Adapt coding/assessment prep, evidence types, and keywords to the user's actual
  field via the intake answers.

## Reference (read before phases 2–6)
`reference/resume-writing-rules.md` · `reference/ats-and-keywords.md` ·
`reference/number-and-honesty-policy.md` · `reference/interview-prep-framework.md`.
Templates: `templates/` (job-folder `_TEMPLATE.md` is the binding 8-file spec).

## Git
The repo ships the SYSTEM only. **Never commit anyone's personal data or generated output** — `.gitignore`
blocks `workspace/`, resumes, and LinkedIn exports as a backstop. If asked to commit, stage only
system files (prompts/templates/reference/docs) and confirm nothing under `workspace/` is staged.
