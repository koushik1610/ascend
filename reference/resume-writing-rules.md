# Resume & Achievement Writing Rules (binding)

Apply these to every bullet, summary line, signal paragraph, and LinkedIn line the system writes —
for any field. They encode what survives both AI/ATS screening and a skeptical human in 2026.

## The bullet formula
`Strong verb + what you did + named tool/method/scope + measured outcome (+ leadership/impact signal)`

- ✅ "Rebuilt the onboarding flow in React, cutting first-week drop-off from 38% to 19% across 40k
  monthly signups."
- ❌ "Responsible for improving the onboarding experience."

Every bullet should answer: *what did you do, how big was it, and what changed because of it?*

## The rules, in order
1. **Outcome first, method second.** The result is the point; the tool is how. Don't lead with the
   tech/tool unless the tool *is* the differentiator the role screens for.
2. **One signal per flagship bullet.** Senior/lead resumes need evidence of scope, ownership,
   influence without authority, or a standard others adopted — one such signal per top bullet.
3. **Scale is the hook.** Lead bullets carry the ratio/scope (users, dollars, accounts, team size,
   geography) that frames the achievement.
4. **Quantify everything you honestly can.** A bullet without a number is weaker. If you don't have
   the number, state *what you'd measure* — never fabricate one. (See `number-and-honesty-policy.md`.)
5. **Specific nouns beat adjectives.** "Migrated 1,200 endpoints" not "significantly modernized the
   platform." AI screeners and humans both read specificity as credibility; vague = padding.
6. **Vary the verbs and rhythm.** Uniform bullet shapes and repeated verbs read as templated/AI-
   generated. Mix sentence lengths; don't start five bullets the same way.
7. **Keyword coverage in context, not stuffing.** Embed 15–25 role-relevant keywords *inside
   achievement bullets* (contextualized keywords rank far higher than a skills-list-only mention).
   Stuffing is detectable and penalized.
8. **Mirror the JD's vocabulary once each.** Use the posting's own terms for the same concept once per
   relevant bullet — fluency, not parroting. Never twice.
9. **No slop.** Ban "spearheaded, leveraged, cutting-edge, passionate, synergy, results-driven, team
   player, go-getter." Read each bullet aloud: if it could appear on anyone's resume, rewrite it.
10. **No personal pronouns, no full sentences-as-paragraphs.** Bullet points, active voice, present
    tense for current role / past tense for prior.

## Bullet writing — anti-AI-tell + ATS (binding)
Two goals that pull apart: ATS wants literal keyword matches; a human recruiter rejects text that reads
AI-generated. Follow the punctuation/vocabulary bans strictly (zero ATS cost) and integrate keywords
deliberately (where the real optimization is). Check every bullet against `../.claude/banned-words.md`.

**1. Punctuation (hard bans).**
- **No em dashes (—) or en dashes as sentence breaks** — the single most-cited AI tell. Use a period,
  comma, or plain colon.
- **No semicolons joining two independent clauses** in a bullet. A bullet is one clean statement, not two
  stitched together.
- **No dramatic-reveal colon** ("The result: a 40% lift"). State it plainly. (A colon introducing a list
  is fine.)
- Never open a bullet with **"Successfully," "Effectively," or "Proactively."**

**2. Banned vocabulary.** The full list lives in `../.claude/banned-words.md` (verbs like *leverage,
utilize, streamline, spearhead, drive, optimize, orchestrate, pioneer*; adjectives like *robust,
seamless, innovative, comprehensive, results-driven, proven, impactful*; nouns like *synergy, landscape,
ecosystem, journey, testament*; clichés like *proven track record, team player, extensive experience
in*). Any tense/plural/`-ing` form counts. **Cut vague verbs/adjectives; keep specific-noun ATS keywords.**

**3. Rhythm.** Vary bullet length within a section (mix short and long — uniform 15–20-word bullets read
AI). Don't repeat the "X, resulting in Y" template more than twice per résumé, and don't stack the same
`[Verb]+[Task]+[Metric]` skeleton back to back. Some structural unevenness reads human.

**4. Specificity over polish.** Never leave a vague capability claim ("improved cloud security posture").
Name the mechanism: the actual service (EKS, GuardDuty, a Terraform module), the config, the number.
"Built a detection rule that flagged X" beats "built a robust detection capability." If no metric exists,
state the concrete deliverable, don't inflate with an adjective. No internal contradictions with the summary.

