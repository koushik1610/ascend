# The Ascend console (`/ascendui`)

A graphical, no-typing way to start Ascend. Open Claude Code in the repo and run:

```
/ascendui
```

A small local server starts and your browser opens a **Jarvis-style console**: it greets you, then
walks you through a 5-step intake — *did you download your LinkedIn data?* (yes → native folder picker,
or **No → show me how**), your résumé, target roles, an honest calibration step, and an optional
**daily-brief time**. When you finish, Ascend runs the whole pipeline and the console shows each phase
completing, ending with an **Open my dashboard** button.

## How it actually works (and why a server)
A browser tab can't, on its own, read your folders, run an AI, or schedule a job — browsers sandbox all
of that for safety. So `/ascendui` starts **`ui/server.py`**, a tiny server built on the Python 3
**standard library only** (no installs), bound to **`127.0.0.1` (your machine only)**. It does the
real work the browser can't: native folder/file pickers, writing your `intake.md`, installing the
daily-brief schedule, reporting pipeline progress, and serving your dashboard. Nothing leaves your
machine; everything it writes is under `workspace/<you>/`, which is gitignored.

**Why it's safe even though a localhost port is technically reachable by other tabs:** the server
defends against CSRF and DNS-rebinding — it only answers requests whose `Host` is `127.0.0.1`/`localhost`
(so a rebound hostname is rejected), and every `/api/*` call requires a per-session token injected into
the console page (a random website can't read that token, so it can't drive the API). It sends no CORS
headers, so other origins can't read your `workspace` files either.

```
/ascendui ──► Claude Code starts ui/server.py (localhost) ──► browser opens the console
   console wizard ──► server writes workspace/<you>/intake.md + a "ready" flag
   Claude Code sees the flag ──► runs the pipeline ──► writes progress to .ascend-state.json
   console shows it LIVE (phase board + activity feed) ──► "Open my dashboard" ──► start-here.html
```

**You watch it in the browser, not the terminal.** Once you finish the wizard, the console shows each
phase completing and a live activity feed — you never have to switch back to the terminal. And because
the repo ships a **scoped `.claude/settings.json`** that pre-approves the pipeline's tools (workspace
writes + web research + a few commands; see `CLAUDE.md → Permissions`), the run goes **straight through
without stopping for approval prompts**. The agent process still lives in your Claude Code session — but
you don't have to look at it.

**When it finishes, the results open right in the console** — a left-hand list of every output (Start
here, LinkedIn analysis, Master résumé, Job queue, Interview packet, your apply packs) with a reading
pane beside it. HTML dashboards render as-is; Markdown files render as clean, dark documents (the server
turns them into styled HTML offline — no CDN). "Open full dashboard ↗" pops `start-here.html` out to its
own tab.

## What you need (the honest part)
- **Python 3** — preinstalled on macOS and Linux. (Windows: install Python, then see notes below.)
- **An agentic CLI that can read local files + search the web** — this is the engine that does the
  analysis. **Claude Code** is the reference. The console and the daily brief also **auto-detect
  `gemini` (Gemini CLI) and `codex` (Codex CLI)** and use whatever you have.
- ⚠️ **A free *web-chat* tier (claude.ai / chatgpt.com / gemini.google.com) cannot drive this** — those
  websites can't read your local files (a browser security limit, not an Ascend choice). The closest
  free path is a free **CLI** tier (e.g., Gemini CLI's free tier). The UI, folder picker, and
  scheduling work with just Python; the *intelligence* needs a local agent CLI.

## The daily brief
**Off by default (beta).** The preferred path is on demand: say **"Ascend today"** in Claude Code for
the same briefing with you watching. The unattended scheduler is opt-in behind a notice in Step 5 — it
runs your agent CLI on a timer with no human in the loop, on content it fetches, and isn't proven
end-to-end on real data yet. If you opt in, the server installs a **cron job** (macOS/Linux) that runs
`ui/run-daily-brief.sh <you>` at the time you pick. The wrapper detects your agent CLI and runs the
**Daily Briefing** (Phase 13) headlessly, writing `workspace/<you>/daily-briefing.md`. Turn it off by
removing the `# Ascend-DAILY-BRIEF-<you>` line from `crontab -e`.

- **Headless runs vary by CLI.** Non-interactive agent runs that touch files/web may need the CLI
  configured for that (permissions/flags). If the scheduled run can't complete, just open Claude Code
  and say **"Run Ascend today"** — same briefing, manually.
- **Windows** has no cron: the console will show the command to register in **Task Scheduler** instead,
  or run the brief manually with "Run Ascend today."

## Prefer typing? Use `/ascend`
The console is optional sugar. The text flow (`/ascend`) does everything the same way in chat, and is
the better path if you like the terminal or are on a platform where the GUI bits don't apply.

## The résumé builder
The server does double duty as the résumé PDF engine. Two entry points:

- **`python3 ui/server.py --render <filled.html> --out <Name>-Resume-<Company>.pdf`** — a one-shot
  headless render (no server started). It detects a Chrome-class engine (Chrome/Chromium/Edge/Brave)
  and prints the résumé to a one-page, ATS-safe, text-selectable PDF using the template's own print CSS.
  If no engine is found it exits with the two-click "open and Save as PDF" fallback. This is what
  `prompts/08-export-pdf.md` calls automatically in Phases 3 and 5.
- **`/resume-builder`** (served while the console runs) or just opening
  `templates/resume-builder.template.html` in a browser — the **standalone builder**: a form with a
  live preview, a one-page boundary warning, and **Create PDF / Sample / Export / Import / Clear**. Data
  round-trips as `resume.json` (JSON Resume schema). Reachable via `/ascend build-resume`.

## Files here
- `server.py` — the local control server + résumé PDF renderer (stdlib only; shells to Chrome for `--render`).
- `index.html` — the console UI (self-contained; talks only to the local server).
- `run-daily-brief.sh` — the cron wrapper that runs the daily brief with your agent CLI.
- `.port` — runtime file with the chosen port (gitignored).
