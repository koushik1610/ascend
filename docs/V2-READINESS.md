# Ascend 2.0 readiness

**As of:** 2026-10-22. **Status:** beta. Built module by module on branch `ascend-v2` (spec
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
| Apply (M8) | an approved real job up to the apply sheet | every gate held, on a queue whose links to job folders were written by hand |
| Engines B and C, LinkedIn (M9) | a day of real Gmail, one web search, one LinkedIn search | a real "next steps" email resolved by the model moved a job to screen. A stale search result and a silent-skip bug found and fixed |
| Daily sync (M10) | the real workspace | every stage ran in 21 seconds at zero tokens |
| From scratch, run 1 (2026-10-17) | a new workspace from the user's intake, master and 15 v1 job folders, engine C | setup checks held. Found: 30 of 127 boards wrong, no link from job folders to the queue (approve never reached a sheet, interview mail matched nothing, v1 roles scored again), hybrid jobs passing remote-only, a token estimate 18 times the measured day. Fixed in the PR that follows |
| From scratch, run 2 (2026-10-18) | the same inputs on the fixed branch, engine C, no hand edits to tool data | no v1 role re-scored; Grow and Netflix mail matched their folders; a v1 pack reached an apply sheet through the hub; the 30-day first read cost about 92K tokens once. Found: interview mail from a hiring address filed as a cold lead, newsletters filed as assessments, old mail able to land on a job queued later. Fixed before run 3 |
| From scratch, run 3 (2026-10-19) | the same inputs and run 2's mail replayed, engine C; a second-day read; Phase 5 from the queue on a copy | the hiring-address interview mail filed as an interview for its folder, newsletters as other, nothing pinned by mistake; the second read skipped its overlap with no duplicates; a newly approved job went through `show`, a pack, `link` and a complete apply sheet. Found: mail matched on arrival could still move a job never sent; fixed with one date-and-title rule for every event |

| Workday and Eightfold sources (2026-10-21) | Zillow's Workday board and Netflix's Eightfold board, live | 25 Zillow and 32 Netflix security postings at zero tokens (Netflix in 25 seconds, polled slowly after a 429). The careers-page probe found Arctic Wolf's Workday site and a second Greenhouse slug for Cerebral |
| Automatic apply form filler (2026-10-22) | dry runs, nothing submitted, test persona data, on live Anthropic, Datadog (Greenhouse), Snyk (Ashby) and Lyra Health (Lever) forms | contact fields, résumé upload, yes/no buttons, dropdowns and multi-selects filled; every form stopped on a question only the user can answer (an essay, an office-attendance or legal question). Found and fixed with tests: required questions whose asterisk is drawn by CSS were skipped, dropdowns a few pixels wide were missed, a browser-blocked submit read as unclear |

## Still beta, and why

- **Engine A's live Google sign-in** has run only against a fake Google server. It needs the user's own
  OAuth client (`docs/GMAIL-SETUP.md`), which only the user can create.
- **Automatic apply has not submitted a real application yet.** It is built and tested against local fake
  forms and live forms in dry runs. The user chose to ship it before the 50-send callback number in spec
  criterion 6 exists (`docs/superpowers/specs/2026-10-22-ascend-v2-auto-apply-design.md` §2); the caps and
  the reply-rate pause are the guard. Every real form carries an invisible bot check that may reject a
  headless submission; how often is unknown until it runs.
- **Claude submitting on its own ("agent" mode) is not offered.** Claude fills stopped jobs only with the
  user and submits after a yes in chat for that batch.
- **Token figures are estimates** (characters divided by four). Each stage replaces its default once three items are
  recorded (one batch of 25 scored jobs counts as 25), and the hub labels them as estimates.
- **LinkedIn card leads carry no description**, so they rank last on keyword overlap until enriched.
- The design's release gate stands: assisted mode with engine A becomes stable after one week of real use, and
  everything else stays beta until it has run for real.

## Not built from the spec

Spec §11 has the reasons. In short: no Sources & settings tab (edit `data/sources.json`), no 48-hour
"applied?" follow-up, no per-run token cap, no board backoff and retry, no automatic fallback from engine
A to C, and cron instead of launchd (a sleeping Mac skips that day's sync).

## Risks you accept by turning things on

- **Automatic apply** submits applications in your name without asking each time. Some job boards' terms
  forbid automated applications. Ascend does nothing to get past bot checks, so some submissions may be
  rejected and land in Needs you. A wrong answer in `apply-answers.json` or `answer-bank.json` is repeated on
  every form until you fix it.

- **LinkedIn search** drives your own logged-in LinkedIn session. Automated browsing can break LinkedIn's
  terms of use and put the account at risk. Claude asks before every search.
- **Engines B and C** let Claude read your Gmail through the claude.ai connector, limited to job senders
  and job subjects. Its write tools are denied in this repo's `.claude/settings.json`. Mail is untrusted and
  the same session can fetch web pages. This repo asks you before every `WebFetch`, so a fetch an email
  asked for needs your yes; on engine C, `"deny": ["WebFetch"]` in your own `.claude/settings.local.json`
  rules fetches out. The search also misses a recruiter writing from a personal
  address with no job word in the subject, and a thread whose subject names only the company ("Acme:
  Thursday?"). Engine A reads all mail and has neither gap.
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