**5. ATS keyword integration.** Pull **exact-match** keywords from the JD (tool/framework/cert names, job-
title variants) and use each **verbatim at least once** in a bullet where it's true. Give both the acronym
and full term once ("Cloud Security Posture Management (CSPM)"). Put the highest-priority JD keywords in
the **top third**. Don't stuff a single bullet with unrelated tools (a red flag to ATS *and* humans);
spread them where actually used. Match the JD's exact term where accurate ("incident response," not only
"incident handling"). The **Skills** section may be a plain comma/pipe list of exact-match nouns.

**6. Self-check before finalizing each bullet.** Banned word? → rewrite. Em dash? → period/comma. Could
it describe *any* candidate with no tool/number/company swapped in? → add the specific detail. Uses a JD
keyword verbatim where accurate? → if not and one applies, work it in. Read it aloud: does it sound like a
person describing their work, or a press release? → plainer if the latter.

## Structure & format (ATS-safe)
- Reverse-chronological. Sections: Header → Summary → Experience → Skills → Education → (optional)
  Projects/Certs. Standard section *names* (ATS matches on them). **This is the standard variant's
  section set — an academic CV uses a different one; see Résumé variants below.**
  **Relevance ordering applies to bullets WITHIN a role, never across roles.** A current role listed
  below an older one reads as concealment and is one of the fastest rejects in a résumé screen. This
  is now gated mechanically: `tools/lint_artifacts.py` fails a `resume.json` whose `work[]` entries
  are out of order, along with a years-of-experience claim that contradicts the dates on the same
  page (the `scan` category).
- Length: 1 page under ~10 years, 2 pages for 10+. Never exceed 2 **on the standard variant**. The
  executive, academic-CV and non-US variants below are the named exceptions, and they are the only
  ones.
- Single column. No tables, text boxes, columns, headers/footers, icons, or graphics (parsers drop
  them). PDF unless the portal demands .docx.
- File name: `<Name>-Resume[-<Company>].pdf` (recruiters search download folders).

## Typography & layout (hiring-manager best practices — ALWAYS follow)
These are encoded as the default CSS in `../templates/resume-builder.template.html`; keep any edit within
these ranges, and never render below the **compliant minimums**.
- **Font:** a classic, professional, ATS-safe font ONLY — **Calibri / Arial / Helvetica / Times New
  Roman**. No stylized/display fonts (they misrender across systems and can break parsers). Use **one
  family** for body and name (builder default: Calibri, with Helvetica/Arial fallback).
- **Body size:** **10–12pt** (default 10.5pt; **10pt is the hard floor** — never smaller to force a fit).
- **Section headings:** **12–14pt** (default 12pt); the name is larger still. Job titles are bold, one
  consistent size.
- **Margins:** **0.5in–1in** on all sides (default 0.5in; **never below 0.5in**).
- **Line spacing:** **1.15–1.5** (default 1.25; **never below 1.15**).
- **Consistency:** identical font + size for every element of the same kind (all job titles alike, all
  bullets alike); use **bold/italics sparingly** to highlight, not decorate.
- **To fit one page:** cut/trim *content* to the budget below and tighten only to the compliant minimums
  (10pt / 1.15 / 0.5in). If it still overflows, drop the lowest-relevance bullet or go to 2 pages —
  **do not** drop below the font/margin/spacing floors.

## One-page content budget (the builder standard)
**This budget is the standard variant's** (see Résumé variants below for the four cases where it
does not apply). Per-job resumes default to **exactly one page**. The page is not made to fit by shrinking type (10pt is
the ATS floor); the *content* is generated to fit the fixed layout. The layout is the locked CSS in
`../templates/resume-builder.template.html` (US-Letter, 0.5in margins, Calibri body ~10.5pt, 12pt
section headings — see **Typography & layout** above). These
budgets were calibrated against that template (a résumé at the ceiling renders to one page; aim a notch
under it for white space):

- **Summary:** ≤ 3 lines (~40–50 words).
- **Experience:** 2–4 roles; **≤ 12 bullets total** across all roles (13 is the hard ceiling).
- **Bullet:** ≤ 2 printed lines each (~140 characters / ~22 words).
- **Projects:** 0–2 entries, ≤ 1–2 lines each (omit on a dense resume to protect the one page).
- **Education:** 1–2 entries, one line each.
- **Skills:** ≤ ~16 items.

