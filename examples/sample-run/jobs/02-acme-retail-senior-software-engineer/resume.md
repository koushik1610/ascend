<!--
🧪 FICTIONAL SAMPLE, invented persona, company, and metrics. No real resume.

DELTA LOG, selection record (not a rewrite)
- Queue entry: #2, Acme Retail · Senior Software Engineer, Payments
- JD link: https://jobs.example-greenhouse.io/acme-retail/senior-software-engineer-payments (sample/unverified)
- JD title (verbatim): Senior Software Engineer, Payments
    Headline carries it exactly. Held titles under Experience stay as held.
- Date: 2026-11-08
- ATS target: Lever · constraints: single-column, standard headings, no tables in body, PDF.
- Master entries selected, in order, and why:
    Summary B (backend / payments lane), role is checkout and payments services.
    E2 (latency) → E5 (idempotency) → E3 (reliability) → E1 (platform range) → E9 (mentoring) → E6
      (0→1 event-driven service) → E8 (retail inventory sync, domain bridge). Leads with the payments
      pillar to match the JD.
    ORDERING: relevance ranking applies to bullets WITHIN an employer only. Employers stay strictly
      reverse-chronological (resume-writing-rules.md). Applying the relevance order across employers
      reads as concealment and is a fast reject. Enforced by lint_artifacts.py's `scan` category.
    Projects: P2 (latency work) selected; P1/P3 omitted to keep one page on payments.
- JD keywords (verbatim): payments | distributed systems | idempotency | Kafka | PostgreSQL | Go
- True gaps: none
- Verbatim JD phrases inserted ONCE each: "distributed systems", "idempotency".
- Number policy: public values (M4 "~60%", M5 "~1.2M", M6 "14 to 5", M13 "tripling"). Grep for raw
    internals: PASS.
- Export filename: Jordan-Rivera-Resume-Acme-Retail.pdf
- MASTER GAPS: none, every bullet traces to a master entry ID.
-->

# Jordan Rivera
Senior Software Engineer, Payments · Go, PostgreSQL, Kafka
Austin, TX (remote-first / hybrid-OK) · xyz@abc.org · 111-111-1111
Portfolio: https://example.com/jordanrivera · GitHub: https://example.com/gh/jordanr

## Summary
Senior backend engineer, 9 years, who keeps services that carry money fast and correct. Cut
payments-API p99 latency ~60% at ~1.2M transactions a day and designed the **idempotency** keys that
stopped retried payments from double-charging. Comfortable owning **distributed systems** end to end,
from the design doc to on-call.

## Experience

**Acme Pay · Senior Software Engineer** · Austin, TX (remote) · Mar 2021 – Present
*Payments platform team of 7 in a ~60-engineer fintech org.*
- Cut payments-API p99 latency ~60% at ~1.2M transactions a day by fixing PostgreSQL query plans and
  adding a Redis read path with write-through invalidation. *(E2)*
- Designed idempotency keys and a Kafka outbox for payment events, ending a class of duplicate-charge
  bugs caused by client retries. *(E5)*
- Introduced SLOs, OpenTelemetry tracing, and runbooks, bringing Sev-1 incidents from 14 to 5 a
  quarter. *(E3)*
- Built the shared deploy platform 6 teams moved 40+ services onto. Mentors 3–4 engineers and runs
  the weekly design review. *(E1, E9)*

**Acme Corp · Software Engineer II** · Austin, TX (hybrid) · Jun 2018 – Feb 2021
*Logistics marketplace · order-routing team of 5.*
- Built the order-routing service 0→1 in Go, replacing a Python cron job with an event-driven Kafka
  consumer and tripling peak throughput. *(E6)*

**Acme Inc · Software Engineer** · Austin, TX · Jul 2016 – May 2018
*Software consultancy · rotated across ~6 client projects.*
- Built backend APIs for 6 client projects in Python and PostgreSQL, including a retail inventory
  sync that went to production at 40 stores. *(E8)*

## Selected Project
**Payments-API latency work**, pprof and traces to three root causes, flagged fixes, and a Redis read
path. https://example.com/jordanrivera/latency *(P2)*

## Skills
Go · Python · SQL · PostgreSQL · Redis · Kafka · distributed systems · idempotency and the outbox
pattern · payments · gRPC and REST APIs · AWS · Kubernetes · observability · mentoring.

## Education
B.S., Computer Science, Acme State University, 2016.
