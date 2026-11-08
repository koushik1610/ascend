# Ascend 2.0: find, apply and track, from one local hub

**Status:** design approved 2026-10-16. Amended 2026-10-17 after the council review of PR #15: see §11,
which overrides earlier sections where they differ.
**Branch:** `ascend-v2`
**Builds on:** v1 pipeline (phases 1 to 26), `tools/pipeline.py` ledger, `ui/server.py` console, `templates/start-here.template.html` hub, Phase 13 daily brief, Phase 14 ATS aggregation

---

## 1. Goal

Ascend v1 produces excellent apply packs and then stops. Across four real runs it produced zero sends, while a commercial auto-applier (JobHire.ai) sent 1,029 applications for the same user and got 3 interview invites. v2 closes the loop between those two failure modes:

- **Find** matching jobs continuously from several sources.
- **Apply** at a pace the user sets, in the apply mode the user picks, with Ascend's honesty gates intact.
- **Track** what happened (sent, acknowledged, replied, info requested, interview, rejected, ghosted) automatically from Gmail, on a dashboard in the existing hub.
- **Spend tokens only where judgment is needed,** and show the user what each run costs.

### Success criteria
1. The hub shows a current funnel (found → screened → matched → queued → applied → replied → interviewing → offer) updated from Gmail with no manual logging.
2. A day's run at 15 to 25 queued matches is estimated before it starts, and its cost by stage is recorded and shown in the hub. *(Amended, §11: Claude Code exposes no token counts, so "measured" cannot be met. The figures are character-based estimates and are labelled that way.)*
3. No application is ever sent twice, and no application is sent with a claim the master résumé cannot source.
4. Info requests and assessments surface within one sync of arriving (the leak that left 108 unanswered on JobHire).
5. Every v1 workflow keeps working unchanged for a user who never opts into v2 features.
6. *(Added, §11.)* Callbacks, not volume: over the first 50 applications sent through v2, the share that reaches an interview is reported in the hub against JobHire's baseline of 3 in 1,029 (0.3%). Agent-submit and fully automatic modes are not proposed again until this number exists and beats that baseline.

### Non-goals
- A hosted, multi-user service. v2 is local and single-user, like v1.
- Bypassing CAPTCHAs, bot checks or login walls. The agent stops and hands the job to the user.
- Reading LinkedIn messages or applications through an API. LinkedIn does not offer one. LinkedIn data comes from the export or from Chrome on demand.
- Submitting applications through ATS APIs. Greenhouse, Lever and Ashby accept application submissions only with the employer's API key.

---

## 2. Decisions taken

| Question | Decision |
|---|---|
| Apply modes | **All three**, chosen per run and overridable per job: assisted, agent-submit, fully automatic. Each shows a token warning. |
| Engines | **All three**, chosen per run: A deterministic core, B agent-driven, C core + claude.ai Gmail connector. |
| Deployment | Local, single user. Data under `workspace/<name>/`. |
| Job sources | Public ATS boards, LinkedIn Jobs via Chrome (on demand), job-alert emails in Gmail, recruiter inbound in Gmail. |
| Pace | Tuned for 15 to 25 queued matches a day. |

---

## 3. Apply modes

| Mode | What happens | Est. tokens per application | At 20/day |
|---|---|---|---|
| **Assisted** | Score, select bullets, render PDF, pre-fill an apply sheet. Hub "Apply" copies answers and opens the posting. User submits. | 5K to 10K | 100K to 200K |
| **Agent-submit** | As assisted, then Claude in Chrome fills and submits each job the user approved in the hub. | 30K to 80K | 0.6M to 1.6M |
| **Fully automatic** | Agent-submit without per-job approval for anything above the match threshold, up to a daily cap. | 30K to 80K | 0.6M to 1.6M |

Estimates are replaced by measured per-stage figures from `usage.jsonl` once a mode has run.

