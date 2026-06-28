# Phase 3 — Master Resume → `master-resume.md`

**Goal:** build the user's **master resume** — a superset document holding ALL their career content at
maximum detail, from which every per-job resume is later *selected* (never rewritten). This is the
single most important artifact in the system; get it right and tailoring becomes a filter operation.

**Read first:** `workspace/<name>/intake.md`, the user's resume + LinkedIn export,
`../templates/master-resume-template.md` (the structure to follow), `../reference/ats-and-keywords.md`,
`../reference/resume-writing-rules.md`, `../reference/number-and-honesty-policy.md`.

**Audit folded in (was Phase 2):** before building, do a quick ATS + 2026-trends pass on the user's
current resume (per `../reference/ats-and-keywords.md`) — format hazards, the 6-second-scan verdict,
the **keyword set** (Tier-1/Tier-2 → present / missing-but-claimable / true-gap), and the weakest
bullets. Capture it as a short **"Gaps & fixes" section at the top of `master-resume.md`** and use it
to drive the build (missing-but-claimable keywords get their substantiating bullet added here, at the
source). The keyword set you derive becomes the master's §4 reference — Phases 4 and 5 reuse it instead
of re-deriving. (Only produce a standalone `resume-audit.md` if the user explicitly asks — Phase 2.)

---

## What a master resume is
A private superset, never sent anywhere, with no length limit. Individual resumes are derived per job
by *selecting* bullets — never by writing new ones. If tailoring later needs a bullet that doesn't
exist here, that's a defect in THIS file to fix, not a license to invent.

## Build it to `../templates/master-resume-template.md`
Fill every section with this user's real content:

1. **Header** — name, contact, links, location, work authorization (only if the user stated it),
   certifications with status (mark expired/in-progress honestly).
2. **Positioning summaries** — 2–3 per-audience summaries (their main target lane + alternates), each
   in a 40-word and 80-word version, liftable verbatim. Lead with the user's strongest differentiator.
3. **Metrics bank** — ONE table of every number the user can claim: metric, exact value, public/
   sendable value (per their sanitization rule), source, tag. This is the only place numbers live;
   bullets reference it. For users with no sensitive employer data, public = exact for most rows.
4. **Skills inventory** — full taxonomy; every skill maps to ≥1 evidence bullet or project. Mark which
   are ATS keywords for the target roles (from `resume-audit.md` §4 + `../reference/ats-and-keywords.md`)
   and keep an honest gap list (keywords they CANNOT claim).
5. **Experience** — every role, reverse-chronological. For each achievement, write: (a) a standard
   bullet (≤2 lines, formula-shaped, public values), (b) an expanded bullet (3–4 lines, for depth),
   (c) tags for JD-matching (define a tag set fitting the user's field), (d) source reference, and
   (e) a STAR cross-ref if relevant. Merge near-duplicate bullets from the old resume into one entry
   with the strongest phrasing; keep alternates as variants beneath it. Give every entry a stable ID
   (e.g., `E1`, `E2` per role) so per-job resumes can cite it.
6. **Projects / portfolio** — each with a one-liner, a full paragraph, stack, metrics (from the bank),
   status, and a link if public.
7. **Education & credentials.**
8. **Story bank index** — map the user's STAR stories to the experience entries and tags they support
   (this seeds the Phase 6 interview packet).
9. **Tailoring protocol** — the standing instructions for deriving a per-job resume: paste JD → extract
   keywords → ATS gap-score against §4 → select bullets by tag → swap to public number values → run the
   6-second pass → run the honesty + writing checklist. (This is what Phase 5 follows.)
10. **Conflicts & coverage log** — any facts that disagreed across the resume vs. LinkedIn vs. intake
    (record both with sources; don't silently resolve), and a checklist confirming each source was used.

## Writing rules (binding)
- Every bullet follows `../reference/resume-writing-rules.md`: verb + named system/scope + measured
  outcome + (signal). Strong verbs, no slop ("spearheaded/leveraged/cutting-edge/passionate"), vary
  phrasing, specific nouns.
- Honesty gates per `../reference/number-and-honesty-policy.md`. Dual-value numbers (exact ↔ public)
  recorded as pairs where the user has sanitization needs; derived resumes use only the public value.
- Nothing enters the master that the user can't substantiate. Where the resume audit found a "missing
  but claimable" keyword, add the substantiating bullet here (this is where the keyword gap gets fixed
  at the source).

## Master public résumé PDF
After `master-resume.md` is built, also produce a **public, generic-default résumé PDF** from it (a
real résumé the user can use when no specific JD applies — not the private superset). Select the
primary-lane summary and the strongest standard bullets, swap every metric to its **public** value, and
exclude the private sections (metrics bank, story bank, conflicts log, INTERNAL pairs). Then run
**Phase 8** to emit `master.resume.json`, the filled builder `.html`, and the rendered PDF. The master
public résumé is the one exception to the one-page default: **up to 2 pages**, page 1 strongest.

## Verify
- Every metric/claim traces to the resume, the LinkedIn export, or an intake answer.
- Every experience entry has an ID, a standard bullet, and a public-value form.
- The honest-gap list exists and the positioning summaries lead with a real differentiator.
- The Conflicts log exists (even if empty).
- `master.resume.json` + the master public résumé PDF exist and carry **no** INTERNAL/sanitized values
  (number-policy grep clean).

## Checkpoint
Tell the user where the file is, how many experience entries/bullets it holds, confirm the positioning
summaries sound like them, and point them at the master public résumé PDF. This file is the source of
truth for Phases 4–6.
