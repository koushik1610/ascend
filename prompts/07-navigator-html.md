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
2. **This week — the action loop (TOP of page).** This is the point of the dashboard: drive *action*,
   not reading. Set `weekly.applyTarget` / `referralTarget` (sensible defaults 3 / 2) so the two
   target cards render, plus the top 3–5 highest-leverage actions (send apply pack #1, ask the referral
   at company X, the biggest LinkedIn fix). The system optimizes applications-sent + referrals-asked,
   not documents-produced.
3. **Scoreboard** — the funnel: identified → referrals → applied → screening → onsite → offers. The
   leading indicators, up high, before any document links.
4. **Pipeline status** — the phases with completion state, each linking to its output.
5. **Pre-application blockers** — the checklist from `job-queue.md`, with check states.
6. **Deadlines & follow-ups** — set each job's `deadline` / `nextAction` in the JSON (read from its
   `application-log.md`).
7. **The job board** — all jobs, each linking into `jobs/<folder>/` (resume.md, application-log.md;
   prep links appear once a job's prep pack is built). Show rank, company, title, **Fit Score (0–100
   from `job-queue.md`)**, location, comp, ATS, and **status read from each `application-log.md`** — `application-log.md` is the single source of
   truth for status; Phase 7 copies it into the JSON (don't let the two drift — re-read on refresh).
8. **Interview packet** — links to each packet file.
9. **How to use this system** — a short note + pointer to the README maintenance loop ("Run SPIDER
   maintenance" weekly; "/spider prep \<NN>" when a screen books; update application-logs as you go).

## Build requirements
- Start from `../templates/start-here.template.html`. Fill the **`<script type="application/json"
  id="spider-data">` block** (strict JSON — double-quoted, no comments, no trailing commas); the page
  renders from it via `JSON.parse`. Per job you may set `status`, and optionally `deadline`
  (`YYYY-MM-DD`) and `nextAction` (these surface in the Deadlines & Follow-ups strip). **Validate the
  JSON parses** before declaring done — a syntax error blanks the dashboard. Don't edit the render JS.
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
