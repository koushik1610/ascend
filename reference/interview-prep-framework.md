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
4. Gap areas — the queue's honest handling lines, verbatim.
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
