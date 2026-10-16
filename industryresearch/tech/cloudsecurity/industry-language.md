# Industry language: tech / cloud security

**Built:** 2026-10-16
**Industry:** tech · **Domain:** cloudsecurity
**Sample:** 49 LinkedIn profiles read in full (experience detail pages), plus one security-tooling job posting
**Scope:** Staff, Principal, Senior Staff and Technical Lead + Manager engineers in cloud security, detection, product security and AI security tooling, and the managers, heads and directors of cloud security they report to or became.

This file says how people at this level **phrase** true things. It never says what is true about a user. Facts always come from the user's own evidence (`workspace/<name>/master-resume.md` and its sources). Built and refreshed by `prompts/26-industry-language.md`.

Profiles are anonymized: no names, no employer attached to an individual career path, and phrases are short fragments or patterns rather than copied bullets.

---

## 1. The sample

| Group | Count | Employer mix |
|---|---|---|
| Staff / Senior Staff (cloud, detection, product security) | 22 | Fintech, payments, rideshare, comms API, data cloud, social, streaming, HR SaaS, security vendors, AI cloud |
| Principal / Senior Principal | 16 | Hyperscalers, retail, CDN, design software, enterprise open source, research firm, AI startups |
| Technical Lead + Manager (TLM) at Staff level | 3 | Hyperscaler, social, consulting |
| Managers, Senior Managers, Heads, Directors, SVPs | 8 | Healthcare, insurance, banks, payments fintech |

Searches used: principal cloud security engineer · staff cloud security engineer · staff security engineer AI cloud · principal security engineer AWS · cloud security engineering manager · head of cloud security · staff security engineer detection cloud · principal security engineer AI security tooling.

**Career paths seen** (patterns, not people):

- Staff → Principal → Senior Manager → Director → back to Staff IC in AI security.
- Principal → Senior Manager in about 15 months.
- Lead engineer → Head of Cloud Security Engineering in under 2 years, growing a team from zero.
- Staff TLM → Senior Engineering Manager → Senior Staff → Principal.
- Project Lead → Cloud Security Architect → Manager. "Lead" and "Architect" titles are the usual stepping stones.
- CISO or Director → Principal IC in AI security (seen twice).

Moving into management and back to IC is a normal ladder in this field, not a step down.

---

## 2. What the strong profiles have in common

About a third of the Staff and Principal profiles had **no description at all**. At this level the title, company and tenure carry the profile. Of the ones that wrote something, about a dozen were clearly strong, and they did five things:

1. **Name the scope before the deed.** company-wide, org-wide, "for the entire detection and response organization", "across every engineering team". The scope is the level signal.
2. **Say what changed for other people.** adopted across the organization, adopted as the standard across product orgs, teams now ship into it without help. Adoption by others is the Staff proof.
3. **Name a class of risk removed, not a count of findings.** eliminating an entire class of external attack surface, eliminating a primary attack vector, reducing top-severity risks a tier.
4. **Show the role inside the project.** Technical lead for, Project lead for, Design architect for, Creator and maintainer of, Security lead for. This answers "what did you do" without "helped" or "contributed".
5. **Attach outside proof to the work it came from.** "This led to a conference talk", "an industry first", "open sourced as", "patent". The proof sits on the bullet, not in a separate section.

The weak ones did the opposite:

- Keyword paragraphs (IAM, device trust, infra-as-code, posture management, secrets, multi-cloud…) with no deed or outcome.
- Generic "Label: sentence" bullets ("Strategic Advisory: partnered with executive leadership…") that fit anyone.
- Large percentages on every line (99.99% uptime, 95% of incidents eliminated, 92% fewer vulnerabilities). Readers treat these as padding, and Ascend's honesty policy blocks unsourced ones anyway.
- Duty lists in the present tense for old jobs ("Manage…", "Administer…").

---

## 3. Bullet anatomy

One template per bullet, one level signal per bullet.

| Template | Shape | Use for |
|---|---|---|
| **Scope, deed, adoption** | [Scope] + [built or led X] + [who adopted it] | Platforms and programs other teams use |
| **Class elimination** | [Built X] to [find and fix Y] across [scope], removing [a class of risk] | Detection, guardrails, identity |
| **Role in project** | [Technical lead / Design architect / Creator and maintainer] of X, which [does Y] for [users] | Work where the team was bigger than you |
| **Decision rights** | Own [decision] for [scope]: decide [what ships / when it is enforced / what retires] | Ownership at Principal |
| **Lifecycle** | Took X from prototype to production and own its [correctness / false-positive rate / reliability] | Security tooling roles |
| **Translation** | Turned [findings] into [concrete remediation steps] that [non-security engineers] can act on | Partnering and enablement |
| **Framing line, bullets, stack line** | One sentence of mandate, 3 to 5 bullets, then "Technologies: …" | LinkedIn experience sections, not the résumé |

**Tense:** present for the current role ("Own", "Run", "Lead"), past for earlier roles. 41 of 49 profiles did this.

**Numbers:** at most one per bullet, and only ones the user can source. Strong profiles used scope numbers (accounts, teams, endpoints, engineers mentored) more often than outcome percentages.

---

## 4. Level vocabulary

**Staff signals**
org-wide · company-wide · across every engineering team · adopted by · the standard for · technical lead for · set the direction for · defined the roadmap for · partnered with platform, infrastructure and application teams · mentored · unblocked · operationalize detection at scale · durable detections · self-service

**Principal signals**
own [decision] · established the function from the ground up · where no standard existed · defined the strategy for · standards adopted across engineering · represent the company on or at · creator and maintainer · industry first · enterprise-wide · trusted advisor to engineering · balance risk against productivity

