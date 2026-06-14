# 🕷️ S.P.I.D.E.R.

**Strategic Profile Intelligence & Direct Employment Routing**

A reusable, AI-driven job-search system that runs end-to-end inside [Claude Code](https://claude.com/claude-code).
It interviews you, analyzes your LinkedIn data, audits your resume, builds a **master resume**, finds
**15+ real jobs** matched to your profile, and generates a complete **per-job application + interview
workspace** for each — then ties it all together in a single navigator you open in your browser.

> One person built it for their own search (a LinkedIn audit, a master resume, 12 live roles, and 96
> per-job prep files). This repo is that system, generalized so **anyone** can run it on their own data.
> Your data never leaves your machine and is never committed to git.

---

## What it produces

| Output | What it is |
|---|---|
| **`linkedin-analysis.html`** | A visual audit of your LinkedIn presence (findability score, keyword gaps, network, activity) **+ 10 ranked, actionable next steps** to grow reach and recruiter exposure. |
| **`resume-audit.md`** | An ATS + 2026-trends gap report on your current resume: what's failing parsers, the 6-second-scan verdict, missing keywords, and sample bullet rewrites. |
| **`master-resume.md`** | Your superset resume — every achievement, tagged, with a metrics bank. Every per-job resume is *selected* from it, never rewritten. |
| **`job-queue.md`** | 15+ ranked candidate jobs matched to your profile (each link fetched and marked verified / unverified — postings rot, so you re-open before applying), each with a resume delta, talking points, and gaps. |
| **`jobs/<NN-company-role>/`** | One folder per job, **8 files each**: tailored resume, prep-doc, interview questions (coding + behavioral), study plan, outreach, company research, a sendable one-pager, and an application log. |
| **`interview-packet/`** | Cross-job prep reused by every folder: STAR stories, project deep-dives, metrics cheat-sheet, intro scripts, questions to ask, company positioning. |
| **`start-here.html`** | The front door — a dashboard linking everything, with a live application funnel and your "this week" actions. **Open this first.** |

All of it lands in `workspace/<your-name>/`, which is **gitignored**.

---

## How it works — the 7-phase pipeline

```
  Phase 0  Intake interview ......... prompts/00-orchestrator.md   (asks your name, data location, targets)
     │
  Phase 1  LinkedIn analysis ........ prompts/01-linkedin-analysis.md  → linkedin-analysis.html (+10 next steps)
  Phase 2  Resume audit ............. prompts/02-resume-audit.md       → resume-audit.md
  Phase 3  Master resume ............ prompts/03-master-resume.md      → master-resume.md
  Phase 4  Job search (15+) ......... prompts/04-job-search.md         → job-queue.md
  Phase 6  Interview packet ......... prompts/06-interview-packet.md   → interview-packet/   (runs before 5)
  Phase 5  Per-job folders .......... prompts/05-job-folders.md        → jobs/*/ (8 files each)
  Phase 7  Navigator ................ prompts/07-navigator-html.md     → start-here.html

  On demand:
  Export   Resume → ATS-safe PDF .... prompts/08-export-pdf.md
  Maintain Weekly refresh + retro ... prompts/09-maintenance.md
```

The **orchestrator** (Phase 0) runs the whole thing: it interviews you, builds your workspace, then
drives each phase in order, **pausing at a checkpoint after each** so you can review, redirect, or skip.
(Phase 6 runs just before Phase 5 so the interview stories exist before the job folders cite them.) A
run manifest (`.spider-state.json`) makes it **resumable** — close your laptop mid-run and say *"Run
SPIDER resume"* later.

---

## Prerequisites

1. **Claude Code** installed and working ([install guide](https://docs.claude.com/en/docs/claude-code)).
2. **Your LinkedIn data export.** On LinkedIn: *Settings → Data Privacy → Get a copy of your data →
   "The works" → Request archive.* You'll get an email with a zip (minutes to ~24h). **Unzip it.**
3. **Your current resume** (PDF, .docx, or .md). Optional — the system can build one from your LinkedIn
   export + the interview if you don't have one.
4. (Optional) Your portfolio / GitHub / personal-site URLs.

> **New to terminals / not technical?** Read [`docs/SETUP.md`](docs/SETUP.md) first — it walks through
> installing Claude Code, getting your LinkedIn export, and finding a folder path, step by step.

---

## Costs, runtime & requirements

Be realistic before you start:

- **You need a Claude subscription / API access** — this runs inside Claude Code and uses tokens like
  any Claude session. A full run is **token-heavy**.
- **A full run is long:** live web research for 15+ roles + ~100 generated files often means **1–3+
  hours** of Claude working, across several check-in points. It is not instant.
- **Sample it first.** You don't have to run everything at once. Start with just Phase 1 ("Run SPIDER
  Phase 1") to get your LinkedIn analysis, or ask for a **lite pass** ("run SPIDER but only find 3 jobs
  and build 1 folder") to see the output shape and gauge cost before committing to the full run.
- **The PDF step is now automated** (Phase export, `prompts/08-export-pdf.md`) — but you still press
  "Save as PDF" in your browser once and eyeball it before submitting.
- **Platform:** developed on macOS; works on Linux. On **Windows**, use WSL or Git Bash for the
  smoothest path (see `docs/SETUP.md`).

Want to see what the output looks like without spending anything? Open the fictional
[`examples/sample-run/start-here.html`](examples/sample-run/) in your browser.

---

## Quick start

```bash
# 1. Clone
git clone https://github.com/koushik1610/spider.git
cd spider

# 2. Put your inputs somewhere on disk (the system will copy them into your private workspace).
#    Unzip your LinkedIn export; note the folder path. Note your resume's path.

# 3. Open Claude Code in this folder and start the system:
```

In Claude Code, type:

```
/spider
```

…or just say **"Run SPIDER."** Claude will start the **intake interview** — it asks your name, where
your LinkedIn export folder is, where your resume is, and what jobs you're aiming for (roles,
seniority, companies, location/remote, comp, timeline, your differentiators, and any honest gaps or
data you shouldn't publish). Then it builds `workspace/<your-name>/` and runs the phases, checking in
with you after each.

When it's done, **open `workspace/<your-name>/start-here.html`** in your browser. That's your HQ.

---

## How you actually use the output (day to day)

1. **Open `start-here.html`.** Clear the **"Before you apply" blockers** first (e.g., fix the resume's
   top ATS issue, apply the LinkedIn next-steps, run a referral sweep).
2. **Work the queue top-down.** For the #1 job: open its folder → `outreach.md` (try a referral
   *before* applying cold) → export `resume.md` to PDF → apply.
3. **Prep** with that folder's `interview-prep.md` (study plan) and `prep-doc.md` (the night-before
   read). Drill `interview-questions.md`.
4. **Track** in each `application-log.md` as you apply and interview; the navigator's funnel reflects it.
5. **Maintain:** re-run **Phase 4** weekly for fresh postings ("Run SPIDER Phase 4"); add new folders
   for new targets.

---

## Privacy model (important)

- **Everything personal lives in `workspace/<name>/` and is gitignored.** Your LinkedIn export, resume,
  master resume, job folders, and HTML dashboards are **never committed**.
- The repo ships only the **system**: prompts, templates, reference rules, and docs.
- The `.gitignore` also blocks resumes, LinkedIn CSVs, and generated artifacts anywhere in the tree as
  a backstop. **When in doubt, it doesn't get committed.**
- Run it for more than one person? Each gets their own `workspace/<name>/`; runs never collide. Delete
  a workspace folder to wipe that person's data entirely.

---

## Honesty & numbers (non-negotiable)

S.P.I.D.E.R. never fabricates. Every claim traces to your LinkedIn export, your resume, or an answer
you gave. It won't invent metrics, titles, certs, skills, or referral contacts. Where a role wants
something you don't have, that's a **gap with honest handling**, not a bluff. Personal "why this
company" essays are produced as honest *outlines* for you to write in your own voice — never as
finished prose. If you have employer-internal numbers you shouldn't publish, intake captures a
sanitization rule and every sendable surface respects it. Full policy:
[`reference/number-and-honesty-policy.md`](reference/number-and-honesty-policy.md).

---

## Works for any field

The pipeline is field-agnostic. The bullet formula, ATS rules, and interview framework are universal;
the *specifics* adapt to you — engineers get algorithm-round prep and system-design set-pieces;
designers/PMs/marketers/ops get portfolio reviews, case studies, and work-sample prep instead. The
intake interview calibrates everything to your roles.

---

## Repo map

```
spider/
├── README.md                  ← you are here
├── START-HERE.md              ← the 60-second "how do I run this" version
├── CLAUDE.md                  ← project instructions Claude Code auto-loads
├── CONTRIBUTING.md · CHANGELOG.md · LICENSE (MIT)
├── .gitignore                 ← privacy backstop (ignores all personal data + output)
├── .claude/commands/spider.md ← the /spider slash command
├── docs/SETUP.md              ← non-technical, step-by-step first-run guide
├── prompts/                   ← the pipeline: 00-orchestrator + phases 01–07 + 08-export + 09-maintenance
├── templates/                 ← job-folder (8-file spec), master-resume, signal, job-queue,
│                                interview-packet, resume-print, linkedin-analysis.html, start-here.html
├── reference/                 ← binding rules: ATS/keywords, resume writing, numbers/honesty,
│                                interview prep framework
├── examples/sample-run/       ← a fictional end-to-end example (open its start-here.html)
└── workspace/                 ← YOUR private output lands here (gitignored)
```

### Day-to-day commands (in Claude Code)
| Say this | What it does |
|---|---|
| `/spider` or "Run SPIDER" | Full run from the intake interview |
| "Run SPIDER Phase 1" | Just the LinkedIn analysis (cheap first taste) |
| "Run SPIDER resume" | Resume an interrupted run from where it stopped |
| "SPIDER job add \<url>" | Add + build one job you found yourself |
| "SPIDER job rebuild 03" | Regenerate one job folder (e.g., JD changed) |
| "SPIDER score \<paste a JD>" | ATS gap score + missing keywords, no files built |
| "SPIDER export Acme" | Turn a job's resume into an ATS-safe PDF |
| "Run SPIDER maintenance" | Weekly: new/closed jobs, follow-ups due, retro patterns |

---

## FAQ

**Do I need an Anthropic/Claude subscription?** Yes — you run this inside Claude Code.

**Will it apply to jobs for me?** No. It finds jobs, builds your materials, and preps you. You review,
export the PDF, and submit — applying for you would violate most sites' terms and skip your judgment.

**Are the job links real?** Phase 4 does live web research and **fetches each link**, marking it
verified-live, unverified (blocked / JS-gated — may still be good), or dead. It never fabricates req
IDs. But job boards block automated checks and postings rot within days, so the queue reports an honest
split (*N candidates, M link-verified*) and **you re-open every link before applying** (the
application-log checklist enforces it). Treat the queue as a high-quality shortlist to act on, not a
guarantee every link is live this minute.

**How long does a full run take, and what does it cost?** A complete run does live web research for 15+
roles and writes ~100 files — it's long (often 1–3+ hours of Claude working) and consumes real tokens
on your plan. Use a smaller first pass if you want to sample it (see *Costs, runtime & requirements*).

**Can it run without a resume?** Yes — it builds the master resume from your LinkedIn export + intake.

**Is my data sent anywhere?** Only to Claude as part of running the pipeline (as with any Claude Code
session). Nothing is committed to git; nothing is published.

**Can I customize the prompts/templates?** Yes — edit anything in `prompts/`, `templates/`, or
`reference/`. The orchestrator reads them at runtime.

---

## License

MIT — see [`LICENSE`](LICENSE). Use it, fork it, run it for your friends and family. Good luck out there. 🕸️
