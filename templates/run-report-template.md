# Run Report — <name> — <YYYY-MM-DD>

<!-- Written by the orchestrator at final handoff (STEP 4) into workspace/<name>/RUN-REPORT.md.
     Purpose: make runs auditable and comparable. Keep it to one page. If a prior RUN-REPORT.md
     exists (or a prior run folder), fill in "What changed since the last run"; otherwise delete
     that section. Everything here is personal data — it stays in the gitignored workspace. -->

## What ran
- **Mode:** full run / partial (phases N…) / resume-after-interruption
- **Intake:** new / carried from <prior run> (what changed, if anything)
- **Master résumé:** built fresh / LOCKED and reused (`master_version: N`)
- **Phases completed:** 1 · 3 · 4 · 6 · 5 · 7 (+ on-demand ops run this session)

## What was produced
| Artifact | Where | Notes |
|---|---|---|
| LinkedIn analysis | `linkedin-analysis.html` | findability score, top next step |
| Master résumé | `master-resume.md` (+ public PDF) | N entries / N bullets; locked? |
| Job queue | `job-queue.md` | N candidates, M link-verified, top Fit Score |
| Apply packs | `jobs/<NN>…` | N packs (breadth choice: top 3–5 / full queue) |
| Interview packet | `interview-packet/` | thin / enriched |
| Navigator | `start-here.html` | — |

## Quality gates
- **Lint (`tools/lint_artifacts.py` over every sendable):** PASS / N findings → resolved how
- **Honesty:** every bullet traces to a master entry ID (Delta Logs); no invented metric/title/cert/
  contact; conviction answers outline-only — PASS/FAIL
- **Numbers:** forbidden-internals scan (lint-config) — zero hits — PASS/FAIL
- **One page:** each per-job résumé PDF is one page; master ≤ 2 — PASS/FAIL
- **Privacy:** `git check-ignore` confirms the workspace is ignored; nothing staged — PASS/FAIL

## What changed since the last run
<!-- diff against the previous RUN-REPORT.md: new/closed jobs in the queue, master version bump,
     new packs, gates that newly pass/fail. Delete this section on a first run. -->

## Blockers / next actions (priority order)
1. …
2. …

## On-demand not built yet (by design)
- Deep prep (`/ascend prep <NN>`) — when a screen books.
- …
