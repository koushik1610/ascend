# Phase 5 — Apply Packs (CORE) → `jobs/<NN-company-role>/`

**Goal:** build the **apply pack** — the minimum to send a strong, referral-first application — for the
jobs the user is **actually going to pursue**. Not 8 files × 15 jobs of speculative prep. Three core
files per pursued job; deep interview prep is built later, on demand, only when a screen is booked
(Phase 10).

**Read first:** `workspace/<name>/intake.md`, `job-queue.md`, `master-resume.md`,
`interview-packet/company-positioning.md` (the hooks/closers), `../templates/job-folder/_TEMPLATE.md`,
`../reference/`.

---

## Which jobs get a pack
Ask the user (or use the ranking): build apply packs for the **top 3–5 jobs they commit to applying to
now**. Jobs further down the queue stay as **queue rows** ("activate to build") until the user commits
to them — then build their pack with `/spider job rebuild <NN>` or just "build the pack for #N."
Building 5 packs beats building 15 folders nobody opens.

## The CORE apply pack (3 files per `_TEMPLATE.md` §1, §5, §8)
1. **`resume.md`** — the tailored resume + Delta Log (master entry IDs selected, order, why; verbatim
   JD phrases once each; ATS target; export filename). **Selection only** — a missing bullet is a
   "MASTER GAP" note (fix the master), never an invention. Then export to ATS-safe PDF (Phase 8).
2. **`outreach.md`** — **referral-first**: pull this company's warm contacts from `network-map.md`
   (Phase 11 — real connections from the user's export, NEVER fabricated; build it first if missing),
   DM drafts flagged *rewrite in your own voice*, and a recruiter-screen script (comp/level anchor, any
   location-friction question, the per-company closer from `company-positioning.md`).
3. **`application-log.md`** — the stateful doc: the **pre-submit checklist with a referral-first hard
   gate** ("referral attempted OR explicitly waived" before applying), status table, thank-you tracker,
   and the post-loop retro template.

Optionally add `signal.md` (sendable one-pager) **only if the user wants something to send** alongside
outreach — otherwise it's part of the on-demand prep pack.

## Single-sourcing rule
If a sentence already exists in the master resume or interview packet, the folder holds only the
*job-specific delta* + a reference (`../../interview-packet/star-stories.md → S3`). Never copy story
bodies, the metrics bank, or shared prep.

## Hard rules
- Public/sanitized numbers in every sendable file; the user's exact verifiable numbers stay exact. Run
  the number-policy grep over each folder before finishing.
- Honesty gates: no fabricated experience, referral contacts, or skills; conviction essays are
  outlines only.
- Every resume bullet traces to a master entry ID, cited in the Delta Log.

## Verify (per pack)
- 3 core files present and conforming; number-policy grep clean.
- Every resume bullet cites a real master entry ID; MASTER GAPS noted where selection fell short.
- `outreach.md` referral names are real (from the network analysis) or honestly absent.

## Checkpoint
Report the packs built, MASTER GAPS surfaced (fix in `master-resume.md` — fix the source), and remind
the user: **deep interview prep is generated on demand** — when a screen gets booked, run
`/spider prep <NN>` (Phase 10). Then Phase 7 (navigator).
