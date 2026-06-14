# Maintenance Loop → keep the search alive

**Goal:** a job search is a campaign, not a one-shot. This phase keeps the pipeline fresh and turns the
per-job logs into action and learning. Run it weekly, or on request ("Run SPIDER maintenance").

**Read first:** `workspace/<name>/intake.md`, `.spider-state.json`, `job-queue.md`, every
`jobs/*/application-log.md`, `master-resume.md`.

---

## 1. Weekly job refresh + diff
Re-run the Phase 4 search (same targets/constraints from `intake.md`). Then **diff against the existing
queue**:
- **New** roles not seen before → add them (with link-status), ranked into the queue; offer to build
  folders for the strongest.
- **Gone** roles (now dead links) → mark `closed` in the queue and the navigator, don't delete the
  folder (keep the prep/retro).
- **Unchanged** → leave as-is, preserving each `application-log.md` status.
Report: "3 new, 1 closed since last week." **Never clobber application status** on a refresh.

## 2. Outreach & referral cadence
Scan each `jobs/*/outreach.md` + `application-log.md` and surface the network actions due:
- Referral asks sent with **no reply after ~5 business days** → suggest a follow-up.
- Target companies with **no referral attempted yet** → flag (referral-first beats cold apply).
- A weekly outreach target (e.g., "2 new conversations, 1 follow-up"). Keep it concrete and small.

## 3. Application follow-ups & deadlines
From the `application-log.md` files, compute what's due and feed the navigator's **Deadlines &
Follow-ups** strip (set `deadline` / `nextAction` in the `start-here.html` JSON):
- Applications past **~7 days with no response** → suggest a polite nudge.
- Upcoming interview dates, take-home due dates, "send thank-you" items post-loop.

## 4. Comp / market research (on request or when an offer/loop nears)
For a given role/level/geo, pull current market salary bands (levels.fyi-style ranges, Glassdoor,
posted ranges in similar reqs) and write a short comp note into that job's `company-research.md`:
the band, the anchor ("targeting <level>-scope — what's the range?"), and a walk-away floor from
`intake.md`. **Cite sources; mark estimates.** Never invent numbers.

## 5. Retro / learning digest
Aggregate the **post-loop retros** across all `application-log.md` files and surface patterns the user
can't see one-loop-at-a-time:
- Where they're dropping (e.g., "3 rejections at recruiter screen" vs. "2 at onsite design round").
- Recurring questions that landed/flopped → push the fixes back into `interview-packet/` and the
  affected `interview-questions.md` predictions.
- Resume/positioning signals (e.g., "every screen asks about management scope" → strengthen that
  master-resume bullet). **Fix the master, then re-derive** — never patch one folder in isolation.
Write the digest to `workspace/<name>/retro-digest.md` and link it from the navigator.

## 6. Refresh the navigator
Re-run Phase 7 so `start-here.html` reflects the new queue, statuses, deadlines, and the funnel.

## Verify & checkpoint
- No application status was lost in the refresh.
- New job links carry honest link-status; no fabricated postings.
- Comp numbers cite sources; retro fixes were pushed to the master/packet, not just one folder.
Report the week's deltas (new/closed jobs, due follow-ups, funnel movement, top retro insight) and the
2–3 highest-leverage actions for the coming week.
