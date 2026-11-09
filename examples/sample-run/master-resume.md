# MASTER RESUME, Jordan Rivera

> **🧪 FICTIONAL SAMPLE · every name, number, company, and link is invented.** No real person, no
> real employer, no real metric. The phone (111-111-1111) and email (xyz@abc.org) are deliberately
> fake. This file demonstrates the master-resume structure only.
>
> **Private superset.** Never sent anywhere; no length limit. Every per-job resume is *selected* from
> here, never rewritten. If tailoring needs a bullet that isn't here, fix THIS file, don't invent on
> the derivative.
>
> **Number policy:** sensitive employer-internal numbers are recorded as
> `[INTERNAL: exact → PUBLIC: "sanitized"]`; derived resumes use ONLY the public value.

---

## §1 HEADER
| Field | Value |
|---|---|
| Name | Jordan Rivera |
| Email · Phone | xyz@abc.org · 111-111-1111 |
| Links | Portfolio: https://example.com/jordanrivera · LinkedIn: https://example.com/in/jordan-rivera-swe · GitHub: https://example.com/gh/jordanr |
| Location · work mode | Austin, TX · remote-first, hybrid-OK (Austin metro) |
| Work authorization | US citizen, no sponsorship required |

**Certifications** (honest status): AWS Certified Solutions Architect, Associate, *Expired 2024* (not
claimed as Active). No active certifications. (Backend hiring rarely gates on certs; shipped systems
and the interview loop are the credential.)

---

## §2 POSITIONING SUMMARIES (per audience, two lengths each)

### A. Staff/Senior Software Engineer, platform and infrastructure lane (PRIMARY)
- **40-word:** Senior Software Engineer, 9 years, who builds internal platforms teams choose to adopt.
  Built a shared deploy platform that 6 teams moved 40+ services onto, cutting deploy lead time from
  ~3 days to under an hour. Go, Kubernetes, Terraform, AWS. IC who mentors.
- **80-word:** Senior Software Engineer with 9 years across fintech, logistics, and consulting work,
  focused on platforms and reliability. At Acme Pay, built the company's first shared deploy platform
  (Go, Kubernetes, Terraform) and moved 40+ services from 6 teams onto it, cutting deploy lead time
  from ~3 days to under an hour. Brought Sev-1 incidents from 14 to 5 a quarter with SLOs and tracing.
  Writes the design doc, gets it through review, and mentors 3–4 engineers, targeting Staff IC scope.

### B. Senior backend / payments lane (ALTERNATE)
- **40-word:** Backend engineer who makes systems that carry money fast and correct. Cut payments-API
  p99 latency ~60% at ~1.2M transactions a day and ended a class of duplicate-charge bugs with
  idempotency keys and an outbox. Go, PostgreSQL, Kafka, Redis.
- **80-word:** Senior backend engineer, 9 years, who owns high-volume services end to end. Cut the
  Acme Pay payments-API p99 latency ~60% at ~1.2M transactions a day through profiling, PostgreSQL
  query work, and a Redis read path with write-through invalidation. Designed idempotency keys and a
  Kafka outbox so retried payments can't double-charge. Earlier, built Acme Corp's order-routing
  service 0→1 in Go, tripling peak throughput. Comfortable on call, in code review, and in the design
  doc.

---

## §3 METRICS BANK
The only place numbers live; bullets reference it.

