# Screen card — <Company> · <Role>

<!--
  BUILT WHEN A SCREEN IS BOOKED. One page. Six minutes of reading. NOT a script — notes.

  WHY THIS EXISTS, AND WHY DEEP PREP MOVED: Phase 10 used to fire on "screen booked" and build a
  20-35 hour study plan for a loop the candidate has not yet earned. Most roles die at the screen.
  Now: screen booked → this card (45 min). Screen PASSED → `/ascend prep <NN>` for the deep pack.
  That reordering saves roughly twenty hours per role that ends at the screen.

  The recruiter screen is the widest point of the funnel and the place candidates are cut for reasons
  that have nothing to do with skill: rambling past two minutes, pricing themselves out, or having no
  specific answer to "why us."
-->

## 1. The 90-second open
<Selected from master §2 + the three strongest bullets for THIS role. Ninety seconds, not sixty —
sixty reads clipped when a recruiter opens with "walk me through your background." Land on a sentence
that connects to why this role: "…which is why this one caught my eye.">

## 2. Why you're leaving
<Three sentences. Forward-facing. No criticism of the current employer, however deserved. This gets
people cut and almost nobody prepares it.>

## 3. Comp — the deflect, the ask, and the number
- **Deflect once:** "I'd rather hear the band for the level first — what range is this budgeted at?"
- **Ask:** the band, and whether the level is fixed.
- **The number, if pushed a third time:** <the honest anchor from `intake.md`>. Say it.
  Deflecting three times reads as difficult, and the number gets extracted at the screen regardless.
  Record what was said in the STATE block as `comp_discussed` — the offer read diffs against it later.

## 4. Five questions to ask
**Ask these two in the first five minutes** — they decide whether the rest of the call is worth having:
1. Is this an IC or a manager role, and what level is it mapped to?
2. What's the band for that level?

The other three, any time:
3. What does the loop look like, and what's the timeline?
4. How long has the req been open, and how many candidates are in process?
5. What changed about this role, or who left?

Record the answer to #1 as `level_discussed`. The level case argues from it and the weekly review
aggregates it — "leveled down in 3 of 4 screens" is the most actionable pattern a search can surface.

## 5. The three disqualifiers for this req
<Lifted verbatim from the queue entry's "gaps & honest handling" and "why you'd lose this one".
Each with the rehearsed honest line, not a deflection.>

## 6. Logistics
Recruiter name + pronunciation · timezone · phone or video · dial-in · what you're sending after.

---
**After the call:** `python3 tools/pipeline.py log workspace/<name> <NN> screen --contact "<name>"`,
then record the outcome. Passed → `/ascend prep <NN>` builds the deep pack. Didn't → `/ascend rejected <NN>`.
