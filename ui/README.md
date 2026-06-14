# The SPIDER console (`/spiderui`)

A graphical, no-typing way to start SPIDER. Open Claude Code in the repo and run:

```
/spiderui
```

A small local server starts and your browser opens a **Jarvis-style console**: it greets you, then
walks you through a 5-step intake — *did you download your LinkedIn data?* (yes → native folder picker,
or **No → show me how**), your résumé, target roles, an honest calibration step, and an optional
**daily-brief time**. When you finish, SPIDER runs the whole pipeline and the console shows each phase
completing, ending with an **Open my dashboard** button.

## How it actually works (and why a server)
A browser tab can't, on its own, read your folders, run an AI, or schedule a job — browsers sandbox all
of that for safety. So `/spiderui` starts **`ui/server.py`**, a tiny server built on the Python 3
**standard library only** (no installs), bound to **`127.0.0.1` (your machine only)**. It does the
real work the browser can't: native folder/file pickers, writing your `intake.md`, installing the
daily-brief schedule, reporting pipeline progress, and serving your dashboard. Nothing leaves your
machine; everything it writes is under `workspace/<you>/`, which is gitignored.

```
/spiderui ──► Claude Code starts ui/server.py (localhost) ──► browser opens the console
   console wizard ──► server writes workspace/<you>/intake.md + a "ready" flag
   Claude Code sees the flag ──► runs the pipeline ──► writes .spider-state.json
   console polls progress ──► "Open my dashboard" ──► start-here.html
```

## What you need (the honest part)
- **Python 3** — preinstalled on macOS and Linux. (Windows: install Python, then see notes below.)
- **An agentic CLI that can read local files + search the web** — this is the engine that does the
  analysis. **Claude Code** is the reference. The console and the daily brief also **auto-detect
  `gemini` (Gemini CLI) and `codex` (Codex CLI)** and use whatever you have.
- ⚠️ **A free *web-chat* tier (claude.ai / chatgpt.com / gemini.google.com) cannot drive this** — those
  websites can't read your local files (a browser security limit, not a SPIDER choice). The closest
  free path is a free **CLI** tier (e.g., Gemini CLI's free tier). The UI, folder picker, and
  scheduling work with just Python; the *intelligence* needs a local agent CLI.

## The daily brief
If you pick a time, the server installs a **cron job** (macOS/Linux) that runs
`ui/run-daily-brief.sh <you>` at that time. The wrapper detects your agent CLI and runs the
**Daily Briefing** (Phase 13) headlessly, writing `workspace/<you>/daily-briefing.md`. Turn it off by
removing the `# SPIDER-DAILY-BRIEF-<you>` line from `crontab -e`.

- **Headless runs vary by CLI.** Non-interactive agent runs that touch files/web may need the CLI
  configured for that (permissions/flags). If the scheduled run can't complete, just open Claude Code
  and say **"Run SPIDER today"** — same briefing, manually.
- **Windows** has no cron: the console will show the command to register in **Task Scheduler** instead,
  or run the brief manually with "Run SPIDER today."

## Prefer typing? Use `/spider`
The console is optional sugar. The text flow (`/spider`) does everything the same way in chat, and is
the better path if you like the terminal or are on a platform where the GUI bits don't apply.

## Files here
- `server.py` — the local control server (stdlib only).
- `index.html` — the console UI (self-contained; talks only to the local server).
- `run-daily-brief.sh` — the cron wrapper that runs the daily brief with your agent CLI.
- `.port` — runtime file with the chosen port (gitignored).