| # | Metric | Exact value | Public/sendable value | Source | Tag |
|---|---|---|---|---|---|
| M1 | Services moved onto the shared deploy platform | 42 of 48 | "40+ services" | platform repo | PUBLIC-OK |
| M2 | Teams adopting the platform | 6 of 7 | "6 teams" | intake | PUBLIC-OK |
| M3 | Deploy lead time (merge to production) | 3.1 days → 47 min | "from ~3 days to under an hour" | deploy metrics | INTERNAL→PUBLIC |
| M4 | Payments-API p99 latency | 820 ms → 317 ms (−61.4%) | "cut p99 latency ~60%" | APM dashboard | INTERNAL→PUBLIC |
| M5 | Payments-API volume | 1,180,000 transactions/day | "~1.2M transactions a day" | internal | INTERNAL→PUBLIC |
| M6 | Sev-1 incidents per quarter | 14 → 5 | "14 → 5 a quarter" | incident tracker | INTERNAL→PUBLIC (band-safe) |
| M7 | Compute spend reduction | −34.8% | "cut compute spend ~35%" | cloud bill | INTERNAL→PUBLIC |
| M8 | CI pipeline time | 41 min → 14 min | "41 → 14 minutes" | CI dashboard | INTERNAL→PUBLIC (band-safe) |
| M9 | Engineers mentored | 4 (3 junior, 1 mid) | "3–4 engineers" | intake | PUBLIC-OK |
| M10 | Design docs (RFCs) authored and approved | 11 | "11 design docs" | doc index | PUBLIC-OK |
| M11 | Merged PRs to a public open-source Go library | 23 | "23 merged PRs" | public repo | PUBLIC-OK |
| M12 | Mean time to recover (Sev-1) | 52 min → 19 min | "under 20 minutes" | incident tracker | INTERNAL→PUBLIC |
| M13 | Order-routing peak throughput | 3.2x | "3x peak throughput" | load tests | INTERNAL→PUBLIC |
| M14 | Meetup talks given | 2 (Go and platform meetups) | "2 meetup talks" | public | PUBLIC-OK |

---

## §4 SKILLS INVENTORY
ATS keywords for Staff/Senior Software Engineer roles are marked `[ATS]`; each maps to evidence.

**Languages:** Go `[ATS]` (E1,E2,E6) · Python `[ATS]` (E7,E8) · SQL (E2,E8) · Java (reads and patches,
E8) · TypeScript (basic, small UI fixes).

**Backend & distributed systems:** distributed systems `[ATS]` (E5,E6) · microservices `[ATS]`
(E1,E6) · REST and gRPC APIs `[ATS]` (E2,E8) · event-driven design with Kafka `[ATS]` (E5,E6) ·
idempotency and the outbox pattern (E5) · caching with Redis `[ATS]` (E2).

**Data:** PostgreSQL `[ATS]` (E2,E8) · query tuning and indexing (E2) · schema migrations (E8).

**Infrastructure:** AWS `[ATS]` (E1,E4) · Kubernetes `[ATS]` (E1) · Terraform `[ATS]` (E1) · Docker
(E1,E7) · CI/CD `[ATS]` (E1,E7) · GitHub Actions (E1,E7) · autoscaling and cost work (E4).

**Reliability:** observability `[ATS]` (E3) · OpenTelemetry tracing (E3) · Prometheus and Grafana
(E3) · SLOs and error budgets `[ATS]` (E3) · incident response and on-call (E3).

**Collaboration & leadership:** technical design docs `[ATS]` (E9) · code review (E9) · mentoring /
IC leadership `[ATS]` (E9) · cross-team technical direction (E1) · open-source contribution (E10).

**Honest gap list** (keywords Jordan CANNOT claim, handled honestly, never bluffed):
- "Engineering manager / people manager / direct reports": Jordan is an IC who mentors; **no
  management title.** Claim "IC leadership / mentoring" instead.
- "ML engineer / model training / MLOps / PyTorch": Jordan has built queues and APIs around a
  model-serving endpoint, but has **not** trained or served models. Claim nothing ML.
- "Front-end engineer / React owner": reads and fixes React, ships small UI changes; does **not** own
  a front-end codebase. Claim "full-stack fluent" only.
- "Rust / C++ systems programming": not used professionally; don't list.

---

## §5 EXPERIENCE (reverse-chronological)

