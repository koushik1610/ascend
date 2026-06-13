# Phase 7 — Navigator → `start-here.html`

**Goal:** build the single front door to the user's entire job-search system — a polished HTML
dashboard that links to everything and shows live status at a glance. This is the file the user opens
every day.

**Read first:** everything produced so far in `workspace/<name>/` (linkedin-analysis.html,
resume-audit.md, master-resume.md, job-queue.md, jobs/*, interview-packet/*) and
`../templates/start-here.template.html`.

---

## What it must contain
1. **Header** — the user's name, target role(s), and a one-line positioning summary (from the master
   resume §2). Today's date.
2. **Pipeline status** — a visual of the 7 phases with completion state, each linking to its output
   (the LinkedIn analysis HTML, the resume audit, the master resume, the job queue, the packet).
3. **Pre-application blockers** — the checklist from `job-queue.md` (the things to do before applying
   to anything), shown prominently with check states.
4. **The job board** — a card or table for all jobs, each linking into its `jobs/<folder>/` (link the
   folder and the key files: resume.md, prep-doc.md, application-log.md). Show per-job: rank, company,
   title, location/mode, comp, ATS, and **application status** (pulled from each `application-log.md`
   — not-started / referral-sought / applied / screening / onsite / offer / rejected). Make status
   filterable or at least color-coded.
5. **Funnel** — a simple count strip: jobs identified → applied → screening → onsite → offers.
6. **Interview packet** — links to each packet file.
7. **This week** — the top 3–5 next actions (highest-leverage first: usually a LinkedIn next-step, the
   biggest resume fix, and the #1 job's referral path).
8. **How to use this system** — a short "what to do" note + a pointer back to the repo README for the
   maintenance loop (re-run Phase 4 weekly; update application-logs as you go).

## Build requirements
- **Single self-contained HTML**, opens offline. Inline CSS. Any JS inline. Relative links to the
  workspace files so they open from the same folder.
- **Premium look**, consistent with `linkedin-analysis.html`: dark theme, clean type, stat cards,
  status color-coding, responsive. Real text, accessible contrast, semantic headings.
- **Links must resolve** relative to `workspace/<name>/start-here.html` (e.g.,
  `./jobs/01-acme-staff-engineer/resume.md`, `./linkedin-analysis.html`).
- Because `application-log.md` files change as the user applies, include a one-line note on how to
  refresh status (re-run this phase, or hand-edit the status data block — make the data a clearly
  marked inline JS object the user can edit without touching layout).

## Verify
- Every link points to a file that exists in the workspace (check paths).
- Job count on the board equals the queue count.
- Status values come from the real `application-log.md` files (or default to "not started").
- Opens cleanly in a browser; no broken markup or dead relative links.

## Final handoff (orchestrator does this)
This is the last phase. Tell the user: open `workspace/<name>/start-here.html` — it's the front door
to everything. Recap the top 3 actions and the maintenance loop. Confirm nothing personal was
committed to git.
