# Field Dimension Catalogs — starter packs for the Industry Analysis Framework

The framework (`industry-analysis-framework.md`) is field-agnostic; the *dimensions* and *synonym seeds*
are field-specific. This file gives a non-expert a starting point so the method runs without already
knowing a field's must-haves. **Adapt, don't obey** — these are seeds, and the actual must-haves come from
the user's real posting sample, not this list.

Each pack lists: **dimensions to measure** · **synonym-normalization seeds** (the hardest step for a
non-expert — terms to merge before counting) · **proof artifacts** the field tends to reward.

---

## Software / Security Engineering
- **Dimensions:** cloud platforms · IaC · languages · workload/container security · native vs 3rd-party
  tooling by layer (CSPM / SIEM / EDR / IdP / CI-CD) · architecture patterns (zero-trust, policy-as-code,
  detection-from-telemetry) · certs · comp · years · work-mode · geography.
- **Synonym seeds:** EKS/GKE/AKS → Kubernetes · CloudFormation/Terraform/Pulumi → IaC · Entra/AzureAD/Entra ID
  → one token · Defender/MDE → Microsoft Defender · GuardDuty/Security Hub → AWS-native detection.
- **Proof rewarded:** OSS contributions, public detections/rules, CVEs, conference talks, benchmarks, a blog.

## Product Design / UX
- **Dimensions:** tools (Figma, etc.) · design-systems maturity · prototyping fidelity · research methods ·
  domain (B2B/consumer) · motion/interaction · accessibility · collaboration model · seniority · work-mode.
- **Synonym seeds:** Sketch/Figma/XD → design tool · "design system"/component library/tokens → design systems ·
  user research/usability/discovery → research.
- **Proof rewarded:** a portfolio of **case studies** (problem → process → measurable outcome), not screenshots.

## Product Management
- **Dimensions:** product type (B2B/B2C/platform/growth) · analytics/SQL · experimentation (A/B) · roadmap/
  strategy scope · technical depth · domain · stakeholder/leadership scope · seniority.
- **Synonym seeds:** A/B/experimentation/optimizely → experimentation · SQL/Looker/Amplitude/Mixpanel → analytics ·
  PRD/spec/roadmap → product planning.
- **Proof rewarded:** **shipped-product narratives** with metrics moved; a portfolio of launches/case studies.

## Data / ML Engineering
- **Dimensions:** languages (Python/SQL/Scala) · warehouses (Snowflake/BigQuery/Databricks) · pipeline/
  orchestration (Airflow/dbt/Spark) · cloud · ML frameworks/MLOps · streaming · seniority.
- **Synonym seeds:** BigQuery/Snowflake/Redshift → cloud warehouse · Airflow/Dagster/Prefect → orchestration ·
  dbt/ELT/ETL → transformation.
- **Proof rewarded:** OSS, Kaggle/benchmarks, public pipelines/dashboards, writeups.

## Marketing / Growth
- **Dimensions:** channels (SEO/SEM/paid social/lifecycle) · martech stack · analytics/attribution · content ·
  ABM/demand-gen · industry · seniority · budget scope.
- **Synonym seeds:** GA4/Amplitude/attribution → analytics · HubSpot/Marketo/Pardot → marketing automation ·
  SEO/SEM/PPC → search.
- **Proof rewarded:** **campaign case studies** with results (pipeline, CAC, conversion), a portfolio/links.

---

## Worked non-security example (so generalization is demonstrated, not asserted)

**Product Designer, Senior, US-remote — a thin-data run (N≈45 → Directional mode).**
- **Demand:** Figma 41/45 (must-have) · "design systems" 33/45 (must-have) · prototyping 28 · "0→1" 19 ·
  accessibility 14 · motion 9 (nice-to-have).
- **Scarcity scan (proxy = requirement ÷ portfolio-evidence frequency):** *design-systems ownership* is
  demanded (33) but few candidates show **system-building** case studies → **high-demand + low-supply →
  LEAD on "I built/owned the design system,"** not "proficient in Figma" (table-stakes).
- **Disqualifier found:** 12/45 require "must include a portfolio link" → no portfolio = auto-reject; that's
  a gate, not a keyword.
- **Values read (deep set):** repeated "low-ego," "ambiguity," "craft" → values keyword set for the summary.
- **Map to user:** headline = design-systems ownership; urgent gap = publish one system case study (proof
  gap, not a skill gap); keyword buckets → recruiter-search ("Design Systems," "Figma"), ATS ("0→1,"
  "accessibility"), headline ("design-systems owner").
- **Mode note:** N=45 → everything labeled *indicative*; Fit-Score skills-match down-weighted; corroborated
  with one published design-hiring survey.

The point: identical method, different dimensions/proof — and the *scarcity scan* still produces the
positioning leverage ("lead on systems ownership"), exactly as it produces "GCP is the rare asset" in the
security worked example.
