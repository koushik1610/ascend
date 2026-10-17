# WORKFLOW.md: how people actually use Ascend

This is the **journey index**: who the user is, what they start with, and the path they take for
each way of using Ascend. It complements the mechanics. It does not restate them. The canonical
**run order, phases, and state machine live in [`prompts/00-orchestrator.md`](prompts/00-orchestrator.md)**;
the canonical **op list lives in [`.claude/commands/ascend.md`](.claude/commands/ascend.md)**. When a
journey below says "runs the pipeline," that prompt is the source of truth for *how*.

Each journey is written as: **the user → what they start with → the trigger → the path → what they
end with**. If a journey's trigger has a precondition (a built workspace, a booked screen), it's
called out: that's the difference between a step that works and one that errors.

---

## What every user starts with

The shared baseline. A journey only lists what it needs *beyond* this.

- **Claude Code** open in a clone of this repo, with a Claude subscription / API access (it runs on
  tokens).
- A **LinkedIn data export**: *LinkedIn → Settings → Data Privacy → Get a copy of your data → "The
  works"* → a zip → unzipped to a folder. (The `Connections.csv` inside it powers the network map.)
- **Optionally** a current resume (PDF / .docx / .md). No resume? Ascend builds the master from the
  LinkedIn export + intake answers instead.
- A rough idea of **target roles** (the title you want recruiters to search for) and seniority.

Everything personal lands in **`workspace/<your-name>/`**, which is gitignored. That folder *is* your
run. Delete it to wipe yourself entirely; run for a friend and they get their own.

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
  LOOP + LATE STAGE: J14 Weekly review · J15 Rejection · J16 Adjacent titles · J17 Offers
                     J18 Work sample · J19 References · J20 Industry language
  ASCEND 2.0: J21 Daily sync · J22 Score and approve · J23 Apply · J24 Track replies
