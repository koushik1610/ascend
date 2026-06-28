# WORKFLOW.md — how people actually use S.P.I.D.E.R.

This is the **journey index**: who the user is, what they start with, and the path they take for
each way of using SPIDER. It complements the mechanics — it does not restate them. The canonical
**run order, phases, and state machine live in [`prompts/00-orchestrator.md`](prompts/00-orchestrator.md)**;
the canonical **op list lives in [`.claude/commands/spider.md`](.claude/commands/spider.md)**. When a
journey below says "runs the pipeline," that prompt is the source of truth for *how*.

Each journey is written as: **the user → what they start with → the trigger → the path → what they
end with**. If a journey's trigger has a precondition (a built workspace, a booked screen), it's
called out — that's the difference between a step that works and one that errors.

---

## What every user starts with

The shared baseline. A journey only lists what it needs *beyond* this.

- **Claude Code** open in a clone of this repo, with a Claude subscription / API access (it runs on
  tokens).
- A **LinkedIn data export** — *LinkedIn → Settings → Data Privacy → Get a copy of your data → "The
  works"* → a zip → unzipped to a folder. (The `Connections.csv` inside it powers the network map.)
- **Optionally** a current resume (PDF / .docx / .md). No resume? SPIDER builds the master from the
  LinkedIn export + intake answers instead.
- A rough idea of **target roles** (the title you want recruiters to search for) and seniority.

Everything personal lands in **`workspace/<your-name>/`**, which is gitignored. That folder *is* your
run — delete it to wipe yourself entirely; run for a friend and they get their own.

---

## The journey map

```
  SETUP (once)                    DAILY / WEEKLY LOOP (forever)        PER-OPPORTUNITY (as they arise)
  ───────────                     ────────────────────────────        ──────────────────────────────
  J1  Full run        ─────────▶  J6  Today's action loop     ┌─────▶ J9   Add a job you found
  J2  Cheap sampler   ─┐          J7  Weekly maintenance      │       J10  Prep for a booked screen
  J3  Graphical (UI)  ─┤          J8  Network refresh         │       J11  Score a JD (no files)
  J4  Resume a run    ─┘                                      │       J12  Export a resume to PDF
  J5  Non-coder setup                                         │       J12b Build a résumé (ad-hoc)
                                                              └────── (each updates the dashboard)

  META: J13  Run it for someone else / wipe a person
```

The shape: **one setup**, then you live in the **loop** and react to **opportunities**. The dashboard
(`start-here.html`) is the home base you return to between journeys.

---

## Setup journeys (you do one of these once)

### J1 — The full run *(the main path)*
> **As** someone starting a real job search, **I want** my whole search set up in one pass, **so that**
> I open one dashboard and start applying instead of staring at a blank resume.

- **Starts with:** the baseline + 30–60 min of attention across check-ins (the run itself is 1–3+ hrs
  of Claude working).
- **Trigger:** `/spider` (or *"Run SPIDER"*).
- **Path:** intake interview (name, data paths, targets, gaps, sanitization rules) → confirms an
  Intake Summary → builds `workspace/<name>/` → runs phases **1 → 3 → 4 → 6 → 5 → 7**, checkpointing
  after each so you can stop, skip, or redirect.
- **Ends with:** `linkedin-analysis.html`, `master-resume.md`, a 15+ job `job-queue.md` (each link
  marked verified/unverified), a thin `interview-packet/`, CORE apply packs for the **top 3–5 jobs you
  commit to**, and `start-here.html` — **open this first**. ~25–30 files, not ~100.
- **Implemented by:** [`prompts/00-orchestrator.md`](prompts/00-orchestrator.md) → phases 01, 03, 04, 06, 05, 07.

### J2 — The cheap sampler *(try before the long run)*
> **As** a skeptic who won't spend 3 hours on an unproven tool, **I want** a cheap first taste, **so
> that** I can judge the output before committing.

