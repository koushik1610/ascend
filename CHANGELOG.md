# Changelog

All notable changes to S.P.I.D.E.R. Format loosely follows [Keep a Changelog](https://keepachangelog.com/);
versioning is [SemVer](https://semver.org/).

## [Unreleased]

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
