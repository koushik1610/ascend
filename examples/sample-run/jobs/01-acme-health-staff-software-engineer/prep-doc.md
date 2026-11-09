<!-- 🧪 FICTIONAL SAMPLE: invented company, role, and metrics. Night-before read, ≤2 pages. -->

# Prep-Doc, Acme Health · Staff Software Engineer, Platform

**Hook (line 1):** "I build the internal platform other teams choose to use, and I'd rather own that
at a health company, where a bad deploy delays care, than at one more ad-tech shop."

## Role thesis (why I win this loop)
Acme Health is hiring a Staff IC to give a dozen product teams one paved road to production. That is
the shape of my last four years: I wrote the design doc for Acme Pay's deploy platform, built it,
and got 6 teams to move 40+ services onto it without a mandate. I also own reliability on a system
that carries money, which maps straight onto health's uptime and audit needs.

## Talking points (expanded)
1. **Platform adoption (E1 / M1–M3).** 40+ services, 6 teams, deploy lead time ~3 days to under an
   hour. Lead with this; it's the JD's #1 ask.
2. **Reliability (E3 / M6, M12).** SLOs, tracing, runbooks: Sev-1 from 14 to 5 a quarter, recovery
   under 20 minutes.
3. **Cost (E4 / M7).** ~35% compute cut with no SLO regressions. Shows I think about the bill.
4. **Correctness under load (E2, E5).** p99 ~60% lower at ~1.2M transactions a day; idempotency
   keys and an outbox. Shows depth below the platform layer.
5. **IC leadership (E9 / M9, M10).** 11 design docs, weekly design review, 3–4 mentees. The honest
   answer to "have you led."

## Story map
| Round / theme | Story | Job-specific opening line |
|---|---|---|
| System design: deploy platform | D1 | "Let me start with who the users are: the product engineers, and what they do today." |
| System design: high-volume API | D2 | "Before scaling it, I'd measure where the time actually goes." |
| Behavioral: influence | S2 | "Six teams, no mandate. I treated adoption as a product." |
| Behavioral: conflict | S3 | "A partner launch was two weeks out and retries could double-charge. Here's how I held the bar." |
| Behavioral: failure | S5 | "My cache rollout served stale merchant config for 40 minutes. Here's what changed after." |

## Gaps + rehearsed handling lines (verbatim)
- **No manager title:** "I'm an IC who multiplies: I mentor 3–4 engineers and run our design review,
  and I'm targeting Staff IC scope, not management. If this role needs a people manager, I want to be
  upfront that that's not what I'm after."
- **New to health:** "I've worked under PCI in fintech, so audit and access constraints aren't new.
  I'd spend my first weeks learning your HIPAA controls before changing the platform."
- **No ML:** "I've built the queues and APIs around a model endpoint. I haven't trained or served
  models, and I won't pretend to."

## Closer (verbatim)
"This is the closest match I've seen to the work I want next: a platform other teams depend on, at a
company where reliability matters to patients. What would make someone exceptional in this seat in
the first six months?"

## Numbers-discipline box
- **Say aloud (public/sanitized):** 40+ services · 6 teams · ~3 days to under an hour · Sev-1 14 → 5 ·
  under 20 minutes recovery · ~60% p99 · ~1.2M transactions a day · ~35% compute · 41 → 14 minute CI.
- **Stay exact (own/verifiable):** 23 merged open-source PRs, 11 design docs, 9 years, 3–4 mentees.
- **Never say:** the platform's internal codename ("Bluejay"), exact 61.4% / 1,180,000 / 34.8%,
  current comp.

## Questions to ask (5 from packet + 2 fresh)
From packet: (1) How do you measure platform success? (2) Is the platform team central or embedded?
(3) What does Staff mean here versus Senior? (4) How are design docs reviewed? (5) What does on-call
look like for the platform team?
Fresh for Acme Health: (6) Which HIPAA controls shape the deploy path most? (7) Is there an existing
platform to evolve, or is this a new build?

## Footer
Portfolio: https://example.com/jordanrivera · deploy-platform write-up:
https://example.com/jordanrivera/deploy-platform · external proof: 23 merged open-source PRs, 2 meetup
talks.
