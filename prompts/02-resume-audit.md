# Phase 2 — Resume Audit → `resume-audit.md`

**Goal:** read the user's current resume and produce a precise, prioritized improvement report —
what's failing ATS, what's failing the 6-second recruiter scan, which target-role keywords they're
missing, and which 2026 trends they're not leveraging. This report feeds Phase 3 (master resume).

**Read first:** `workspace/<name>/intake.md`, the user's resume at `inputs/current-resume.*`,
`../reference/ats-and-keywords.md`, `../reference/resume-writing-rules.md`,
`../reference/number-and-honesty-policy.md`.

If the user has **no resume**, skip the audit and note that Phase 3 will build a master resume from
the LinkedIn export + intake answers; capture in `resume-audit.md` what's needed to do that well.

---

## Produce `resume-audit.md` with these sections

### 1. Snapshot
Current target alignment in one paragraph: does the resume read at the level/role the user is aiming
for, or above/below it? Name the gap.

### 2. ATS pass/fail
Score the resume 0–100 for ATS parseability and keyword coverage. Check, per
`../reference/ats-and-keywords.md`:
- Format hazards (tables, columns, text boxes, headers/footers, graphics, non-standard section names).
- Standard section presence and naming (Summary, Experience, Skills, Education).
- Keyword coverage in *context* (contextualized keywords rank higher than skills-list-only).
- Knockout-risk items (years of experience phrasing, certs, work authorization).
List each issue with a concrete fix.

### 3. The 6-second scan
Role-play a senior recruiter giving it 6 seconds. What's visible, what's missing, what would make them
toss it. Verdict: advance / maybe / reject, and the one change that most improves it.

### 4. Keyword gap table
Three columns: **present** (target-role keywords already there), **missing-but-claimable** (the user
has the evidence but the resume doesn't say it — pull evidence from LinkedIn/intake), **true gaps**
(keywords the user cannot honestly claim — these get honest-handling, never bluffing). Derive the
target keyword set from `intake.md` + the role-family rows in `../reference/ats-and-keywords.md`.

### 5. 2026 trend leverage
Which current resume-effectiveness trends is the user *not* using? (e.g., contextualized keywords over
skills lists, AI-screening-aware specific nouns/numbers, two pages for 10+ yrs, named tools + scope +
measured outcome per bullet, quantified results everywhere). Specific, not generic.

### 6. Bullet rewrites (sample)
Take 3–5 of the user's weakest bullets and rewrite them to the formula in
`../reference/resume-writing-rules.md` (verb + named system + scope + measured outcome + signal),
using only facts the user can substantiate. Show before → after. These previews seed the master
resume's phrasing.

### 7. Prioritized fix list
The improvements ranked by impact. Mark which are pure-formatting (do immediately) vs. content gaps
(resolved in Phase 3) vs. true gaps requiring honest framing or skill-building.

## Honesty & numbers
- Apply `../reference/number-and-honesty-policy.md`: keep the user's verifiable numbers exact; round or
  remove employer-internal operational numbers per their `intake.md` sanitization rule; never invent a
  metric to fill a gap. If a bullet has no number, suggest *what to measure*, don't fabricate one.

## Verify
- Every claimed "missing keyword" is genuinely absent from the current resume (grep/scan to confirm).
- Every rewrite uses only substantiable facts.
- ATS score has a transparent rationale.

## Checkpoint
Give the user the ATS score, the single biggest fix, and the count of missing-but-claimable keywords
(the easy wins). Confirm the target keyword set with them before Phase 3.
