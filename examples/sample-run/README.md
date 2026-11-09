# 🧪 FICTIONAL SAMPLE, Jordan Rivera

> **🧪 FICTIONAL SAMPLE: every name, number, company, and link is invented.**
> Nothing here is real. There is no Jordan Rivera. The phone number (111-111-1111) and email
> (xyz@abc.org) are deliberately fake. Every company is a made-up Acme name ("Acme Pay," "Acme
> Corp," "Acme Inc," "Acme Health," "Acme Retail," and so on). Every metric, referral name, and job
> link is invented for demonstration, and all links point to `example.com` placeholders that **do
> not** lead to live postings. Real runs go in `workspace/<name>/` and are never committed.

## What this is

A complete worked example of what Ascend produces end to end, so you can inspect the structure and
quality of the output without running the pipeline yourself.

## The persona

**Jordan Rivera, Senior Software Engineer (backend and platform)**, 9 years' experience, based in
Austin, TX (remote or hybrid). Targeting **Staff / Senior Software Engineer** roles on platform and
backend teams at B2B SaaS, fintech, health, and commerce companies.

- **Strengths:** internal platforms teams adopt, reliability and performance on services that carry
  money, design docs and mentoring.
- **Honest gaps (handled, never hidden):** no people-management *title* (an IC who mentors), no
  production ML, limited front-end.
- **Invented career arc:** Senior Software Engineer at *Acme Pay* (fintech) → Software Engineer II at
  *Acme Corp* (logistics marketplace) → Software Engineer at *Acme Inc* (a software consultancy).

## File tour

| File | What it is |
|---|---|
| `intake.md` | The intake summary, the run's source of truth |
| `linkedin-analysis.html` | Phase 1 dashboard: findability score, keyword gaps, 10 next steps (open in a browser) |
| `master-resume.md` | Phase 3: the private superset every per-job resume is *selected* from (the ATS/keyword audit is folded in, there's no separate audit file). |
| `master-resume.json` · `Jordan-Rivera-Resume.pdf` | The public master résumé as JSON Resume data + a one-page ATS-safe PDF rendered by `tools/render_resume.py`. |
| `job-queue.md` | Phase 4: **15 ranked fictional jobs**, each with an explainable Fit Score (0–100) + a watch list. |
| `interview-packet/` | Phase 6: STAR stories, project deep-dives, metrics cheat-sheet |
| `jobs/01-…/` | Phase 5: a **CORE apply pack** (`resume.md` · `outreach.md` · `application-log.md`) **plus** the on-demand **deep-prep pack** (`prep-doc` · `interview-questions` · `interview-prep` · `company-research` · `signal`), what a job looks like once a screen books. Also carries `resume.json` + a rendered one-page PDF. |
| `jobs/02-…/` | Phase 5: a **CORE apply pack only** (the 3 files), what a committed job looks like before a screen is booked. Deep prep isn't built speculatively. |
| `start-here.html` | Phase 7: the navigator / front door (open in a browser) |

## How to read it

1. Open **`start-here.html`** in a browser. It's the front door and links to everything.
2. Open **`linkedin-analysis.html`** to see the Phase 1 dashboard.
3. Read **`master-resume.md`** to see the superset, then open **`jobs/01-…/resume.md`** to see how a
   per-job resume is *selected* from it (the Delta Log cites the master entry IDs `E#`). The same job's
   **`resume.json`** + **`Jordan-Rivera-Resume-Acme-Health.pdf`** show the JSON Resume data model
   and the one-page ATS-safe PDF.
4. Compare **`jobs/01-…/`** (full: CORE + deep prep, the post-screen state) with **`jobs/02-…/`**
   (CORE only, the pre-screen state) to see the lazy two-tier model.
5. The HTML files are self-contained and render offline: no build step, no network.

## A note on the numbers

Every metric is invented but shaped to be *realistic* for the role: p99 latency, deploy lead time,
incident counts, compute cost, CI time. In a real run, these would trace to the user's LinkedIn
export, resume, or intake answers, and sensitive employer-internal figures would be sanitized before
they reach anything sendable.