When selecting bullets for a per-job resume, cut to this budget by relevance to the JD (lead with the
audience-default set), not by truncating mid-thought. If everything genuinely earns its place and still
overflows, drop the lowest-relevance role's weakest bullets or a Project before touching font size. The
builder shows a live overflow warning as the backstop; the budget above is the real control.

The **master public resume** (rendered from `master-resume.md` for a generic default) is exempt from
the one-page default — up to 2 pages, page 1 carrying the strongest material.

## Summaries
- 2–3 sentences: role + scope/years → 1–2 biggest quantified wins → the differentiator. No "seeking
  opportunities" (that's an objective, not a summary). Include the target-role keywords.

## Field adaptation
The formula is universal; the *evidence type* changes by field — engineers quantify systems/scale,
designers quantify funnel/adoption/usability lift, PMs quantify launches/revenue/retention, marketers
quantify reach/conversion/pipeline, ops quantify cost/throughput/SLA. Keep the verb-scope-outcome
shape; swap in the metrics that field actually rewards.

## Résumé variants (when the default shape above is wrong)
Everything above describes the **standard variant**: one page, reverse-chronological, ATS-first. It is
the right default for the large majority of applications and it is what the renderer enforces. Four
situations need a different shape, and applying the default to them is itself a defect.

**Pick the variant once, at intake, and record it.** The variant is a property of the *target*, not of
the artifact: a user applying to both a staff engineering role and a research post needs two. The
mechanics, so the decision is not made and then lost:
- `../prompts/00-orchestrator.md` STEP 1 asks for it under **Targeting**.
- `../prompts/03-master-resume.md` writes a `Résumé variant:` line into `master-resume.md` §1, per
  `../templates/master-resume-template.md`.
- `../prompts/05-job-folders.md` and `../prompts/08-export-pdf.md` **read that line** before selecting
  or rendering, and pass the variant's page count to the renderer.

Default to **Standard** when the line is absent, and say so in the Delta Log rather than guessing from
the user's seniority. Never switch variants silently mid-run.

| Variant | Use when | What changes from the default |
|---|---|---|
| **Standard** | almost always | nothing — the rules above are it |
| **Executive** | director and above, or P&L / org ownership | 2 pages is normal. Lead with scope (org size, budget, revenue owned) before activity. A short **Leadership Profile** replaces the summary. **Each role carries the company's size and stage at entry and at exit** — "VP Engineering, 2019-2023" tells a search consultant nothing; "(joined at 35 engineers / Series B; left at 140 / Series D)" is the screen, passed. Bullets move up a level: what the org did under you, not what you personally built. Board/advisory and P&L lines earn space. **Assume a human search consultant reads this and no ATS does** — above director, roles are filled through retained search and the hiring executive's network, so scale-and-stage match is the binding constraint and keyword coverage nearly isn't. A separate one-page third-person **executive bio** is a normal request at this level; produce it alongside. |
| **Academic CV** | faculty, postdoc, research scientist, grants | **length is uncapped and the one-page budget does not apply.** Sections: Education, Appointments, Publications, Grants, Teaching, Service, Talks. Publications in the field's citation style, exhaustive and reverse-chronological, the user's name and **authorship position** visible. **The CV is not the primary screen — the cover letter is**, with the research and teaching statements behind it; the committee uses the CV to verify the letter's claims, so build the letter first. Industry impact metrics are not the currency, but **the field's own are** and some are scored directly: authorship position, venue tier, recency, and funding **as PI versus co-I**. Split by search type — research-intensive leads with publications and funding; teaching-focused (SLAC, community college, teaching-track) leads with the teaching statement and documented teaching effectiveness; a postdoc application is the cover letter plus the first-author list and little else. No summary. |
| **Portfolio-led** | design, creative, content, front-end where work is seen | the résumé stays standard and ATS-safe; **the portfolio URL moves into the header** and the strongest 2-3 pieces get a one-line Selected Work block with outcomes. The visual artifact lives in the portfolio, never in the parsed document. See `../prompts/24-work-sample.md`. |
| **Non-US market** | applying outside the US | **2 pages is standard** in the UK and most of the EU, not an exception. Check the target market's own conventions on photo, date of birth and nationality before applying the defaults in this file — a photo is conventional in DACH and disqualifying-odd in the US. The one-page ATS-first rule above is a **US large-company convention, not a universal one**, and a non-US candidate who follows it ships a résumé that reads as thin. |

