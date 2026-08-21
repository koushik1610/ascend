# <Name> — Triage Brief

<!--
  WHAT THIS IS. A deliberately small file (~1.5-2K tokens) that Phase 4's first pass reads INSTEAD OF
  the full evaluation stack. It is written by Phase 3 at the lock checkpoint, so it is versioned with
  the master resume: bump it whenever `master_version` bumps.

  WHY IT EXISTS. Phase 4 used to run the full five-part Fit Score on every candidate, which meant the
  twelfth posting was scored with eleven full JDs and an industry scan still in context. That is the
  largest source of unexplained variance in the queue's headline number, and it made "at least 15" a
  budget rather than a target. Now: triage 40 against this file, score the survivors properly.

  KEEP IT SHORT. Every line is read once per posting during a batch. Include only what changes a
  go/no-go. The narrative, the STAR stories and the negotiation scripts stay in the master and the
  packet. If you find yourself pasting a bullet in here, put the metric in and leave the prose out.
-->

## Identity
<One line: seniority, discipline, years, location/timezone, work-authorization constraints.>

## Target archetypes
The roles actually wanted. A direct hit scores 4-5, an adjacent title 3, a mismatch 1-2.
Include the "analog" titles that are the same work under a different market label, so triage
recognizes them as targets rather than scoring them as misses. (Phase 22 `/ascend titles` writes here.)

| # | Archetype | What they are buying (the evidence that makes this a fit) |
|---|---|---|
| 1 | <name> | <the capability, with the master entry ID that proves it> |
| 2 | <name> | <…> |
| 3 | <name> | <…> |

## Proof points
The strongest quantified accomplishments, in public/sanitized form. Triage counts how many map to a JD.
- <accomplishment, metric, scope> *(E#)*
- <accomplishment, metric, scope> *(E#)*
- <accomplishment, metric, scope> *(E#)*

## Comp floor
| Threshold | Conditions |
|---|---|
| <$X> | <the floor, and what would have to be true to go below it> |

## Location and work mode
<Remote-only / hybrid metros / on-site-OK where / relocation appetite. Score 5 for a direct match,
1 for a hard conflict. Note any "remote" that is actually country-locked.>

## Hard disqualifiers
Any hit caps the score at 2.5 and ends the triage. These are real blockers, not preferences.
- <e.g. requires a clearance the user does not hold>
- <e.g. on-site 5 days in a metro the user will not move to>
- <e.g. a named company on the do-not-apply list>

## Soft red flags
Each costs -0.5. Preferences, not blockers.
- <e.g. no posted comp band in a jurisdiction that requires one>
- <e.g. posting older than 60 days>

## Priority overrides
Companies that PASS regardless of score, because the user said so. Check the name before returning
a verdict.
- <company> — <why>
