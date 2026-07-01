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
  Projects/Certs. Standard section *names* (ATS matches on them).
- Length: 1 page under ~10 years, 2 pages for 10+. Never exceed 2.
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
Per-job resumes default to **exactly one page**. The page is not made to fit by shrinking type (10pt is
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
