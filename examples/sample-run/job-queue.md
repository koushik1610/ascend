# Jordan Rivera, Job Queue (ranked)

> **🧪 FICTIONAL SAMPLE: every name, number, company, and link is invented.** All companies are
> made-up Acme names; all links point to `example.com` / `jobs.example-greenhouse.io` placeholders
> and are **sample / unverified: they do not lead to live postings.**

**What this is:** the priority-ordered application list, scored against the master resume. Each job
carries an explainable **Fit Score (0–100)** = skills + seniority + comp + location + excitement
(each 0–20). The top few become apply packs under `jobs/`; the rest stay leads until they earn a pack.
**Ranking formula:** evidence fit × level match × comp × location feasibility × shortlist probability.
**Built:** 2026-11-08 · **Targets:** Staff / Senior Software Engineer (backend, platform) ·
**Constraints:** Austin TX, remote-first / hybrid-OK Austin metro, no sponsorship needed.

**🔗 Link status:** every link below is a placeholder for this sample. In a real run each link is a
LIVE posting re-verified on the build date; re-verify before applying, postings rot.

---

## ⚠ Do these BEFORE applying to anything
1. Confirm the master resume's flagship bullets carry their numbers (the ATS/keyword audit is folded
   into `master-resume.md`; there is no separate audit file).
2. Apply the LinkedIn next-steps from `linkedin-analysis.html`, especially the headline fix and the
   Featured deploy-platform write-up (steps 1–3).