### Acme Pay, Senior Software Engineer | Austin, TX (remote) | Mar 2021 – Present
**Scope line:** Payments platform team of 7 inside a ~60-engineer fintech org; owns the payments API
and, since 2022, the shared deploy platform.

#### E1, Built the shared deploy platform
- **(a) Standard:** Built Acme Pay's first shared deploy platform (Go, Kubernetes, Terraform, GitHub
  Actions) and moved 40+ services from 6 teams onto it, cutting deploy lead time from ~3 days to
  under an hour (M1, M2, M3).
- **(b) Expanded:** Wrote the design doc, then built the platform as tech lead with two engineers: a Go
  service that turns a short service manifest into Kubernetes resources, Terraform modules for the
  AWS pieces, and a GitHub Actions pipeline with canary and automatic rollback. Drove adoption across
  6 of 7 teams with a migration guide, office hours, and pairing on each team's first move. Deploy
  lead time fell from ~3 days to under an hour (M1–M3).
- **Variants:** "Led the deploy platform from design doc to 40+ services across 6 teams."
- **(c) Tags:** [platform] [kubernetes] [terraform] [adoption] [leadership] [staff-scope]
- **(d) Source:** resume + platform repo
- **(e) STAR:** S2 (influence without authority), D1 (deep-dive)

#### E2, Cut payments-API latency
- **(a) Standard:** Cut payments-API p99 latency ~60% at ~1.2M transactions a day by profiling hot
  paths, fixing PostgreSQL query plans, and adding a Redis read path with write-through invalidation
  (M4, M5).
- **(b) Expanded:** Profiled the payments API with pprof and tracing, found three causes (an N+1 query
  on merchant config, a missing composite index, and connection-pool starvation under bursts), fixed
  each behind a flag, and moved merchant-config reads to Redis with write-through invalidation. p99
  latency fell ~60% at ~1.2M transactions a day (M4, M5).
- **Variants:** "Owned a payments-API latency fix that cut p99 ~60%."
- **(c) Tags:** [performance] [postgresql] [redis] [go] [payments]
- **(d) Source:** APM dashboard (sanitized)
- **(e) STAR:** S5 (the cache incident), D2

#### E3, Reliability: SLOs, tracing, and on-call
- **(a) Standard:** Introduced SLOs, OpenTelemetry tracing, and runbooks for the payments services,
  bringing Sev-1 incidents from 14 to 5 a quarter and recovery time under 20 minutes (M6, M12).
- **(b) Expanded:** Defined SLOs and error budgets with product, added OpenTelemetry tracing across
  the payments path, wrote runbooks for the ten most common pages, and redesigned the on-call rotation
  so pages go to the owning team. Sev-1 incidents fell from 14 to 5 a quarter and recovery time from
  ~50 minutes to under 20 (M6, M12).
- **Variants:** "Set up SLOs and tracing that cut Sev-1 incidents from 14 to 5 a quarter."
- **(c) Tags:** [reliability] [observability] [slo] [on-call] [staff-scope]
- **(d) Source:** incident tracker (sanitized)
- **(e) STAR:** S3, D2

#### E4, Compute cost reduction
- **(a) Standard:** Cut compute spend ~35% by right-sizing services, adding autoscaling, and moving
  batch jobs to spot capacity (M7).
- **(b) Expanded:** Built a weekly cost report per service, right-sized the 15 most over-provisioned
  services, added horizontal autoscaling on request rate, and moved nightly batch jobs to spot
  capacity with retry. Compute spend fell ~35% with no SLO regressions (M7).
- **(c) Tags:** [cost] [aws] [kubernetes] [autoscaling]
- **(d) Source:** cloud bill (sanitized)
- **(e) STAR:**

#### E5, Idempotent payment retries
- **(a) Standard:** Designed idempotency keys and a Kafka outbox for payment events, ending a class
  of duplicate-charge bugs caused by client retries.
