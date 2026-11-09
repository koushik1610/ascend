# Metrics Cheat-Sheet, Jordan Rivera

> **🧪 FICTIONAL SAMPLE:** invented numbers for a demonstration persona. Applies the intake
> sanitization rule: round employer-internal operational numbers on anything sendable or said aloud;
> keep Jordan's own verifiable numbers exact; never name internal codenames.

---

## Say freely (exact, sendable / verifiable)
- **40+ services** moved onto the deploy platform (M1).
- **6 teams** adopted it (M2).
- **23 merged PRs** to a public open-source Go library (M11).
- **11 design docs** written and approved (M10).
- **2 meetup talks** on platform engineering (M14).
- **3–4 engineers mentored**; **0 direct reports** (state the honest framing, M9).
- **9 years** in software engineering: fintech, logistics, consulting.

## Round aloud / on paper (employer-internal → public band)
- Deploy lead time: say **"from ~3 days to under an hour"** (exact 3.1 days → 47 min, M3).
- Payments p99: say **"~60%"** (exact figure stays internal, M4).
- Volume: say **"~1.2M transactions a day"** (exact count stays internal, M5).
- Sev-1 incidents: **"14 → 5 a quarter"** is band-safe (a count trend, not volume, M6).
- Compute spend: say **"~35%"** (M7).
- CI time: **"41 → 14 minutes"** (M8).
- Recovery time: say **"under 20 minutes"** (M12).
- Order routing: say **"tripled peak throughput"** (M13).

## Never say
- The deploy platform's internal codename.
- Exact transaction counts or exact dollar savings.
- Exact headcount of any org.
- Current/prior compensation in a screen (anchor to target level instead).
- "Active" for the AWS cert: it's **expired (2024)**.

---

## Five 10-second stat lines (rehearse until automatic)
1. "I built a deploy platform that **6 teams** moved **40+ services** onto, cutting deploy lead time
   from **~3 days to under an hour**."
2. "I cut payments-API **p99 latency ~60%** at **~1.2M transactions a day**."
3. "SLOs and tracing brought **Sev-1 incidents from 14 to 5 a quarter**, with recovery **under 20
   minutes**."
4. "I built an order-routing service **0→1** in Go that **tripled peak throughput**."
5. "I'm an **IC multiplier**: I mentor **3–4 engineers** and run our design review, with **zero
   direct reports**. I'm targeting **Staff IC** scope."