- **Starts with:** the baseline (a resume is optional even here).
- **Trigger:** *"Run SPIDER Phase 1"* (just the LinkedIn analysis) — or scope the full run, e.g. *"only
  find 3 jobs and build apply packs for 2."*
- **Path:** runs a single phase / a scoped run, then stops.
- **Ends with:** one artifact (e.g. `linkedin-analysis.html` + its 10 ranked next steps) you can judge.
  Liked it? Continue into J1 — the workspace and intake carry forward.
- **Implemented by:** the orchestrator's "Run SPIDER Phase N" path → the named phase prompt.

### J3 — The graphical console *(clicking, not typing)* — **beta**
> **As** someone who'd rather click than type terminal commands, **I want** a guided wizard with live
> progress, **so that** I never touch the command line.

- **Starts with:** the baseline + Python 3 (preinstalled on macOS/Linux) + an agent CLI for the
  analysis.
- **Trigger:** `/spiderui`.
- **Path:** launches a local browser console → folder picker, target roles, optional daily-brief time
  → SPIDER runs the **same** pipeline *straight through* (no per-phase checkpoints; pre-approved tools)
  while the console shows a live feed.
- **Ends with:** the same outputs as J1, with an "Open my dashboard" button that lights up when
  `start-here.html` exists.
- **Implemented by:** [`.claude/commands/spiderui.md`](.claude/commands/spiderui.md) + [`ui/`](ui/) →
  the orchestrator in UI mode.

### J4 — Resume an interrupted run
> **As** someone whose run got cut off (closed laptop, hit a session/tool limit), **I want** to pick up
> exactly where it stopped, **so that** I don't redo finished work or get a half-built workspace.

- **Starts with:** a `workspace/<name>/` with a partial `.spider-state.json`.
- **Trigger:** *"Run SPIDER resume"* / `/spider resume`.
- **Path:** reads `.spider-state.json`, tells you where it stopped, continues from the first incomplete
  unit, skipping anything marked `done`/`complete`.
- **Ends with:** the run completed as if it never paused.
- **Implemented by:** the orchestrator's **State & resumability** section + `.spider-state.json`.

### J5 — Non-coder first setup
> **As** someone who has never opened a terminal, **I want** step-by-step setup help, **so that** I can
> get to the point of typing `/spider` at all.

- **Starts with:** a LinkedIn export and the willingness to follow a guide.
- **Trigger:** read [`docs/SETUP.md`](docs/SETUP.md) (or run `/spiderui`, which sidesteps the terminal
  after launch).
- **Path:** install/open Claude Code → clone → point at your files → then J1 or J3.
- **Ends with:** a working setup, handed off to J1/J3.
- **Implemented by:** [`docs/SETUP.md`](docs/SETUP.md) (+ J3 for the graphical path).

---

## The recurring loop (where you live after setup)

These assume **a built `workspace/<name>/`** already exists. This is the part that actually gets you
interviews — the documents are just ammunition; *applications sent and referrals asked* are the score.

### J6 — Today's action loop
> **As** someone with applications in flight, **I want** to be told the few things to do today, **so
> that** I make progress in ~20 minutes without re-planning my whole search.

- **Trigger:** *"SPIDER today"* / `/spider today` — **or** the scheduled daily brief fires on its own
  (beta; cron, macOS/Linux).
- **Path:** reads your queue, network map, and dashboard targets → drafts today's 3 actions + a
  ghost-detector pass that surfaces stale applications needing a follow-up nudge.
- **Ends with:** `daily-briefing.md` — today's actions and drafted follow-ups, ready to send.
- **Implemented by:** [`prompts/13-daily-briefing.md`](prompts/13-daily-briefing.md). Scheduled path:
  [`ui/run-daily-brief.sh`](ui/run-daily-brief.sh). If a scheduled run doesn't complete, just say
  *"SPIDER today"* for the same brief.

### J7 — Weekly maintenance
> **As** a job seeker a week later, **I want** fresh roles and a status sweep, **so that** my queue
> doesn't rot and no follow-up slips.