- **(b) Expanded:** After two duplicate-charge incidents traced to client retries, wrote the design
  doc for idempotency keys on every write endpoint plus a transactional outbox that publishes payment
  events to Kafka exactly once in effect. Held the line on shipping it before a partner launch (S3).
  No duplicate charge has been reported since.
- **(c) Tags:** [distributed-systems] [kafka] [correctness] [payments] [design-doc]
- **(d) Source:** design doc + incident tracker
- **(e) STAR:** S3

### Acme Corp, Software Engineer II | Austin, TX (hybrid) | Jun 2018 – Feb 2021
**Scope line:** Logistics marketplace; order-routing team of 5; Go and Python services on AWS.

#### E6, 0→1 order-routing service
- **(a) Standard:** Built Acme Corp's order-routing service 0→1 in Go, replacing a Python cron job
  with an event-driven Kafka consumer and tripling peak throughput (M13).
- **(b) Expanded:** Took order routing from a 15-minute Python cron job to an event-driven Go service:
  wrote the design doc, built the Kafka consumer and routing rules engine, ran it in shadow mode
  against the old job for three weeks, then cut over by region. Peak throughput tripled and orders
  route in seconds instead of minutes (M13).
- **Variants:** "Owned the 0→1 build of an event-driven routing service in Go."
- **(c) Tags:** [0-to-1] [go] [kafka] [distributed-systems] [migration]
- **(d) Source:** load tests (sanitized)
- **(e) STAR:** S1 (ambiguity), D3

#### E7, CI speed and test health
- **(a) Standard:** Cut the CI pipeline from 41 to 14 minutes by parallelizing tests, caching builds,
  and quarantining flaky tests (M8).
- **(b) Expanded:** Split the test suite into parallel shards, added Docker layer and dependency
  caching, and built a flaky-test quarantine with an owner and a fix-by date. CI went from 41 to 14
  minutes and engineers stopped re-running builds by habit (M8).
- **(c) Tags:** [ci-cd] [developer-productivity] [python] [docker]
- **(d) Source:** CI dashboard
- **(e) STAR:** S4

### Acme Inc, Software Engineer | Austin, TX (on-site) | Jul 2016 – May 2018
**Scope line:** Software consultancy; rotated across ~6 client projects (retail, health, SaaS).

#### E8, Consultancy backend work
- **(a) Standard:** Built backend APIs for 6 client projects in Python and PostgreSQL, including a
  retail inventory sync that went to production at 40 stores.
- **(b) Expanded:** As a consultancy engineer, owned the backend for 6 client projects (Django and
  Flask APIs, PostgreSQL schemas and migrations, a Java integration patched for one client), including
  a retail inventory sync that went to production at 40 stores.
- **(c) Tags:** [backend] [python] [postgresql] [breadth] [client]
- **(d) Source:** resume
- **(e) STAR:** S1

#### E9, Mentoring, design docs, and code review (spans roles)
- **(a) Standard:** Mentors 3–4 engineers and runs the team's weekly design review; wrote 11 design
  docs that other teams built on (M9, M10).
- **(b) Expanded:** Across Acme Corp and Acme Pay, mentored 3–4 junior and mid engineers (pairing,
  code review, design-doc coaching), started and runs the weekly design-review meeting, and wrote 11
  approved design docs. IC leadership with no direct reports. *Honesty: mentoring, not people
  management.*
- **(c) Tags:** [mentoring] [IC-leadership] [design-doc] [code-review]
- **(d) Source:** intake + doc index
- **(e) STAR:** S4

#### E10, Open source and community (spans roles)
- **(a) Standard:** Contributed 23 merged PRs to a public open-source Go library and gave 2 meetup
  talks on platform engineering (M11, M14).
- **(b) Expanded:** Contributes to a public Go HTTP-middleware library (23 merged PRs, mostly
  retry and timeout handling) and gave 2 local meetup talks on running a deploy platform.
- **(c) Tags:** [open-source] [go] [community]
- **(d) Source:** public repo + meetup pages
- **(e) STAR:**

