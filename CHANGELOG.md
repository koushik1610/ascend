# Changelog

All notable changes to S.P.I.D.E.R. Format loosely follows [Keep a Changelog](https://keepachangelog.com/);
versioning is [SemVer](https://semver.org/).

## [Unreleased]

## [0.2.0] — 2026-06-13
A simplification + re-targeting release (from a second council review). Same capabilities, far less
speculative output, and a modern README.

### Changed — leaner workflow (the headline)
- **Tiered job folders.** A folder is now a **CORE apply pack** (`resume.md` · `outreach.md` ·
  `application-log.md`) built only for the **top 3–5 jobs you commit to**, plus a **deep interview-prep
  pack** built **on demand** when a screen is booked (`prompts/10-deep-prep.md`, `/spider prep <NN>`).
  A first run now produces ~25–30 files instead of ~100 — no deep prep for leads that never call back.
- **Resume audit folded into the master resume** (was a standalone Phase 2). Keyword set is derived
  once (master §4) and reused downstream instead of re-computed per phase.
- **Default order is now 1 → 3 → 4 → 6 → 5 → 7**, with 02/08/09/10 on demand.

### Added — targeting the real objective (interviews, not paperwork)
- **Weekly action loop + scoreboard** on the navigator: apply-N / ask-N-referrals targets and a
  referrals→applied→screening→onsite→offers funnel up top; `"SPIDER today"` action list.
- **Referral-first hard gate** in `application-log.md` — can't mark "applied" until a referral was
  attempted or explicitly waived.
- **Mock-interview drill** in the on-demand prep pack (reps, not just reading).
- Single-source job status (`application-log.md` → navigator JSON) to prevent drift.

### Added — brand & docs
- `assets/spider-banner.svg` (static, dashboard-token brand mark) and a modernized README: banner,
  badges, tagline, demo-GIF slot, collapsible sections, ASCII spider, "see a fictional run" link.

## [0.1.0] — 2026-06-13
First public version. A reusable, Claude Code-driven job-search pipeline.

### Added
- **7-phase pipeline** (`prompts/00-orchestrator` + `01`–`07`): intake interview → LinkedIn analysis
  (HTML + 10 next steps) → resume audit → master resume → 15+ job search → per-job folders (8 files
  each) → interview packet → `start-here.html` navigator.
- **Utility phases:** `08-export-pdf` (ATS-safe Markdown→PDF) and `09-maintenance` (weekly job
  refresh + diff, outreach cadence, follow-ups/deadlines, comp research, retro-learning digest).
- **Templates:** job-folder 8-file spec, master-resume, signal, job-queue, interview-packet,
  `resume-print` (ATS-safe print shell), and two self-contained dashboards (linkedin-analysis,
  start-here) driven by a validated JSON data block.
- **Reference rules:** ATS/keywords, resume-writing, number-&-honesty policy, interview-prep framework.
- **Resumability:** `.spider-state.json` run manifest + `resume`, `job add`, `job rebuild`, `score`,
  `export`, `maintenance` operations via the `/spider` command.
- **Privacy model:** everything personal under gitignored `workspace/`; PII banners on both dashboards;
  a fictional worked example under `examples/sample-run/`.
- **Docs:** comprehensive `README`, `START-HERE`, non-technical `docs/SETUP.md`, `CONTRIBUTING`,
  `.github/` issue & PR templates.

### Fixed
- **Privacy:** closed a `.gitignore` re-include hole where personal data dropped into
  `examples/`/`templates/`/`reference/`/`prompts/` was not ignored. Verified with `git check-ignore`.

### Honesty
- Reframed the job-search promise to an honest "15+ candidates, N independently link-verified" with a
  real per-link fetch/status gate, instead of asserting all links are live.
