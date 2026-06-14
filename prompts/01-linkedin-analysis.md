# Phase 1 — LinkedIn Data Analysis → `linkedin-analysis.html`

**Goal:** turn the user's raw LinkedIn export into a single, visually rich HTML dashboard that audits
their professional presence and hands them **10 concrete next steps** to grow reach and recruiter
findability. This is the first thing the user sees, so it must be genuinely useful and good-looking.

**Read first:** `workspace/<name>/intake.md`, `../reference/ats-and-keywords.md`,
`../templates/linkedin-analysis.template.html`.

---

## Inputs
The unzipped LinkedIn export under `workspace/<name>/inputs/linkedin-export/`. Common files (names vary
by export; handle missing ones gracefully):
- `Profile.csv` — headline, summary, industry, location.
- `Positions.csv` — roles, companies, dates, descriptions.
- `Skills.csv` + `Endorsement_Received_Info.csv` — listed skills, endorsement counts.
- `Connections.csv` — network size, companies, positions, connected-on dates.
- `Invitations.csv` — inbound/outbound invite ratio.
- `messages.csv` — outreach volume (counts only — DO NOT read or quote message contents).
- `Education.csv`, `Certifications.csv`, `Recommendations_*.csv`, `Shares.csv` / posts.

If the export is missing, build a lighter analysis from the intake answers and the resume, and say so.

## Analysis to perform (compute from the data — never invent numbers)
1. **Profile completeness** vs. a recruiter-ready bar: headline quality (does it carry the *searched*
   target title + 2–3 keyword domains?), About section (length, keyword coverage, has a hook?),
   Featured section (populated?), skills ordering, custom URL, photo/banner presence.
2. **Keyword gap** — compare the profile's skills/headline/About terms against the target-role keyword
   set (derive it from `intake.md` targeting + `../reference/ats-and-keywords.md`). List present vs.
   missing-but-claimable vs. true-gap keywords.
3. **Network analysis** — connection count, top companies in network, top titles, connection growth
   over time, inbound/outbound invitation ratio, penetration at target companies (how many existing
   connections sit at the user's named targets — this seeds the referral map later).
4. **Activity & reach** — post count/cadence, recency, engagement signals if present. Flag if dormant.
5. **Recruiter-findability score (0–100)** — a transparent composite of headline title-match, endorsed
   skills, activity signal, and Featured/About completeness. Show the sub-scores, not just the total.
6. **Positioning coherence** — does the headline/About tell one clear story, or is it scattered /
   out-of-date / new-grad-ordered?

## The 10 next steps (the payload)
Produce **exactly 10** prioritized, concrete actions to grow LinkedIn presence and recruiter exposure,
ordered by *activation energy* (lowest-effort, highest-compound first). Each step: the action, why it
matters (tie to a finding above), estimated time, and a copy-pasteable starter where applicable
(e.g., a rewritten headline draft, 3 skills to add, a first-post hook). Calibrate to 2026 reality:
the searched title must be in the headline; endorsed skills drive recruiter filters; native short
video and specific-number posts outperform; an empty Featured section reads junior; consistency
between LinkedIn and the resume matters for semantic/AI matchers. Pull current best-practice framing
from `../reference/ats-and-keywords.md`. Mark any step that depends on a fact you should verify with
`VERIFY:`.

## Build the HTML
Start from `../templates/linkedin-analysis.template.html`. Fill the **`<script type="application/json"
id="spider-data">` block** with this user's real numbers — it is strict JSON (double-quoted keys, no
comments, no trailing commas), and the page renders from it via `JSON.parse`. **`steps` must hold
exactly 10 objects.** After writing, **validate the JSON parses** (extract the block and run it through
a JSON parser) — a syntax error there blanks the entire dashboard. Don't edit the render `<script>`.
Requirements:
- **Single self-contained file**, opens offline in any browser. Inline CSS. Charts via inline SVG or a
  single CDN charting lib (Chart.js) — if you use a CDN, also render a text fallback so it's readable
  offline.
- **Modern, premium look**: dark theme, clean type scale, generous spacing, a hero with the
  findability score as the centerpiece, stat cards, at least 3 visualizations (e.g., keyword
  coverage bar, network-by-company chart, completeness radar or gauge, activity timeline).
- **Accessible**: real text (not images of text), sufficient contrast, semantic headings.
- Sections in order: hero (score + one-line verdict) → profile completeness → keyword gap →
  network → activity → **the 10 next steps** (the visual focal point of the lower page) → a short
  "how this was computed" note.
- Numbers shown must be traceable to the export; mark estimates as estimates.

## Verify
- The HTML opens and renders (sanity-check the markup; no unclosed tags, no broken script).
- Exactly 10 next steps, each actionable and time-estimated.
- Every displayed metric traces to the export or is labeled an estimate.
- Apply the user's sanitization rule from `intake.md` (this file is for them, so internal numbers are
  OK here — but if they plan to screenshot/share it, flag what to redact).

## Checkpoint
Tell the user the file path, the headline findability score, and the single highest-leverage next
step. Offer to draft any of the 10 starters (headline rewrite, first post) in full.
