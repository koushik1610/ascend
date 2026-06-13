---
description: Start the S.P.I.D.E.R. job-search pipeline (intake interview → LinkedIn analysis → resume audit → master resume → 15+ jobs → per-job folders → navigator)
---

Run S.P.I.D.E.R. Follow `prompts/00-orchestrator.md` from the top: begin with the intake interview
(name, LinkedIn export location, resume location, target roles/companies/location/comp, differentiators,
honest gaps, any sanitization needs), reflect back an Intake Summary for confirmation, then build
`workspace/<name>/` and drive phases 1–7, pausing at a checkpoint after each.

If the user passed a phase number or name in `$ARGUMENTS` (e.g. "Phase 4"), skip the interview, read
`workspace/<name>/intake.md` for context, and run that phase directly from its `prompts/` file.

Honor the binding rules in `CLAUDE.md`: person-agnostic, honesty gates absolute, selection-not-invention,
all personal output under `workspace/` only, never commit personal data.
