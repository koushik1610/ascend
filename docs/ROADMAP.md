# S.P.I.D.E.R. — Roadmap

Where the project is going, and why. Built from a 5-surface market-research council (June 2026) on how
people actually use Claude/AI for job hunting — Reddit & forums, LinkedIn/X creators, Medium/Substack
guides, GitHub OSS tools, and commercial products. Items are scored for **impact × feasibility × fit
with the honesty/local model**. Everything here stays inside that model: **no fabrication, no auto-apply,
no scraping, no real-time interview copilots.**

> **Status legend:** 🟢 shipped · 🔵 in progress (this cut) · ⚪ planned

---

## The 6 signals (every panel, independently)

1. **Relationships beat volume.** Referrals convert ~**35×**; warm intros + targeted apps drive 60–80%
   of fills while online-app offers fell 73%→60%. The clearest gap: SPIDER drafts referral messages but
   can't **find** the contacts or **map your network**.
2. **"AI slop" is the #1 recruiter complaint.** ~35% of applicants paste the *same* ChatGPT answer;
   generic AI résumés are "the new typos." Validates the honesty gates; demands an active
   **de-genericizer**.
3. **A match score + a standing feed are table stakes.** Jobright/OphyAI/Resume-Matcher give a 0–100 fit
   number and a daily curated feed. SPIDER does on-demand search with no composite score.
4. **Interactivity beats documents.** The standout technique is *"interview me one question at a time"* —
   for achievement mining and live mock drills. Voice mock is a defensible category (Yoodli; Google
   Interview Warmup shut down April 2026).
