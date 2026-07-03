# Phase 12 — Application Answer Sheet → `answer-bank.md` (+ per-job `answer-sheet.md`)

**Goal:** kill the most tedious, error-prone part of applying — the open-ended application questions —
without a ToS-violating autofill bot. Generate an honest, **reusable** answer bank the user copy-pastes,
with **varied phrasings** so 15 applications don't carry the identical paste-able paragraph that
recruiters now flag instantly. Run on request: *"build my answer sheet,"* `/ascend answers`, or per job
when a posting has custom screener questions.

**Read first:** `workspace/<name>/intake.md`, `master-resume.md` (the real evidence to draw from),
`interview-packet/` (positioning hooks), the job's `jobs/<NN>/` if per-job,
`../reference/number-and-honesty-policy.md`.

> **Language gate (binding for anything sendable).** Every line the user could paste or send follows
> `../reference/resume-writing-rules.md → Bullet writing` and `../.claude/banned-words.md`: no em/en-dash
> sentence breaks, no banned vocabulary, no clause-joining semicolons, no dramatic-reveal colons.
> Sanitize at GENERATION, not as a post-hoc résumé-only pass. Gate mechanically before presenting:
> `python3 tools/lint_artifacts.py <the files you wrote>` (add `--config workspace/<name>/lint-config.json`
> if it exists) → 0 findings.

> **Honesty:** every answer is drawn from the user's real evidence — no invented experience or numbers.
> Anything requiring the user's genuine motivation or opinion (a real "why this company," a personal
> values answer) is produced as **beats/outline only**, flagged `DRAFT — WRITE IN YOUR VOICE`. Factual
> screeners (work auth, notice period, salary) are filled from `intake.md` only.

---

## 1. `answer-bank.md` — the reusable core (workspace-level, built once)
Honest, ready answers to the questions almost every application asks, each with **2–3 phrasing
variants** so the user rotates them and never pastes the same block twice:

- **"Why are you interested in this role / type of work?"** (role-level, company-agnostic — variants)
- **"Tell us about yourself / your background"** (a tight written version of the intro script)
- **"Greatest strength / what you'd bring"** (tied to the master résumé's differentiators)
- **"Salary expectations"** — the honest anchor from `intake.md` ("targeting <range> for this level;
  open to discussing the full package") — never a number the user didn't authorize.
- **Logistics screeners** — work authorization, sponsorship need, notice period, location/remote,
  willing-to-relocate, earliest start — straight from `intake.md` (mark any unknown `ASK USER`).
- **Voluntary EEO / demographic questions** — note these are **optional**; the honest default guidance
  is "prefer not to answer" unless the user chooses otherwise. Don't auto-fill identity data.
- **"Anything else we should know?"** — one short, genuine value-add (variant options).

## 2. Per-job `answer-sheet.md` (only when a posting has custom questions)
For a specific application's open-ended questions ("Why <Company>?", "Describe a time you…", a
take-home prompt, a portfolio question):
- Pull the company's custom questions (from the JD / application page; mark `VERIFY:` if you can't see
  the live form).
- Answer the **evidence-based** ones by *selecting* from the master résumé + STAR stories (reference
  story IDs, don't re-author).
- For "Why <Company>?" and any motivation question → **outline the honest beats only**, flagged for the
  user's own voice (per the conviction-essay rule). Never ship generated conviction as final.
- Keep each answer to the posting's word/char limit; note the limit.

## Anti-sameness check
Before finishing, scan the bank + any per-job sheets: if two answers to the same question are near
identical, vary them. Remind the user this is the whole point — identical pasted answers are a top
"AI applicant" tell.

## Wire it in
- Optional addition to a job's CORE apply pack when the posting needs custom answers.
- The daily briefing can remind the user the bank exists when an application has open-ended fields.

## Verify
- Every factual answer traces to `intake.md` or the master résumé — nothing invented.
- Motivation/EEO answers are user-owned (outlines / "prefer not to answer" default), not fabricated.
- Same-question answers are genuinely varied.

## Checkpoint
Tell the user where the bank is, that the phrasings are varied on purpose, and which screeners need a
real answer from them (the `ASK USER` items).
