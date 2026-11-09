# Project Deep-Dives, Jordan Rivera

> **🧪 FICTIONAL SAMPLE:** invented projects for a demonstration persona. These are **engineering**
> deep-dives (architecture and trade-offs), the anchors for system design and "walk me through a
> project" rounds.

Three projects, each with a stable ID. Per-job folders reference these by ID; they don't restate
the bodies.

---

### D1, Acme Pay deploy platform (platform case study)
- **60-second walkthrough:** "Every team at Acme Pay deployed differently, and merge to production
  took about three days. I wrote the design doc for a shared platform and built it with two
  engineers: a Go service that turns a short manifest into Kubernetes resources, Terraform modules
  for the AWS pieces, and a pipeline with canary deploys and automatic rollback. Nobody had to adopt
  it, so I ran office hours and paired on each team's first move. Six of seven teams moved 40+
  services, and lead time dropped to under an hour."
- **Probing questions you'll get:**
  - *"Why build instead of buy?"* → Beats: evaluated two hosted options; both needed our network and
    compliance setup rebuilt; the manifest layer was small enough to own.
  - *"How do you handle a team that needs something the platform doesn't do?"* → Beats: escape hatch
    (raw Kubernetes YAML) with an owner; track who uses it; the top requests become features.
  - *"How did you measure success?"* → Beats: lead time, deploy success rate, rollback count, and the
    share of services on the platform; not lines of code.
  - *"Where did teams push back?"* → Beats: secrets handling and log formats; resolved by
    co-designing those two pieces with the loudest team.
- **Failure / limitation:** The first design doc tried to cover deploys, secrets, and service
  discovery at once and stalled in review. I cut it to deploys only, shipped, and added the rest in
  later docs. Lesson: a platform earns its scope one adopted feature at a time.

---

### D2, Payments-API latency (performance case study)
- **60-second walkthrough:** "Payments p99 latency had crept up as volume grew to about 1.2 million
  transactions a day. I profiled with pprof and traces and found three causes: an N+1 query on
  merchant config, a missing composite index, and connection-pool starvation during bursts. I fixed
  each behind a flag and moved merchant-config reads to Redis with write-through invalidation. p99
  fell about 60%."
- **Probing questions you'll get:**
  - *"How did you prioritize the three causes?"* → Beats: trace share of time per cause; the index
    was cheapest and biggest, so it went first.
  - *"How do you keep a cache correct?"* → Beats: write-through on update, short TTL as a backstop,
    and a version check. This is where S5 comes in.
  - *"How did you prove the change, not traffic, moved p99?"* → Beats: flags per fix, before/after
    at the same hour of day, and a load test that replayed recorded traffic.
- **Failure / limitation:** The first cache rollout served stale merchant config for 40 minutes
  (S5). The invalidation path missed one write endpoint. Fixed with a version check and a staged
  rollout by merchant tier.

---

### D3, Acme Corp order routing (0→1 distributed-systems case study)
- **60-second walkthrough:** "Order routing ran as a Python cron job every 15 minutes, so orders sat
  waiting and peak days backed up. There was no spec, only the old code. I wrote the design doc for
  an event-driven Go service: a Kafka consumer plus a rules engine. We ran it in shadow mode for three
  weeks, compared every decision against the old job, then cut over by region. Peak throughput
  tripled and orders route in seconds."
- **Probing questions you'll get:**
  - *"How did you handle ordering and duplicates?"* → Beats: partition by order ID; idempotent
    consumer keyed on order ID plus version; a dead-letter topic for poison messages.
  - *"Why shadow mode?"* → Beats: the old job's behavior was the only spec; diffs showed three
    undocumented rules we would have broken.
  - *"What would you change?"* → Beats: add tracing from day one; we added it after the first
    regional cutover.
- **Failure / limitation:** One region's cutover was rolled back after a day because a carrier
  integration expected batch timing. We added a small batching adapter for that carrier and retried
  the cutover a week later.
