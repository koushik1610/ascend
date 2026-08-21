---
description: Start the Ascend job-search pipeline (intake interview → LinkedIn analysis → master resume (audit folded in) → triaged + ranked jobs → interview packet → apply packs → navigator)
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
  then render via LaTeX (`tools/render_resume.py`) to a `.tex` plus the one-page ATS-safe PDF. Falls
  back to the filled builder HTML when no TeX engine is installed.
- **`build-resume`** → open the standalone résumé builder (`templates/resume-builder.template.html`,
  also served at `/resume-builder` when the UI server runs) for ad-hoc résumé creation/editing: Import
  an existing `resume.json`, or build from scratch and Create PDF. Not tied to any job folder.
- **`score <paste JD>`** → report the **0–100 Fit Score** (Phase 4 rubric: skills/seniority/comp/
  location, 0–25 each, with excitement reported separately as a veto/tie-break + reasoning) and the missing-but-claimable keywords; build nothing.
- **`export-docx <company>`** → also emit an ATS-safe Word copy from the same `resume.md` via the
  allow-listed `pandoc` (`prompts/08-export-pdf.md` → DOCX section). The PDF stays the default.
- **`aggregate`** → **ATS Job Aggregation** (`prompts/14-ats-aggregation.md`): pull currently-open roles
  straight from Greenhouse/Lever/Ashby public JSON + RSS for target companies; de-dupe + Fit-score into
  the queue.
- **`crm`** → **Networking CRM** (`prompts/15-network-crm.md`): keep warm referral relationships alive —
  a tracker of contacts, touchpoints, and due follow-ups, seeded from `network-map.md`.
- **`mine`** → **Achievement-Mining Interview** (`prompts/16-achievement-mining.md`): a guided interview
  that extracts real, quantified accomplishments into new `master-resume.md` entries (extract, never invent).
- **`drill [NN|track]`** → **"Interview Me" Drill** (`prompts/17-interview-me.md`): a live mock interview
  — one question at a time with rubric feedback grounded in the user's real stories.
- **`degenericize [file]`** → **De-Genericizer** (`prompts/18-degenericizer.md`): a specificity pass that
  replaces generic/AI-flavored text with the user's real evidence (tightens what's true; adds nothing).
- **`negotiate [company]`** → **Salary Negotiation Studio** (`prompts/19-salary-studio.md`): a grounded
  per-offer plan — researched market anchors, the user's three numbers, and rehearsed scripts (no
  dishonest tactics).

**Running the search week to week (these are what keep it alive past week three):**
- **`log <NN> <status>`** → record what actually happened, in one command. Runs
  `python3 tools/pipeline.py log workspace/<name> <NN> <status> [--on DATE] [--note "…"]`. Statuses:
  `queued applied responded screen onsite offer rejected move-on`. It rewrites only the fenced STATE
  block in that job's `application-log.md` and appends to the append-only ledger. Every other number
  in the system reads from this, so it is the one command worth making a habit.
- **`week`** → **The Weekly Review** (`prompts/20-weekly-review.md`): the 15-minute heartbeat — count
  what you did, capture what moved, calibrate the funnel with denominators, check the lead floor,
  decide exactly one thing. A search dies from attrition, not from a bad résumé.
- **`rejected <NN>`** → **Rejection Protocol** (`prompts/21-rejection-protocol.md`): capture what was
  actually said, verbatim, record the stage it died at, and activate a named replacement target.
  90 seconds. Never asks the user to theorize about why.
- **`titles`** → **Adjacent Titles** (`prompts/22-adjacent-titles.md`): job titles the user's own
  evidence already supports, on three labeled axes (lateral / stretch / pivot), each citing master
  entry IDs, written into their targeting only on confirmation.

Honor the binding rules in `CLAUDE.md`: person-agnostic, honesty gates absolute, selection-not-invention,
all personal output under `workspace/` only, never commit personal data. Update `.ascend-state.json`
after each phase and each job folder so the run is always resumable.
