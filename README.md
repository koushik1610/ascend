<div align="center">

<!-- Banner: the SVG below is the on-brand fallback. Once you generate the raster banner,
     save it as assets/ascend-banner.png and swap the next line to:
     ![Ascend](assets/ascend-banner.png) -->
![Ascend](assets/ascend-banner.svg)

**AI-run job search and career advancement, grounded in your real history.**

![License: MIT](https://img.shields.io/badge/License-MIT-5b9dff?style=flat-square)
&nbsp;![CI](https://github.com/koushik1610/ascend/actions/workflows/ci.yml/badge.svg)
&nbsp;![Built for Claude Code](https://img.shields.io/badge/built%20for-Claude%20Code-5b9dff?style=flat-square)
&nbsp;![Version](https://img.shields.io/badge/version-v0.4.0-8b97a7?style=flat-square)
&nbsp;![PRs welcome](https://img.shields.io/badge/PRs-welcome-36d399?style=flat-square)
&nbsp;![Data stays local](https://img.shields.io/badge/data-stays%20local-36d399?style=flat-square)

**Your entire job search, run by an agent that doesn't make things up.**
From your LinkedIn export to tailored applications and interview prep — one command, zero fabrication.
Works for any field: engineering, design, product, marketing, ops.

[**▶ See a full fictional run**](examples/sample-run/) &nbsp;·&nbsp; [Quickstart](#quickstart) &nbsp;·&nbsp; [How it works](#how-it-works) &nbsp;·&nbsp; [User journeys](WORKFLOW.md) &nbsp;·&nbsp; [Setup for non-coders](docs/SETUP.md)

</div>

<!-- DEMO: record a 10–15s clip of `/ascend` → intake → a phase completing → opening start-here.html.
     Export GIF ≤8MB ≤1200px wide → commit to assets/demo.gif → replace this comment with:
     <div align="center"><img src="assets/demo.gif" alt="Ascend demo" width="900"></div>
     Until then, the fictional examples/sample-run/start-here.html is the "see it" link above. -->

---

> **Status — pre-1.0.** The text pipeline (`/ascend`) is the stable path. The graphical console
> (`/ascendui`), the scheduled daily brief, and the newer on-demand ops are **beta** — built and
> code-checked, but not yet proven end-to-end on real data. See **[Known limitations](#known-limitations)**;
> version history and what's next live in **[`docs/ROADMAP.md`](docs/ROADMAP.md)**.

## Quickstart

```bash
git clone https://github.com/koushik1610/ascend.git
cd ascend
# Unzip your LinkedIn export; note the folder path + your resume's path.
claude          # open Claude Code in this folder
```

Then type **`/ascend`** (or *"Run Ascend"*). It interviews you — name, where your LinkedIn export and
resume are, what jobs you want — builds a private `workspace/<your-name>/`, and runs the pipeline,
checking in after each step. When it's done, open **`workspace/<your-name>/start-here.html`**.

> New to terminals? **[`docs/SETUP.md`](docs/SETUP.md)** walks through it step by step.
> Want to sample it cheaply first? Say *"Run Ascend Phase 1"* (just the LinkedIn analysis).

**Prefer clicking to typing?** Run **`/ascendui`** instead — it opens a graphical, Jarvis-style console
in your browser that walks you through everything (folder picker, target roles, an optional daily-brief
time) and shows the pipeline running live. It needs only Python 3 (preinstalled on macOS/Linux) plus an
agent CLI for the analysis. See [`ui/README.md`](ui/README.md).

---

## What you get

| Output | What it is |
|---|---|
| **`linkedin-analysis.html`** | A visual audit of your LinkedIn presence (findability score, keyword gaps, network, activity) **+ 10 ranked next steps** to grow reach and recruiter exposure. |
| **`master-resume.md`** | Your superset resume — every achievement, tagged, with a metrics bank. Every per-job resume is *selected* from it, never rewritten. (The ATS/keyword audit is folded in.) Also rendered to a public **master résumé PDF** as a generic default. |
| **`job-queue.md`** | 15+ ranked candidate jobs matched to your profile, each link fetched and marked verified/unverified (postings rot — you re-open before applying). |
| **`jobs/<NN-company-role>/`** | A tailored **apply pack** per job you pursue — résumé (markdown + `resume.json` + a clean one-page **ATS-safe PDF** from the résumé builder), referral-first outreach, application log. Deep interview prep is generated **on demand** when a screen gets booked. |
| **`interview-packet/`** | Cross-job prep reused everywhere: STAR stories, positioning hooks, metrics cheat-sheet. |
| **`start-here.html`** | The front door — a dashboard with your weekly action loop, application scoreboard, and every job. **Open this first.** |

Everything lands in `workspace/<your-name>/`, which is **gitignored** — it never leaves your machine.

---

## How it works

```
  Phase 0  Intake interview ............ asks your name, data location, targets
     │
  1  LinkedIn analysis ........ linkedin-analysis.html  (+10 next steps)
  3  Master resume ............ master-resume.md  (resume audit folded in)
  4  Job search ............... job-queue.md  (15+ ranked candidates)
  6  Interview packet ......... interview-packet/  (thin; enriched on demand)
  5  Apply packs .............. jobs/<NN>/  (résumé · outreach · log — top 3–5 you commit to)
  7  Navigator ................ start-here.html

  On demand:
  network    Warm referral paths from your connections .... 11-network-map.md
  answers    Reusable answers to application questions ..... 12-answer-sheet.md
  today      Daily briefing + follow-up nudges ............. 13-daily-briefing.md
  prep <NN>  Deep interview prep when a screen books ...... 10-deep-prep.md
  export     Résumé → one-page ATS-safe PDF (builder) ...... 08-export-pdf.md
  build-resume  Standalone résumé builder (ad-hoc) ........ templates/resume-builder.template.html
  maintenance Weekly refresh, follow-ups, retros ........... 09-maintenance.md
```

**Lazy by design.** A first run produces **~25–30 files** — a master resume, a 15-job queue, a thin
packet, and a 3-file apply pack for the few jobs you commit to — *not* 100 speculative prep files for
leads that never call back. Deep interview prep is built per job, exactly when it converts. A run
manifest (`.ascend-state.json`) makes everything **resumable** — close your laptop mid-run, say *"Run
Ascend resume"* later.

<details>
<summary><b>the ASCII sunrise, for the terminal-romantics</b></summary>

```
        \   |   /
         \  |  /
   - - - ( ● ) - - -     Ascend
  ___________________    find · tailor · apply · rise
```
</details>

---

## Day-to-day (in Claude Code)

| Say this | What it does |
|---|---|
| `/ascendui` *(beta)* | **Graphical console** — browser intake wizard + live progress + daily-brief scheduling |
| `/ascend` / "Run Ascend" | Full run from the intake interview (text) |
| "Run Ascend Phase 1" | Just the LinkedIn analysis (cheap first taste) |
| "Run Ascend resume" | Resume an interrupted run where it stopped |
| "Ascend today" | **Daily briefing** — today's 3 actions + ghost-detector follow-ups, drafted |
| "Ascend network" | **Warm-network map** — who you already know at each target company |
| "Ascend answers" | Reusable, varied answers to common application questions |
| "Ascend job add \<url>" | Add + build an apply pack for a job you found |
| "Ascend prep 03" | Build deep interview prep for job #3 (when a screen books) + mock drill |
| "Ascend score \<paste a JD>" | 0–100 Fit Score + missing keywords, no files built |
| "Ascend export Acme" | Render a job's résumé to a one-page ATS-safe PDF (résumé builder) |
| "Ascend build-resume" | Open the standalone résumé builder (form + live preview + Create PDF) |
| "Run Ascend maintenance" | Weekly: new/closed jobs, follow-ups due, retro patterns |

Every job also gets an explainable **Fit Score (0–100)** so you work the best matches first. For the
full picture of who uses each command and when — what you start with and the path through each one —
see **[`WORKFLOW.md`](WORKFLOW.md)**. The **roadmap** ([`docs/ROADMAP.md`](docs/ROADMAP.md)) tracks
what's next.

**The objective is action, not paperwork.** The dashboard leads with a weekly *apply N / ask N
referrals* loop and a funnel scoreboard — applications sent and referrals asked are what get you
interviews; tailored documents are just the ammunition.

---

<details>
<summary><b>Costs, runtime & requirements</b></summary>

- **You need a Claude subscription / API access** — this runs inside Claude Code and uses tokens.
- **A full run is long:** live web research for 15+ roles + the generated files often means **1–3+
  hours** of Claude working, across several check-ins. Sample it first ("Run Ascend Phase 1", or "only
  find 3 jobs and build apply packs for 2").
- **The PDF step is automated** (`08-export-pdf` renders headless via the résumé builder + Chrome). If
  no Chrome-class browser is found it falls back to a two-click "Save as PDF". Eyeball it either way.
- **Platform:** developed on macOS; works on Linux; on **Windows** use WSL or Git Bash (see
  [`docs/SETUP.md`](docs/SETUP.md)).
- **See output for free:** open the fictional [`examples/sample-run/start-here.html`](examples/sample-run/).
</details>

<details>
<summary><b>Privacy &amp; honesty</b></summary>

**Privacy.** Everything personal lives in `workspace/<name>/` and is **gitignored** — your LinkedIn
export, résumés, job folders, and dashboards are never committed. The `.gitignore` also blocks
résumés and LinkedIn CSVs anywhere in the tree as a backstop, and both dashboards carry a "contains
personal data — keep it local" banner. Run it for more than one person and each gets their own
`workspace/<name>/`; delete a folder to wipe that person entirely.

**Honesty.** Ascend never fabricates. Every claim traces to your LinkedIn export, your résumé, or an
answer you gave — no invented metrics, titles, certs, skills, or referral contacts. A role wants
something you don't have? That's a **gap with honest handling**, not a bluff. Personal "why this
company" essays come out as honest *outlines* for you to write in your voice — never as finished prose.
Job links are fetched and marked verified/unverified; req IDs are never invented. Full policy:
[`reference/number-and-honesty-policy.md`](reference/number-and-honesty-policy.md).
</details>

<details>
<summary><b>FAQ</b></summary>

**Do I need an Anthropic/Claude subscription?** Yes — you run this inside Claude Code.

**Will it apply to jobs for me?** No. It finds jobs, builds your materials, and preps you. You review,
export the PDF, and submit — applying for you would violate most sites' terms and skip your judgment.

**Are the job links real?** Phase 4 fetches each link and marks it verified/unverified/dead, and never
fabricates req IDs. Job boards block automated checks and postings rot, so the queue reports an honest
split (*N candidates, M link-verified*) and you re-open every link before applying.

**Can it run without a résumé?** Yes — it builds the master résumé from your LinkedIn export + intake.

**Is my data sent anywhere?** Only to Claude as part of running the pipeline (like any Claude Code
session). Nothing is committed to git; nothing is published.

**Can I customize it?** Yes — edit anything in `prompts/`, `templates/`, or `reference/`.
</details>

<a id="known-limitations"></a>
<details>
<summary><b>Known limitations</b></summary>

Honest about what's proven vs. still beta (and the path to 1.0 is tracked in [`docs/ROADMAP.md`](docs/ROADMAP.md)):

- **Beta surfaces** — `/ascendui`, the scheduled daily brief, and the newer on-demand ops (`network`,
  `answers`, `today`, `prep`) are built and code-checked but **not yet verified end-to-end on real
  data**. The text `/ascend` pipeline is the stable path.
- **Scheduled daily brief** — the cron runs your agent CLI headlessly, which may need it configured for
  non-interactive use (permissions/flags). If a scheduled run doesn't complete, just say **"Run Ascend
  today"** in Claude Code for the same briefing. Detecting a CLI (`claude`/`gemini`/`codex`) does not
  guarantee it completes a multi-file run unattended.
- **Platform** — the daily-brief scheduler uses cron (**macOS/Linux**); **native Windows is not
  supported** for scheduling (use WSL/Git Bash, or run the brief manually). The Linux folder picker
  needs `zenity`/`kdialog`, otherwise paste the path.
- **Free tier** — a free *web-chat* tier can't read local files; you need a local agent CLI (a free
  *CLI* tier like Gemini CLI is the closest free path).
- **Job links** — fetched and marked verified/unverified; postings rot, so re-open each before applying.
- **Tests** — a smoke-test harness + CI cover the server, dashboards, gitignore, and prompt cross-refs;
  there is no full end-to-end test (that requires a real run).
</details>

<details>
<summary><b>Repo map</b></summary>

```
ascend/
├── README.md · START-HERE.md · WORKFLOW.md · CLAUDE.md · CONTRIBUTING.md · CHANGELOG.md · LICENSE (MIT)
├── .gitignore                       privacy backstop (ignores all personal data + output)
├── .claude/commands/                the /ascend + /ascendui slash commands
├── ui/                              the graphical console: server.py (also `--render` → PDF), index.html, run-daily-brief.sh
├── assets/ascend-banner.svg         the brand banner (+ a slot for a demo.gif)
├── docs/                            SETUP.md (first-run guide) · ROADMAP.md (versions + what's next)
├── prompts/                         00-orchestrator + phases 01–07; on-demand 08–13
│                                    (export, maintenance, deep-prep, network-map, answer-sheet, daily-briefing)
├── templates/                       job-folder (tiered spec), master-resume, signal, job-queue,
│                                    interview-packet, resume-builder (the PDF builder),
│                                    linkedin-analysis + start-here (HTML)
├── reference/                       binding rules: ATS/keywords, résumé writing, numbers/honesty,
│                                    interview-prep framework
├── tests/smoke.py                   stdlib smoke tests (server, dashboards, gitignore, cross-refs)
├── examples/sample-run/             a fictional end-to-end example (open its start-here.html)
└── workspace/                       YOUR private output lands here (gitignored)
```

See [`CONTRIBUTING.md`](CONTRIBUTING.md) to add field packs, polish the dashboards, or fix prompts.
</details>

---

<div align="center">

**MIT** — see [`LICENSE`](LICENSE). Use it, fork it, run it for your friends and family.

</div>
