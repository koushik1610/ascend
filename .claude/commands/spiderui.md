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
finishes the wizard. **Poll** for that flag (e.g., check every ~10–15s with a bounded loop) — do NOT
re-interview the user in the terminal; the UI already did it. When `.ui-ready` files exist under
`workspace/*/`, pick the **most recently modified** one (a fresh run must win over a stale flag from a
previous run), use its parent folder as the slug, then **delete that flag** (`rm -f workspace/<slug>/.ui-ready`) before
proceeding (so it can never mis-route a later run). Read that folder's `intake.md`.

## 3. Run the pipeline in UI mode — keep the browser the surface
With `intake.md` in hand, run the normal default pipeline from `prompts/00-orchestrator.md`
(canonical order **1 → 3 → 4 → 6 → 5 → 7**; defined in `00-orchestrator.md`). The user is watching the **browser**, not the terminal — so drive the
console, don't ask the user to switch back. UI-mode adjustments:

- **Skip the Step-1 intake interview** — it's already captured. Confirm the LinkedIn export + résumé
  paths from `intake.md` resolve; if a path is missing, proceed with the documented fallback and note it
  in the log (don't block waiting on the browser).
- **Don't stop for per-phase checkpoints in UI mode** — the committed `.claude/settings.json` pre-approves
  the pipeline's tools (workspace writes + web research + a few commands), so run **straight through**
  without pausing for approval or confirmation. (If something genuinely outside that allow-list comes up,
  surface it briefly in the log rather than silently hanging.)
- **Write live progress to `workspace/<slug>/.spider-state.json`** so the console's live feed updates.
  After every phase boundary — and ideally at the start of long phases too — write the JSON with:
  - `"phases": {"1":"done", "3":"in-progress", ...}` using phase numbers `1,3,4,6,5,7`,
  - `"current": "<one short line of what's happening now>"` (e.g. *"Searching for jobs — 12 candidates so far…"*),
  - `"log": [ … ]` — a growing list of short human-readable lines (append, keep the last ~14), e.g.
    `"▸ Phase 1 — analyzing your LinkedIn presence"`, `"✓ Master résumé built (24 bullets)"`,
    `"▸ Phase 4 — searching jobs…"`, `"✓ 16 candidates ranked"`. Keep them friendly and specific; this
    is what the user reads instead of the terminal.
  The console enables "Open my dashboard" automatically once `start-here.html` exists.

Honor the honesty gates, number policy, and lazy-by-default tiering (apply packs for the top 3–5 only).

## 4. Finish
When `start-here.html` is written, tell the user the dashboard is ready (the console's button is now
live) and summarize the top 3 next actions. If they scheduled a daily brief, confirm it's set. The
server can keep running (it serves the dashboard); the user can close the terminal/console when done,
or POST `/api/shutdown` from the console.

**Honesty note for the user (say it once):** the console + folder picker + daily-brief scheduling run
locally with just Python. The *analysis* uses your installed agent CLI (Claude Code here; the daily
brief auto-detects claude/gemini/codex). A fully-free *web-chat* tier can't read your local files —
that's a browser limit — so this needs a local agent CLI, not the website.
