# Interview Prep Framework

How the system builds `interview-questions.md` and `interview-prep.md` for any role. Universal
structure; field-aware specifics.

## 1. STAR behavioral stories
Every senior loop probes behavior. Build the user 6–10 stories (in `interview-packet/star-stories.md`),
each in **Situation → Task → Action → Result → Proves**, each with a stable ID (`S1`…). Cover:
ambiguity / zero prior art · influence without authority · leverage/scale · conviction under pushback ·
coaching/multiplying others · conflict/disagreement · operational excellence · a genuine failure +
what you learned. Per job, map each likely behavioral question to a story ID and to that company's
value system (its published values, leadership principles, or culture norms). Stories are **real
events only**; the failure story must be a true one (interviewers dig).

## 2. Coding / assessment calibration (be honest about the real loop)
Encode what the company *actually* does — never invent a round.

- **Algorithm-heavy loops** (big-tech SWE/SRE/security/data, many infra roles): give 8–15 named
  LeetCode-style problems by pattern, plus the language and round count.
  - Arrays / hashing — frequency maps, two-sum family, sliding window, LRU cache.
  - Intervals — merge/insert intervals (maps to ranges, scheduling).
  - Graphs / BFS-DFS — islands, course schedule (topo sort), clone graph, shortest path.
  - Heaps / two-pointers — top-K, K-closest, meeting rooms.
  - Strings / parsing — valid parentheses, decode string, calculator, tries for prefix matching.
  - Trees — traversal, BST validation, LCA.
  - Add **domain-flavored** tasks where the role has them (e.g., parse a log file, evaluate a policy,
    transform a dataset).
- **System / domain design rounds** (staff+, most senior roles): rehearse 2–3 set-piece designs the
  user can *draw* — pick their strongest real architectures/projects + 1–2 likely job-specific prompts.
- **Take-home / work-sample loops** (many startups, many non-SWE roles): prep the actual deliverable —
  scope it, time-box it, list what "great" looks like.
- **Non-engineering roles:** replace coding with the real assessment — design portfolio review +
  whiteboard/critique (design), case/product-sense + metrics (PM), campaign/portfolio + analytics
  (marketing), work-sample + scenario (ops/sales/support). Prep each concretely.
- **Rule:** if you're unsure whether a company does LC, say so and mark `VERIFY:` — don't assert a
  round that may not exist.

## 3. `interview-prep.md` structure (per job)
1. Loop structure (rounds + interviewer types; "fill after recruiter screen").
2. Study-areas table: topic | priority P0–P2 | est. hours (20–35h total), gap-ranked, including the
   3–5 deep-dive topics this role demands.
3. Set-pieces to rehearse drawing/doing.
4. Gap areas: the queue's honest handling lines, verbatim, **ranked by how likely each is to end
   the loop**: *dealbreaker* (a stated must-have the evidence doesn't cover, a level or location
   mismatch), *significant* (a preferred skill missing, a short tenure the interviewer will ask
   about), *minor* (everything else). Prep time goes to dealbreakers first. Every keyword on the
   résumé's `Skills-only:` line is at least *significant*: it is a question with no story behind it.
4b. Story allocation across the loop. For each round, the 2–3 questions it most likely asks and the
   story ID that answers each. **No story leads in two rounds of the same loop**; interviewers
   compare notes, and the same story three times reads as a candidate with one story. A story may
   back up a second answer briefly. Use `python3 tools/drills.py summary` to see which stories are
   over-used in practice and which have never been told aloud.
5. Week-by-week plan (2–3 weeks: gaps → set-pieces + coding → behavioral + mocks).
6. Day-before checklist: stat lines, number discipline, the closer, culture-doc re-read, logistics.

## 4. Number discipline in interviews
Rehearse the say-aloud values from `interview-packet/metrics-cheatsheet.md`: own/verifiable numbers
exact (scoped to context), employer-internal numbers rounded, the never-say list off-limits. Discretion
about internals reads senior (see `number-and-honesty-policy.md`).

## 5. The recruiter screen
Open with the 60-second positioning. Anchor comp to the target level, never give current comp first
("I'm targeting <level>-scope roles — what's the band for this level?"). Resolve any location/logistics
friction *first*, before investing in a full loop.

## 6. The answer rubric (mock drills and real-interview debriefs)
One rubric, five dimensions, each scored 1–5 against the anchors below, so a 3 this week means what
a 3 meant last week. `prompts/17-interview-me.md` scores with it, `prompts/31-interview-debrief.md`
self-scores real answers with it, and `tools/drills.py` records every score.

| Dimension | 1 | 3 | 5 |
|---|---|---|---|
| **Substance** (the evidence) | A claim with nothing behind it | Specific action and outcome, no number or scope | Number or scope, what else was considered, why this choice won, and what happened |
| **Structure** (can they follow it) | No discernible point | A clear arc, the result arrives late or gets lost | The headline first, then the arc, every sentence moving it forward |
| **Relevance** (did it answer this question) | Answers a different question | The right story, a third of it background | Nothing could be cut without losing the answer |
| **Credibility** (do they believe it) | Inflated, or "we" with no "I" | Concrete but unverifiable, the user's own part unclear | The user's own decisions named, constraints and trade-offs admitted, someone else's reaction or adoption cited |
| **Differentiation** (only this person could say it) | Any prepared candidate could say it | Real detail, presented as plain execution | A lesson learned the hard way, or a defensible position the user holds because of this work |

2 and 4 sit between their neighbours. Rules that override the score:
- **Credibility is capped at 2** when the answer claims something no master entry (`E#`), story
  (`S#`) or deep dive (`D#`) backs. The fix is a better real story or an honest gap line.
- **A fabricated detail is a stop, not a low score.** Say so plainly and move on to the fix.
- **Differentiation never comes from invention.** Ask "what do you know from this that most people in
  your role don't?" and take the user's own answer. If there isn't one yet, the score is 3, which is
  a fine answer.
- Feedback is the single highest-leverage fix plus a tightened opening line built from the user's own
  story. Not a list of everything that could be better.