**Manager / Head signals**
grew the team from N to M · led the case for (investment, headcount, a new function) · defined KPIs, objectives and roadmaps · quarterly planning (OKRs) · security debt and backlog · obtained headcount from executives · built a training program · developed engineers into leads · budget · multiple stakeholders · threat-informed priorities

**Bridge titles between Staff and manager:** Technical Lead + Manager (TLM) · Lead Cloud Security Engineer · Global Cloud Security Lead Engineer · Project Lead · Secure Architecture Team Lead · Security Lead

**Leading without reports.** A user with no direct reports uses the Staff and Principal signals that describe influence without a reporting line: decision rights, set the roadmap, defined the metrics, trained partner teams, technical lead for. Never use a manager verb that implies reports the user did not have.

---

## 5. Verb bank

**Use:** own, run, lead, set, define, decide, design, build, ship, enforce, retire, find, fix, catch, close, route, gate, block, benchmark, measure, audit, train, partner, translate, unblock, adopt, standardize, operationalize, establish, author, maintain.

**Avoid:** see `.claude/banned-words.md`. The profiles leaned on several of them (spearheaded, leveraged, utilized, empowered, orchestrated) plus "helped", "contributed to" and "responsible for". Replace each with the verb for what the person actually did.

---

## 6. Noun phrases worth borrowing

Use at most one per bullet, and only where the user's evidence supports the fact underneath.

**Cloud posture and guardrails:** security baselines · mandatory controls · enforceable policy · secure-by-design guardrails · secure-by-default · continuous compliance · policy-driven remediation · posture management (CSPM) · misconfiguration classes · exception lifecycle · accepted risk with an owner and an expiry

**Identity:** least privilege · privilege-escalation paths · cross-account role assumption · static credentials removed · non-human identity (NHI) · workload identity · identity-centric controls · toxic combinations

**Detection:** detection-as-code · detection logic · correlation of existing signals · configuration-state detection · detection correctness · false-positive rate · findings that reach an owner · alert routing · operationalize detection · coverage against MITRE ATT&CK · durable detections paired with upstream controls

**AI for security work:** AI-assisted or AI-augmented (vary it) · agentic workflows · human approval on every write · bounded autonomy · deterministic gates where a decision touches access · benchmarked against ground truth · "build with AI and secure AI systems" (the two-sided framing, on 4 profiles) · AI enablement · MCP integrations

**Programs and influence:** program · roadmap · metrics that resist gaming · adopted by partner teams · taught or trained · internal technical talks (say internal)

---

## 7. Keyword clusters

36 of the 49 profiles had any description. Counts are profiles whose current or most recent senior role mentions the cluster, so terms that only appear in older roles are undercounted.

| Cluster | Terms | Profiles |
|---|---|---|
| Cloud platforms | AWS, GCP, Azure, multi-cloud | nearly all 36 |
| AI security / AI for security | agentic, LLM, MCP, AI enablement, AI security strategy, Bedrock | 17 |
| Detection and response | detection engineering, threat hunting, SIEM, SOAR, MITRE ATT&CK, MTTR/MTTD | 15 |
| Identity | IAM, least privilege, zero trust, NHI | 12 |
| Compliance | NIST 800-53, CIS, SOC 2, PCI, ISO 27001 | 10 |
| CI/CD and supply chain | CI/CD, GitHub Actions, SAST/DAST/SCA, supply chain, secrets lifecycle | 8 |
| IaC and policy | Terraform, policy-as-code, CloudFormation, OPA | 7 |
| Kubernetes and containers | Kubernetes, EKS/GKE, container runtime | 4 |
| Observability | ELK, Grafana, Prometheus, Splunk | 2 (more in older roles) |

AI is the most common cluster after the cloud platforms themselves, and it now appears in titles at every level ("AI Cloud Security Engineer", "Head of Cloud & AI Security", "Staff Security AI Engineer").

Each user maps their own evidence against these clusters in `workspace/<name>/industry-fit.md`, never in this file.

---

## 8. Posting language worth keeping (security tooling roles)

From a 2026 security-tooling posting for a first dedicated security hire. Useful framing wherever it is true for the user:

- turn raw signal into actionable security insight
- own the full lifecycle of security tooling from prototype to production, including reliability and false-positive rates
- translate findings into specific remediation steps for engineers without deep security backgrounds
- how core cloud services (IAM, VPC, security groups) are commonly misconfigured or attacked
- use AI/LLM tools to build analysis or automation tooling (code review, log analysis, anomaly detection, classification)
- build tools, not just configure existing ones

---

## 9. Rewrite rules for Ascend (Phases 3, 5 and 18 read these)

1. **Scope first.** Open each flagship bullet with who it covers or the decision owned.
2. **One adoption or class-removed clause per flagship bullet.** If the user's evidence has neither, it is not a flagship.
3. **Role-in-project noun** when others did part of the work.
4. **Lifecycle words for tooling bullets:** prototype to production, correctness, false positives, findings that reach owners.
5. **Translation clause for partner-facing work.**
6. **Two-sided AI framing** in summaries when true: builds AI tooling for security work and designs the controls that keep it safe.
7. **Present tense for the current role, past tense for earlier ones.**
8. **No keyword paragraphs on the résumé.** Keywords go in the skills line, once each.
9. **Leadership without reports:** decision rights, roadmap, metrics, training. No manager verb that implies reports.
10. **Numbers:** scope over outcome percentages, at most one per bullet, all sourced.

---

## 10. Refresh

Phase 26 rebuilds this file when it was not built in the current calendar month. Keep the section numbering so prompts can cite sections.
