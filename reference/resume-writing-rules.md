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

## Structure & format (ATS-safe)
- Reverse-chronological. Sections: Header → Summary → Experience → Skills → Education → (optional)
  Projects/Certs. Standard section *names* (ATS matches on them).
- Length: 1 page under ~10 years, 2 pages for 10+. Never exceed 2.
- Single column. No tables, text boxes, columns, headers/footers, icons, or graphics (parsers drop
  them). PDF unless the portal demands .docx.
- File name: `<Name>-Resume[-<Company>].pdf` (recruiters search download folders).

## One-page content budget (the builder standard)
Per-job resumes default to **exactly one page**. The page is not made to fit by shrinking type (10pt is
the ATS floor); the *content* is generated to fit the fixed layout. The layout is the locked CSS in
`../templates/resume-builder.template.html` (US-Letter, 0.5in margins, serif name, 10pt body). These
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
