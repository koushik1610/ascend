# Ascend 2.0: automatic apply, Workday and Eightfold sources (design)

Date: 2026-10-22. Builds on `2026-10-16-ascend-v2-design.md` and PR #17 (`fix/v2-rerun-council`).
Branch: `feat/v2-auto-apply`, stacked on PR #17.

## 1. Goal

Make Ascend apply the way JobHire does: jobs are found, scored, tailored and submitted every day without
a click per job, while the honesty gates, the duplicate guard and the user's own answers stay in charge.
Cover the companies the finder cannot see today because they hire through Workday or Eightfold.

Success criteria:

1. A Greenhouse, Ashby or Lever job that passes every gate in §5 is submitted by the runner with no
   click, and is marked applied only after the ATS's confirmation page was seen.
2. Every job the runner cannot finish lands in **Needs you** with the reason and a filled apply sheet.
   No job is ever marked applied on a guess.
3. Zillow and Arctic Wolf (Workday) and Netflix (Eightfold) postings reach the queue through the daily
   finder at zero tokens.
4. The full council approves v2 as a release (§10).

## 2. Decisions the user made (2026-10-21 and 2026-10-22)

- **Fully automatic apply, before the 50-send callback benchmark.** This overrides criterion 6 of the v2
  spec (agent modes wait until 50 sends beat JobHire's 0.3% callback rate). The auto-pause on a low
  reply rate (§6) stays.
- **A local runner submits, Claude helps with the stops.** The runner is a script on the user's Mac,
  not Claude. Claude's browser rules need the user's yes before each submission, so Claude only fills
  stopped jobs in a session and submits after one yes per batch.
- **Stored answers for the sensitive questions.** Work authorization, sponsorship, salary and start
  date are filled from `data/apply-answers.json`, which the user writes. Claude never writes, edits or
  infers these answers.
- **Claude in Chrome form filling and file upload are allowed again** (removed from the deny list).
  Page scripting, batch, image upload and shortcuts stay denied.

## 3. New job sources

### Workday

Board entry in `data/sources.json`:

```json
{"company": "Zillow", "ats": "workday", "slug": "zillow", "pod": "wd5", "site": "Zillow_Group_External"}
```

- List: `POST https://{slug}.{pod}.myworkdayjobs.com/wday/cxs/{slug}/{site}/jobs` with
  `{"appliedFacets": {}, "limit": 20, "offset": N, "searchText": S}`. `S` is the board's `search` field,
  else the first `title_include` pattern with regex syntax removed. Pages until `total` or 200 rows.
- Detail: `GET .../wday/cxs/{slug}/{site}{externalPath}` for the description, location, remote type and
  requisition ID. Detail is fetched only for rows whose title passes `title_include`/`title_exclude`, so a
  board with 300 jobs costs a handful of requests.
- `posting_id` is `workday:{slug}:{jobReqId}`. The apply URL is built from `slug`, `pod`, `site` and
  `externalPath`; nothing from the response body becomes a URL host.
- Verified 2026-10-21: Zillow returned 24 security postings with no login.

### Eightfold (Netflix)

```json
{"company": "Netflix", "ats": "eightfold", "slug": "netflix", "host": "explore.jobs.netflix.net", "domain": "netflix.com"}
```

- List: `GET https://{host}/api/apply/v2/jobs?domain={domain}&query={S}&start=N&num=10`, detail by
  position ID. Requests are spaced at least 2 seconds apart.
- HTTP 429 marks the board **throttled** in `board-health.json` (not broken). It honors `Retry-After`
  and tries again on the next daily run. The hub shows throttled boards separately from broken ones.

### Probe

`finder.py probe COMPANY [--careers URL]` also reads the careers page for `*.wdN.myworkdayjobs.com/<site>`
and Eightfold links and prints a ready board entry. Unknown systems (Phenom, own sites) are reported as
"not supported" with the system name when the page shows it.

### Applying to Workday and Eightfold jobs

Both need an account with a password. The runner never creates accounts or types passwords, so these jobs
always go to Needs you with their apply sheet.

## 4. The runner (`tools/autoapply.py`)

- **Browser.** Playwright with Chromium, using its own profile directory under
  `workspace/<name>/.autoapply-profile/`, separate from the user's Chrome. Playwright is imported only
  inside the runner. Without it, the runner exits with "auto-apply needs Playwright: pip install
  playwright && playwright install chromium", and the hub shows the same line. Every other tool stays
  stdlib-only.
- **Forms.** One filler per ATS (Greenhouse, Ashby, Lever) in `tools/autoapply_forms.py`. A filler finds
  each field by its label, maps the label to an answer source, fills it, uploads the job's tailored
  résumé PDF, and returns the list of fields it could not fill.
- **Answer sources, in order:**
  1. `data/profile.json`: name, email, phone, location, LinkedIn, website, GitHub.
  2. `data/apply-answers.json` (user-written): work authorization, sponsorship, salary, start date,
     plus the user's own answers to fixed demographic questions (each may be "decline to answer").
  3. `data/answer-bank.json` (user-written): free-text questions, matched by normalized question text.
     Claude may draft entries only into `data/answer-bank.proposed.json`.
  Anything else that is required is an unknown field, and the job stops.
- **Stops (job goes to Needs you with the reason):** CAPTCHA or bot check, login or account wall, an
  unknown required field, a failed upload, a résumé that fails `lint_artifacts.py` or is stale, the
  duplicate guard, a host not on the allow-list, or no confirmation within 30 seconds of submit.
- **Confirmation.** Each filler has the ATS's confirmation signal (URL change or confirmation text).
  Seen means `submitted`. Not seen means `unclear`, and the job goes to Needs you, never to applied.
- **Evidence.** Screenshots of the filled form before submit and of the confirmation page are saved to
  `jobs/NN-*/apply/`. One row per attempt goes to `data/apply-log.jsonl`:
  `{posting_id, mode: "auto", result: submitted|unclear|stopped, reason, at, screenshots}`.
- **Dry run.** `--dry-run` fills every form and takes the screenshots but never clicks submit.
- **Commands:** `autoapply.py run WS [--dry-run] [--limit N]`, `autoapply.py status WS`,
  `autoapply.py pause WS [--reason TEXT]`. There is no command that turns auto-apply on (§6).

## 5. The automatic flow

A job is **ready** when all of these hold:

1. It passed the rule prefilter and is in state `matched` or `approved`.
2. Its fit score, written through `jobqueue.py score`, is at or above the threshold (default 75).
3. Its job folder has a tailored résumé PDF that passes `lint_artifacts.py` and is not stale.
4. `pipeline.py guard` finds no earlier application to the same role.
5. Its ATS is Greenhouse, Ashby or Lever and the apply URL, rebuilt from the board entry and posting ID,
   has an exact allowed host: `job-boards.greenhouse.io`, `boards.greenhouse.io`, `jobs.ashbyhq.com`,
   `jobs.lever.co`.
6. The company has had fewer than 2 applications from Ascend in the last 30 days.

The model's fit score is one of six gates, so it can never send an application on its own.

`daily.py` gains an `autoapply` stage after prefilter, which submits ready jobs up to the day's cap when
auto-apply is on and not paused. Scoring and tailoring still need Claude. They run in a `/ascend run-v2`
session, or in an optional scheduled headless session (`run.py schedule --claude`, default off) that
runs prompt 29 in auto mode for the top 5 new jobs (about 15K to 30K tokens a day).

A job the runner submits moves `matched` or `approved` → `applying` → `applied` (confirmation seen) or
`needs-you` (anything else). The hub shows `applying` as "submitting", never as sent.

## 6. Controls

- `data/auto.json`: `{enabled, enabled_at, daily_cap, fit_threshold, paused, paused_reason}`.
- It is turned on only through the hub: a switch, then the user types `apply for me` into a box.
  `POST /api/auto` checks the session token, Origin and the phrase. `.claude/settings.json` denies
  Claude's Edit and Write on `auto.json`, `apply-answers.json` and `answer-bank.json`. The runner refuses
  to run when `auto.json` was not written by the server (the server stores a keyed hash of the file with a
  secret kept outside `workspace/`).
- Defaults: 25 a day (5 a day in the first 7 days after enabling), fit 75, max 2 per company per 30 days.
- Pause and resume are one click in the hub. `autoapply.py pause` also pauses. Resume only through the
  hub.
- Auto-pause: once 50 applications are sent, auto-apply pauses when fewer than 5% of the last 50 got any
  reply (`events.jsonl` interview, rejection, recruiter or assessment for that job). Three `unclear`
  results in one day also pause it.

## 7. Claude for the stopped jobs

Prompt 28 gains a "finish stopped jobs" step for a session. For each Needs you job on Greenhouse, Ashby
or Lever, Claude in Chrome opens the rebuilt apply URL, fills the form with `form_input` and
`file_upload` from the same three answer sources, and lists what it filled. It submits nothing until the
user says yes in chat to that batch, by job. CAPTCHAs, logins and unknown fields stay with the user.
Links from email are never opened by Claude in this step.

## 8. Permissions and policy changes

- `.claude/settings.json`: remove `form_input` and `file_upload` from the Claude in Chrome deny list.
  Add Edit and Write denies for `auto.json`, `apply-answers.json`, `answer-bank.json` (both path forms).
  Add `python3 tools/autoapply.py *` to the allow list.
- `CLAUDE.md` and `reference/untrusted-content-policy.md`: one scoped exception to "never transmit
  workspace data": the runner, and Claude after the user's batch yes, send one job's application
  content to that job's allowed ATS host. Nothing else leaves the machine.
- `README.md` and `docs/V2-READINESS.md` describe the runner, its risks, and that some ATS terms forbid
  automated applications.

## 9. Testing

- Unit (stdlib, run in CI): Workday and Eightfold normalization from saved responses, throttled board
  health, probe link parsing, every gate in §5, the host allow-list against lookalike hosts
  (`job-boards.greenhouse.io.evil.com`, userinfo, IDN), label mapping, answer-bank matching, `auto.json`
  integrity, caps, auto-pause, state moves.
- Runner (needs Playwright; skipped with a printed reason when it is missing): local fake Greenhouse,
  Ashby and Lever forms served by the test server, with variants for a CAPTCHA, an unknown required
  field, a failed upload and no confirmation. Asserts submitted, stopped and unclear outcomes and that
  `--dry-run` never submits.
- Existing gates stay green: `tests/smoke.py`, `grade_run.py`, all `tests/test_v2_*.py`.
- Live: `--dry-run` on the user's real queue, screenshots reviewed by the user before the first real
  submit.

## 10. Release review

After the build, the full council (10 personas, disposition verdicts) reviews the whole v2 pipeline,
not only this branch's diff: sources, mail, queue, apply, runner, hub, permissions and docs, against a
fresh run. Each round's fixes go into this PR with tests, and a rerun follows. The loop ends when all 10
return APPROVE for v2 as a release. Every round's verdicts, rulings and deferred minors are kept in the
ledger and the PR body.

## 11. Not in scope

CAPTCHA solving, account creation, typing passwords, submitting on Workday, Eightfold or Phenom, LinkedIn
Easy Apply, and any submission to a host outside §5's allow-list.

## 12. Risks the user accepts

- Some ATS terms of service forbid automated applications. A company may flag or ignore them.
- A wrong stored answer is repeated on every form until the user fixes `apply-answers.json`.
- Sending before the callback benchmark exists means volume can outrun quality. The caps and the
  auto-pause are the guard.
