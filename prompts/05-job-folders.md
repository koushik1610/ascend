# Phase 5 — Per-Job Folders → `jobs/<NN-company-role>/`

**Goal:** for every job in the queue, build a complete application + interview workspace — one folder,
**8 files**, built by *selection* from the master resume and *reference* to the interview packet. This
is the deep, enriched per-job work.

**Read first:** `workspace/<name>/intake.md`, `job-queue.md`, `master-resume.md`,
`interview-packet/` (if built — Phase 6), `../templates/job-folder/_TEMPLATE.md` (THE binding 8-file
spec), `../reference/` (all four files).

> **Scale tip:** this is the heaviest phase. Build folders in batches (e.g., 4 at a time). For each
> folder you may dispatch a focused sub-agent given: the job's queue entry, the master resume, the
> packet, the template, and the reference rules — with strict instructions to touch only its own
> folder and to run the verification grep before finishing. Or build them sequentially. Either way,
> every folder must conform to `_TEMPLATE.md` exactly.

---

## The 8 files (per `../templates/job-folder/_TEMPLATE.md`)
1. `resume.md` — the tailored resume + a **Delta Log** (which master entry IDs were selected, in what
   order, why; verbatim JD phrases inserted once each; ATS target; export filename). Selection only —
   a missing bullet is a "MASTER GAP" note, never an invention.
2. `prep-doc.md` — the ≤2-page night-before read: positioning hook, role thesis, talking points, story
   map (round → story ID → job-specific opening line), rehearsed gap-handling lines, closer, a
   numbers-discipline box.
3. `interview-questions.md` — predicted technical/design questions (bullet-skeleton answers, ≥3 design
   prompts); a **coding section calibrated to this company's real loop** (named LeetCode-style problems
   where the company actually tests algorithms; practical/domain tasks where it doesn't; the user's
   field decides the flavor); behavioral questions mapped to the user's STAR stories.
4. `interview-prep.md` — the study plan: prioritized topics + hours, set-piece designs to rehearse,
   gap-handling verbatim, a week-by-week plan, a day-before checklist.
5. `outreach.md` — referral targets (seeded from the LinkedIn network analysis — real connections at
   this company; NEVER fabricated names), DM drafts (flagged *rewrite in your own voice*), a
   recruiter-screen script with the comp/level anchor and any location-friction question.
6. `company-research.md` — team intel, `VERIFY:` items to confirm with live search before the loop,
   an interviewer-notes table, comp/negotiation anchors, level context.
7. `signal.md` — the **sendable** one-pager for this job: a re-lead of the master positioning summary
   with evidence reordered for the role. Public values only. Send as PDF or pasted text, never `.md`.
8. `application-log.md` — the only stateful doc: pre-submit checklist, status log, thank-you tracker,
   post-loop retro template.

## Single-sourcing rule
If a sentence already exists in the master resume or interview packet, the folder holds only the
*job-specific delta* plus a reference (e.g., `../../interview-packet/star-stories.md → S3`). Never copy
story bodies, the metrics bank, or shared prep wholesale.

## Coding calibration (field-aware)
Encode the real interview reality for each company/role:
- **Software/SRE/security/data roles at big tech** → algorithm rounds: give 8–15 named LeetCode-style
  problems by pattern (arrays/hashing, intervals, graphs/BFS-DFS, heaps, strings, trees) plus any
  domain-flavored coding tasks. Where a company is known for *not* doing LC (many startups, many
  non-SWE roles), say so and give the practical/take-home/portfolio reality instead.
- **Non-engineering roles** (design, PM, marketing, ops, etc.) → replace the coding section with the
  real assessment for that field (portfolio review, case study, take-home exercise, work sample) and
  prep for it concretely.
Always be honest about what the loop actually contains; never invent a coding round that isn't there.

## Hard rules (per `../templates/job-folder/_TEMPLATE.md` + `../reference/`)
- Public/sanitized numbers in every sendable file (resume, signal, outreach); the user's exact
  verifiable numbers stay exact. Run the user's number-policy grep over each folder before finishing.
- Honesty gates: no fabricated experience, no fabricated referral contacts, no claimed skills the user
  doesn't have, no completed personal "why this company" essays (outlines only — the user writes them).
- Every resume bullet traces to a master entry ID, cited in the Delta Log.

## Verify (per folder)
- Exactly 8 files, all conforming to the template.
- Number-policy grep clean (no leaked sensitive internals).
- Every resume bullet cites a real master entry ID; MASTER GAPS noted where selection fell short.

## Checkpoint
Report folders built, the per-folder verification results, and any MASTER GAPS surfaced (fix those in
`master-resume.md` — fix the source, not the derivative). Then proceed to Phase 7 (navigator).