3. **Referral sweep:** message any existing connection at the target company *before* applying cold
   (see each folder's `outreach.md`).
4. Start daily coding reps now. Every loop in this set has at least one coding round.

---

## #1: Acme Health · Staff Software Engineer, Platform
| | |
|---|---|
| Req / Link | AH-PLT-204 · https://jobs.example-greenhouse.io/acme-health/staff-software-engineer-platform *(sample/unverified)* |
| Level / Comp | Staff (IC) · $210k–$250k base posted |
| Location | Remote (US) · HQ Austin, TX, hybrid optional |
| ATS | Greenhouse |

**Fit Score: 92 / 100**: skills 19 · seniority 19 · comp 18 · location 20 · excitement 16.

**Why it ranks here:** Best evidence fit in the set. The role is an internal-platform team giving a
dozen product teams one path to production, which is Jordan's lead pillar (E1, E3, E4). IC Staff
track (no management title required) matches the honest gap. Austin HQ plus remote means zero
location friction, and the band covers the floor.

**Resume delta (vs master):** lead **E1 → E3 → E4 → E2**, then E9, then E6/E7 for range. Insert JD
phrases once each: "platform engineering," "developer experience," "observability."

**Talking points:** (1) Deploy platform, 40+ services, 6 teams, ~3 days to under an hour (E1/M1–M3).
(2) Sev-1 from 14 to 5 a quarter (E3/M6). (3) ~35% compute cut (E4/M7). (4) Mentors 3–4, runs
design review (E9/M9).

**Expected interview questions:** two coding rounds; system design of a deploy pipeline; "how do you
drive adoption without authority"; behavioral on conflict (correctness vs. ship date → S3).

**Gaps & handling:** *No manager title.* Honest line: "I mentor 3–4 engineers and run our design
review, and I'm targeting Staff IC scope, not management." *Health-domain newness:* "I've worked
under PCI; here's how I'd ramp on your HIPAA controls."

**Logistics:** Greenhouse, keep the PDF single-column. Referral angle: sample ex-teammate (see
outreach). Recruiter screen: confirm IC-track and the coding-round language first.

---

## #2: Acme Retail · Senior Software Engineer, Payments
| | |
|---|---|
| Req / Link | AR-PAY-2207 · https://jobs.example-greenhouse.io/acme-retail/senior-software-engineer-payments *(sample/unverified)* |
| Level / Comp | Senior (IC) · $185k–$220k base posted |
| Location | Hybrid, Austin, TX (3 days/wk) |
| ATS | Lever |

**Fit Score: 87 / 100**: skills 18 · seniority 17 · comp 17 · location 18 · excitement 17.

**Why it ranks here:** Direct payments fit (E2, E5) plus a retail surface that maps to the
consultancy inventory-sync work (E8). Senior, not Staff, but at a larger company where Senior scope
is broad. Below #1 on level and on platform emphasis.

**Resume delta (vs master):** lead **E2 → E5 → E3**, then E1 (platform range), then E9. Insert once
each: "distributed systems," "idempotency."

**Talking points:** (1) p99 ~60% lower at ~1.2M transactions a day (E2/M4–M5). (2) Idempotency keys
and outbox (E5). (3) Sev-1 14 → 5 (E3/M6). (4) Retail inventory sync at 40 stores (E8).

**Expected interview questions:** coding round; system design of a checkout or payment service with
retries; "walk me through an incident"; failure behavioral (S5).

**Gaps & handling:** *Hybrid 3 days.* Inside the stated work mode for Austin, so no gap, but confirm
it's firm in the screen.

**Logistics:** Lever. Referral: sample alum (see outreach). Ask whether system design is one round
or two.

---

## #3: Acme Cloud · Senior Software Engineer, Infrastructure
| | |
|---|---|
| Req / Link | AC-INF-19 · https://jobs.example-greenhouse.io/acme-cloud/senior-software-engineer-infrastructure *(sample/unverified)* |
| Level / Comp | Senior · $190k–$228k base posted |
| Location | Remote (US) |
| ATS | Ashby |

**Fit Score: 83 / 100**: skills 18 · seniority 17 · comp 18 · location 20 · excitement 10.

**Why it ranks here:** Kubernetes and Terraform heavy (E1, E4), fully remote. Ranks below #1–#2
because the team runs customer-facing infrastructure, and the JD leans on Kubernetes operator
development Jordan hasn't done.

**Resume delta (vs master):** lead **E1 → E4 → E3**, then E7. Insert once: "infrastructure as
code," "Kubernetes."

**Talking points:** deploy platform (E1); ~35% compute cut (E4); SLOs and tracing (E3); CI 41 → 14
minutes (E7).

**Expected interview questions:** coding; system design of a multi-tenant control plane; debugging
a failing deploy; behavioral on ambiguity (S1).

**Gaps & handling:** *Kubernetes operators.* Honest line: "I've built a controller-style service
that generates Kubernetes resources; I haven't written a custom operator with CRDs yet."

**Logistics:** Ashby. Confirm whether the role is on call for customer clusters.

---

## #4: Acme Logistics · Staff Software Engineer, Backend
| | |
|---|---|
| Req / Link | AL-BE-77 · https://jobs.example-greenhouse.io/acme-logistics/staff-software-engineer-backend *(sample/unverified)* |
| Level / Comp | Staff · $195k–$235k base posted |
| Location | Hybrid, Austin (3 days/wk) |
| ATS | Workday |

**Fit Score: 79 / 100**: skills 17 · seniority 18 · comp 16 · location 15 · excitement 13.

**Why it ranks here:** Staff title and a logistics domain Jordan shipped in at Acme Corp (E6). Ranks
here because Workday applications get little recruiter attention without a referral, and Jordan has
none at this company yet.

**Resume delta (vs master):** lead **E6 → E2 → E5**, then E1, then E9.

**Talking points:** order routing 0→1, tripled throughput (E6/M13); payments latency (E2); idempotency
(E5); design docs and mentoring (E9).

**Expected interview questions:** coding; system design of an order-routing or dispatch service;
"how do you migrate off a legacy system safely" (S1).

**Gaps & handling:** none blocking. Look for a 2nd-degree path before applying.

**Logistics:** Workday, re-check the PDF parses into their form fields.

---

## #5: Acme Bank · Senior Software Engineer, Core Ledger
| | |
|---|---|
| Req / Link | AB-LED-5 · https://jobs.example-greenhouse.io/acme-bank/senior-software-engineer-core-ledger *(sample/unverified)* |
| Level / Comp | Senior · $185k–$222k base posted |
| Location | Hybrid, Austin (2 days/wk) |
| ATS | Greenhouse |

**Fit Score: 76 / 100**: skills 17 · seniority 15 · comp 17 · location 16 · excitement 11.

**Why it ranks here:** Ledger correctness work fits E5 and the fintech background. Ranks here
because the stack is Java and the team is described as slow-moving.

**Resume delta (vs master):** lead **E5 → E2 → E3**, then E1.

**Talking points:** idempotency and outbox (E5); p99 ~60% (E2); Sev-1 14 → 5 (E3).

**Expected interview questions:** coding (`VERIFY:` whether Java is required); design a
double-entry ledger; conflict behavioral (S3).

**Gaps & handling:** *Java.* Honest line: "I read and patch Java; my production depth is Go and
Python, and I'd ramp fast."

**Logistics:** Greenhouse. Ask about the language requirement before prep time goes in.

---

## #6: Acme Labs · Software Engineer III, Developer Productivity
| | |
|---|---|
| Req / Link | AL-DP-12 · https://jobs.example-greenhouse.io/acme-labs/al-dp-12 *(sample/unverified)* |
| Level / Comp | $175k–$205k base posted · Greenhouse · Remote (US) |

**Fit Score: 74 / 100**: skills 19 · seniority 13 · comp 14 · location 20 · excitement 8.
**Why / fit:** CI and build tooling (E7) plus platform work (E1). Ranks here because it levels below Senior, a step sideways. **Delta:** lead E7 → E1 → E3. **Gap & handling:** *leveling*: anchor Senior/Staff evidence in the screen and ask about the promotion path before committing.

---

## #7: Acme Commerce · Senior Backend Engineer
| | |
|---|---|
| Req / Link | ACM-BE-31 · https://jobs.example-greenhouse.io/acme-commerce/acm-be-31 *(sample/unverified)* |
| Level / Comp | $180k–$212k base posted · Ashby · Hybrid, Austin (2d/wk) |

**Fit Score: 72 / 100**: skills 17 · seniority 16 · comp 15 · location 17 · excitement 7.
**Why / fit:** Order and inventory services (E6, E8). Less platform scope than #1–#3. **Delta:** lead E6 → E2 → E8. **Gap & handling:** *stack*: Java-first shop. Honest line: "I read and patch Java; my production depth is Go and Python."

---

## #8: Acme AI · Senior Software Engineer, ML Platform
| | |
|---|---|
| Req / Link | AAI-MLP-4 · https://jobs.example-greenhouse.io/acme-ai/aai-mlp-4 *(sample/unverified)* |
| Level / Comp | $195k–$230k base posted · Lever · Remote (US) |

**Fit Score: 70 / 100**: skills 13 · seniority 17 · comp 18 · location 20 · excitement 2.
**Why / fit:** Platform skills transfer (E1, E3), but half the JD is model serving and training pipelines. **Delta:** lead E1 → E3 → E4. **Gap & handling:** *ML is a true gap.* Say so in the screen; never claim MLOps. Apply only if the role is mostly infrastructure.

---

## #9: Acme Insurance · Staff Software Engineer
| | |
|---|---|
| Req / Link | AIN-STF-9 · https://jobs.example-greenhouse.io/acme-insurance/ain-stf-9 *(sample/unverified)* |
| Level / Comp | $190k–$226k base posted · Workday · Hybrid, Austin (3d/wk) |

**Fit Score: 69 / 100**: skills 15 · seniority 18 · comp 16 · location 15 · excitement 5.
**Why / fit:** Staff title and a modernization brief (E6 migration pattern). **Delta:** lead E6 → E1 → E9. **Gap & handling:** *IC vs. lead*: posting mentions "leading a team of 4". `VERIFY:` whether that means direct reports.

---

## #10: Acme Software · Senior Software Engineer, Reliability
| | |
|---|---|
| Req / Link | ASW-REL-7 · https://jobs.example-greenhouse.io/acme-software/asw-rel-7 *(sample/unverified)* |
| Level / Comp | $182k–$215k base posted · Greenhouse · Remote (US) |

**Fit Score: 68 / 100**: skills 18 · seniority 15 · comp 15 · location 20 · excitement 0.
**Why / fit:** Pure SRE brief (E3, E4). Series A with a short runway. **Delta:** lead E3 → E4 → E1. **Gap & handling:** *runway*: `VERIFY:` funding before investing prep time.

---

## #11: Acme Media · Senior Software Engineer
| | |
|---|---|
| Req / Link | AMD-SE-22 · https://jobs.example-greenhouse.io/acme-media/amd-se-22 *(sample/unverified)* |
| Level / Comp | $170k–$200k base posted · Ashby · Remote (US) |

**Fit Score: 66 / 100**: skills 15 · seniority 15 · comp 13 · location 20 · excitement 3.
**Why / fit:** General backend (E2, E6). Comp near the floor. **Delta:** lead E2 → E6 → E3. **Gap & handling:** *comp*: below the total-comp floor unless equity closes it.

---

## #12: Acme Education · Senior Backend Engineer
| | |
|---|---|
| Req / Link | AED-BE-5 · https://jobs.example-greenhouse.io/acme-education/aed-be-5 *(sample/unverified)* |
| Level / Comp | $172k–$204k base posted · Lever · Remote (US) |

**Fit Score: 64 / 100**: skills 15 · seniority 15 · comp 13 · location 20 · excitement 1.
**Why / fit:** Backend APIs and PostgreSQL work (E2, E8). **Delta:** lead E2 → E8 → E3. **Gap & handling:** *mission fit*: Jordan to decide if the domain motivates; do not invent a reason.

---

## #13: Acme Systems · Software Engineer, Distributed Storage
| | |
|---|---|
| Req / Link | ASY-DS-3 · https://jobs.example-greenhouse.io/acme-systems/asy-ds-3 *(sample/unverified)* |
| Level / Comp | $185k–$215k base posted · Greenhouse · Remote (US) |

**Fit Score: 62 / 100**: skills 11 · seniority 15 · comp 16 · location 20 · excitement 0.
**Why / fit:** Distributed-systems interest (E5, E6), but storage internals and C++ are true gaps. **Delta:** lead E6 → E5 → E2. **Gap & handling:** *C++ and storage engines*: not claimed. Honest line: "My distributed-systems work is at the service layer."

---

## #14: Acme Energy · Senior Software Engineer
| | |
|---|---|
| Req / Link | AEN-SE-18 · https://jobs.example-greenhouse.io/acme-energy/aen-se-18 *(sample/unverified)* |
| Level / Comp | $168k–$198k base posted · Workday · Hybrid, Austin (4d/wk) |

**Fit Score: 60 / 100**: skills 15 · seniority 15 · comp 12 · location 12 · excitement 6.
**Why / fit:** Solid backend fit, but 4 days a week in office. **Delta:** lead E2 → E3 → E6. **Gap & handling:** *RTO*: 4 days on-site is outside the stated work mode.

---

## #15: Acme Mobility · Staff Software Engineer, Growth
| | |
|---|---|
| Req / Link | AMO-GRW-2 · https://jobs.example-greenhouse.io/acme-mobility/amo-grw-2 *(sample/unverified)* |
| Level / Comp | $192k–$224k base posted · Ashby · Remote (US) |

**Fit Score: 58 / 100**: skills 10 · seniority 16 · comp 16 · location 16 · excitement 0.
**Why / fit:** Staff title, but the role is experimentation and front-end heavy. **Delta:** lead E1 → E2 → E9. **Gap & handling:** *front-end*: React ownership is a true gap. Don't stretch for it.

---

## Watch list: not applying yet (and why)
| Role | Why not now | Trigger to revisit |
|---|---|---|
| Acme Robotics · Engineering Manager, Platform | People-management title, off Jordan's IC track | If Jordan decides to pursue management |
| Acme Vision · Senior ML Engineer | Model training and serving are true gaps | After real ML infrastructure work |
| Acme Quantum · Principal Engineer | Principal is a stretch above target this cycle | After 1–2 Staff loops to calibrate |

---

## Cross-cutting interview prep (applies to every loop)
- **Assessment reality across the set:** every role has at least one **coding round**
  (LeetCode-style mediums; Go or Python allowed in most, `VERIFY:` #5 and #7 for Java). #1, #3, #4,
  #9 and #15 add a **system design** round at Staff depth; #3 and #10 add a **debugging** exercise.
  Mark `VERIFY:` the exact round mix in each recruiter screen.
- **Set-piece designs to rehearse:** D1 (deploy platform), D2 (payments latency), D3 (order routing).
  These three cover most system design prompts in the set.
- **Universal stat lines:** see `interview-packet/metrics-cheatsheet.md`.
- **Per-company conviction answers (mission/why) are written personally, never generated.**

## Application log
Apply packs are built only for the jobs Jordan commits to (the top two here); the rest stay leads
until they earn a pack. Each committed job tracks its own state in `jobs/<NN>-…/application-log.md`.

| Applied | Date | Req | Resume version | Referral | Status |
|---|---|---|---|---|---|
| | | AH-PLT-204 | Jordan-Rivera-Resume-Acme-Health.pdf | sample ex-teammate | apply pack built |
| | | AR-PAY-2207 | (build on commit) | sample alum | apply pack built |
| | | AC-INF-19 | (build on commit) | | lead |
| | | #4–#15 | (build on commit) | | lead |
