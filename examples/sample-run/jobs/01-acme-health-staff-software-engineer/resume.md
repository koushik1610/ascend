<!--
🧪 FICTIONAL SAMPLE, invented persona, company, and metrics. No real resume.

DELTA LOG, selection record (not a rewrite)
- Queue entry: #1, Acme Health · Staff Software Engineer, Platform
- JD link: https://jobs.example-greenhouse.io/acme-health/staff-software-engineer-platform (sample/unverified)
- JD title (verbatim): Staff Software Engineer, Platform
    Headline carries it exactly. Held titles under Experience stay as held.
- Date: 2026-11-08
- ATS target: Greenhouse · constraints: single-column, standard section names, no tables in body, PDF.
- Master entries selected, in order, and why:
    Summary A (platform / infrastructure lane), role is an internal-platform team.
    E1 (deploy platform + adoption) → E3 (SLOs + tracing) → E4 (cost) → E2 (latency, with E9
      mentoring folded into the same employer block) → E6 (0→1 range) → E7 (CI, developer experience).
      Leads with the platform pillar to match the JD's #1 ask.
    Projects: P1 (deploy platform) selected; P2/P3 omitted to keep one page on platform work.
- JD keywords (verbatim): platform engineering | developer experience | Kubernetes | Terraform | observability | Go | AWS
- True gaps: none
- Skills-only: platform engineering
- Verbatim JD phrases inserted ONCE each: "platform engineering", "developer experience",
    "observability".
- Number policy: all metrics swapped to public/sanitized values (M3 "~3 days to under an hour", M4
    "~60%", M5 "~1.2M", M7 "~35%"). Grep for raw internals over this file: PASS (no "61.4",
    "1,180,000", "34.8", "Bluejay").
- Data model + export: parsed to `resume.json` (JSON Resume), filled into the résumé builder, and
    rendered one-page via `python3 tools/render_resume.py`.
- Export filename: Jordan-Rivera-Resume-Acme-Health.pdf
- MASTER GAPS: none, every bullet below traces to a master entry ID.
-->

# Jordan Rivera
Staff Software Engineer, Platform · Kubernetes, Terraform, Go
Austin, TX (remote-first / hybrid-OK) · xyz@abc.org · 111-111-1111
Portfolio: https://example.com/jordanrivera · GitHub: https://example.com/gh/jordanr

## Summary
Senior Software Engineer with 9 years across fintech, logistics, and consulting work, focused on
**platform engineering** and reliability. Built Acme Pay's first shared deploy platform and moved 40+
services from 6 teams onto it, cutting deploy lead time from ~3 days to under an hour. Writes the
design doc, gets it through review, and mentors the engineers who build on it, targeting Staff IC
scope.

## Experience

**Acme Pay · Senior Software Engineer** · Austin, TX (remote) · Mar 2021 – Present
*Payments platform team of 7 in a ~60-engineer fintech org.*
- Built Acme Pay's first shared deploy platform (Go, Kubernetes, Terraform, GitHub Actions) and moved
  40+ services from 6 teams onto it, cutting deploy lead time from ~3 days to under an hour. *(E1)*
- Built the payments **observability** stack (SLOs, OpenTelemetry tracing, runbooks), bringing Sev-1
  incidents from 14 to 5 a quarter and recovery time under 20 minutes. *(E3)*
- Cut AWS compute spend ~35% by right-sizing services, adding autoscaling, and moving batch jobs to
  spot capacity. *(E4)*
- Cut payments-API p99 latency ~60% at ~1.2M transactions a day. Mentors 3–4 engineers and runs the
  weekly design review, IC leadership without a manager title. *(E2, E9)*

**Acme Corp · Software Engineer II** · Austin, TX (hybrid) · Jun 2018 – Feb 2021
*Logistics marketplace · order-routing team of 5.*
- Built the order-routing service from scratch in Go, replacing a Python cron job with an event-driven Kafka
  consumer and tripling peak throughput. *(E6)*
- Improved **developer experience** by cutting the CI pipeline from 41 to 14 minutes with parallel
  tests, build caching, and a flaky-test quarantine. *(E7)*

**Acme Inc · Software Engineer** · Austin, TX · Jul 2016 – May 2018
*Software consultancy · rotated across ~6 client projects.*
- Built backend APIs for 6 client projects in Python and PostgreSQL, including a retail inventory
  sync that went to production at 40 stores. *(E8)*

## Selected Project
**Acme Pay deploy platform**, service manifests to Kubernetes, Terraform modules, canary deploys with
automatic rollback. https://example.com/jordanrivera/deploy-platform *(P1)*

## Skills
Platform engineering · Go · Python · Kubernetes · Terraform · AWS · CI/CD · GitHub Actions ·
observability (OpenTelemetry, Prometheus) · SLOs · Kafka · PostgreSQL · distributed systems ·
mentoring / IC leadership.

## Education
B.S., Computer Science, Acme State University, 2016.
