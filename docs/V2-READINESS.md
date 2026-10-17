# Ascend 2.0 readiness

**As of:** 2026-10-17. **Status:** beta. Built module by module on branch `ascend-v2` (spec
`docs/superpowers/specs/2026-10-16-ascend-v2-design.md`, plan `docs/superpowers/plans/2026-10-16-ascend-v2.md`).

Each module was checked twice: unit tests on synthetic fixtures (no real data in the repo), and a run
against one real user's workspace, kept in gitignored `workspace/`. Only counts from those runs are
written down anywhere.

## What has run on real data

| Area | Real run | Result |
|---|---|---|
| Mail classifier (M1) | 49 real messages, hand-labelled | 77.6% correct as first built, 100% after calibration, 1 of 49 sent to a model |
| Ledger ingest and guard (M2) | the same mailbox and 15 real job folders | an interview reminder moved one job to screen. A re-application was blocked |
| Hub (M3) | the real workspace in Chrome | three display bugs found and fixed, each with a test |
| Finder and prefilter (M5) | 127 company boards | 15,092 postings in 22 seconds at zero tokens, 48 survivors after four rule fixes |
| Alerts and inbound (M6) | real alert and recruiter mail | one alert lead extracted, three staffing emails filtered as not remote |
| Scoring and queue (M7) | 10 real survivors scored, 2 approved in the browser | about 5,200 estimated tokens for the batch. Four duplicate roles merged |
| Apply (M8) | an approved real job up to the apply sheet | every gate held |
| Engines B and C, LinkedIn (M9) | a day of real Gmail, one web search, one LinkedIn search | a real "next steps" email resolved by the model moved a job to screen. A stale search result and a silent-skip bug found and fixed |
| Daily sync (M10) | the real workspace | every stage ran in 21 seconds at zero tokens |

## Still beta, and why

- **Engine A's live Google sign-in** has run only against a fake Google server. It needs the user's own
  OAuth client (`docs/GMAIL-SETUP.md`), which only the user can create.
- **Agent-submit and fully automatic are not in this release.** The council review of PR #15 split them out
  to the `ascend-v2-agent-modes` branch. They come back as their own PR after assisted mode passes its
  one-week gate, with the security findings listed in that branch's readiness doc fixed first.
- **Token figures are estimates** (characters divided by four). They replace the design's defaults after
  three runs of a stage, and the hub labels them as estimates.
- **LinkedIn card leads carry no description**, so they rank last on keyword overlap until enriched.
- The design's release gate stands: assisted mode with engine A becomes stable after one week of real use, and
  everything else stays beta until it has run for real.

## How to check a fresh setup

```
python3 tests/smoke.py                                   # includes every tests/test_v2_*.py suite
python3 tools/run.py plan workspace/<you> --engine C
python3 tools/daily.py workspace/<you>
python3 ui/server.py   # then open /hub?slug=<you>
```
