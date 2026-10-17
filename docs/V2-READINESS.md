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
  one-week gate and the callback number in spec criterion 6 exists, with the agent-path findings in
  spec §11 fixed first.
- **Token figures are estimates** (characters divided by four). They replace the design's defaults after
  three runs of a stage, and the hub labels them as estimates.
- **LinkedIn card leads carry no description**, so they rank last on keyword overlap until enriched.
- The design's release gate stands: assisted mode with engine A becomes stable after one week of real use, and
  everything else stays beta until it has run for real.

## Not built from the spec

Spec §11 has the reasons. In short: no Sources & settings tab (edit `data/sources.json`), no 48-hour
"applied?" follow-up, no per-run token cap, no board backoff and retry, no automatic fallback from engine
A to C, and cron instead of launchd (a sleeping Mac skips that day's sync).

## Risks you accept by turning things on

- **LinkedIn search** drives your own logged-in LinkedIn session. Automated browsing can break LinkedIn's
  terms of use and put the account at risk. Claude asks before every search.
- **Engines B and C** let Claude read your Gmail through the claude.ai connector, limited to job senders
  and job subjects. Its write tools are denied in this repo's `.claude/settings.json`. Mail is untrusted and
  the same session can fetch web pages: only the content quarantine stands between an email's instructions
  and a fetch. This repo allows `WebFetch` for every domain, and a narrower local allow does not override
  it. Close it with `"ask": ["WebFetch"]` (every fetch asks you) or, on engine C, `"deny": ["WebFetch"]` in
  your own `.claude/settings.local.json`. The search also misses a recruiter writing from a personal
  address with no job word in the subject.
- **LinkedIn search** runs in your logged-in browser. "Never use Easy Apply" is an instruction to Claude,
  not a setting. Claude in Chrome's per-action permission prompts are the guard, so keep them on.
- **Engine A in Google's Testing mode** signs you out after about seven days. The daily sync then fails
  its Gmail stage and the hub shows a reconnect banner.

## How to check a fresh setup

```
python3 tests/smoke.py                                   # includes every tests/test_v2_*.py suite
python3 tools/run.py plan workspace/<you> --engine C
python3 tools/daily.py workspace/<you>
python3 ui/server.py   # then open /hub?slug=<you>
```
