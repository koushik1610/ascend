# Comparative analysis: Ascend against two peer career-operations systems

**Date:** 2026-08-20 · **Ascend at:** v0.6.0 + unreleased run-council work on `main`

**Compared against two open-source career-operations projects**, referred to throughout as:
- **Peer A** — a large, mature, local-first career operating system. Roughly 70 deterministic
  scripts, 40 agent "modes", 80+ job-board providers, ~1,100 files, many contributors.
- **Peer B** — a small third-party extension to Peer A: a form-filling layer and a persistent
  answer knowledge base, ~600 lines.

They are deliberately unnamed here. This document exists to record what Ascend learned and what it
decided, not to grade anyone else's project, and the findings stand on their own merits without the
attribution. Both are open source and the patterns discussed are visible in any comparable system.

This is a read of two mature peers against ours, a list of what Ascend is genuinely missing, and a
tiered plan for what to take. It is analysis only. Nothing here is a scope-freeze exception: see
[Sequencing against the scope freeze](#sequencing-against-the-scope-freeze).

---

## 1. The three systems in one line each

| | What it is | Shape |
|---|---|---|
| **Ascend** | An evidence-grounded job-search pipeline that interviews you, builds a locked master résumé, and generates a lean set of apply packs | **19 prompts, 2 Python tools, ~6k lines.** Prompt-driven. The agent is the runtime. |
| **Peer A** | A local-first, AI-agnostic career operating system | **~70 Node scripts, 40 modes, 80+ job-board providers, ~1,100 files.** Data-driven. Scripts compute, the agent narrates. |
| **Peer B** | A form-filling and answer-learning extension for Peer A | **6 modes, ~10 Python files, one SQLite KB.** A learning loop bolted onto someone else's pipeline. |

### The structural difference that explains everything else

**Ascend produces artifacts. Peer A accumulates evidence.**

Ascend's durable state is `.ascend-state.json` plus a tree of Markdown the agent re-reads and
re-reasons over. Peer A's durable state is a declared **data contract**: a canonical tracker
(`data/applications.md`), append-only observation ledgers (`status-log.tsv`,
`salary-observations.tsv`, `scan-history.tsv`, `assessments.tsv`, `portal-health.tsv`), and a
settled doctrine that *files are canonical, databases are derived* (their issue #918 — SQLite is
never promoted to a primary store because the web UI, the Go dashboard, plugins, and forks all read
the files).

Everything Peer A has that Ascend doesn't — funnel velocity, rejection-pattern detection,
repost detection, company response history, skill-gap aggregation, salary-observation folding — is
downstream of that one decision. You cannot compute "your median days from Applied to Screen" from a
folder of prose. Ascend's Phase 13 ghost detector is the clearest symptom: it works by asking the
agent to read every `jobs/*/application-log.md` and eyeball the dates. That is a script's job, and
without a ledger it is also unreliable and non-reproducible.

The second structural difference: **Peer A does an enormous amount of work at zero tokens.**
Discovery, liveness, dedup, tracker reconciliation, funnel math, skill extraction, repost detection
— all deterministic Node. Ascend routes nearly everything through the agent, which costs money and
makes two runs of the same phase non-identical.

---

## 2. Where Ascend is actually ahead

Worth stating plainly, because the gap list below is long and one-directional.

- **Cold start.** Ascend interviews you and builds the master résumé from a LinkedIn export.
  Peer A largely assumes you arrive with a finished `cv.md`; its `intake.mjs` is a newer,
  narrower ingest (`documents/` → `pdftotext` → agent-proposed merges).
- **Lock the master + selection-only.** `master_locked` / `master_version` in `.ascend-state.json`
  makes "downstream may reorder and trim but never reword or add" a *machine-checkable state*, not a
  guideline. Peer A has strong source-of-truth rules in `_shared.md` but no lock/version
  mechanism, so nothing structurally prevents drift across derivatives.
- **MASTER GAP.** Naming the missing-bullet case and routing it back to the master, rather than
  letting the derivative invent, is a better-designed honesty primitive than anything in Peer A.
- **The renderer fails instead of shipping.** `tools/render_resume.py` enforcing a one-page budget
  and erroring on overflow is stricter than Peer A's PDF path.
- **The warm-network layer.** Phase 11 mining `Connections.csv` + `messages.csv` for real DM warmth
  is genuinely unique. Peer A's `contacts.tsv` is a phonebook you fill in by hand.
- **Visual entry points.** `linkedin-analysis.html`, `start-here.html`, the résumé builder, and
  `/ascendui` have no Peer A equivalent in the core (their web UI is a separate Next.js app; the
  Go TUI is optional and isolated).
- **Leanness.** ~25–30 files on a first run against Peer A's 70-script flat root. That is a real
  usability advantage and should survive everything below.

---

## 3. What Ascend is missing

Grouped by layer, most structural first. "Roadmap" notes where `docs/ROADMAP.md` already has the item.

### A. The state layer (the root gap)

| # | Missing | Peer A equivalent | Consequence for Ascend |
|---|---|---|---|
| A1 | **A canonical tracker.** Ascend's per-job `application-log.md` files *are* the state; there is no single table. | `data/applications.md` + a derived SQLite index | No funnel math, no cross-run diff, no reliable status query |
| A2 | **An append-only status ledger.** Nothing records *when* a status changed. | `data/status-log.tsv`: `{ref}\t{date}\t{from}\t{to}\t{source}\t{note}`, written by `set-status.mjs`, never edited in place | Cannot compute stage velocity, time-to-first-response, or rejection latency |
| A3 | **Append-only observation logs** for comp, assessments, scan history | `salary-observations.tsv`, `assessments.tsv`, `scan-history.tsv` with trust-tiered folding on read | Comp facts live in prose and get overwritten; no history |
| A4 | **A declared system/user boundary.** `.gitignore` covers the *privacy* half; nothing covers the *upgrade* half. | `DATA_CONTRACT.md` + `SYSTEM_PATHS`/`USER_PATHS`, with `updater-migration-tests.mjs` asserting they never overlap | Blocks A5 entirely |
| A5 | **Any self-update path.** A user who cloned v0.3.0 is on v0.3.0 forever. | `update-system.mjs`: backup → fetch → re-exec the new updater → check out `SYSTEM_PATHS` only; `BOOTSTRAP_PATHS` for ancient installs; `npm run rollback` | Every improvement we ship reaches only new clones |

### B. Discovery

| # | Missing | Peer A equivalent |
|---|---|---|
| B1 | **A real provider layer.** `prompts/14-ats-aggregation.md` is 56 lines telling the agent to `WebFetch` three endpoints. | 80+ modules under `providers/` behind a registry, with a shared `_http.mjs`, DNS cache, HTML-entity handling, and a `_trust-validator.mjs`. Adding a board = drop in one file. Zero tokens. |
| B2 | **Deterministic liveness checking.** Phase 4 asks the agent to fetch each link and self-report `✅ verified-live`. | `check-liveness.mjs`: free ATS-API rung first (Greenhouse/Lever, no browser), Playwright for the rest. Zero tokens, reproducible. |
| B3 | **Company → board resolution.** | `discover-ats.mjs` probes vendor APIs for a company list and resolves each to a scannable board; preview-only by default, `--write` to append to the user-layer `portals.yml`. |
| B4 | **Repost / ghost detection from history.** | `detect-reposts.mjs` over `scan-history.tsv` (fuzzy role match, 90-day window, SimHash JD fingerprint column) — the same role relisted 2+ times is a signal. |
| B5 | **A cheap triage tier.** Ascend runs the full 0–100 Fit Score on everything. | `modes/triage.md`: a first-pass go/no-go that writes no files, so full evaluation is spent only on survivors. |
| B6 | **Adjacent-title expansion as a mechanism.** Phase 4 says "surface 2–3 adjacent titles" as a prompt instruction. | `modes/titles.md` reads the CV, proposes titles the user isn't searching, and writes accepted ones into the filter after explicit confirmation. |
| B7 | **Model/spend routing.** | `spend_tier: economy\|standard\|premium` in `profile.yml` with a single routing table, plus standalone evaluators (`ollama-eval.mjs` fully local, `gemini-eval.mjs` free tier, `openai-eval.mjs` any compatible endpoint). |

### C. The right half of the funnel — Ascend's largest functional hole

Ascend is strong from intake through "send the application" and thin after. Peer A has an entire
post-application system.

| # | Missing | Peer A equivalent |
|---|---|---|
| C1 | **Reply ingestion and classification.** | `reply-watch.mjs` + a deterministic `reply-matcher.mjs`: employer replies → classified (`Interview`/`Rejected`/`Offer`/`Noise`/…) → matched to tracker rows by company/role/domain → *recommended* status updates the user approves. |
| C2 | **Invite/rejection matching.** | `invite-match.mjs` — recruiter emails with generic subjects ("Schedule Your Phone Screen") fuzzy-matched to the right tracker row. |
| C3 | **Outcome recording + artifact archival.** | `outcome.mjs` archives the **actually submitted** CV, cover letter, and posting snapshot to `data/outcomes/{n}_{company}_{role}/`. Ascend never snapshots what really went out. |
| C4 | **Assessment logging.** | `assessment-log.mjs` treats "received a HackerRank" as its own pipeline event with platform, threshold, score, staleness note. |
| C5 | **Pipeline analytics.** *(Roadmap P2 #22, unbuilt)* | `analyze-patterns.mjs` (outcomes by archetype/seniority/remote/score), `funnel-velocity.mjs` (your rates vs. sourced market benchmarks in `templates/benchmarks.yml`, plus median/p75 days per stage hop), `rejection-latency.mjs`, `process-quality.mjs` (is the *recruiting process* well run — a third axis beyond fit and interviewer behavior), `company-history.mjs` (per-company responsiveness + posting churn), `stats.mjs`. |
| C6 | **Aggregate skill-gap mapping.** | `upskill.mjs` mines every low-scoring report's named gaps, weights each by `(5.0 − score)`, suppresses anything already in the CV via a shared canonical vocabulary (`skill-extract.mjs`), and emits a tiered "what to learn, in what order" map. Plus `jd-skill-gap.mjs` for a single JD — zero-LLM, three buckets (existing / supported-by-résumé / gap), never auto-adds. |
| C7 | **Offer-stage depth.** Ascend has `19-salary-studio.md` only. | `modes/offer-prep.md` (contract reading companion — clause-by-clause, deltas vs. what was promised, prep for a lawyer meeting), `salary-gap.mjs` (desired vs. advertised vs. actual as append-only trust-tiered observations), `negotiation-roi.mjs` (talking points anchored to a story-bank achievement — **and gated so a number is only usable if it also appears verbatim with matching units in `cv.md`**). |
| C8 | **Interviewer-side red flags.** | `modes/interview-redflag.md` analyses the *interviewer's* behavior in session transcripts: "even if I win, is this company safe to join?" Plus `weekly-digest.mjs` aggregating interview sessions. |

### D. The candidate-protection layer — absent, and the most interesting thing here

Peer A ships five jurisdiction data tables under `templates/`:

- `protected-grounds.yml` — questions employers may not ask, by jurisdiction
- `jurisdiction-prohibited-content.yml` — content employers may not require (e.g. salary history in US-CA)
- `immigration-status-requirements.yml` — "US citizens only" style overreach, with a **mandatory
  `lawful_screening_contrast` field on every row** so the table can't misfire on lawful
  work-authorization questions
- `restrictive-covenants.yml` — non-compete/non-solicit statutory context, keyed per covenant type
  and never conflated across types
- `agency-licensing.yml` — recruiter licensing regimes with a link to the *official* registry, never a mirror

Each carries a hard contribution rule: no row without a citable regulator-grade source, an effective
date, and an `as_of` verification date. No script reads them — the agent does, as a local file
lookup, with matching that is explicitly agent-judged rather than regex ("we will never ask for your
salary history" in a fraud-warning footer must not fire; a form field requesting it must).

**Ascend's honesty gates run in exactly one direction: they protect the employer from the
candidate's fabrication. Nothing protects the candidate from the employer.** That is a real hole in
a system whose entire brand is honesty, and closing it is a natural extension of the same values
rather than a new product direction.

### E. Quality engineering

| # | Missing | Peer A equivalent |
|---|---|---|
| E1 | **An eval harness.** *(Roadmap flags this for v1.5)* `tests/smoke.py` is a structural check; nothing scores output quality, so a prompt edit can silently regress. | `evals/golden/*.json` (10 labeled archetype cases) + `eval-golden.mjs` with a `--replay` mode that runs deterministically at $0 in CI and gates on archetype-agreement with a frozen reference. |
| E2 | **A fact gate, as distinct from a language gate.** `lint_artifacts.py` catches dashes, banned vocabulary, forbidden numbers, retracted claims, and Delta-Log provenance markers — but it does not verify that each claim in a generated document traces to a source file. | `verify-cv-facts.mjs` cross-checks generated documents against source facts, with a user-layer `config/cv-facts.json` allowlist — and it is **called by the PDF generators themselves**, so no generated document escapes the gate. |
| E3 | **A preflight doctor.** New users discover breakage mid-run. | `doctor.mjs` prints a pass/fail prerequisites checklist. |
| E4 | **Drift detection at session start.** | `cv-sync-check.mjs`, mandated to run on the first evaluation of each session. |
| E5 | **Visual regression on the rendered résumé.** | `playwright.cv.config.mjs` + `test/cv-visual` snapshots. |

### F. Ecosystem and extensibility

| # | Missing | Peer A equivalent |
|---|---|---|
| F1 | **Multi-CLI support.** Ascend is Claude-Code-only. | `AGENTS.md` is canonical; `CLAUDE.md`/`CODEX.md`/`GEMINI.md`/`KIMI.md`/`OPENCODE.md` are thin redirects, plus `.agents/skills/` per the agentskills.io standard. Cheap, and it multiplies reach. |
| F2 | **A plugin layer.** `CLAUDE.md` tells users who want a capability fence to hand-write `.claude/settings.local.json`. | `plugins/<id>/manifest.json` — parsed and validated *before* any code is imported — declaring `hooks`, `requiredEnv` (names only), `allowedHosts` (required whenever env is), and `humanInTheLoop: true` (must be true). Default off; two gates (enable in `config/plugins.yml` **and** supply keys). `plugins.lock` records integrity pins and consent. `plugins.local/` is gitignored and never auto-updated. |
| F3 | **An async request queue.** | `agent-inbox.mjs` — an append-only `data/agent-inbox.md` where you drop "evaluate this URL" while not in a session; the agent drains it at session start. |
| F4 | **Headless / batch operation.** | `openrouter-runner.mjs`, the standalone evaluators, Docker + compose. |

### G. From Peer B specifically

The extension's headline is Kimi-driven form typing. **That is not the valuable part.** The valuable
part is the learning loop underneath it.

| # | Missing | Peer B equivalent |
|---|---|---|
| G1 | **An answer knowledge base that learns.** Ascend's `12-answer-sheet.md` writes a static document once and never updates it from reality. | A SQLite KB: every form field you actually filled is normalized to a canonical `intent_key` (`"Are you an Indian Citizen?"` → `citizen_of_india`), stored with `answer_type`, `confidence`, `source`, `seen_count`, and a `kb_question_variants` table mapping every phrasing seen to the same key. Next form asking a semantically equivalent question auto-fills. |
| G2 | **Learning events with correction precedence.** | `learning_events` audits every touch as `new` / `reinforced` (pre-filled correctly, you didn't change it) / `corrected` (you changed it — your value wins and the KB updates). |
| G3 | **A confirmation queue for low-confidence entries.** | `kb-review` surfaces entries with `seen_count == 1` — learned once, never reinforced — so misclassified intents get caught before they poison future applications. |
| G4 | **A poison guard on what gets learned.** | `SKIP_INTENTS` in `learner/learn.py` blocks `why_company`, `why_this_role`, `additional_notes`, cover letters — job-specific text that would be actively harmful if reused. Also skips `file`/`hidden` field types. |
| G5 | **Snapshot-before-submit.** | The pre-submit snapshot captures label, field type, value, options, `was_prefilled`, and `prefilled_value` — which is exactly what makes the `reinforced` vs. `corrected` distinction possible, and what Ascend needs for C3 (archiving what was actually submitted). |
| G6 | **A briefing that reads the datastore.** | `orchestrator.py briefing`: new jobs in the last 24h, reports ready to fill, unconfirmed KB entries, KB size. Read-only, deterministic, no tokens. Ascend's Phase 13 asks the agent to reconstruct the same picture from prose every morning. |
| G7 | **A ToS-safe LinkedIn tier.** Ascend rules out scraping (correctly). | The `linkedin url` tier just *builds the search URL* with the right filters and hands it to you; `linkedin add <url>` takes pasted URLs and pulls company/role from `og:` tags. No scraping, no ToS exposure. |

The extension is also honest about its own weak points, and they are instructive: LinkedIn A/B-tests
its CSS class names weekly so the DOM-walking scraper goes stale; and its own roadmap admits `learn`
overwrites Section G with no audit trail. Both are avoidable if we adopt the idea rather than the code.

---

## 4. What NOT to adopt

- **The flat 70-script root.** Peer A defends it on path-stability grounds — a legitimate
  argument *for them*, given forks and plugins depend on those paths. Ascend has no such
  installed base and leanness is one of its few real advantages. Keep `tools/` organized.
- **Kimi Webbridge / browser form typing.** Fragile by the extension's own admission, and
  `docs/ROADMAP.md` already rules out browser autofill injection on positioning grounds. Take G1–G6,
  leave the typing. The user pastes; the user submits; we learn.
- **DOM-walking LinkedIn scraping.** Same reason. Take G7's URL-builder tier only.
- **Hardcoded model names in prompts.** Peer A's `_shared.md` spend-tier table names specific
  models and openly concedes it can't keep the non-Claude rows current. Adopt the *tier concept*,
  not the table.
- **SQLite as a primary store.** Peer A settled this correctly (files canonical, DB derived) and
  it applies doubly to Ascend, where the whole product is human-readable, git-diffable output. Any
  KB or index we add must be rebuildable from the files.
- **Sixteen translated READMEs, a manifesto, a guestbook workflow, a signature CI.** Community
  scaffolding for a project with thousands of users; pure overhead at Ascend's stage.

---

## 5. Adoption plan

Ordered so that each tier makes the next one possible. Tier 1 is the prerequisite for most of Tiers 3–5.

### Tier 0 — small, and they de-risk the outstanding v1.0 runs

| Item | Source | Why now |
|---|---|---|
| `tools/doctor.py` — preflight checklist (paths readable, LinkedIn export shape, TeX engine, pandoc, Python version, workspace gitignored) | E3 | Runs (b) and (c) are the v1.0 gate; a preflight that fails loudly beats discovering breakage at Phase 4 |
| `docs/DATA-CONTRACT.md` — write down which paths are system and which are user | A4 | Doc-only, no code, and it is the prerequisite for the updater. Also forces the question of where `workspace/<name>/data/` lives |
| Extend `lint_artifacts.py` with a `--facts` mode that cross-checks claims against `master-resume.md` | E2 | The lint gate is already wired into Phases 3/5/8; a fact check is the natural next category and directly serves the run rubric's honesty line |

### Tier 1 — the state layer (do this before anything in Tiers 3–5)

1. `workspace/<name>/data/applications.tsv` — the canonical tracker. One row per application:
   ref, company, role, job slug, status, applied date, source, link.
2. `workspace/<name>/data/status-log.tsv` — append-only, `{ref}\t{date}\t{from}\t{to}\t{source}\t{note}`.
   Never edited in place; corrections are new rows with `source=correction`.
3. **Invert the relationship**: `jobs/*/application-log.md` becomes a human-readable *view*
   generated from the tracker, not the source of truth. This is the single most consequential change
   in this document.
4. `tools/pipeline.py` — one zero-token script exposing `status set`, `funnel`, `velocity`,
   `overdue`. Phase 13's ghost detector calls it instead of re-reading prose.

**Honesty note:** append-only ledgers are a *better* fit for Ascend's values than for Peer A's.
"Never edited in place, corrections are new rows" is the same principle as "selection, not
invention," applied to the tracker.

### Tier 2 — the answer KB (most value per line of code)

Adopt G1–G4 and G6, in Python stdlib (`sqlite3` is stdlib, so no new dependency), under
`workspace/<name>/data/answers.db`, rebuildable from a plain-text `answers.tsv` so the file stays
canonical.

Three Ascend-specific additions the extension doesn't have:

- **Provenance on every entry.** Tag each answer `verified` (traces to master résumé / intake /
  `lint-config.json`) or `user-asserted` (typed into a form, never independently confirmed). Only
  `verified` entries may feed a sendable surface without a review prompt. This is the honesty gate
  applied to the KB.
- **Never overwrite, always version.** Peer B's own roadmap regrets that `learn` overwrites
  Section G. Keep the history from day one.
- **Route it through `18-degenericizer.md`.** A reused answer is by definition a repeated answer,
  and identical answers across applications are a known recruiter tell — which Ascend's own roadmap
  already identifies (P1 #8). The KB stores the *fact*; the degenericizer varies the *phrasing*.

Then rewrite `12-answer-sheet.md` as a read/write surface over the KB, and add `/ascend learn <job>`:
paste what you actually submitted, KB updates, `kb-review` surfaces anything seen once.

### Tier 3 — deterministic discovery

1. `tools/scan_ats.py` with a provider-registry structure — start with the five endpoints Phase 14
   already names, but shaped so adding a board is one file, not a prompt edit.
2. `tools/check_liveness.py` — free ATS-API rung, then a plain fetch. This replaces the
   agent-fetches-every-link loop and is what makes Phase 4's "N candidates, M link-verified" split
   actually trustworthy rather than self-reported.
3. A user-layer `tracked-companies.yml` plus a `discover` op resolving company → board (B3).
4. A triage tier in Phase 4 (B5) so the full Fit Score is spent only on survivors.

### Tier 4 — close the funnel

Once Tier 1 exists these are mostly small scripts over the ledgers: reply ingestion with
user-approved status updates (C1/C2), outcome recording with submitted-artifact archival (C3),
pattern + funnel analytics against sourced benchmarks (C5), the aggregate upskill map (C6). C7's
`offer-prep` and the verified-number gate in `negotiation-roi.mjs` are worth reading closely before
extending `19-salary-studio.md` — that gate (a number is usable only if it also appears verbatim
with matching units in the source document) is the same discipline as our Delta-Log provenance rule,
and we should copy the *rule*, not the code.

### Tier 5 — the candidate-protection layer

Port the jurisdiction-table pattern (D), starting with two or three jurisdictions rather than a
broad seed. Keep Peer A's three disciplines exactly: citable regulator-grade source, effective
date, `as_of`; agent-judged matching, never regex; and the mandatory `lawful_screening_contrast`
field so the immigration table can't misfire on lawful work-authorization questions. Wire it into
Phase 4 (JD text) and Phase 12 (form questions).

This is the one item on this list that would make Ascend *better than* Peer A at something
Peer A invented, because it lands inside an honesty framework that is already the product's
stated identity.

### Tier 6 — ecosystem

`AGENTS.md` as canonical with a thin `CLAUDE.md` redirect (F1) is a few hours and multiplies who can
run Ascend. The eval harness with golden fixtures and a `--replay` mode (E1) is the thing that lets
us change prompts without fear. The plugin layer (F2) and the self-updater (A5) are larger, and A5
depends on Tier 0's data contract.

---

## Sequencing against the scope freeze

`docs/ROADMAP.md` records a scope freeze as of 2026-07-02: until real runs (b) and (c) are signed
off, only defect fixes those runs surface may ship. Nothing in this document overrides that.

Read the tiers accordingly:

- **Tier 0** is arguably inside the freeze — a doctor and a fact-check mode exist to make runs (b)
  and (c) pass their own rubric, which is the freeze's purpose. Worth proposing on those grounds
  rather than assuming.
- **Tiers 1–6 are post-1.0.** Tier 1 should be the first thing after the tag, because most of the
  rest depends on it.
- The roadmap's own `n=1` gate still applies to every item: nothing ships that encodes one user's
  structure, one field's vocabulary, or one jurisdiction's law as a default.

## What this comparison is worth, honestly

Peer A is roughly two orders of magnitude more code and has a large contributor base. Most of
what it has that Ascend lacks is not cleverness — it is accumulated surface area. Ascend should not
try to match it feature for feature, and its leanness is a real advantage worth defending.

But three things on this list are not surface area, they are architecture, and they will not get
easier later:

1. **The state layer** (Tier 1) — without it, the entire right half of the funnel stays
   unbuildable.
2. **The learning loop** (Tier 2) — the one idea in Peer B worth taking wholesale, and it
   costs a few hundred lines.
3. **The data contract + updater** (A4/A5) — every day without it, another clone freezes at its
   checkout version.
