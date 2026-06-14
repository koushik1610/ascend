# Portfolio Deep-Dives — Jordan Rivera

> **🧪 FICTIONAL SAMPLE** — invented case studies for a demonstration persona. These are **design**
> deep-dives (case studies), not code walkthroughs — Jordan is a product designer.

Three portfolio case studies, each with a stable ID. Per-job folders reference these by ID for the
portfolio-review round; they don't restate the bodies.

---

### D1 — Beacon Design System (design-systems case study)
- **60-second walkthrough:** "Beacon had five product teams shipping inconsistent UI with heavy QA
  rework and no shared system. As sole design-systems IC, I built one from the ground up: a token
  architecture, 120 Figma components paired 1:1 with engineering's Storybook library, and a governance
  + contribution model so teams extend it instead of forking. I drove adoption without authority —
  migration playbook, office hours, pairing with the most skeptical team first. Five of six teams
  migrated; adopting teams saw new-feature adoption rise ~32% and design QA rework fall roughly in
  half, and I took the components to WCAG 2.1 AA."
- **Probing questions you'll get:**
  - *"How did you decide what becomes a component vs. a one-off?"* → Beats: usage threshold (appears in
    ≥3 flows), variant explosion risk, accessibility surface. Show the governance rubric.
  - *"How do you handle token versioning / breaking changes?"* → Beats: semantic versioning, deprecation
    window, changelog, codemod-style Figma swaps; eng pairing via Storybook PR review.
  - *"How did you measure success — adoption vs. vanity?"* → Beats: adoption = % of net-new UI built on
    the system + rework-ticket reduction (M3, M4); honest that adoption % is the public band.
  - *"Where did engineering push back?"* → Beats: token naming and dark-mode theming; resolved by
    co-owning the Storybook contract.
- **Failure / limitation:** The first contribution model was too heavyweight — a review queue that
  bottlenecked on me. Teams started forking again. I cut the process to a lightweight rubric + async
  review and delegated review rights to two senior designers, which fixed the bottleneck. Lesson:
  governance has to scale past the founder or the system rots.

---

### D2 — Atlas Driver Onboarding (0→1 case study)
- **60-second walkthrough:** "Atlas was hemorrhaging new drivers with no onboarding design and no
  funnel. I owned it 0→1: 12 generative interviews surfaced three drop-off cliffs — document upload,
  approval wait, and first-trip anxiety. I mapped the activation journey, prototyped three variants,
  usability-tested each, and shipped the variant that set expectations up front and chunked the upload.
  First-week drop-off went from 41% to 24% across ~40k monthly signups."
- **Probing questions you'll get:**
  - *"How did you prioritize which cliff to fix first?"* → Beats: impact × addressability; the approval
    wait was structural (couldn't fix in design alone), so I designed *around* it with status
    transparency.
  - *"How did you validate before shipping?"* → Beats: 3 prototyped variants, 8–10 usability sessions
    each, task-success + time-to-complete; chose on evidence, not preference.
  - *"What would you do differently?"* → Beats: instrument earlier; we shipped before analytics were
    fully in place and had to backfill the funnel.
- **Failure / limitation:** The first variant over-explained — a long expectations screen that tested
  worse than the control on time-to-complete. I cut it to a progressive, just-in-time pattern. Honest:
  the win is a relative drop-off reduction (41%→24%), not "halved" — I never round it up.

---

### D3 — Beacon Partner Dashboard Redesign (data-informed B2B case study)
- **60-second walkthrough:** "The B2B partner dashboard had low engagement and a poor NPS. Partnering
  with PM and a data analyst, I read the Amplitude funnels, ran a 600-respondent survey, and reworked
  the information architecture and core task flows. Product NPS rose from 22 to 41 over two quarters.
  Importantly, an *earlier* version of this redesign failed because I'd misread the data — which is
  exactly why I now validate the read with a data partner before designing."
- **Probing questions you'll get:**
  - *"How do you use data without a data background?"* → Beats: I'm a data *partner*, not a modeler — I
    read dashboards, co-design experiments with PM/data, and triangulate quant with qual. Honest
    boundary stated plainly.
  - *"How did you separate IA problems from content problems?"* → Beats: tree-testing + first-click
    tests on the survey cohort.
  - *"How do you know the NPS lift came from your redesign?"* → Beats: phased rollout + survey cohorts;
    honest about confounders.
- **Failure / limitation:** This *is* the failure story (S5) — the first redesign underperformed
  because of a misread funnel (a tracking artifact). The recovery and the durable process change are
  the point.
