# Feature update 4

**Date:** 2026-11-07 · **Ascend at:** `main` (c15dc00)

Three short guides on job-search tooling were reviewed, one at a time, against what Ascend already
does. Each guide got its own lite council (software engineer, AI security, pragmatist) with a
priority verdict. Most of what the guides describe, Ascend already has. The useful part was a short
list of mechanisms, not features.

Sources are deliberately not named. This file records what Ascend took and why.

---

## Guide 1: a tailored résumé and cover letter for every job

**What it describes:** one career profile is the only source for every document. Each posting is
matched requirement by requirement. Anything the profile can't back is shown as a gap. The model
never decides whether a requirement is covered: it only names which profile skill a requirement is
about, and code decides covered, partial or gap. A skill listed in the profile but tied to no role is
**partial**. Seniority is judged in both directions: a role far below the candidate's level is as
much a mismatch as one far above. It also writes a cover letter that says what the résumé can't.

**Already in Ascend:** one source (the locked master), selection not invention, a gap line
(`True gaps:`), keyword coverage checked by the linter, a years-vs-dates check, never auto-sending.

### Council verdict

```
COUNCIL VERDICT: Guide 1 (per-job tailoring)
Mode: lite · Personas: software-engineer, ai-security, pragmatist · Voting: off

P0
1. Skills-only keywords pass the coverage gate. lint `coverage` accepts a must-have keyword
   found anywhere on the page, so one that sits only in the Skills line passes. That is fine
   for a Boolean search and bad in the screen, where "tell me about your Kubernetes work" has
   no bullet behind it. Add an `evidence` check: a must-have keyword that no experience or
   project bullet uses is reported, unless the Delta Log lists it on a `Skills-only:` line,
   which records that the user chose it.  [software-engineer]

P1
1. Seniority is one-sided. Phase 4 calls a down-level "note it", so a role two levels below
   the user can still score 80+ and rank first. Make the seniority sub-score symmetric and
   cap the total below 70 when the gap is two or more levels in either direction.  [pragmatist]
2. No cover letter outside academic CVs. Greenhouse and Ashby forms often take one. Add an
   on-demand cover-letter prompt and skill. The letter must not repeat the résumé. It names
   the problem the posting is hiring for, then gives one or two proof stories by master or
   story ID. "Why this company" stays the user's own words (outline beats only, as for every
   conviction essay).  [pragmatist]
3. The posting reaches the letter's context. Wire it through the quarantine like Phase 5,
   and pass the letter through lint_artifacts before "done".  [ai-security]

P2
1. Per-application facts ("this one is remote, I'm relocating"). Intake already covers most
   of it. Deferred.

Rejected
- A creativity dial (faithful / balanced / expressive). It conflicts with the master lock:
  a locked bullet is never reworded.
- Chat refine, version history, tone presets. These are UI features for an app. Ascend's
  equivalent is the master plus the Delta Log.

Dissenting view (pragmatist): the skills-only check will fire on every honest résumé at first
and get waved through. Accepted risk: the `Skills-only:` line makes the wave-through a recorded
choice, and the deep-prep pack can read it to find the questions with no story behind them.
```

---

## Guide 2: three one-word prompts that tailor a résumé

**What it describes:** paste a résumé and a posting, add one word, and the model rewrites the
résumé, flags weak bullets, or lists missing keywords.

**Already in Ascend:** all three. Tailoring is Phase 5 (selection from the master, not a rewrite),
weak bullets are Phase 2 and the de-genericizer (Phase 18), missing keywords are the `coverage`
gate plus the `score` op.

### Council verdict

```
COUNCIL VERDICT: Guide 2 (one-word prompts)
Mode: lite · Personas: software-engineer, ai-security, pragmatist · Voting: off

P0  none
P1  none
P2  none

Rejected
- A one-word "rewrite" mode. A free rewrite of a pasted résumé is the exact path Ascend's
  honesty gates close: no master, no provenance, no Delta Log.  [ai-security]
- Aliases for the existing ops. `/ascend score`, `audit` and `degenericize` already do these
  jobs, and the skill layer already triggers on plain phrases.  [pragmatist]

Dissenting view (software-engineer): the low-friction entry point is real. Someone with no
workspace gets nothing from Ascend today. Recorded, not acted on: skills refuse to run without
intake, on purpose.
```

