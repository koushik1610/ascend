---
description: Launch the graphical S.P.I.D.E.R. console — a local Jarvis-style intake wizard that collects your info, schedules the daily brief, and shows the pipeline running. Then run the pipeline from what it captured.
---

Launch the **SPIDER console** (the graphical front end) and then drive the pipeline from what it
collects. Do this in order:

## 1. Start the local console server (background)
Run the server in the background so it keeps serving while you continue:
```
python3 ui/server.py
```
Use the Bash tool with `run_in_background: true`. The server binds to `127.0.0.1`, finds a free port,
writes it to `ui/.port`, prints `SPIDER console → http://127.0.0.1:<port>/`, and **opens the browser
automatically**. (Requires Python 3 — preinstalled on macOS/Linux. If `python3` is missing, tell the
user to install it or use the text flow `/spider` instead.)

Then tell the user: *"Your SPIDER console is open in the browser — complete the short intake there
(name, LinkedIn folder, target roles, daily-brief time). I'll start working the moment you finish."*

## 2. Wait for the intake (don't ask the questions again in chat)
The console writes `workspace/<slug>/intake.md` and a `workspace/<slug>/.ui-ready` flag when the user
finishes the wizard. **Poll** for that flag (e.g., check every ~10–15s with a bounded loop, or use a
short `until` loop) — do NOT re-interview the user in the terminal; the UI already did it. When a
`.ui-ready` file appears under any `workspace/*/`, read that folder's `intake.md`.

## 3. Run the pipeline in UI mode
With `intake.md` in hand, run the normal default pipeline from `prompts/00-orchestrator.md`
(order **1 → 3 → 4 → 6 → 5 → 7**), with two UI-mode adjustments:
- **Skip the Step-1 intake interview** — it's already captured. Confirm the LinkedIn export + résumé
  paths from `intake.md` resolve; if a path is missing, proceed with the documented fallback and note
  it (don't block waiting on the browser).
- **Update `workspace/<slug>/.spider-state.json` after each phase** with `"phases": {"1":"done", ...}`
  using the phase numbers `1,3,4,6,5,7`. The console polls this to advance its progress board, and
  enables "Open my dashboard" once `start-here.html` exists.

Keep the per-phase checkpoints brief in UI mode (the user is watching the browser), but still honor the
honesty gates, number policy, and lazy-by-default tiering (apply packs for the top 3–5 only).

## 4. Finish
When `start-here.html` is written, tell the user the dashboard is ready (the console's button is now
live) and summarize the top 3 next actions. If they scheduled a daily brief, confirm it's set. The
server can keep running (it serves the dashboard); the user can close the terminal/console when done,
or POST `/api/shutdown` from the console.

**Honesty note for the user (say it once):** the console + folder picker + daily-brief scheduling run
locally with just Python. The *analysis* uses your installed agent CLI (Claude Code here; the daily
brief auto-detects claude/gemini/codex). A fully-free *web-chat* tier can't read your local files —
that's a browser limit — so this needs a local agent CLI, not the website.
