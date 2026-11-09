<!-- 🧪 FICTIONAL SAMPLE: invented company and loop. Question bank for a SOFTWARE ENGINEERING loop. -->

# Interview Questions, Acme Health · Staff Software Engineer, Platform

## (a) Technical / domain questions (~14)
Each has a bullet-skeleton answer (approach · key terms · proving artifact).

1. **Walk me through your deploy platform.** → Problem (3-day lead time, every team rolling its own) ·
   approach (manifest → Kubernetes, Terraform modules, canary + rollback) · outcome (40+ services) ·
   artifact: D1 / P1.
2. **How do you design a paved road without blocking teams that need to leave it?** → Sensible
   defaults, escape hatches with an owner, measure who leaves and why · artifact: D1.
3. **How do you roll out a breaking change to a platform 6 teams depend on?** → Versioned manifests,
   deprecation window, migration tool, office hours · artifact: S2.
4. **How do you get teams to adopt something they don't have to?** → Treat adoption as a product;
   pair on the first move; start with the most skeptical team · artifact: S2.
5. **How do you define an SLO for an internal platform?** → Deploy success rate and lead time, not
   just uptime; error budget agreed with users · artifact: E3.
6. **Walk me through a production incident you led.** → Detect, mitigate first, then root cause;
   blameless review; the fix that stuck · artifact: S5.
7. **How would you cut p99 latency on a busy API?** → Measure (pprof, traces), find the top causes,
   fix behind flags, cache with an invalidation plan · artifact: D2.
8. **How do you make payment retries safe?** → Idempotency keys, transactional outbox, at-least-once
   delivery with idempotent consumers · artifact: E5 / S3.
9. **Terraform at scale: modules, state, drift?** → Small composable modules, remote state per
   environment, drift detection in CI · artifact: E1.
10. **How do you keep cloud cost in check without hurting reliability?** → Per-service cost report,
    right-sizing, autoscaling, spot for batch · artifact: E4.
11. **What makes CI fast and trustworthy?** → Sharding, caching, flaky-test quarantine with owners ·
    artifact: E7.
12. **How would you add audit logging to every deploy for a regulated environment?** → Signed,
    append-only deploy events; who, what, when; retention policy · honesty: would ramp on HIPAA
    specifics first.
13. **Kafka: how do you handle reprocessing and ordering?** → Partition keys, idempotent consumers,
    replay from offsets, dead-letter topic · artifact: D3.
14. **What's a design doc of yours that got rejected?** → The first platform RFC was too ambitious;
    cut scope to deploys only · artifact: D1 limitation.

## (b) Coding and system design (calibrated to Acme Health's REAL loop)
This is a standard engineering loop. `VERIFY:` exact mix in the recruiter screen. Expected
components:

- **Coding, 2 rounds (45–60 min each):** LeetCode-style mediums. Expect graphs, intervals, hash maps,
  heaps, and string parsing. Use Go or Python (`VERIFY:` allowed languages). Prep: 2 timed problems a
  day, talk through complexity out loud, write tests for edge cases before running.
- **System design (60 min):** likely "design a deploy pipeline for many teams" or "design a rate
  limiter / job scheduler." Prep: D1 and D2 as anchors; practice requirements, API, data model,
  scaling, failure modes, and what you'd measure.
- **Code review or debugging (45 min, `VERIFY:`):** read a PR with planted bugs (race, missing
  timeout, unbounded retry). Prep: review three open-source Go PRs a week and write the comments.
- **No take-home expected.** If one is offered, time-box it and ask what "done" means.

## (c) Behavioral (mapped to STAR S1–S5 + Acme Health's likely values)
| Question | Story | Maps to (Acme Health value, VERIFY published values) |
|---|---|---|
| "Tell me about driving change without authority." | **S2** | Collaboration |
| "A time you held a quality bar under deadline pressure." | **S3** | Patient safety first |
| "How have you grown other engineers?" | **S4** | Mentorship |
| "Tell me about a failure." | **S5** | Learning |
| "A project with no spec." | **S1** | Ownership |
| "A time data changed your mind." | **S5 / D2** | Evidence over opinion |

> **DO-NOT-GENERATE:** "Why Acme Health / why health?" Jordan writes this personally from honest
> conviction; the system supplies only the honest beats (see outreach.md).

## (d) Curveballs / values screens
- "What would you do in week one if there's *no* platform yet?" → interview teams, map the deploy
  path, pick one painful step to fix first.
- "Platform consistency versus team autonomy?" → defaults plus escape hatches, measured (E1).
- "What's a strong opinion you've changed?" → S5 (cache invalidation as a rollout risk, not a detail).