---

## Guide 3: an interview coach that scores every answer

**What it describes:** mock interviews scored on five dimensions (substance, structure, relevance,
credibility, differentiation) with an anchored description of each level. A state file keeps score
history, so practice weeks apart is comparable. Real interviews get a debrief: questions recalled,
stories used, what the interviewer reacted to. Stories are allocated across a loop so the same one
doesn't lead in two rounds. It also anticipates the interviewer's concerns about this candidate.

**Already in Ascend:** a live drill (Phase 17) with a four-dimension 1-5 score, a STAR story bank
with IDs, deep-prep with gap handling lines, salary scripts (Phase 19), JD analysis.

### Council verdict

```
COUNCIL VERDICT: Guide 3 (interview coach)
Mode: lite · Personas: software-engineer, ai-security, pragmatist · Voting: off

P0
1. Scores are not comparable. Phase 17's 1-5 has no anchors, so a 3 today and a 3 next
   week can mean different things, and "brevity & signal" overlaps "structure". Replace it
   with five anchored dimensions (substance, structure, relevance, credibility,
   differentiation) in reference/interview-prep-framework.md, the one home for the rubric.
   Credibility is capped at 2 when the answer claims something no master or story ID backs.
   A fabricated detail is a stop, not a low score.  [software-engineer]
2. Nothing persists between drills. Phase 17 summarises a set and forgets it. Add an
   append-only drill ledger (tools/drills.py, workspace-confined like every tool): one row
   per answer with question, story ID, five scores and source (mock or real). `summary`
   reports the per-dimension trend (first five vs last five answers) and story use, so
   over-used and never-used stories are counted, not guessed.  [software-engineer]

P1
1. Real interviews teach nothing back. Add a debrief op: within a day, capture the
   questions asked, the story used for each, the interviewer's reactions and the surprises.
   Questions go into the job's interview-questions.md, scores into the ledger as `real`.
   A pasted transcript or a recruiter's feedback email is untrusted data.  [ai-security]
2. Story collisions across a loop. Deep-prep maps questions to stories but not rounds to
   stories, so the strongest story gets told three times in one onsite. Add a per-round
   allocation: no story leads in two rounds of the same loop.  [pragmatist]
3. Concerns are answered piecemeal. Deep-prep has gap handling lines. Rank them as
   dealbreaker / significant / minor, so prep time goes to the dealbreakers first.
   [pragmatist]

Rejected
- A "directness level" for harsher feedback. Tone setting, not a mechanism.  [pragmatist]
- Score-to-outcome calibration. It needs three or more real outcomes to say anything.
  The ledger's `source` field keeps the door open.  [pragmatist]
- A second salary or JD-decode module. Phases 19 and 4 already cover both.

Dissenting view (ai-security): the debrief is the first op that routinely takes a pasted
interviewer email or transcript. Treat it like a posting: quote, never obey, and never let it
add a master entry. Accepted: written into the prompt and the skill.
```

---

## What this update ships

| # | Change | Where |
|---|---|---|
| 1 | `evidence` lint check plus the `Skills-only:` Delta Log line | `tools/lint_artifacts.py`, `templates/job-folder/_TEMPLATE.md` |
| 2 | Symmetric seniority, total capped below 70 on a two-level gap | `prompts/04-job-search.md`, `prompts/27-score-queue.md` |
| 3 | Cover letter op | `prompts/30-cover-letter.md`, `.claude/skills/ascend-cover-letter/` |
| 4 | Five anchored interview dimensions | `reference/interview-prep-framework.md` §6, `prompts/17-interview-me.md` |
| 5 | Drill ledger | `tools/drills.py`, `.claude/settings.json`, tests |
| 6 | Debrief op | `prompts/31-interview-debrief.md`, `.claude/skills/ascend-interview-debrief/` |
| 7 | Per-round story allocation and ranked concerns | `prompts/10-deep-prep.md`, `reference/interview-prep-framework.md` §3 |