5. **Daily cadence, not weekly.** The peer system (Aakash Gupta's Claude-Code "Job Search OS," 18 skills)
   centers on a ~20-min **daily briefing**.
6. **Honest + local + free is on-trend.** Mass auto-apply is dying (Sonara shut down; LinkedIn bans
   "human-impossible velocity"; 819 auto-apps → 0.6% interviews); stealth interview copilots ($148/mo,
   instant-DQ at Amazon) are an ethics wedge. Competitors charge $14–148/mo and **paywall exactly what
   SPIDER does free**: answer generation, contact finding, prep.

**Validated bets:** the bullet-DB "experience library," referral-first stance, no-auto-apply, and
privacy model are all confirmed correct. The whitespace is the **relationship + brand layer**,
**interactivity**, and a **fit-score / standing feed**.

---

## P1 — top 15 (highest impact × honest fit)

| # | Feature | What it is | Why (signal) | Effort | Status |
|---|---|---|---|---|---|
| 1 | **Warm-Network Mapper + Contact Finder** | From the `Connections.csv` in the LinkedIn export, surface warm contacts at each target company; identify likely recruiter/HM; rank by referral reachability | Referrals 35×; "Insider Connections" is Jobright's marquee paid feature; all 5 panels | M | 🔵 |
| 2 | **Networking CRM** | Track contacts, last-touch, coffee-chat status, dormant-thread nudges, thank-yous | Relationships rank #1; "dormant referral conversations" | M | ⚪ |
| 3 | **Explainable Job Match Score (0–100)** | Transparent composite per JD (skills/seniority/comp/keyword/excitement) **with reasoning** | Table stakes (Jobright, OphyAI, Resume-Matcher) | S–M | 🔵 |
| 4 | **Achievement-Mining Interview** | Conversational, one-question-at-a-time intake that extracts quantified wins into the bullet DB | Highest-value technique across blogs | M | ⚪ |
| 5 | **Interactive "Interview Me" Drill** | Live text drill: ask → wait → score → swap stories → ratchet difficulty | Recurs everywhere; current drill is static | M | ⚪ |
| 6 | **De-Genericizer / "Sounds-Human" Gate** | Score any résumé/cover/outreach for AI-tells; rewrite in the user's real voice before sending | #1 recruiter complaint; 80% of HMs view obvious AI letters negatively | M | ⚪ |
| 7 | **Salary Negotiation Studio** | Comp → leveling band (P25/50/75, base vs equity) → counter scripts + objection drills | Discrete high-ROI step others monetize | S | ⚪ |
| 8 | **Application Answer Sheet** | Reusable **varied** honest answers to common app questions (why-us, EEO, work-auth, salary, screeners) to copy-paste | The honest substitute for paywalled autofill; identical answers are a top tell | S | 🔵 |
| 9 | **Daily Briefing Mode** | ~20-min daily scan + rank + 3 actions, alongside weekly maintenance | Aakash OS signature; market cadence | S | 🔵 |
| 10 | **Standing Job-Match Feed** | Scheduled re-search → ranked, deduped, **verified + fit-scored** feed | #1 stickiness driver (Jobright/Sorce) | M | ⚪ |
| 11 | **Coffee-Chat / Info-Interview Kit** | Sub-400-char request scripts referencing the person's real content, 20-min ask, 70/30 agenda, 24h thank-you | Pre-engagement lifts acceptance to 40–50%; <400 chars = 22% reply lift | S | ⚪ |
| 12 | **Ghost-Detector + Follow-Up Engine** | Per-app aging timers → "follow up vs move on" nudges with drafted, spaced messages | Ghosting at a 3-year high | S | 🔵 |
| 13 | **JD → Résumé Diff View** | Side-by-side "what the JD asks vs what your résumé shows," exact missing phrases highlighted | Concrete; recurs in guides | S | ⚪ |
| 14 | **Résumé PDF Parser Intake** | Extract structured fields from an existing résumé PDF to seed the master résumé | Smooths onboarding; #1 bug class in OSS tools | M | ⚪ |
| 15 | **Personal-Brand Content Engine** | Honest post drafts mined from the bullet DB (wins/learnings/build-in-public), 80/20, 3–5/wk | Active brands get 47% more inbound, 8× engagement | M | ⚪ |

## P2 — next 15

| # | Feature | One-liner | Effort |
|---|---|---|---|
| 16 | Voice Mock Interview | Spoken practice + delivery scoring (pace, fillers, structure) — opt-in | L |
| 17 | Honest Job Aggregation | Pull from **official** Greenhouse/Lever/Ashby public JSON + RSS (not scraping) | M |
| 18 | ATS Parse-Preview | Show the stripped-text view of how an ATS reads the PDF | S |
| 19 | Multi-Format Export | DOCX + JSON beyond the ATS PDF | S |
| 20 | Signature STAR Bank + Reuse | Canonical 5–7 stories tagged to question types; auto-inject across surfaces | M |
| 21 | Adaptive Weak-Spot Study Loop | Track missed topics → map to concepts → targeted practice in difficulty order | M |
| 22 | Pipeline Analytics + Résumé A/B | Conversion funnel math + which résumé variant correlates with callbacks | S–M |
| 23 | Anti-Burnout Volume Coach | Conversion-math insight → nudge from spray to targeted/referral | S |
| 24 | LinkedIn Profile Score | Numeric Jobscan-style score (25+ checks) — repackages existing analysis | S |
| 25 | Recruiter-DM Responder Pack | Triage inbound recruiter messages → draft qualifying replies | S |
| 26 | Interviewer Dossier Depth | Interviewer background + recent company news per scheduled loop | M |
| 27 | Structured Post-Interview Debrief | Capture each asked Q, score the answer, feed fixes back into prep + bullet DB | S |
| 28 | Application-Similarity Guard | Flag near-identical résumés/answers across apps before sending | S |
| 29 | Cross-ATS Master-Profile Export | A field sheet to paste into Workday/Greenhouse — autofill's benefit, zero ToS risk | S |
| 30 | Portfolio / Work-Sample Packager | Case-study one-pagers for design/PM/DS roles | M |

## Deliberately NOT building (positioning, not omission)
Each "popular but wrong" behavior has an honest substitute already in P1/P2:
- **Real-time stealth interview copilot** → DQ'd at FAANG, ethics wedge → ship the offline pre-interview
  recall page ("cheat sheet, not cheating").
- **Browser auto-apply / autofill injection** → bans, ~0.6% conversion, Sonara died → ship #8 Answer
  Sheet + #29 Profile Export.
- **Scraping LinkedIn/Indeed** → velocity flags, proxy-fragile → ship #17 official ATS APIs/RSS.
- **Auto-messaging recruiters** → prohibited → **draft** (#1/#11/#25); the user sends manually.

## Design guardrail
Per the project's simplicity principle: most P1/P2 items are **on-demand commands or enhancements to
existing phases**, not new mandatory phases. The default run stays lean (~25–30 files); power features
are opt-in.

---

## Sources (selected)
Reddit/forums: [819-job AI experiment](https://jobsearchwithai.substack.com/p/i-let-ai-apply-to-819-jobs-for-me) ·
[AI-resume flood](https://www.aol.com/flood-ai-generated-resumes-causes-202147399.html) ·
[referrals 35× AMA](https://www.teamblind.com/post/referrals-35x-more-offers-networking-lessons-from-1000-jobseekers-ama-v2d1q5eh) ·
[ATS 2026](https://blog.theinterviewguys.com/ats-resume-optimization/).
Creators: [Aakash Gupta — Job Search OS](https://www.news.aakashg.com/p/job-search-os) ·
[reverse recruiting](https://hrexecutive.com/15k-to-land-a-job-what-hr-can-make-of-reverse-recruiting/) ·
[LinkedIn outreach scripts](https://www.senseicopilot.com/blog/linkedin-outreach-scripts-2026-proven-messages-that-actually-get-replies) ·
[personal brand](https://connectsafely.ai/articles/build-personal-brand-linkedin-authority-guide-2026).
Guides: [Claude job-search workflow](https://findskill.ai/blog/claude-cowork-job-search-workflow/) ·
[ask AI to interview you](https://gaiinsights.substack.com/p/ask-ai-to-interview-you-to-create) ·
[using Claude to get interviews](https://medium.com/@shrikulk20/using-claude-to-get-interviews-d8c47dbbfcdf).
OSS: [Reactive-Resume](https://github.com/AmruthPillai/Reactive-Resume) ·
[Resume-Matcher](https://github.com/srbhr/Resume-Matcher) · [JobSpy](https://github.com/speedyapply/JobSpy) ·
[OpenResume](https://github.com/xitanggg/open-resume).
Commercial: [Jobright](https://jobright.ai/) · [Simplify review](https://jobright.ai/blog/simplify-copilot-review-2026-features-pricing-and-top-alternatives/) ·
[Jobscan auto-apply](https://www.jobscan.co/blog/auto-apply-job-tools/) · [Levels.fyi](https://www.levels.fyi/) ·
[Yoodli](https://resumehog.com/blog/posts/yoodli-review-2026-is-this-ai-interview-coach-worth-it.html).
