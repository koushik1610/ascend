<!-- 🧪 FICTIONAL SAMPLE — invented company and loop. Question bank for a DESIGN loop (no LeetCode). -->

# Interview Questions — Northwind Health · Staff Product Designer

## (a) Technical / domain / design questions (~14)
Each has a bullet-skeleton answer (approach · key terms · proving artifact).

1. **Walk me through your design system.** → Problem (5 teams, inconsistency, QA rework) · approach
   (tokens → components → governance) · outcome (~32% adoption) · artifact: D1 / P1.
2. **How do you decide what becomes a component?** → Usage threshold (≥3 flows), variant-explosion
   risk, a11y surface · key terms: governance rubric · artifact: D1 governance rubric.
3. **How do you version a design system without breaking teams?** → Semantic versioning, deprecation
   window, changelog, codemod-style Figma swaps · artifact: D1.
4. **How do you drive adoption with no authority?** → Treat adoption as a product; migration playbook,
   office hours, pair with the skeptic first · artifact: S2.
5. **How do you keep design and engineering in sync?** → Storybook contract, PR review, annotated
   specs, pairing · outcome: −44% spec drift · artifact: E3.
6. **How do you approach accessibility in a component library?** → Contrast, focus order, semantics,
   reduced-motion; WCAG 2.1 AA; bake into tokens · artifact: E3 / M11.
7. **Critique this screen** (they'll show one). → Critique against the *goal* first; separate "broken"
   from "I'd explore" · key terms: structured critique · artifact: S4 crit format.
8. **How would you bring systems rigor to a health platform with strict compliance?** → Map regulatory
   constraints to tokens/patterns; a11y as table-stakes · honesty: would ramp on domain first.
9. **0→1 vs. systems — which are you?** → Both; 0→1 (E5) + systems (E1); systems *is* 0→1 for tooling.
10. **How do you measure design-system success?** → Adoption % of net-new UI + rework reduction, not
    component count alone · artifact: M3, M4.
11. **Tell me about an IA decision.** → Partner-dashboard rework; tree-testing; NPS 22→41 · artifact: D3.
12. **How do you handle a designer who won't adopt the system?** → Understand friction, co-author an
    extension path, make the system the easy choice · artifact: S2.
13. **What's your prototyping process?** → Variant testing (3 onboarding variants, 8–10 users each) ·
    artifact: D2.
14. **How do you use data without a data background?** → Read funnels, co-design experiments, triangulate
    quant+qual; data *partner* not modeler · honesty boundary · artifact: D3 / S5.

## (b) Design assessment section (calibrated to Northwind's REAL loop — NOT LeetCode)
Northwind runs a **design loop**, not an algorithm loop. There is **no coding round.** `VERIFY:` exact
mix in the recruiter screen. Expected components:

- **Portfolio review (60–75 min):** present 2 case studies. Lead with **D1 (design system)** — Staff
  evidence — then **D3 (data-informed dashboard)** for range. Prep: 60-sec walkthrough each, the
  probing-question beats, the honest failure/limitation for each.
- **Live whiteboard critique (45 min):** they show a current Northwind screen or component set; you
  critique and propose a systems fix. Prep: critique-against-the-goal format (S4); name token/pattern
  consolidations out loud; ask clarifying questions before redesigning.
- **Take-home or live design exercise (`VERIFY:` which):** likely "audit this small component set and
  propose a system." Scope it, time-box to ~4 hrs, deliver: audit → token proposal → 2–3 components →
  governance note. "Great" = shows systems thinking + a11y + a migration path, not pixel polish.
- **No LeetCode / algorithm round.** Do not prepare one. If a recruiter mentions a "technical" round,
  confirm it means a *design* exercise.

## (c) Behavioral (mapped to STAR S1–S5 + Northwind's likely values)
| Question | Story | Maps to (Northwind value — VERIFY published values) |
|---|---|---|
| "Tell me about driving change without authority." | **S2** | Influence / collaboration |
| "A time you held a quality bar under deadline pressure." | **S3** | Patient/quality-first (health) |
| "How have you grown other designers?" | **S4** | Mentorship / team |
| "Tell me about a failure." | **S5** | Humility / learning |
| "Navigating ambiguity on a 0→1 problem." | **S1** | Ownership / bias to action |
| "A time you used research/data to change a decision." | **S5 / D3** | Evidence-driven |

> **DO-NOT-GENERATE:** "Why Northwind / why health?" — Jordan writes this personally from honest
> conviction; the system supplies only the honest beats (see outreach.md).

## (d) Curveballs / values screens
- "What would you do in week one if there's *no* existing design system?" → 0→1 systems plan (audit →
  tokens → pilot team).
- "How do you balance design-system consistency with team autonomy?" → governance-as-guardrails, not
  gatekeeping (E2).
- "What's a strong opinion you've changed?" → S5 (data misread → process change).