```

The shape: **one setup**, then you live in the **loop** and react to **opportunities**. The dashboard
(`start-here.html`) is the home base you return to between journeys.

---

## Setup journeys (you do one of these once)

### J1: The full run *(the main path)*
> **As** someone starting a real job search, **I want** my whole search set up in one pass, **so that**
> I open one dashboard and start applying instead of staring at a blank resume.

- **Starts with:** the baseline + 30–60 min of attention across check-ins (the run itself is 1–3+ hrs
  of Claude working).
- **Trigger:** `/ascend` (or *"Run Ascend"*).
- **Path:** intake interview (name, data paths, targets, gaps, sanitization rules) → confirms an
  Intake Summary → builds `workspace/<name>/` → runs phases **1 → 26 → 3 → 4 → 11 → 6 → 5 → 7**, checkpointing
  after each so you can stop, skip, or redirect.
- **Ends with:** `linkedin-analysis.html`, `master-resume.md`, a 15+ job `job-queue.md` (each link
  marked verified/unverified), a thin `interview-packet/`, CORE apply packs for the **top 3–5 jobs you
  commit to**, and `start-here.html`: **open this first**. ~25–30 files, not ~100.
- **Implemented by:** [`prompts/00-orchestrator.md`](prompts/00-orchestrator.md) → phases 01, 03, 04, 06, 05, 07.

### J2: The cheap sampler *(try before the long run)*
> **As** a skeptic who won't spend 3 hours on an unproven tool, **I want** a cheap first taste, **so
> that** I can judge the output before committing.

- **Starts with:** the baseline (a resume is optional even here).
- **Trigger:** *"Run Ascend Phase 1"* (just the LinkedIn analysis), or scope the full run, e.g. *"only
  find 3 jobs and build apply packs for 2."*
- **Path:** runs a single phase / a scoped run, then stops.
- **Ends with:** one artifact (e.g. `linkedin-analysis.html` + its 10 ranked next steps) you can judge.
  Liked it? Continue into J1: the workspace and intake carry forward.
- **Implemented by:** the orchestrator's "Run Ascend Phase N" path → the named phase prompt.

### J3: The graphical console *(clicking, not typing)* (**beta**)
> **As** someone who'd rather click than type terminal commands, **I want** a guided wizard with live
> progress, **so that** I never touch the command line.

- **Starts with:** the baseline + Python 3 (preinstalled on macOS/Linux) + an agent CLI for the
  analysis.
- **Trigger:** `/ascendui`.
- **Path:** launches a local browser console → folder picker, target roles, optional daily-brief time
  → Ascend runs the **same** pipeline *straight through* (no per-phase checkpoints; pre-approved tools)
  while the console shows a live feed.
- **Ends with:** the same outputs as J1, with an "Open my dashboard" button that lights up when
  `start-here.html` exists.
- **Implemented by:** [`.claude/commands/ascendui.md`](.claude/commands/ascendui.md) + [`ui/`](ui/) →
  the orchestrator in UI mode.

### J4: Resume an interrupted run
> **As** someone whose run got cut off (closed laptop, hit a session/tool limit), **I want** to pick up
> exactly where it stopped, **so that** I don't redo finished work or get a half-built workspace.

- **Starts with:** a `workspace/<name>/` with a partial `.ascend-state.json`.
- **Trigger:** *"Run Ascend resume"* / `/ascend resume`.
- **Path:** reads `.ascend-state.json`, tells you where it stopped, continues from the first incomplete
  unit, skipping anything marked `done`/`complete`.
- **Ends with:** the run completed as if it never paused.
- **Implemented by:** the orchestrator's **State & resumability** section + `.ascend-state.json`.

### J5: Non-coder first setup
> **As** someone who has never opened a terminal, **I want** step-by-step setup help, **so that** I can
> get to the point of typing `/ascend` at all.

- **Starts with:** a LinkedIn export and the willingness to follow a guide.
- **Trigger:** read [`docs/SETUP.md`](docs/SETUP.md) (or run `/ascendui`, which sidesteps the terminal
  after launch).
- **Path:** install/open Claude Code → clone → point at your files → then J1 or J3.
- **Ends with:** a working setup, handed off to J1/J3.
- **Implemented by:** [`docs/SETUP.md`](docs/SETUP.md) (+ J3 for the graphical path).

---

## The recurring loop (where you live after setup)

These assume **a built `workspace/<name>/`** already exists. This is the part that actually gets you
interviews: the documents are just ammunition; *applications sent and referrals asked* are the score.

### J6: Today's action loop
> **As** someone with applications in flight, **I want** to be told the few things to do today, **so
> that** I make progress in ~20 minutes without re-planning my whole search.

- **Trigger:** *"Ascend today"* / `/ascend today`, **or** the scheduled daily brief fires on its own
  (beta; cron, macOS/Linux).
- **Path:** reads your queue, network map, and dashboard targets → drafts today's 3 actions + a
  ghost-detector pass that surfaces stale applications needing a follow-up nudge.
- **Ends with:** `daily-briefing.md`: today's actions and drafted follow-ups, ready to send.
- **Implemented by:** [`prompts/13-daily-briefing.md`](prompts/13-daily-briefing.md). Scheduled path:
  [`ui/run-daily-brief.sh`](ui/run-daily-brief.sh). If a scheduled run doesn't complete, just say
  *"Ascend today"* for the same brief.

### J7: Weekly maintenance
> **As** a job seeker a week later, **I want** fresh roles and a status sweep, **so that** my queue
> doesn't rot and no follow-up slips.

- **Trigger:** *"Run Ascend maintenance"* / `/ascend maintenance` (alias `refresh`).
- **Path:** re-runs the search and diffs it (new / closed roles), lists follow-ups due, refreshes comp
  research, and digests retro patterns from your `application-log.md` files.
- **Ends with:** an updated queue + a maintenance digest of what changed and what's due.
- **Implemented by:** [`prompts/09-maintenance.md`](prompts/09-maintenance.md).

### J8: Network refresh
> **As** someone who'd rather get referred than cold-apply, **I want** to know who I already know at
> each target company, **so that** my outreach starts warm.

- **Starts with:** a `Connections.csv` in your LinkedIn export.
- **Trigger:** *"Ascend network"* / `/ascend network`.
- **Path:** mines *your own* connections for warm referral paths per target company (never invents
  contacts).
- **Ends with:** `network-map.md`: best warm paths per company, which J6's outreach and apply packs
  pull from. (Best run *before* apply packs so outreach has named targets.)
- **Implemented by:** [`prompts/11-network-map.md`](prompts/11-network-map.md).

---

## Per-opportunity journeys (triggered by something happening)

Each reacts to a real event and updates the dashboard.

### J9: Add a job you found
> **As** someone who spotted a role outside the queue, **I want** to pull it in and get materials, **so
> that** I can apply to it the same way as the ranked ones.

- **Trigger:** *"Ascend job add <url>"* / `/ascend job add <url-or-description>`.
- **Path:** fetches and verifies the posting → appends one entry to `job-queue.md` (with link status)
  → builds its **CORE apply pack** (resume · outreach · application-log). Doesn't rebuild the queue.
- **Ends with:** `jobs/<NN-company-role>/` ready to work.
- **Implemented by:** [`prompts/05-job-folders.md`](prompts/05-job-folders.md).
- **Related:** *"Rebuild job NN"* / `/ascend job rebuild <NN>` regenerates a folder (JD changed, master
  improved) while preserving its `application-log.md` status.

### J10: Prep for a booked screen
> **As** someone who just got a screen for job #3, **I want** deep, job-specific prep, **so that** I
> walk in ready, and only build this for jobs that actually convert.

- **Precondition:** the job exists in the queue/folders **and** a screen is booked (this is the
  lazy-by-design payoff: deep prep is built per job, on demand, not for all 15 up front).
- **Trigger:** *"Ascend prep 03"* / `/ascend prep <NN>`.
- **Path:** builds the deep interview-prep pack for that job, then offers a mock-interview drill.
- **Ends with:** the job folder's deep-prep pack (5 files, led by `prep-doc.md`) + an optional mock.
- **Implemented by:** [`prompts/10-deep-prep.md`](prompts/10-deep-prep.md).

### J11: Score a JD before investing
> **As** someone weighing a posting, **I want** an honest fit score with no files built, **so that** I
> decide whether it's worth pursuing first.

- **Trigger:** *"Ascend score <paste a JD>"* / `/ascend score <JD>`.
- **Path:** runs Phase 4's rubric against the pasted JD: five sub-scores + reasoning.
- **Ends with:** a **0–100 Fit Score** + the missing-but-claimable keywords, **in chat, nothing
  written to disk.** Worth it? Feed it into J9.
- **Implemented by:** the orchestrator's score op (Phase 4 rubric + §9 tailoring protocol).

### J12: Export a resume to PDF at apply time
> **As** someone about to submit, **I want** a one-page ATS-safe PDF, **so that** the application goes
> through clean.

- **Precondition:** the job folder exists with a built `resume.md`.
- **Trigger:** *"Ascend export Acme"* / `/ascend export <company>`. (Also runs automatically when each
  pursued job's pack is built in Phase 5, and for the master public résumé in Phase 3.)
- **Path:** parses `resume.md` into `resume.json`, then renders through **LaTeX** into a `.tex` and a
  one-page ATS-safe PDF. The `.tex` is written even with no TeX toolchain, so you can always compile
  it on Overleaf. With no engine installed it falls back to the HTML builder rendered headless via
  the trusted server, and then to pressing "Save as PDF" once. Then eyeball it.
- **Ends with:** a submittable one-page PDF, plus the `resume.json` and the portable `.tex`.
- **Implemented by:** [`prompts/08-export-pdf.md`](prompts/08-export-pdf.md) +
  [`tools/render_resume.py`](tools/render_resume.py) +
  [`templates/resume-latex.template.tex`](templates/resume-latex.template.tex), with
  [`templates/resume-builder.template.html`](templates/resume-builder.template.html) +
  [`ui/server.py`](ui/server.py) `--render` as the fallback.

### J12b: Build a résumé from scratch (ad-hoc)
> **As** someone who just wants a clean résumé without running the whole pipeline, **I want** a visual
> builder, **so that** I can type or import my details and get a one-page ATS-safe PDF.

- **Precondition:** none (works standalone, no workspace required).
- **Trigger:** *"Ascend build-resume"* / `/ascend build-resume`, or just open
  [`templates/resume-builder.template.html`](templates/resume-builder.template.html) in a browser, or
  visit `/resume-builder` while the console runs.
- **Path:** fill the form (or Import a `resume.json`), watch the live preview with a one-page boundary
  warning, then Create PDF / Export JSON.
- **Ends with:** a one-page ATS-safe PDF and a reusable `resume.json`.
- **Implemented by:** [`templates/resume-builder.template.html`](templates/resume-builder.template.html).

### Also on demand: the answer sheet
> **As** someone slogging through application questionnaires, **I want** reusable honest answers, **so
> that** I stop rewriting "why this company" from scratch.

- **Trigger:** *"Ascend answers"* / `/ascend answers`.
- **Ends with:** `answer-bank.md` (reusable core) + per-job `answer-sheet.md` for postings with custom
  screeners. Conviction/"why us" answers come out as **honest outlines you finish in your voice**, never
  finished prose.
- **Implemented by:** [`prompts/12-answer-sheet.md`](prompts/12-answer-sheet.md).


### J14: The weekly review *(the 15-minute habit)*
- **Trigger:** `/ascend week`, once a week from week three.
- **Path:** counts what you did, captures outcomes with `tools/pipeline.py`, shows the funnel in your own
  numbers, checks the lead floor, and ends on exactly one decision.
- **Ends with:** `reviews/week-NN.md`.
- **Implemented by:** [`prompts/20-weekly-review.md`](prompts/20-weekly-review.md).

### J15: Close out a rejection
- **Trigger:** `/ascend rejected <NN>` when a "no" lands.
- **Path:** logs the stage it died at, extracts the one learnable thing if there is one, and activates a
  named replacement target so the pipeline does not shrink.
- **Implemented by:** [`prompts/21-rejection-protocol.md`](prompts/21-rejection-protocol.md).

### J16: Widen the search honestly
- **Trigger:** `/ascend titles` when the queue runs thin.
- **Path:** surfaces adjacent titles on three labelled axes (lateral, stretch, pivot), each citing master
  entries and naming its gap, and folds the confirmed ones into targeting.
- **Implemented by:** [`prompts/22-adjacent-titles.md`](prompts/22-adjacent-titles.md).

### J17: Decide between offers
- **Trigger:** `/ascend offers` once two processes finish (Phase 19 negotiates one number; this decides).
- **Path:** compares offers component by component, reads the letter, and works the deadline.
- **Ends with:** `offers/decision-<date>.md`.
- **Implemented by:** [`prompts/23-offer-compare.md`](prompts/23-offer-compare.md).

### J18: Build the work sample that decides the loop
- **Trigger:** `/ascend work-sample [NN]`.
- **Path:** one portfolio piece or take-home plan, built properly once and re-angled per job.
- **Ends with:** `work-sample.md`.
- **Implemented by:** [`prompts/24-work-sample.md`](prompts/24-work-sample.md).

### J19: Keep a reference bench
- **Trigger:** `/ascend references`, early, so an offer-stage request is a lookup.
- **Path:** a consent-tracked list of referees plus the brief that shapes each call.
- **Ends with:** `references.md`.
- **Implemented by:** [`prompts/25-references.md`](prompts/25-references.md).

### J20: Learn how your target level writes
- **Trigger:** automatic as Phase 26 of every run (after intake, before the master résumé), or
  `/ascend industry` on demand.
- **Path:** `python3 tools/industry_research.py status <industry> <domain>`. FRESH (built this calendar
  month) → reuse. STALE or MISSING → read 30 to 50 profiles at and around the target level, write the
  anonymized shared reference under `industryresearch/<industry>/<domain>/`, lint it. Either way, map
  the user's evidence against it in `industry-fit.md`.
- **Ends with:** `industryresearch/<industry>/<domain>/industry-language.md` (shared) and
  `workspace/<name>/industry-fit.md` (personal).
- **Implemented by:** [`prompts/26-industry-language.md`](prompts/26-industry-language.md) and
  [`tools/industry_research.py`](tools/industry_research.py).


### J20b: Set up Ascend 2.0 (once)
- **Trigger:** the first `/ascend run-v2` on a workspace that finished a v1 run.
- **Path:** `prompts/29-run-v2.md` Step 0 builds `data/profile.json` and `data/sources.json` with the user
  from the intake and master §4, then one `finder.py run` checks every board slug. `tools/run.py plan`
  refuses to start until master, boards and profile exist, and says which is missing.
- **Ends with:** a plan that passes, then `tools/schedule.py install` for the daily sync.

### J21: The daily sync (Ascend 2.0)
- **Trigger:** cron, from `python3 tools/schedule.py install workspace/<name> --at HH:MM`.
- **Path:** `tools/daily.py`: Gmail sync and classify (engine A), ingest, finder, prefilter, alerts, mail
  retention, hub build. Zero tokens. A failing stage is logged and the rest still run. Gmail signed out
  or an empty board list is a failed stage with the fix in its message, and the hub shows a banner.
  Cron does not run while the Mac sleeps, so a closed laptop at the scheduled time skips that day.
- **Ends with:** a current `hub.html` and a row in `data/run-log.jsonl`.

### J22: Score and approve
- **Trigger:** `/ascend run-v2`.
- **Path:** `tools/run.py plan` (token estimate, prerequisite check) → Phase 27 scores the survivors with
  reasons and gaps → the user approves or rejects in the served hub.
- **Implemented by:** [`prompts/29-run-v2.md`](prompts/29-run-v2.md), [`prompts/27-score-queue.md`](prompts/27-score-queue.md).

### J23: Apply
- **Trigger:** an approved job; `/ascend apply`.
- **Path:** the user approves in the hub → `tools/apply.py sheet` gate → the user submits in their own
  browser → **I submitted it** → `tools/apply.py record`.
- **Implemented by:** [`prompts/28-apply.md`](prompts/28-apply.md).

### J24: Track replies
- **Trigger:** new mail.
- **Path:** `classify.py` (rules, zero tokens) → the model resolves only what the rules leave
  (`classify.py resolve`) → `pipeline.py ingest` moves each job → the hub pins info requests and
  assessments with due dates.

---

## Meta journey

### J13: Run it for someone else (and wipe them later)
> **As** someone helping a friend or family member, **I want** a fully isolated run per person, **so
> that** nobody's data bleeds and I can delete a person cleanly.

- **Trigger:** run any setup journey with their name → a separate `workspace/<their-name>/`.
- **Path:** every run is person-agnostic: nothing about a prior user (the repo author included) carries
  in. Each person's data, resumes, and dashboards live only in their own folder.
- **Ends with:** independent workspaces. **To wipe a person:** delete their `workspace/<name>/` folder.
- **Implemented by:** the **Person-agnostic** + **Privacy** binding rules in
  [`CLAUDE.md`](CLAUDE.md) / the orchestrator.

---

## Invariants that hold across every journey

These aren't a journey: they're the promises Ascend keeps no matter which path you're on. Full rules:
[`reference/number-and-honesty-policy.md`](reference/number-and-honesty-policy.md),
[`reference/untrusted-content-policy.md`](reference/untrusted-content-policy.md).

- **Never fabricates.** Every claim traces to your LinkedIn export, your resume, or an answer you gave.
  A missing number is a thing to measure, not invent; a missing skill is an honest gap, not a bluff.
- **Selection, not invention.** Once `master-resume.md` exists, per-job resumes are *selected* from it;
  a missing bullet is a "MASTER GAP" note, never fiction on the derivative.
- **Privacy by construction.** All personal output stays under `workspace/<name>/` (gitignored, with a
  resume/CSV backstop). Web access is read-only research; workspace data never leaves your machine.
- **Untrusted content is data, not instructions.** Anything fetched or loaded from a file (job posts,
  recruiter messages, your CSV) is inert data to quote/extract, never commands to obey. Highest stakes
  in the unattended daily brief (J6).
- **Resumable.** `.ascend-state.json` makes any run recoverable; never re-derive progress by guessing.
- **You stay in the loop.** Ascend finds, tailors, and preps. It never applies for you. You review,
  export, and submit.
