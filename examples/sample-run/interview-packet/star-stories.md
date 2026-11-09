# STAR Stories, Jordan Rivera

> **🧪 FICTIONAL SAMPLE:** invented events for a demonstration persona. In a real run these are the
> user's true events only; the failure story (S5) must be genuine because interviewers dig.

Five behavioral stories in STAR form, each with a stable ID. Per-job folders map likely questions to
these IDs; they do **not** restate the bodies.

---

### S1, Ambiguity / no spec (0→1 order routing)
- **S:** Acme Corp's order routing ran as a 15-minute cron job that backed up on peak days. Nobody
  owned a spec; the old Python code was the only description of the rules.
- **T:** Replace it with something faster without breaking routing rules nobody had written down.
- **A:** Read the old code end to end and wrote the rules into a design doc, then built an
  event-driven Go service on Kafka. Ran it in shadow mode for three weeks and diffed every decision
  against the cron job, which surfaced three undocumented rules. Cut over one region at a time.
- **R:** Peak throughput tripled and orders route in seconds. The design doc became the team's
  reference for routing rules.
- **Proves:** Comfort without a spec; careful migration; 0→1 ownership. Leads for backend and
  distributed-systems loops.

---

### S2, Influence without authority (deploy-platform adoption)
- **S:** I built Acme Pay's deploy platform, but six other teams had their own pipelines and no
  obligation to switch. I had no authority over any of them.
- **T:** Get teams onto the platform without a mandate, so deploys got faster and safer everywhere.
- **A:** Treated adoption as a product: asked each team what hurt about deploying, wrote a migration
  guide, held weekly office hours, and paired with the most skeptical team first. Pitched it on their
  pain (three-day lead times, manual rollbacks), not on consistency.
- **R:** 6 of 7 teams moved 40+ services; lead time fell from ~3 days to under an hour. The skeptical
  team's lead now presents the platform to new hires.
- **Proves:** Influence without authority; Staff-scope leverage. Leads for platform and Staff loops.

---

### S3, Conflict / conviction under pushback (idempotency vs. the launch date)
- **S:** Two weeks before a partner launch, I found that client retries could double-charge a
  customer. A PM wanted to launch and fix it after.
- **T:** Hold the correctness bar without becoming the person who blocks every launch, and bring the
  PM along.
- **A:** Quantified it: showed the two past duplicate-charge incidents, the refund cost, and the
  partner's retry behavior. Proposed a split: idempotency keys on the two launch endpoints before
  launch, the full outbox after. Paired with another engineer and shipped the must-have part in four
  days.
- **R:** Launched on time with no duplicate charges; the full outbox shipped three weeks later. "Name
  the risk, then split the fix" became how we scope correctness work.
- **Proves:** Conviction handled with data and compromise. Leads for quality and conflict questions.

---

### S4, Coaching / multiplying (mentoring + design review)
- **S:** Design discussions on our team happened in long PR threads, and two junior engineers were
  stuck: lots of effort, slow growth, unsure what "good" looked like.
- **T:** Raise the team's bar as an IC, without a manager title.
- **A:** Started a weekly 45-minute design review with a one-page doc template (problem, options,
  decision, risks). Took on mentoring two juniors and one mid engineer: weekly pairing, specific
  code-review feedback, and coaching each through writing their first design doc. Put my own docs up
  for review first.
- **R:** Both juniors led features within two quarters; PR threads got shorter because debates moved
  into docs. Mentored 3–4 engineers total without a direct report.
- **Proves:** IC leadership, the honest answer to "have you led a team?"

---

### S5, Genuine failure + learning (the cache rollout)
- **S:** As part of the latency work, I moved merchant-config reads to a Redis cache.
- **T:** Cut payments-API latency without changing behavior.
- **A (what went wrong + the fix):** My invalidation path missed one admin write endpoint. After a
  merchant changed their payout settings, the API served stale config for 40 minutes until the TTL
  expired. Support caught it, not our alerts. I owned it in the incident review, added a version
  check on every cached read, an alert on cache/database mismatch, and a staged rollout by merchant
  tier for any cache change.
- **R:** The corrected rollout shipped two weeks later and p99 still fell ~60%. Every cache change on
  the team now ships with a mismatch alert and a staged rollout.
- **Proves:** A real failure, owned, with a process change that stuck. Leads for "tell me about a
  failure" and reliability questions.