**Guardrails, all modes:** honesty gates and `lint_artifacts.py` run before any send. CAPTCHA, login wall, missing file, unanswerable question or a sensitive field (password, government ID, bank details) stops the agent and moves the job to **Needs you**. Fully automatic needs a typed confirmation to enable, has a daily cap (default 25), a one-click pause, and auto-pauses when the reply rate over the last 50 sends falls below a threshold (default 5%).

---

## 4. Engines

All engines produce the same files (§5). The hub, the ledger, scoring, tailoring and apply read only those files, so switching engines between runs loses nothing.

| Stage | A: deterministic core | B: agent-driven | C: core + claude.ai Gmail |
|---|---|---|---|
| Find jobs | `finder.py` | Claude WebSearch/WebFetch | `finder.py` |
| Pre-filter | `prefilter.py` | Claude applies the same rules | `prefilter.py` |
| Gmail | `gmail_sync.py` (user's own OAuth client) | Gmail connector in session | Gmail connector in session |
| Classify mail | `classify.py` rules, Claude for leftovers | Claude | `classify.py` over connector output, Claude for leftovers |
| Score, tailor, apply | Claude | Claude | Claude |
| Setup | Google Cloud OAuth client, once | none | none |
| Unattended | yes (launchd, 0 tokens) | scheduled Claude session only | finder yes, Gmail in session only |
| Est. tokens per daily run before apply | 50K to 120K | 400K to 1M+ | 80K to 200K |

**Selection:** `/ascend run` (or the hub's Run panel) asks for engine and apply mode, showing the estimate and last measured usage for each combination. The choice is stored in `.ascend-state.json` as the default for scheduled runs. If the chosen engine cannot run (A without an OAuth client, C without the connector), the run says why and offers the next cheapest.

---

## 5. Data contract

All under `workspace/<name>/data/`. JSON Lines files are append-only. JSON files are rewritten atomically (tmp + `os.replace`), following `tools/state.py`.

| File | Writer | Shape (key fields) |
|---|---|---|
| `postings.jsonl` | finder, alerts, linkedin_search, engine B | `id` (source:board:posting_id), `source`, `company`, `title`, `location`, `remote`, `comp_min/max`, `url`, `apply_url`, `ats`, `first_seen`, `last_seen`, `closed`, `text_hash` |
| `candidates.jsonl` | prefilter | `posting_id`, `passed`, `reasons[]`, `keyword_overlap`, `run_id` |
| `queue.json` | score, hub actions | per job: `posting_id`, `fit` (0-100 + components), `gaps[]`, `state` (matched, approved, rejected, needs-you, applying, applied, applied?), `mode_override`, `nn` (job folder once tailored) |
| `mail.jsonl` | gmail_sync, engine C | `msg_id`, `thread_id`, `from`, `subject`, `date`, `body_excerpt` (≤2,000 chars), `labels` |
| `events.jsonl` | classify | `msg_id`, `category`, `confidence`, `rule` or `llm`, `posting_id` or `nn` if matched, `due` (for info requests/assessments) |
| `usage.jsonl` | every Claude stage | `run_id`, `engine`, `mode`, `stage`, `input_tokens`, `output_tokens`, `items` |
| `sync-state.json` | gmail_sync | `history_id`, `last_sync`, `account` (no secrets) |
| `sources.json` | user via hub | company board list, alert senders, filters, caps |

Email categories: `acknowledgement`, `rejection`, `info-request`, `assessment`, `interview-invite`, `status-update`, `recruiter-inbound`, `job-alert`, `other`.

`pipeline.py ingest` maps events to ledger transitions with `source=gmail`, keeping the ledger's append-only rule: acknowledgement → `applied` (confirms an `applied?`), info-request/assessment → `responded`, interview-invite → `screen`, rejection → `rejected`. Ghosting stays computed by `pipeline.py overdue`.

---

## 6. Components

| Unit | Responsibility | Tokens |
|---|---|---|
| `tools/finder.py` | Fetch Greenhouse, Lever, Ashby, Workable, SmartRecruiters public JSON for `sources.json` companies. Dedupe by posting ID and text hash, track first/last seen, mark closed. Backoff and per-board skip on failure. | 0 |
| `tools/prefilter.py` | Hard rules from `intake.md` and `sources.json`: title families, seniority, remote/location, posted pay floor, excluded keywords, blocklist, already applied. Keyword overlap against master §4 keyword set. | 0 |
| `tools/gmail_sync.py` | OAuth installed-app loopback flow, `gmail.readonly`, refresh token in macOS Keychain via `security`. Incremental sync via Gmail `history`; 30-day date resync when the cursor expires. Stdlib only (`urllib`). | 0 |
| `tools/classify.py` | Rule table (ATS sender domains, phrase patterns) to category. Match to a queued job by company and title. Leftovers written to `classify-pending.jsonl` for a Claude batch. | 0 (+~1K per leftover) |
| `tools/alerts.py` | Parse LinkedIn and Indeed job-alert emails into `postings.jsonl`. Recruiter inbound into queue entries flagged `needs-you`. | 0 |
| `tools/usage.py` | Append and summarize token usage by run, engine, mode, stage. | 0 |
| Phase 27 prompt `27-score-queue.md` | Claude scores prefilter survivors in batches against the master and `industry-fit.md`. Writes `queue.json`. | 2K to 4K per posting |
| Phase 5 (existing) | Tailor approved jobs: CORE pack by selection, render PDF. | 3K to 6K per job |
| Phase 28 prompt `28-apply.md` | Assisted: build apply sheet. Agent modes: Claude in Chrome fill and submit with stop rules. | 0 / 30K to 80K |
| `linkedin_search` (op) | On demand, reads result cards only, writes `postings.jsonl`. | 10K to 20K per search |
| `tools/pipeline.py` (existing) | Gains `ingest WS` and a duplicate-apply guard (`guard WS company posting_id title`). | 0 |
| `ui/server.py` + hub | New read endpoints for each data file, write endpoints for approve, reject, apply, mode, pause, Gmail connect. Same token, Host and Origin checks as today. | 0 |

### Hub
`start-here.html` keeps the weekly loop and gains four tabs:
1. **Dashboard:** funnel, this week's counts, reply and ghost rates, low-reply warning, token spend by stage, engine and mode.
2. **Queue:** matched jobs with Fit Score, reasons, gaps. Approve, Reject, Apply, Send to agent. Mode switch with token warning. Needs you list.
3. **Inbox:** classified mail with category, matched job, Gmail link. Info requests and assessments pinned with due dates.
4. **Sources & settings:** boards, alert senders, filters, engine, apply mode, daily cap, per-run token cap, Gmail status, pause.

---

## 7. Failure handling

| Failure | Behaviour |
|---|---|
| Board rate-limit or outage | Backoff, skip board this run, record in run log. |
| Gmail cursor expired | 30-day resync by date, dedupe by `msg_id`. |
| OAuth token revoked | Hub shows disconnected + reconnect. A offers C if available. |
| CAPTCHA, login, missing file, unknown question, sensitive field | Agent stops, screenshot, job → `needs-you` with reason. |
| No submit confirmation | State `applied?`. Confirmed by a later acknowledgement or asked after 48h. |
| Duplicate apply | `pipeline.py guard` blocks same company + posting ID, or company + normalized title within 60 days. |
| Token cap reached | Stage stops. Remaining items stay queued. |

Every stage is idempotent and resumable. One stage failing does not block others.

---

## 8. Privacy and security

- Personal data stays under gitignored `workspace/`. Nothing leaves the machine except application content sent to the employer the user is applying to.
- **This is a deliberate, scoped exception** to v1's binding rule "never transmit `workspace/` data outward". It applies only in the agent apply modes, only to finder-sourced application URLs on the allow-listed ATS domains, and only with the content of that job's pack and answer sheet. CLAUDE.md and `reference/untrusted-content-policy.md` are updated to state the exception in the module that introduces agent apply (M8), not before.
- Gmail: read-only scope, user-owned OAuth client, refresh token in Keychain, headers + 2,000-char excerpt only, no attachments, 180-day retention by default.
- Email bodies and job pages are untrusted data under `reference/untrusted-content-policy.md`. Rules match patterns only. Claude classification and the Chrome agent never follow instructions found in content.
- Agent modes open only finder-sourced URLs on known application domains (Greenhouse, Lever, Ashby, Workable, SmartRecruiters, Workday). Links from email always need the user's click, in every mode.
- The answer sheet never fills passwords, government IDs or bank details.
- Server write endpoints reuse the per-session token, Host and Origin checks. OAuth redirect binds 127.0.0.1 and checks `state`.
- `.claude/settings.json` gains only pinned forms of the new tools.

---

## 9. Testing

- Fixtures only: recorded ATS JSON per board type. A synthetic mailbox (~60 messages across all categories plus ambiguous ones). No real mail in the repo.
- Unit: prefilter rules, dedupe, cursor expiry path, classifier accuracy (≥95% on rule-covered categories), event matching, `ingest` idempotency, duplicate guard, usage accounting.
- Agent modes: a local fake application form served by the test server, with CAPTCHA and unknown-question variants. Asserts the stop behaviour. `--dry-run` fills without submitting.
- Engines: A and C produce identical `events.jsonl` from the same fixture. B is checked against the schema.
- Existing gates extend: `tests/smoke.py`, `lint_artifacts.py`, `grade_run.py`, `ops.json` parity.
- Release: assisted mode + engine A become **stable** after one week of real use. Agent-submit, automatic, B and C ship **beta** until they have run for real.

---

## 10. Delivery

Built one module at a time on `ascend-v2`, each module merged only when v1 smoke stays green, per the implementation plan in `docs/superpowers/plans/2026-10-16-ascend-v2.md`. Every module is useful on its own: the tracker works before the applier exists, and the finder works before the tracker.

---

## 11. Amendments after the council review (2026-10-17)

The first council round on PR #15 (ten personas) returned nine CONDITIONAL and one REJECT. The user
chose to split the PR. These amendments override the sections above.

- **One apply mode in this release: assisted.** Agent-submit, fully automatic, the local fake form and
  the CLAUDE.md / untrusted-content-policy submit exception (§3, §8) moved to the
  `ascend-v2-agent-modes` branch. Nothing in this release transmits an application, so v1's rule "never
  transmit workspace data outward" holds without exception. The follow-up PR must first fix the
  council's agent-path findings recorded on that branch: the allow-list URL-parsing bypass, a
  model-forgeable automatic confirmation, no "applying" claim before a submit, an unvalidated
  `apply_url` from Claude-added rows, and model-written fit alone authorizing a send.
- **Approval is the user's click.** `jobqueue.py set-state` refuses `approved` and `applied` from the
  command line. A sent job never moves back to approved.
- **Gmail through the claude.ai connector is read-only in settings,** not only by policy:
  `.claude/settings.json` denies the connector's send, reply, forward, draft, label, spam and trash
  tools and Drive's write tools. `run.py plan`, the README and prompt 29 state each engine's
  permissions.
- **Retention is enforced** by the daily sync: mail older than `retention_days` (default 180) is
  deleted, mail placed as not job-related keeps headers only, and promotions, social and forums mail is
  never fetched.
- **Criterion 2 amended and criterion 6 added** (§1).
- **Not built in this release.** The hub has three tabs, not four. There is no Sources & settings tab:
  boards and filters are edited in `data/sources.json`. Also not built: the 48-hour "applied?" follow-up
  (moot without agent modes), a per-run token cap, board backoff and retry, an automatic fallback from
  engine A to C, and launchd. The scheduler uses cron, which skips a run while the Mac sleeps.
  `docs/V2-READINESS.md` keeps this list current.

## 12. Amendment (2026-10-22): automatic apply

The user chose to ship fully automatic apply before criterion 6's benchmark. It is specified in
`2026-10-22-ascend-v2-auto-apply-design.md`, which overrides §11's "one apply mode" and "nothing transmits an
application" for applications sent by the local runner (or by Claude after the user's yes per batch) to the
job's own allowed job-board page. Agent-submit by Claude on its own stays out of the release.
