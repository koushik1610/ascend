# Plan: what Ascend takes from a peer job-search app

**Date:** 2026-10-28 · **Base:** `feat/v2-auto-apply` at 85e3a17 (2.0.0-beta) · **Status:** plan only, nothing implemented

A comparison of Ascend against a mature, self-hosted, open-source job-search web app (called "the
peer" here) was read source-first, then put to the full council: nine personas in three groups,
independent analysis, then an anonymous Borda vote. This file records what is worth taking, in what
order, and what was turned down. Like `docs/COMPARATIVE-ANALYSIS.md`, it leaves the peer unnamed: the
findings stand without the attribution.

The bar the user set was "only add it if it is really worth adding". Of 18 peer features and
practices reviewed, 4 go in as P0, 7 as P1 and 6 as P2. The rest are rejected, with the reasons below.

---

## 1. Summary

The most useful thing in the peer is not a feature. It is a habit: **every model step that makes a
claim about the candidate is paired with a code step that has to agree with it.** The model maps a
posting requirement to one of the candidate's own skill names, and code decides covered or gap. The
model rewrites a document, and code (not the model) writes the summary of what changed. After every
generation, code checks names and numbers against the profile.

Ascend already does this in places (the linter, the run grader, Delta Log IDs that must exist). The
review found two places where it doesn't, and both matter more now that automatic apply can send
without a human looking:

1. **A reworded bullet with an invented number passes.** `lint_provenance`
   (`tools/lint_artifacts.py:308`) checks that the IDs a Delta Log cites exist in the master. It never
   checks that the bullet text matches the entry it cites. The model also writes its own Delta Log.
2. **The locked master is editable.** "Locked" is a flag in `.ascend-state.json`
   (`tools/state.py:148`), and `.claude/settings.json` allows `Write(workspace/**)`. Every check
   against the master is circular until the lock means something.

Fix those two before 2.0 GA. Before that, close out v1.0 with a demo GIF recorded from fixtures. After
GA, make scoring checkable by code.

---

## 2. How the two compare

### Flow

| Stage | Ascend | The peer |
|---|---|---|
| Start | Intake interview + LinkedIn export, or no résumé at all | Profile form, or import an existing résumé |
| Evidence | `master-resume.md` with entry IDs, locked by the user | Profile records in Postgres (roles, skills linked to roles, projects, facts) |
| Field phrasing | Industry language research (Phase 26) | None |
| Discovery | Zero-token finder over Greenhouse, Ashby, Lever, Workday, Eightfold (19k postings in 40s), alerts mail, LinkedIn cards, web search | Two paid job-search APIs, HN "Who is hiring" + a startup board, a once-a-day agent |
| Ranking | Rule prefilter, then a model-judged 0–100 Fit Score (5 × 20) | Model-judged 0–100 score with bands, reasons, red flags. Requirement coverage decided in code |
| Tailoring | Select, reorder and trim locked bullets. Never reword. Delta Log by the model | Model rewrites every unit under a strict truthfulness prompt. A fact guard flags unbacked names and numbers. A change summary is built in code |
| Documents | One-page ATS-safe résumé (PDF, LaTeX, DOCX), referral-first outreach, signal page | Résumé in 12 themes, cover letter, application email, 21 languages |
| Iteration | Re-run the phase, MASTER GAP back to the source | Chat refine, per-unit regenerate, 50 versions per document, undo |
| Applying | Apply sheet, or opt-in automatic apply on three ATSs from user-written answers | User sends the email from Gmail. Never applies |
| Tracking | Ledger, deterministic mail classifier, hub, weekly review, rejection protocol | Board and table, Gmail replies classified with questions and times extracted, reply drafts, two-way calendar sync |
| Around the search | Network map, referrals, interview packet, deep prep, drills, salary, offers, references | None |
| Runtime | Claude Code is the runtime. Python tools do the zero-token work | Next.js server with its own LLM layer (any provider, local models too) |

### Where Ascend is ahead, and should stay ahead

Cold start without a résumé. A locked master with ID provenance. Field phrasing research. Referral
first, plus the network map. Interview prep depth. A CI-graded run rubric. Zero-token discovery at a
scale the peer doesn't attempt. A mail classifier calibrated on real mail. Token estimates per engine.
An explicit permission model. Nothing in this plan trades any of these away. In particular, "select,
never reword" is stricter than the peer's "rewrite truthfully, then check". Item A below makes
Ascend's rule enforceable, not looser.

---

## 3. Lessons that are not features

1. **The model never writes its own provenance.** If the model makes a claim about the candidate's
   evidence, the claim carries an ID or a quote that a tool verifies. Today the Delta Log and the
   Fit Score "why" are self-reports. Items A, F and G apply this lesson.
2. **A guard is only as good as what it checks against.** The peer counts the job posting as a fact
   source for the candidate's claims. That means a posting saying "PMP certified, 10,000+ customers"
   would back both in a résumé. A posting is attacker-controlled text. In Ascend, only things the
   user wrote (master, intake, a user-only facts file) back a claim about the user.
3. **Make demo media reproducible.** The peer's README GIF and screenshots come from Playwright
   scripts run against fixture data, with a stand-in model, and the caption says so. Ascend's GIF has
   been "rides with run (b)" since July. Run (b) is another person's real data, which should never be
   in a public GIF anyway.
4. **Stamp outputs with the prompt that made them.** The peer stores `score-posting@1`,
   `tailor-resume@6` with every result. Without this, a rubric change makes old and new scores look
   comparable when they aren't.
5. **Keep only what dedupe needs.** A dismissed posting in the peer keeps its source, ID, dedupe key,
   title and company. Everything else is cleared. Ascend's `postings.jsonl` and `candidates.jsonl` only
   grow.
6. **Docs that contradict the product are bugs.** `docs/ROADMAP.md` still lists "browser auto-apply"
   under "deliberately not building", and 2.0 ships it.

---

## 4. The plan

Sequencing rule (project manager, unanimous): **nothing in this plan merges into PRs #17 or #18.** They
stay fix-only. The order is v1.0 tag, then 2.0 GA, then 2.0.x, then a backlog pulled only by real pain.
Each item lists its vote weight from the anonymous tally (appendix).

### Phase 0: close out v1.0 (this week)

**S. Fix the stale roadmap line and write down the sequencing rule.** P0 · size S · 26 pts
- Change: `docs/ROADMAP.md` moves "browser auto-apply" out of "not building" and links the 2.0 spec
  amendment (2026-10-22). Add the sequencing rule above to the roadmap.
- Done: no doc in the repo says Ascend never submits.

**E. Reproducible demo GIF from fixtures.** P0 · size S–M · 22 pts
- Why: the only thing left blocking the v1.0 tag besides ceremony. It also removes the plan to record
  a real person's run for a public README.
- Change: `tools/demo.py` (or `tests/demo_record.py`) builds a fixture workspace from
  `examples/sample-run/`, serves it with `ui/server.py`, and drives Playwright (already pinned for
  automatic apply) through start-here, the hub's queue, approve and an apply sheet. It writes a
  webm, then turns it into `assets/demo.gif` (≤ 8 MB, ≤ 1200 px). The README caption says "fixture
  data, recorded by `tools/demo.py`".
- Done: one command regenerates the GIF. A test greps the frames' source workspace against a list of
  real-run names and finds none. The v1.0 DoD row is checked.

### Phase 1: the 2.0 GA gate (one PR after #18 merges)

Automatic apply sends model-tailored packs with no human in the loop, so these belong before GA.

**B. Make the lock real: per-entry hashes, recorded amendments.** P0 · size S–M · 55 pts
- Change: at `state.py master --lock`, record a sha256 for **each master entry** (E1, E1a, P3, M7 …)
  in `.ascend-state.json` as `master_hashes`. Entry-level, not whole-file, per the dissent in §7.
  - `lint_artifacts.py`, `grade_run.py` and the send gate in `apply.py` compare the cited entries
    against their hashes.
  - An entry changed since lock fails. An entry added since lock is an **amendment**: `state.py master
    --amend E3a` records it after the user says yes, without a full relock.
  - Packs that cite only unchanged entries stay valid. The hub shows "master changed since lock" with
    the entry IDs.
- Also deny Claude's `Edit`/`Write` on `workspace/*/.ascend-state.json`, the same way `queue.json` is
  denied today. Otherwise the hashes can be rewritten along with the master.
- Done: editing one locked bullet makes lint fail for packs citing it and only those packs. Adding
  E3a and amending passes. A Claude `Write` to the state file is refused.

**A. Bullet equality, and a Delta Log computed by the tool.** P0 · size M · 57 pts
- Change: in `lint_artifacts.py`, parse master bullets into `{id: normalized_text}` next to
  `parse_master_ids`. Normalization folds whitespace, markdown emphasis and smart quotes.
  - Every bullet in a per-job `resume.md`'s experience and project sections must equal one master
    bullet exactly.
  - The tool works out which IDs were used and writes the Delta Log selection block itself
    (`lint_artifacts.py --delta resume.md`). The model may still add a free-text "why" line per pick,
    but no longer the list.
  - A log that cites an ID not used, or a bullet with no master match, fails.
- Pin the word "trim": it means dropping bullets. A shorter version of a bullet is its own master
  entry (`E3a`), added through B's amendment flow. Update `prompts/03` and `prompts/05` to say so.
- The automatic-apply send gate (`apply.ready`) refuses a pack that fails A.
- Gate order: A becomes a hard gate in the same PR as B's amendment flow, never before. Without
  amendments, A plus B turns every tailoring session into a relock (see §7).
- Done: a fixture résumé with one digit changed in a bullet that cites a valid ID fails. A
  dropped-but-still-cited bullet fails. The untouched fixture passes. Running it over the existing
  real packs (the user's, run (b)'s and Niraj's) gives zero false failures, or each one is explained
  and fixed in the normalizer.

**C. Prose fact guard for numbers and credentials, warn first.** P1 · size M · 21 pts
- Why: outreach, the signal page, answer sheets, apply answers and the interview packet are free
  prose. Only the banned-word and forbidden-number lists stand between them and an invented "cut
  costs 40%".
- Change: `tools/factguard.py`, called by the linter.
  - Extract numbers in any format (`4,000+` = 4000, `120k`, `30%`, spelled-out numbers), years and
    credential words (certified, licensed, chartered, accredited).
  - Check each against a source set built only from user-written inputs: `master-resume.md`,
    `intake.md`, the per-job `facts.md` (item D), plus years of experience computed from dated
    entries.
  - The posting text never backs a claim about the candidate. Model-written company research counts
    only on lines that cite a source URL.
  - Capitalized-name extraction is left out. It is the noisy part and flags every person in the
    network map.
- Rollout: warn-only, listed in RUN-REPORT and the hub. Calibrate on the real packs the way the mail
  classifier was, counting precision. It becomes a gate only after precision clears a threshold
  written down in V2-READINESS.
- Never described as proof of truth. It checks tokens, not claims ("led the zero-trust migration"
  has no number and passes). The README wording stays "no detectable fiction".
- Done: 20 seeded inventions across the artifact types are caught at ≥ 90%. The real packs show a
  counted, written-down false-flag rate.

**D. A user-only `facts.md` per job.** P1 · size S · 6 pts (rides with C)
- Change: `workspace/<name>/jobs/<slug>/facts.md`, for things true about this application that don't
  belong in the master ("I used their product at my last job", "relocating in March"). Deny Claude's
  `Edit`/`Write` on it in `.claude/settings.json`, as with `apply-answers.json`. If the model could
  write its own backing facts, C would prove nothing.
- Done: a Claude `Write` to `facts.md` is refused. C accepts a number found only there.

**H. An immutable copy of exactly what was sent.** P1 · size S · 21 pts
- Change: when an application is marked applied (by the runner or the user's click),
  `apply.py` copies the submitted PDF, the answers sent and the form screenshots to
  `jobs/<slug>/sent/<date>/`, read-only, with a sha256 manifest. No version-history UI and no
  restore. It is covered by `forget` (M).
- Done: every applied job in the ledger has a `sent/` folder whose manifest verifies. Regenerating a
  pack afterwards leaves `sent/` unchanged.

**M. `forget <name>`.** P1 · size S · 18 pts
- Why: Ascend is run for other people (run (b), Niraj), and their mail-derived data lives on this
  machine.
- Change: `tools/forget.py` removes `workspace/<name>/`, the Keychain refresh token
  (`delete_refresh` already exists), `~/.config/ascend/<name>` and cron entries. It prints what it
  cannot delete: Claude Code transcripts under `~/.claude/projects` hold the intake verbatim. Say the
  same in `docs/SETUP.md`.
- Done: after `forget`, a grep for the name across those paths finds nothing, and the printout lists
  the transcript paths.

**L. Recruiter-scam signals in the classifier.** P1 · size S · 17 pts
- Change: in `classify.py`, flag mail whose sender domain doesn't match the ledger company and that
  asks for a national ID, bank details, a payment for equipment, or a move to a chat app. Flagged mail
  goes to Needs you with the reason, and nothing is ever drafted for it (relevant if K is built).
- Done: fixture scam mails are flagged. Precision is checked on the 49-message real corpus with zero
  real recruiter mail flagged.

### Phase 2: 2.0.x, after GA

**F. Scoring that code can check.** P1 · size M · 20 pts
- Change: the Phase 27 score row becomes
  `{posting_id, fit, band, rubric, reqs: [{quote, id}], why, red_flags, thin}`.
  - `quote` is a verbatim phrase from the posting. `id` is a master entry or null.
  - `jobqueue.score` checks that each quote is a substring of the stored posting text and that each
    ID exists in the master. It also checks that `why` cites at least one existing ID. Years
    requirements are compared in code with years computed from dated entries (reuse `grade_run`'s
    `YEARS_CLAIM` logic).
  - Code computes coverage (requirements with an ID ÷ requirements) and shows it next to the model's
    fit in the hub.
- Prompt additions to `prompts/27`: band meanings (85–100 clearly meets the core requirements, 70–84
  a gap or two, 50–69 a stretch, under 50 poor), at most three red flags, "if the posting is too thin
  to judge, say so and score conservatively" (this is the LinkedIn-card case), and never infer
  anything from protected characteristics, the user's own included.
- Done: a row citing E99, or a quote not found in the posting, is refused. A description-less card
  scores ≤ 50 with `thin: true`.

**G. Stamp every score with its rubric.** P1 · size S · 20 pts (ships with F)
- Change: `prompts/27` carries a `rubric: 27-score-queue@<n>` line. `jobqueue.score` stores it and
  refuses rows without it. The hub can filter "scored under an older rubric".
- Done: rescore the 10 real survivors from M7 under the new rubric and record the before/after
  in V2-READINESS.

### Backlog: pulled only by real pain

Each item is done when it has one real-run row in V2-READINESS.

| Item | Pts | When to pull it | Notes |
|---|---|---|---|
| **J.** `finder.py fetch <url>`: JobPosting JSON-LD first, else main text | 18 | LinkedIn card leads keep ranking last for lack of a description | The SSRF guard is mandatory, not optional: the local hub server holds a session token. https only, connect to the resolved IP, block loopback, RFC 1918, link-local and IPv6 ULA on every redirect, at most 5 redirects, 2 MB, 10 s. Test that redirects to 127.0.0.1 and 169.254.169.254 are refused. LinkedIn will often block it: fall back to asking the user to paste. |
| **R.** Tests offline by default against recorded fixtures, live tests opt-in by filename | 8 | Next time a test needs the network | Mostly a convention. Keeps OAuth tokens out of CI. |
| **Q.** Compact `postings.jsonl` / `candidates.jsonl`: closed postings older than 60 days become `{id, url_hash, role_key}` stubs | 5 | `candidates()` gets slow, or the files pass ~50 MB | Same privacy idea as lesson 5. |
| **I.** `canonical_url()` for web and LinkedIn rows (strip `utm_*`, `gh_src`, `lever-origin`, `trk`, fragments, lowercase the host). Accent folding in `normalize_title` | 4 | A duplicate from tracking parameters shows up in the queue | Board postings already have canonical ATS IDs (`finder.ats_id`). Only web rows key on `sha1(raw url)`. |
| **K.** Read-only reply support: deterministic extraction of the questions an email asks and any proposed interview time, into the Needs-you row, plus a local `.ics` file | 3 | Replies start arriving faster than the user can read them | If a reply draft is ever added: written in-session to a file, context limited to the per-job résumé and the answer bank (never intake, salary, references or the network map), salary, notice, start date, visa and ID fields always `[…]` placeholders, run through C, never for mail L flags. A canary string in `intake.md` must never appear in a draft. No Gmail write and no calendar write, ever. |
| **N.** PDF fit: when over the page budget, drop the lowest-ranked Delta Log picks one at a time (≤ 6 renders) and log the cuts | 1 | Hand-trimming to one page becomes a regular chore | Rank by relevance, not the peer's oldest-first, because Ascend has a ranked pick list. |

---

## 5. Not adopting

| Peer feature | Why not |
|---|---|
| Cover letter (and the application email) | It is the "why this company" essay at four times the length, against the outlines-only honesty rule, and with automatic apply it would be unattended model persuasion. A form that requires one stops and goes to Needs you, the same as other essays. Dropped by vote (2 pts, 2 disputes). |
| HN "Who is hiring" and the startup board | Free text anyone can post (the densest injection surface Ascend would have), third-party contact emails pulled into someone's workspace, and the startup board needs an account. To reach startups, add their Ashby and Greenhouse slugs to `sources.json`: data, not code. Dropped by vote (0 pts, 7 of 9 disputing). |
| Two-way calendar sync, sending from Gmail | Needs write OAuth scopes that Ascend's read-only design denies on purpose. A local `.ics` file gets most of the value (K). |
| Refine chat with "declined" | Claude Code is the chat, and MASTER GAP already does "add it to your profile first", at the source rather than in one document. |
| Full version history with restore | Nobody has lost a pack. The sent-copy (H) is the part that matters, and unbounded history is unbounded retention. |
| The once-a-day agent itself | The daily sync already exists. A scheduled headless Claude session for scoring is already an unbuilt spec item (V2-READINESS), not something new to plan here. |
| Twelve themes, theme builder, 21 document languages | Another product's taste. One ATS-safe template is the point. |
| Local models, provider choice, a connector so Claude can drive the app | There is no LLM layer to swap: the agent is the runtime, and Claude already drives Ascend natively. An inbound control channel would be new attack surface. |
| Tone and creativity settings | A creativity knob contradicts "never reword". |
| Strength meter, suggestion chips | Web-app UI. Ascend's bullet-quality gate already covers what the meter measures. |
| Export/import file, nightly backups, "delete everything" | The workspace is plain files, so export already exists. Backups double the retention surface. `forget` (M) is the part worth building. |
| Prompt-injection line on every posting | Ascend's quarantine policy and anomalies table are already stronger. |
| Usage ping | Telemetry in a tool that holds other people's job-search data. |

---

## 6. Risks this plan carries

- **A and C make output blander.** In an agent runtime the model "fixes" a warning by deleting the
  specific detail. Watch outreach quality on the first real run after C. That is why C stays
  warn-only until its precision is measured.
- **The amendment flow (B) is the load-bearing part.** If amending is awkward, users will relock to
  get unstuck, and the lock stops meaning anything. Build it so adding E3a takes one confirmation.
- **Scope creep in C.** Hold it to numbers, credentials and bullet equality. No name extraction, no
  "fact platform".
- **Everything here is weighed against the first supervised real send**, which hasn't happened yet.
  If the two compete for time, the supervised send wins.

---

## 7. Dissent (kept, not outvoted)

**Devil's advocate, on A and B together.** If "trim" means only dropping bullets, every shorter variant
becomes a new master entry. If any master change breaks the lock, adding one variant fails every pack
in flight. Built naively, the honesty pair turns a normal tailoring session into a relock cycle and
grows the master into a variant dump. A year out, users relock out of habit and the lock is
meaningless.

*How the plan answers it:* B hashes entries, not the file. Adding an entry is a recorded amendment
the user approves, not a relock. Packs citing unchanged entries stay valid. A is not a hard gate
until that flow ships. If the first real run shows more than a handful of amendments per pack,
revisit the "trim means drop" rule before anything else.

Smaller dissents: the Claude-expert persona disputes K even read-only (scheduling prose is where
invention creeps in). The project manager disputes J before GA. Two personas want C to gate sooner,
arguing a warn-only list nobody reads is noise.

---

## Appendix: the vote

Full council: software engineer, systems engineer, Claude expert, AI security, cybersecurity,
compliance, pragmatist, devil's advocate, project manager. Phase 1 independent in three groups,
Phase 2 anonymous Borda (top 8, 8 points to 1).

| Item | Points | Disputing | Result |
|---|---|---|---|
| A Bullet equality + tool-built Delta Log | 57 | 1 | P0, Phase 1 |
| B Per-entry master hashes + amendments | 55 | 0 | P0, Phase 1 |
| S Roadmap fix + sequencing rule | 26 | 0 | P0, Phase 0 |
| E Demo GIF from fixtures | 22 | 0 | P0, Phase 0 |
| C Prose fact guard, warn first | 21 | 1 | P1, Phase 1 |
| H Sent-copy snapshot | 21 | 0 | P1, Phase 1 |
| F Code-checkable scoring | 20 | 0 | P1, Phase 2 |
| G Rubric stamp on scores | 20 | 0 | P1, Phase 2 |
| J Fetch by URL + SSRF guard | 18 | 1 | P2, backlog |
| M `forget <name>` | 18 | 0 | P1, Phase 1 |
| L Recruiter-scam signals | 17 | 0 | P1, Phase 1 |
| R Offline fixture tests | 8 | 0 | P2, backlog |
| D User-only `facts.md` | 6 | 0 | P1, with C |
| Q Compact postings files | 5 | 0 | P2, backlog |
| I Canonical URLs for web rows | 4 | 0 | P2, backlog |
| K Read-only reply support | 3 | 2 | P2, backlog |
| P Cover letter | 2 | 2 | Dropped |
| N PDF fit by pick rank | 1 | 0 | P2, backlog |
| O HN / startup sources | 0 | 7 | Dropped |
