# Find, apply, track (beta)

The apply packs get your first applications out. This layer keeps the search running: it finds
matching roles every day, prepares the applications you approve, and reads your inbox to track what
happened. Everything runs on your machine. **You submit every application yourself. Ascend never
sends one.**

```
every day, zero tokens    finder (public ATS boards) → prefilter → alerts → Gmail sync → classify → ledger → hub
when you run it           score the survivors (Phase 27) → you approve → apply (Phase 28) → hub
```

Start it with `/ascend run-v2` after a first `/ascend` run. The prompt is
[`prompts/29-run-v2.md`](../prompts/29-run-v2.md).

## Pick an engine

You choose the engine per run, and see the token estimate and the permissions before anything is
spent: `python3 tools/run.py plan workspace/<you> --engine A`.

| Engine | How it gathers | Setup |
|---|---|---|
| **A** deterministic core | Python reads the job boards and your Gmail (your own Google sign-in, read-only) | a Google Cloud OAuth client, once ([gmail-setup.md](gmail-setup.md)) |
| **B** agent-driven | Claude does every stage, including web search | none, but the most tokens |
| **C** core + connector | Python reads the boards. Claude reads Gmail through the claude.ai connector | none |

## What you grant

`run.py plan` prints this list every time.

| | Engine A | Engines B and C |
|---|---|---|
| Gmail | Your own Google OAuth client, `gmail.readonly` scope. Ascend cannot send, change or delete mail. The token stays in your macOS Keychain. | Claude reads your mail through the claude.ai Gmail connector. Its write tools (send, reply, forward, drafts, labels, spam, trash) are denied in `.claude/settings.json`. |
| Google Drive | Not used. | Share, create, update, copy and trash are denied. |
| Web | Public job-board APIs, read only. Page fetches ask you every time. | B adds Claude's web searches. Page fetches ask you every time. |
| Applications | Never submitted by Ascend. Claude in Chrome's form-input, upload, scripting and batch tools are denied. It can still click and type, so keep its per-action prompts on. | Same. |
| Approve, "I submitted it" | Your click in the hub, with a confirm. Claude's file tools cannot edit the queue or the apply log. | Same. |

Engines B and C search Gmail with a query limited to job senders and job subjects: 30 days on the
first read, then from the day before the last read. Your own sent mail is never stored, but a thread
Claude opens still shows your replies in that session.

The mail Claude reads is untrusted, and the same session can fetch web pages. Claude treats mail as
data, and this repo's settings ask you before every web fetch, so a fetch an email asked for still
needs your yes. Deny beats ask beats allow, so a narrower allow in a local file cannot skip that
question. On engine C, which never needs a fetch, you can add `"deny": ["WebFetch"]` to your own
`.claude/settings.local.json`.

**LinkedIn search** is opt-in on every engine. It drives your own logged-in LinkedIn session through
Claude in Chrome and reads result cards only. Automated browsing can break LinkedIn's terms of use and
put the account at risk, so Claude asks before each search.

## First run

`/ascend run-v2` sets up two files with you:

- `data/profile.json`: the only answers an apply sheet pre-fills. Claude asks for your contact details
  and shows you the file.
- `data/sources.json`: the company boards to watch and your filters. Find each board with
  `python3 tools/finder.py probe "Company"`, because a guessed slug fails quietly. Companies on Workday
  or their own career sites cannot be watched.

`run.py plan` will not start until both exist. Job folders from your first run join the queue
(`jobqueue.py sync`), so their mail is tracked and their roles are not scored again. Restart
`python3 ui/server.py` after updating Ascend: the server keeps the tool code it started with.

## Applying

For each job you approve, the hub shows an apply sheet: the answers to copy, the résumé to attach and
the application link. You submit, then press **I submitted it**. The sheet is built only when the job
is approved, it is not a duplicate, its résumé passes the linter, and every answer comes from your own
`data/profile.json`. Work authorization, sponsorship, salary and start date are always left for you.

## The hub and the daily sync

- **Hub:** `python3 tools/hub.py build workspace/<you>`, or served with actions at `/hub?slug=<you>`.
  It shows the funnel from found to offer, this week's applications, replies and interviews, mail
  waiting on you with its due date, a queue you approve from, a classified inbox, and token spend.
- **Schedule:** `python3 tools/schedule.py install workspace/<you> --at 06:30` runs the zero-token part
  every morning (cron skips the run if the Mac is asleep). It also deletes mail older than 180 days
  from the workspace and keeps only the headers of mail that is not about a job.

What has run on real data: [history/v2-readiness.md](history/v2-readiness.md).
