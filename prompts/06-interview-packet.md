# Phase 6 — Interview Packet → `interview-packet/`

**Goal:** build the cross-job interview-prep kit the per-job folders reference by ID. Built once,
reused by every job folder, so a story or metric lives in exactly one place.

**Read first:** `workspace/<name>/intake.md`, `master-resume.md` (esp. the story-bank index + metrics
bank), `../templates/interview-packet-template.md`,
`../reference/interview-prep-framework.md`.

> **Sequencing:** build this right before or alongside Phase 5, since the job folders cite its story
> IDs. If you build folders first, build a thin packet first (story stubs with stable IDs), then
> enrich here.

---

## Produce these files in `interview-packet/`

1. **`star-stories.md`** — the user's behavioral stories in STAR form (Situation → Task → Action →
   Result → what-it-proves), each with a **stable ID** (`S1`, `S2`, …) the job folders reference. Aim
   for 6–10 covering the dimensions every senior loop probes: ambiguity / zero-prior-art, influence
   without authority, leverage/scale, technical conviction under pushback, coaching/multiplying,
   conflict/disagreement, operational excellence, and a genuine failure-and-learning. Derive them from
   the master resume's experience entries; never invent events. Note which story leads for which
   audience.
2. **`project-deep-dives.md`** — for the user's 3–6 most impressive projects/initiatives: a 60-second
   walkthrough, the probing questions they'll get, and an honest failure/limitation story for each
   (interviewers always ask). IDs `D1`, `D2`, …
3. **`metrics-cheatsheet.md`** — the say-aloud number discipline: what's exact-and-sendable, what's
   rounded, what's never said (per the user's `intake.md` sanitization rule + the master metrics bank).
   Plus 5 rehearsed 10-second stat lines.
4. **`intro-scripts.md`** — 30-second, 90-second, and 3-minute introductions, all reducing to the same
   positioning. Used to open recruiter screens and "tell me about yourself."
5. **`questions-to-ask.md`** — strong questions the user asks the interviewer, grouped by round type
   (recruiter, hiring manager, peer, leadership).
6. **`company-positioning.md`** — per-target-company one-liner hooks + closers (seed from the job
   queue's "why it ranks" notes; the job folders' prep-docs reuse these).

## Rules
- **Single source of truth:** each story/metric lives here once; job folders reference by ID. Don't
  duplicate.
- **Honesty:** every STAR story is a real event the user can defend under follow-up questioning. Mark
  any detail the user must confirm with `VERIFY:`. Personal-conviction answers (e.g., "why this
  mission") are prompts/beats, never finished prose — the user writes those.
- **Field-aware:** for non-engineering users, `project-deep-dives.md` becomes portfolio/case-study
  walkthroughs; the framework in `../reference/interview-prep-framework.md` adapts.

## Verify
- Every STAR story maps to a master-resume experience entry (no orphan events).
- IDs are stable and referenced correctly by any job folders already built.
- The metrics cheat sheet matches the master metrics bank and the user's sanitization rule.

## Checkpoint
List the stories (with IDs + one-line themes) and confirm with the user they're all real and
defensible before the job folders lean on them.