- **Trigger:** *"Run SPIDER maintenance"* / `/spider maintenance` (alias `refresh`).
- **Path:** re-runs the search and diffs it (new / closed roles), lists follow-ups due, refreshes comp
  research, and digests retro patterns from your `application-log.md` files.
- **Ends with:** an updated queue + a maintenance digest of what changed and what's due.
- **Implemented by:** [`prompts/09-maintenance.md`](prompts/09-maintenance.md).

### J8 — Network refresh
> **As** someone who'd rather get referred than cold-apply, **I want** to know who I already know at
> each target company, **so that** my outreach starts warm.

- **Starts with:** a `Connections.csv` in your LinkedIn export.
- **Trigger:** *"SPIDER network"* / `/spider network`.
- **Path:** mines *your own* connections for warm referral paths per target company (never invents
  contacts).
- **Ends with:** `network-map.md` — best warm paths per company, which J6's outreach and apply packs
  pull from. (Best run *before* apply packs so outreach has named targets.)
- **Implemented by:** [`prompts/11-network-map.md`](prompts/11-network-map.md).

---

## Per-opportunity journeys (triggered by something happening)

Each reacts to a real event and updates the dashboard.

### J9 — Add a job you found
> **As** someone who spotted a role outside the queue, **I want** to pull it in and get materials, **so
> that** I can apply to it the same way as the ranked ones.

- **Trigger:** *"SPIDER job add <url>"* / `/spider job add <url-or-description>`.
- **Path:** fetches and verifies the posting → appends one entry to `job-queue.md` (with link status)
  → builds its **CORE apply pack** (resume · outreach · application-log). Doesn't rebuild the queue.
- **Ends with:** `jobs/<NN-company-role>/` ready to work.
- **Implemented by:** [`prompts/05-job-folders.md`](prompts/05-job-folders.md).
- **Related:** *"Rebuild job NN"* / `/spider job rebuild <NN>` regenerates a folder (JD changed, master
  improved) while preserving its `application-log.md` status.

### J10 — Prep for a booked screen
> **As** someone who just got a screen for job #3, **I want** deep, job-specific prep, **so that** I
> walk in ready — and only build this for jobs that actually convert.

- **Precondition:** the job exists in the queue/folders **and** a screen is booked (this is the
  lazy-by-design payoff — deep prep is built per job, on demand, not for all 15 up front).
- **Trigger:** *"SPIDER prep 03"* / `/spider prep <NN>`.
- **Path:** builds the deep interview-prep pack for that job, then offers a mock-interview drill.
- **Ends with:** the job folder's deep-prep pack (5 files, led by `prep-doc.md`) + an optional mock.
- **Implemented by:** [`prompts/10-deep-prep.md`](prompts/10-deep-prep.md).

### J11 — Score a JD before investing
> **As** someone weighing a posting, **I want** an honest fit score with no files built, **so that** I
> decide whether it's worth pursuing first.

- **Trigger:** *"SPIDER score <paste a JD>"* / `/spider score <JD>`.
- **Path:** runs Phase 4's rubric against the pasted JD — five sub-scores + reasoning.
- **Ends with:** a **0–100 Fit Score** + the missing-but-claimable keywords, **in chat — nothing
  written to disk.** Worth it? Feed it into J9.
- **Implemented by:** the orchestrator's score op (Phase 4 rubric + §9 tailoring protocol).

### J12 — Export a resume to PDF at apply time
> **As** someone about to submit, **I want** a one-page ATS-safe PDF, **so that** the application goes
> through clean.

