# Per-Job Folder Template — two tiers, built when they're needed

A job folder is built in **two tiers**, so you don't generate deep interview prep for 15 cold leads
that may never call back:

- **🟢 CORE — the "apply pack" (build now, for jobs you'll actually pursue):**
  `resume.md` · `outreach.md` · `application-log.md`. The minimum to send a strong, referral-first
  application. This is what Phase 5 builds.
- **🔵 PREP PACK — deep interview prep (build *on demand* when a screen is booked, via Phase 10 /
  `/spider prep <NN>`):** `prep-doc.md` · `interview-questions.md` · `interview-prep.md` ·
  `company-research.md` · `signal.md`. Don't build these speculatively.
- **⚪ OPTIONAL:** `cover-letter.md` (only when the posting requires one).

Build by *selection* from the master resume and *reference* to the interview packet — never copy shared
content wholesale, never invent facts. Replace every `<…>` placeholder with the real value.

**Naming:** `jobs/<NN>-<company-slug>-<role-slug>/` (e.g., `jobs/01-acme-staff-engineer/`). Two-digit
prefix = queue rank.

**Single-sourcing rule:** if a sentence already exists in `../../master-resume.md` or
`../../interview-packet/`, this folder holds only the *job-specific delta* + a reference
(`../../interview-packet/star-stories.md → S3`). Never duplicate story bodies, the metrics bank, or
shared prep.

---

## 1. `resume.md` — the tailored resume
- **Top: HTML-comment Delta Log** — queue entry #, JD link, date, ATS target + its constraints, which
  master-resume entry IDs were selected and in what order + why, verbatim JD phrases inserted (each
  used ONCE), the number-policy grep confirmation, export filename
  `<name>-resume-<company-role>.pdf`, and a **MASTER GAPS** note if any needed bullet didn't exist.
- **Body:** full liftable resume — header line, Summary (the matching master §2 summary), Experience
  (bullets selected per the queue delta), optional Selected Projects, Skills (JD-keyword-ordered),
  Certifications (honest status — no "Active" unless true), Education.
- **Format:** single column, standard section headings, bullets ≤2 lines, no tables in the body.
  Every bullet is a master entry (a)/(b)/variant — selection, not writing. Missing bullet → MASTER GAPS
  note, never an invention.
- **Export:** turn this into an ATS-safe PDF via the export prompt (`prompts/08-export-pdf.md`) →
  `<Name>-Resume-<Company>.pdf`. Don't leave Markdown→PDF to the user.

## 2. `prep-doc.md` — the night-before read (≤2 pages, 20-min readable)
1. **Line 1 = the positioning hook** for this company (from `company-positioning.md` / the queue's
   "why it ranks").
2. Role thesis — one paragraph: why the user wins this loop.
3. The 3–5 talking points (from the queue entry, expanded with master entry / metric references).
4. **Story map** — table: round/theme → story ID (S#/D#) → the job-specific *opening line*.
5. Gaps + **verbatim rehearsed handling lines** (from the queue "gaps & handling").
6. Closer script, verbatim.
7. **Numbers-discipline box** — the say-aloud values for this conversation (public/sanitized) and the
   exact verifiable numbers that stay exact; the user's never-say list.
8. Questions-to-ask shortlist: 5 from the packet + 2 written fresh for this company/team.
9. Footer: portfolio/links + any external-proof note.

## 3. `interview-questions.md` — the question bank
- **(a) Technical / domain / design (~12–18):** seed from the queue's expected questions; expand. Each
  with a bullet-skeleton answer (approach, key terms, which artifact proves it). Include ≥3 design /
  case prompts (senior loops are won here).
- **(b) Coding / assessment section — calibrated to this company's REAL loop:**
  - Algorithm-testing companies → 8–15 named LeetCode-style problems by pattern (arrays/hashing,
    intervals, graphs/BFS-DFS, heaps, strings/parsing, trees/tries) + any domain-flavored coding
    tasks. Note the language and round format.
  - Companies/roles that don't do LC → state the real assessment (take-home, system design only,
    work-sample, portfolio review, case study) and prep it concretely.
  - **Never invent a coding round that isn't there.** Be honest about the loop.
- **(c) Behavioral (≥6):** table mapping question → the user's STAR story ID → this company's value
  system / culture (map to the company's published values, leadership principles, or culture norms;
  flag any personal-conviction "why" answer as DO-NOT-GENERATE — the user writes it).
- **(d) Curveballs / values screens** specific to the company.

## 4. `interview-prep.md` — the study plan
1. Loop structure (rounds, interviewer types; "fill in after recruiter screen").
2. **Study-areas table:** topic | priority P0–P2 | est. hours (20–35h total), gap-ranked, including the
   3–5 domain deep-dive topics this specific role demands.
3. Set-piece designs/cases to rehearse (pick the user's strongest + 1–2 job-specific).
4. Gap areas — the queue's "gaps & handling" verbatim + the honest-line script.
5. Week-by-week plan (2–3 weeks).
6. Day-before checklist (stat lines, number discipline, closer, culture-doc re-read, logistics).

## 5. `outreach.md` — referrals + recruiter screen
- **Referral targets:** seeded from the LinkedIn network analysis — real existing connections at this
  company. **NEVER fabricate names or relationships.** If none exist, say so and suggest a cold-but-
  warm path (2nd-degree, alumni, community).
- **DM drafts:** 2 (warm reconnect; cold-but-shared-context), ≤90 words, one concrete sanitized hook,
  one specific ask, each headed `DRAFT — REWRITE IN YOUR VOICE BEFORE SENDING`.
- **Recruiter-screen script:** 60-second positioning open, comp/level anchor ("I'm targeting <level>-
  scope roles — what's the band?" — never give current comp first), any location-friction question to
  resolve first, the per-company closer.
- **Conviction-essay outlines** (if the application has a "why this company/mission" essay): bullet the
  honest beats only, headed `DRAFT-FOR-YOUR-OWN-REWRITE — write personally, never paste generated prose`.

## 6. `company-research.md`
- Team intel (state what's unverified; mark `VERIFY:` items to confirm with live search before the loop
  — never invent news, posts, or interviewer names while offline).
- Interviewer-notes table (fill after scheduling).
- Comp data: the queue's band + negotiation anchors + walk-away guidance.
- Org / level context.

## 7. `signal.md` — the sendable one-pager for THIS job
- A re-lead of the master positioning summary (`../../master-resume.md` §2) with the evidence pillars
  **reordered** so this role's lead evidence comes first. A re-lead, never a new persona.
- Structure: header comment (what it is, send rules) → `> ──── SENDABLE ────` markers around the page →
  name + role-anchored positioning line + contact → narrative paragraph re-led for this role → 3–4
  evidence paragraphs (pillars reordered) → one-line "Why <company>" (the queue closer) → background
  line.
- **Public/sanitized values ONLY** (it leaves the machine by design). No certs unless truly active.
  Send as PDF or pasted text, never `.md`.

## 8. `application-log.md` — the only stateful doc  🟢 CORE
- **Pre-submit checklist with a REFERRAL-FIRST HARD GATE** — do not mark "applied" until:
  - [ ] **Referral attempted _or_ explicitly waived** (a real connection at the company was asked, or
        the user consciously decided to apply cold). Referrals are the #1 interview-rate lever — this is
        a gate, not a suggestion.
  - [ ] Link re-verified live · LinkedIn/profile consistent with the resume.
  - [ ] Resume PDF exported + named + number-policy grep run.
  - [ ] Any pre-application blocker cleared.
- **Key dates** (the ghost-detector reads these): `status` · `applied_on` · `last_contact_on` ·
  `next_followup_due` · `next_action`. Keep them current so the daily briefing (Phase 13) can flag
  quiet threads and the navigator can show deadlines.
- **Status table:** date | action | contact | outcome.
- **Thank-you-note tracker.**
- **Post-loop retro** (fill after each round): questions asked vs predicted | what landed | what
  flopped | story drift | update `interview-questions.md` predictions.

## 9. `cover-letter.md` — OPTIONAL (only if the posting requires/expects a cover letter)
- Build only when the application asks for one (many don't). A focused ≤250-word letter: the hook
  (why this role/company, tied to a real reason), 2–3 sentences of the single most relevant proof
  (selected from the master resume — no new claims), and a confident close.
- **Personal "why this company" sentences are the user's to write** — provide the structure and the
  evidence beats, mark the voice-dependent lines `DRAFT — REWRITE IN YOUR VOICE`, never ship generated
  conviction as final.
- Public/sanitized numbers only (it's sendable). Honesty gates apply.

---

## Hard rules (all files in the folder)
1. **Numbers:** public/sanitized values in anything sendable/pasteable (resume, signal, outreach,
   prep talking points); the user's own verifiable numbers stay exact. Apply the user's `intake.md`
   sanitization rule. Run the user's number-policy grep over the folder before declaring it done.
2. **Honesty gates:** no fabricated experience, metrics, titles, certs, or referral contacts; no
   skills the user can't claim; no "Active" cert that isn't; no finished personal-conviction essays
   (outlines only). Apply `../../../reference/number-and-honesty-policy.md` (adjust the relative path to
   your repo location).
3. **Selection, not writing:** every resume bullet traces to a master entry ID, cited in the Delta Log.
4. **Tone:** specific nouns, strong verbs, no slop ("spearheaded/leveraged/cutting-edge/passionate").
   Files scannable; prep-doc ≤2 pages.