---

## §6 PROJECTS / PORTFOLIO
### P1, Acme Pay Deploy Platform ("Bluejay" internal name, never publish the codename)
- **One-liner:** A shared deploy platform 6 teams moved 40+ services onto.
- **Paragraph:** Service manifest → Kubernetes resources, Terraform modules for AWS, a GitHub Actions
  pipeline with canary and automatic rollback. Deploy lead time from ~3 days to under an hour. *Refer
  to it publicly as "Acme Pay's deploy platform," never the internal codename.*
- **Stack:** Go · Kubernetes · Terraform · AWS · GitHub Actions · **Metrics:** M1–M3 · **Status:**
  in production · **Link:** https://example.com/jordanrivera/deploy-platform

### P2, Payments-API Latency Work
- **One-liner:** Profiling and caching work that cut payments-API p99 latency ~60%.
- **Paragraph:** pprof and traces → three root causes → flagged fixes and a Redis read path.
  **Metrics:** M4, M5 · **Status:** shipped · **Link:** https://example.com/jordanrivera/latency

### P3, Acme Corp Order Routing (0→1)
- **One-liner:** An event-driven Go routing service that tripled peak throughput.
- **Paragraph:** Kafka consumer plus rules engine, three weeks in shadow mode, regional cutover.
  **Metrics:** M13 · **Status:** shipped · **Link:** https://example.com/jordanrivera/order-routing

---

## §7 EDUCATION & CREDENTIALS
- **B.S., Computer Science**, Acme State University (fictional), 2016.
- AWS Certified Solutions Architect, Associate, **Expired 2024** (listed honestly; not claimed Active).

---

## §8 STORY BANK INDEX
| Story | Theme | Experience entries | Tags |
|---|---|---|---|
| S1 | Ambiguity / no spec (0→1 order routing) | E6, E8 | [0-to-1] [ambiguity] |
| S2 | Influence without authority (deploy-platform adoption) | E1, E9 | [influence] [platform] |
| S3 | Conflict / conviction under pushback (idempotency vs. launch date) | E5, E3 | [conflict] [correctness] |
| S4 | Coaching / multiplying (mentoring + design review) | E9, E7 | [mentoring] [IC-leadership] |
| S5 | Genuine failure + learning (cache rollout served stale data) | E2 | [failure] [reliability] |

---

## §9 TAILORING PROTOCOL (how a per-job resume is derived)
1. Paste the JD → extract its keywords.
2. ATS gap-score the master §4 against it (0–100); list present / missing-but-claimable / true-gap.
3. Select bullets by §5 tag-match; lead with the audience-default set.
4. Swap every metric to its public value (§3).
5. Run the 6-second recruiter pass.
6. Run the honesty + writing checklist (`reference/resume-writing-rules.md`).
7. Log the selection (entry IDs) in the job folder's `resume.md` Delta Log.

**Audience defaults:**
- *Platform / infrastructure lane (Summary A):* lead with **E1 → E3 → E4 → E2**, then E9 (IC
  leadership), then E6/E7 for range.
- *Backend / payments lane (Summary B):* lead with **E2 → E5 → E3**, then E1 (platform range), then
  E6/E8.

---

## §10 CONFLICTS & COVERAGE LOG
- **Conflicts:** The old resume said latency was "cut in half or more"; the APM readout shows 820 ms →
  317 ms. **Kept "~60%"** (a rounded public band of the real figure); never inflate it.
- **Conflicts:** LinkedIn headline says "Staff Engineer"; Jordan's held title is Senior Software
  Engineer. **Reconciled to "Senior Software Engineer"** everywhere sendable. Staff is the target, not
  a held title, flagged in §4 and in the LinkedIn steps.
- **Coverage:** Sources used: sample resume, sample LinkedIn export, intake interview. Excluded: a
  2017 mobile app side project (off-target for platform and backend lanes; available on request).