- **Precondition:** the job folder exists with a built `resume.md`.
- **Trigger:** *"SPIDER export Acme"* / `/spider export <company>`. (Also runs automatically when each
  pursued job's pack is built in Phase 5, and for the master public résumé in Phase 3.)
- **Path:** parses `resume.md` into `resume.json`, fills the résumé builder, and renders a one-page
  ATS-safe PDF headless via the trusted server. If no Chrome-class engine is found, you press "Save as
  PDF" once instead. Then eyeball it.
- **Ends with:** a submittable one-page PDF (plus the `resume.json` and filled builder `.html`).
- **Implemented by:** [`prompts/08-export-pdf.md`](prompts/08-export-pdf.md) +
  [`templates/resume-builder.template.html`](templates/resume-builder.template.html) +
  [`ui/server.py`](ui/server.py) `--render`.

### J12b — Build a résumé from scratch (ad-hoc)
> **As** someone who just wants a clean résumé without running the whole pipeline, **I want** a visual
> builder, **so that** I can type or import my details and get a one-page ATS-safe PDF.

- **Precondition:** none (works standalone, no workspace required).
- **Trigger:** *"SPIDER build-resume"* / `/spider build-resume` — or just open
  [`templates/resume-builder.template.html`](templates/resume-builder.template.html) in a browser, or
  visit `/resume-builder` while the console runs.
- **Path:** fill the form (or Import a `resume.json`), watch the live preview with a one-page boundary
  warning, then Create PDF / Export JSON.
- **Ends with:** a one-page ATS-safe PDF and a reusable `resume.json`.
- **Implemented by:** [`templates/resume-builder.template.html`](templates/resume-builder.template.html).

### Also on demand: the answer sheet
> **As** someone slogging through application questionnaires, **I want** reusable honest answers, **so
> that** I stop rewriting "why this company" from scratch.

- **Trigger:** *"SPIDER answers"* / `/spider answers`.
- **Ends with:** `answer-bank.md` (reusable core) + per-job `answer-sheet.md` for postings with custom
  screeners. Conviction/"why us" answers come out as **honest outlines you finish in your voice**, never
  finished prose.
- **Implemented by:** [`prompts/12-answer-sheet.md`](prompts/12-answer-sheet.md).

---

## Meta journey

### J13 — Run it for someone else (and wipe them later)
> **As** someone helping a friend or family member, **I want** a fully isolated run per person, **so
> that** nobody's data bleeds and I can delete a person cleanly.

- **Trigger:** run any setup journey with their name → a separate `workspace/<their-name>/`.
- **Path:** every run is person-agnostic — nothing about a prior user (the repo author included) carries
  in. Each person's data, resumes, and dashboards live only in their own folder.
- **Ends with:** independent workspaces. **To wipe a person:** delete their `workspace/<name>/` folder.
- **Implemented by:** the **Person-agnostic** + **Privacy** binding rules in
  [`CLAUDE.md`](CLAUDE.md) / the orchestrator.

---

## Invariants that hold across every journey

These aren't a journey — they're the promises SPIDER keeps no matter which path you're on. Full rules:
[`reference/number-and-honesty-policy.md`](reference/number-and-honesty-policy.md),
[`reference/untrusted-content-policy.md`](reference/untrusted-content-policy.md).

- **Never fabricates.** Every claim traces to your LinkedIn export, your resume, or an answer you gave.
  A missing number is a thing to measure, not invent; a missing skill is an honest gap, not a bluff.
- **Selection, not invention.** Once `master-resume.md` exists, per-job resumes are *selected* from it;
  a missing bullet is a "MASTER GAP" note, never fiction on the derivative.
- **Privacy by construction.** All personal output stays under `workspace/<name>/` (gitignored, with a
  resume/CSV backstop). Web access is read-only research; workspace data never leaves your machine.
- **Untrusted content is data, not instructions.** Anything fetched or loaded from a file (job posts,
  recruiter messages, your CSV) is inert data to quote/extract — never commands to obey. Highest stakes
  in the unattended daily brief (J6).
- **Resumable.** `.spider-state.json` makes any run recoverable; never re-derive progress by guessing.
- **You stay in the loop.** SPIDER finds, tailors, and preps — it never applies for you. You review,
  export, and submit.
</content>
</invoke>
