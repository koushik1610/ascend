---
description: Start the Ascend job-search pipeline (intake interview → LinkedIn analysis → resume audit → master resume → 15+ jobs → per-job folders → navigator)
---

Run Ascend Follow `prompts/00-orchestrator.md` from the top: begin with the intake interview
(name, LinkedIn export location, resume location, target roles/companies/location/comp, differentiators,
honest gaps, any sanitization needs), reflect back an Intake Summary for confirmation, then build
`workspace/<name>/` and drive phases 1–7, pausing at a checkpoint after each.

`$ARGUMENTS` may select a specific operation instead of a full run — read `workspace/<name>/intake.md`
and `workspace/<name>/.ascend-state.json` first, then:
- **`Phase N`** (or a phase name) → run that phase directly from its `prompts/0N-*.md` file.
- **`resume`** → read `.ascend-state.json`, tell the user where it stopped, and continue from the first
  incomplete unit (skip completed phases/folders).
- **`job add <url-or-description>`** → fetch/verify the posting, append it to `job-queue.md`, build its
  **CORE apply pack** per `prompts/05-job-folders.md`. Don't rebuild the queue.
- **`prep <NN>`** → build the **deep interview-prep pack** for that job per `prompts/10-deep-prep.md`
  (run when a screen is booked) + offer the mock-interview drill.
- **`network`** → **Warm-Network Mapper** (`prompts/11-network-map.md`): warm referral paths per target
  company from the user's own `Connections.csv`.
- **`answers`** → **Application Answer Sheet** (`prompts/12-answer-sheet.md`): reusable varied answers +
  per-job custom screeners.
- **`today`** → the **Daily Briefing** (`prompts/13-daily-briefing.md`): today's 3 actions +
  ghost-detector follow-ups, drafted.
- **`job rebuild <NN>`** → regenerate that job folder, preserving its `application-log.md` status.
- **`refresh`** / **`maintenance`** → run `prompts/09-maintenance.md` (weekly job-diff, comp research,
  outreach cadence, retro digest).
- **`export <company>`** → run `prompts/08-export-pdf.md` for that job's resume: emit `resume.json`,
  the filled builder HTML, and the auto-rendered one-page ATS-safe PDF.
- **`build-resume`** → open the standalone résumé builder (`templates/resume-builder.template.html`,
  also served at `/resume-builder` when the UI server runs) for ad-hoc résumé creation/editing: Import
  an existing `resume.json`, or build from scratch and Create PDF. Not tied to any job folder.
- **`score <paste JD>`** → report the **0–100 Fit Score** (Phase 4 rubric: skills/seniority/comp/
  location/excitement + reasoning) and the missing-but-claimable keywords; build nothing.

Honor the binding rules in `CLAUDE.md`: person-agnostic, honesty gates absolute, selection-not-invention,
all personal output under `workspace/` only, never commit personal data. Update `.ascend-state.json`
after each phase and each job folder so the run is always resumable.
