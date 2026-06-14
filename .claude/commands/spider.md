---
description: Start the S.P.I.D.E.R. job-search pipeline (intake interview → LinkedIn analysis → resume audit → master resume → 15+ jobs → per-job folders → navigator)
---

Run S.P.I.D.E.R. Follow `prompts/00-orchestrator.md` from the top: begin with the intake interview
(name, LinkedIn export location, resume location, target roles/companies/location/comp, differentiators,
honest gaps, any sanitization needs), reflect back an Intake Summary for confirmation, then build
`workspace/<name>/` and drive phases 1–7, pausing at a checkpoint after each.

`$ARGUMENTS` may select a specific operation instead of a full run — read `workspace/<name>/intake.md`
and `workspace/<name>/.spider-state.json` first, then:
- **`Phase N`** (or a phase name) → run that phase directly from its `prompts/0N-*.md` file.
- **`resume`** → read `.spider-state.json`, tell the user where it stopped, and continue from the first
  incomplete unit (skip completed phases/folders).
- **`job add <url-or-description>`** → fetch/verify the posting, append it to `job-queue.md`, build its
  **CORE apply pack** per `prompts/05-job-folders.md`. Don't rebuild the queue.
- **`prep <NN>`** → build the **deep interview-prep pack** for that job per `prompts/10-deep-prep.md`
  (run when a screen is booked) + offer the mock-interview drill.
- **`today`** → the day's action list: apply packs to send, referrals to ask, follow-ups due.
- **`job rebuild <NN>`** → regenerate that job folder, preserving its `application-log.md` status.
- **`refresh`** / **`maintenance`** → run `prompts/09-maintenance.md` (weekly job-diff, comp research,
  outreach cadence, retro digest).
- **`export <company>`** → run `prompts/08-export-pdf.md` for that job's resume.
- **`score <paste JD>`** → run the master-resume §9 tailoring protocol against the JD; report the ATS
  gap score + missing-but-claimable keywords; build nothing.

Honor the binding rules in `CLAUDE.md`: person-agnostic, honesty gates absolute, selection-not-invention,
all personal output under `workspace/` only, never commit personal data. Update `.spider-state.json`
after each phase and each job folder so the run is always resumable.