Rules that hold across every variant, no exceptions: single column and no tables in anything a parser
will read, every claim traceable to a master entry, no decorative graphics in the submitted file. A
"creative" résumé that a parser cannot read is not a creative choice, it is an unreceived application —
if a visually designed version is wanted, it is a *second* file sent alongside the parseable one, and
that is the only arrangement to recommend.

The executive and academic variants exceed the one-page budget **deliberately**. Pass the variant's
real page count to the renderer (`python3 tools/render_resume.py … --max-pages 2`) rather than letting
a two-page executive résumé fail the page budget as if it were an overflow bug. An academic CV is not
rendered by this tool at all — its layout is the field's, not Ascend's.

## Career-change translation (binding method, not a licence to re-label)
A pivot fails on résumé for one reason: the evidence is stated in the vocabulary of the old field, and
the screener — human or ATS — is matching the new one. The fix is **translation, not reinvention**.

What translation is, precisely: the same verified fact, named in the target field's words, with the
original context kept visible. What it is not, and what this method forbids absolutely:
- **Never re-title a role.** "Teacher" does not become "Learning Experience Designer" on the page. The
  real title stays; the *bullets* carry the transfer. Two forms are allowed, and stating the line
  matters because candidates will clarify the title one way or another: a parenthetical scope note
  (`Teacher (curriculum design for 240 students/yr)`), and an appended real responsibility
  (`Science Teacher — Curriculum & Assessment Lead`) **when that second half was an actually assigned
  responsibility**, not a self-description. Replacing the employer-of-record title is never allowed.
- **Never claim a target-field tool or method the user has not used.** A transferable skill is the one
  they exercised; the tool they have not touched is a gap, handled per
  `number-and-honesty-policy.md`.
- **Never drop the old field to hide it.** An unexplained gap costs more than a career change does,
  and the change is the user's most interesting fact in most rooms.

The method, four steps:
1. **Name the target field's actual vocabulary** from the JD set — the same keyword derivation already
   done once in Phase 3 §4. Do not guess at it from the field's reputation.
2. **For each master entry, ask what the underlying activity was**, stripped of domain nouns. "Ran a
   classroom of 30" is cohort management, curriculum design, stakeholder communication with parents,
   and performance measurement against a standard. Those are the facts; "teaching" was the label.
3. **Rewrite in target vocabulary only where the mapping is exact.** Loose mappings get discarded, not
   softened — an approximate translation is the thing a hiring manager catches in the first interview
   and it costs more credibility than the gap would have.
4. **Then add target-field surface area, which is where the pivot is actually won.** Step 3 is
   deliberately strict, and strictness alone would leave the page still phrased as the old field's —
   the exact failure this section opens by naming. The remedy is additive, not a looser translation,
   and all three moves are fully inside the honesty gates:
   - A **Skills/Tools line of exact-match target-field nouns**, listing only what the user has
     genuinely touched, with self-taught and coursework items labelled as such. The keyword screen is
     won here, and it costs nothing in honesty.
   - A **Projects section carrying work actually done in the target field** — the capstone, the
     freelance engagement, the volunteer analysis, the merged PR, the dashboard they built. For a
     pivot this section **outranks Experience and is positioned above it**. Phase 3 §6 already builds
     Projects; a pivot run must route to it rather than treating it as optional filler.
   - A **`Relevant to <target>` selected-highlights block** at the top. This is *selection* from the
     locked master, not rewording, so it passes the lock rule cleanly.
5. **Keep one line that owns the change**, in the summary: what they did, what they are moving to, and
   the real reason. A pivot stated plainly reads as a decision; an unexplained one reads as a failure
   elsewhere.

Where a translation is applied, it is a **rewording event on an unlocked master**, not a derivative
edit: translate in `master-resume.md`, re-lock, then derive. Note what the mechanical gate does and
does not do here — `lint_artifacts.py`'s `provenance` check only verifies that each cited ID **exists**
in the master, so a fully reworded bullet under a valid ID passes clean. There is no text comparison
anywhere in the tool. That is precisely why translation has to happen on the master: nothing downstream
can detect it if it doesn't.

**And the résumé is not the binding constraint for a pivot.** A translated résumé makes the page
not-a-reason-to-reject; it does not make it a reason to interview, and cold-application conversion for
a career change is low enough that fixing the page alone rarely moves the outcome. Route a pivot
through `../prompts/11-network-map.md` (warm paths) and `../prompts/22-adjacent-titles.md` (what the
evidence already supports) as the **primary** channel, with the translated résumé as the artifact that
survives the referral's screen.
