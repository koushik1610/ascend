# Auto-apply and Workday/Eightfold sources: implementation plan

> Executed inline (superpowers:executing-plans). Spec: `docs/superpowers/specs/2026-10-22-ascend-v2-auto-apply-design.md`.

**Goal:** fully automatic apply for Greenhouse, Ashby and Lever with a local Playwright runner, plus
Workday and Eightfold job sources, then a council release loop on all of v2.

**Architecture:** stdlib tools as today. Playwright is imported only in `tools/autoapply_forms.py`.
Gates live in `apply.py` so the hub sheet, the runner and Claude's batch step share them.

## Global constraints
- Stdlib only outside `autoapply_forms.py`. Python 3.9+ syntax.
- Prose follows ai-deslop: no em-dashes. Never `git add` anything under `workspace/`.
- Nothing is marked applied without a seen confirmation. Approval-free sending only when `auto.json` is
  valid, enabled and not paused.
- Gate after every task: unit suites + smoke green.

## Review focus
1. Lookalike hosts and URL tricks reaching the runner (userinfo, suffix, IDN, backslash).
2. A forged or hand-edited `auto.json` turning sending on.
3. A crash mid-submit leaving a job in `applying` forever, or counted as applied.
4. A form whose confirmation never appears (marked unclear, not applied).
5. Workday pagination and 429 from Eightfold not closing open postings.

## Tasks

### Task 1: Workday and Eightfold in the finder
Files: `tools/finder.py`, `tests/test_v2_finder.py`.
- `fetch_board(ats, slug, board=None, filters=None)`; Workday: paged POST list, detail GET for rows whose
  title passes the filters; Eightfold: paged GET with 2 s spacing; 429 raises `Throttled`.
- `normalize` handles `workday` and `eightfold`; ids `workday:{slug}:{reqid}`, `eightfold:{slug}:{id}`.
- `run` records `throttled` in board-health and never closes postings on a throttled board.
- `probe_careers(url)` parses Workday and Eightfold links into a board entry.
- Tests: fake server for both, pagination, title-filtered detail, 429 → throttled and nothing closed,
  probe parsing, apply URL built only from the board entry.

### Task 2: auto.json and its controls
Files: `tools/autoapply.py` (config part), `ui/server.py`, `tests/test_v2_autoapply.py`.
- `load_config(ws)` → dict or None when missing, unsigned or tampered; `save_config(ws, cfg)` signs with
  HMAC-SHA256 using a key at `~/.config/ascend/auto.key` (0600, created on first save).
- `POST /api/auto` actions: `enable` (needs phrase `apply for me`), `pause`, `resume`, `settings`
  (cap 1..50, fit 50..100). CLI: `autoapply.py pause`, `status`. No CLI enable or resume.
- Tests: enable without phrase refused, tampered file refused, CLI has no enable, first-week cap.

### Task 3: gates shared by sheet, runner and Claude
Files: `tools/apply.py`, `tests/test_v2_apply.py`.
- `pack(ws, entry)` (folder, single PDF, lint, stale, same role, duplicate) used by `sheet`.
- `apply_url_for(ws, posting_id)` rebuilds from the board: Greenhouse `job-boards.greenhouse.io/{slug}/jobs/{id}`,
  Ashby `jobs.ashbyhq.com/{slug}/{id}/application`, Lever `jobs.lever.co/{slug}/{id}/apply`; else None.
- `allowed(url)` exact host set, https, no userinfo/port/backslash/encoded slash.
- `ready(ws, entry, cfg)` → `[]` or the reasons; company cap 2 per 30 days.
- `answers(ws)` merges profile + apply-answers + answer bank.
- Tests per gate and the lookalike host list.

### Task 4: the runner
Files: `tools/autoapply.py`, `tools/autoapply_forms.py`, `tools/jobqueue.py`, `tests/test_v2_autoapply.py`,
`tests/fixtures/forms/*.html`.
- `jobqueue.set_state(..., via_runner=True)` allows `applying`, `applied`, `needs-you` from the runner.
- `run(ws, dry_run=False, limit=None, fill=None)`: pick ready jobs by fit, cap remaining, mark applying,
  call the filler, record result, screenshots, auto-pause rules. A stale `applying` (> 1 h) becomes
  `needs-you` with reason "interrupted, check the ATS before retrying".
- `autoapply_forms.fill(page, url, answers, resume, submit)` → `{result, reason, unfilled, shots}`.
- Tests: fake gate-level runs with a stub filler (stdlib), Playwright runs against fake forms
  (skipped with a reason when Playwright is missing).

### Task 5: daily stage, hub, auto-pause
Files: `tools/daily.py`, `tools/hub.py`, `templates/hub.template.html`, tests.
- `autoapply` stage after prefilter/alerts: skipped unless enabled; never raises on missing Playwright.
- Hub: Auto-apply panel (state, today's count/cap, pause reason, switch + phrase box), Needs you reasons,
  "submitting" label, throttled boards.

### Task 6: settings, docs, prompts
Files: `.claude/settings.json`, `CLAUDE.md`, `reference/untrusted-content-policy.md`, `README.md`,
`docs/V2-READINESS.md`, `CHANGELOG.md`, `prompts/28-apply.md`, `prompts/29-run-v2.md`,
`templates/apply-answers.example.json`, `templates/answer-bank.example.json`, smoke parity.

### Task 7: live run
Fresh workspace `koushik-v2d` from the original inputs, Workday/Eightfold boards added, full run,
runner `--dry-run` on real Greenhouse/Ashby/Lever jobs, screenshots checked.

### Task 8: council release loop
Full council over all of v2 until 10 APPROVE. Fixes with tests into this PR, rerun after each round.
