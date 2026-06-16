# S.P.I.D.E.R. — Roadmap

Where the project has been, where it's going, and why. The forward-looking backlog is built from a
5-surface market-research council on how people actually use Claude/AI for job hunting — Reddit &
forums, LinkedIn/X creators, Medium/Substack guides, GitHub OSS tools, and commercial products. Items
are scored for **impact × feasibility × fit with the honesty/local model**. Everything stays inside that
model: **no fabrication, no auto-apply, no scraping, no real-time interview copilots.**

> **Status legend:** 🟢 shipped (version noted) · ⚪ planned

---

## Version lineage — what shipped when

| Version | Theme | What it added |
|---|---|---|
| **0.1.0** | The pipeline | Intake → LinkedIn analysis (HTML + 10 next steps) → master résumé → 15+ job search → per-job folders → interview packet → `start-here.html` navigator; on-demand export/maintenance/deep-prep; resumability (`.spider-state.json`); privacy model; a fictional worked example; honest verified/unverified job-link framing. |
| **0.2.0** | Simpler + outcome-targeted | **Tiered job folders** (CORE apply pack now, deep prep on demand) so a first run is ~25–30 files, not ~100; résumé audit folded into the master résumé; default order 1→3→4→6→5→7. Navigator **weekly action loop + funnel scoreboard**, **referral-first hard gate**, mock-interview drill. Modern README + hand-authored SVG banner. |
| **0.3.0** | P1 first cut (research-driven) | **Explainable Fit Score 0–100** (P1 #3), **Warm-Network Mapper** from your `Connections.csv` (#1), **Application Answer Sheet** (#8), **Daily Briefing + ghost-detector follow-ups** (#9 + #12). `docs/ROADMAP.md` itself. |
| **0.4.0** | Graphical console | **`/spiderui`** — a local Jarvis-style browser wizard (Python-stdlib server, native folder picker, live progress, optional daily-brief cron that auto-detects claude/gemini/codex). |
| **Unreleased** | v1.0 hardening | Server **CSRF / DNS-rebinding hardening** (verified live); **beta labels + Known Limitations** honesty pass; dead-link fix; **smoke-test harness + CI**. 2026-06-15 **council review** (architecture · competitive · security) documented; the two new security gates (**SEC-CRIT-1 prompt-injection**, **SEC-CRIT-2 reader XSS**) plus SEC-HIGH-3 **fixed 2026-06-16** and smoke-tested. (See *Path to v1.0* + *Council review*.) |

---

## Path to v1.0

**Definition of Done (gate the 1.0 tag on all):** ① one real end-to-end run on real LinkedIn data,
archived as proof, honesty gates verified · ② each shipped on-demand op run once or labeled beta ·
③ `/spiderui` security-hardened + run end-to-end once, or beta · ④ smoke harness + CI green · ⑤ no dead
links, phase list consistent · ⑥ README/CHANGELOG represent maturity honestly · ⑦ tag `v1.0.0`.

**Blockers (from the v1.0 readiness council):**

| # | Blocker | Status |
|---|---|---|
| 1 | Local-server CSRF / DNS-rebinding hardening | 🟢 done (Unreleased) — Host allowlist + per-session token + Origin check, verified live |
| 4 | Dead `resume-audit.md` link + stale prompt refs | 🟢 done (Unreleased) |
| 6 | Honest maturity labels (beta surfaces, Known Limitations) | 🟢 done (Unreleased) |
| 5 | Smoke-test harness + CI | 🟢 done (Unreleased) — `tests/smoke.py`; CI workflow added, push needs the `workflow` OAuth scope |
| 7 | **Stored XSS in the `/view` Markdown reader** (SEC-CRIT-2 below) | 🟢 done — scheme allow-list + nonce CSP, smoke-tested |
| 8 | **Prompt-injection hardening of the agent layer** (SEC-CRIT-1 below) | 🟢 done — quarantine policy + per-prompt banners + tightened deny-list, smoke-tested |
| 2 | **One real end-to-end run on real data** | ⬜ **pending — the remaining gate** (needs a real LinkedIn export) |

> Both security gates were surfaced by the 2026-06-15 council and verified against source. See
> [**Security review**](#security-review--council-2026-06-15) for the findings and fixes. They gate the
> 1.0 tag because `/spiderui` runs untrusted web content through a pre-approved, broadly-permissioned agent.

**Should-fix before 1.0 (not hard gates):** ✅ done. The hardening pass covered ready-flag-clears-on-pickup,
`read_status` error surfacing, the `relative_to` traversal guard, and console error handling. The
2026-06-16 pass closed the rest: the **phase run-order is single-sourced** (canonical in
`00-orchestrator.md`; `CLAUDE.md` + `spiderui.md` restate it and `tests/smoke.py` asserts all three match);
the **folder picker returns a status** (`ok`/`cancelled`/`unavailable`/`error`) so the console shows a
*"no native picker — paste the path"* hint on Linux without `zenity`/`kdialog`; and the **daily-brief
wrapper gained a `--check` self-test** (agent detection + prompt assembly, no agent call) wired into the
smoke suite — full end-to-end verification still rides along with the one real run (gate #2).

---

## Council review — 2026-06-15 (architecture · competitive · security)

Three review panels ran against the live repo: **Architecture/Production**, **Competitive Functionality**,
and **Security**. Where a security claim could be checked against source, it was verified (file:line noted).

| Dimension | Composite | Read |
|---|---|---|
| Functionality vs. peers | **65 / 100** | Unusually complete *concept*; thin on traction + a few table-stakes features |
| Production-readiness | **52 / 100** | Excellent local OSS tool; large lift to become a *product* |
| Security | **44 / 100** | Solid web-server hygiene; **two CRITICALs** in the agent/renderer layer, both verified |

### Security review

> **Status legend:** 🔴 critical · 🟠 high · 🟡 medium · ✅ already mitigated · ⬜ open · 🟢 fixed

| ID | Sev | Finding | Evidence | Fix | Status |
|---|---|---|---|---|---|
| **SEC-CRIT-1** | 🔴 | **Indirect prompt injection → exfiltration / RCE.** The pipeline fetches arbitrary job pages + reads the résumé, then runs with **pre-approved** Write/Bash/WebFetch and *no human gate*. A malicious posting can exfiltrate PII via all-domain `WebFetch` or abuse `Bash(node *)` (≈ arbitrary code execution). | Zero injection guidance in `prompts/` (grep); `Bash(node *)` + bare `Read` + `WebFetch` in `.claude/settings.json` | Canonical `reference/untrusted-content-policy.md` + a binding rule in `CLAUDE.md` + a 🔒 banner on every ingesting prompt (01/04/09/10/11/13); deny-list now blocks `node`/`deno`/`bun`/`ruby`/`perl`/`php`/`osascript`/`python3 -c`/`npm`/`npx`/`pip` and `nc`/`ssh`/`scp`/`sftp`/`telnet`; unattended daily-brief restates the quarantine inline. | 🟢 **fixed** (smoke-tested) |
| **SEC-CRIT-2** | 🔴 | **Stored XSS in the `/view` Markdown reader.** The link regex emits `<a href="$2">` with **no scheme sanitization**, so `[x](javascript:…)` in a résumé/JD executes in the localhost origin and can read `workspace` files. | `ui/server.py:219` | Scheme allow-list in the renderer (`http`/`https`/`mailto`/relative only; others render inert) **+ a strict nonce-based `Content-Security-Policy`** on `/view` (`default-src 'none'`, `script-src 'nonce-…'`, `connect-src 'none'`) so even a slipped payload can't execute or phone home. | 🟢 **fixed** (smoke-tested) |
| **SEC-HIGH-3** | 🟠 | **Inherited `settings.json` is too broad.** Bare `Read`, all-domain `WebFetch`, and `Bash(node *)` ship committed, so every cloner inherits an over-permissioned agent by default. | `.claude/settings.json` | Tightened **in place** (kept committed so `/spiderui` still runs uninterrupted): dropped `Bash(node *)`, denied the full set of RCE interpreters/package-managers/exfil tools, broadened the secret deny-list. `Read` stays broad *by design* (must read a résumé/export wherever the user points) with the secret deny-list as guard; `WebFetch` stays broad (career sites are arbitrary) paired with the CRIT-1 quarantine. | 🟢 **fixed** (tightened in place) |
| **SEC-MED-4** | 🟡 | **Session token is injected into the page**, so an XSS (CRIT-2) escalates to driving the API — e.g. installing a cron job. | `ui/index.html` token inject | Largely closed: the CRIT-2 nonce-CSP blocks the script execution that this depended on. Residual: token is still in the page DOM. | 🟢 mitigated (via CRIT-2) |
| **SEC-MED-5** | 🟡 | **No per-slug authorization on `/view`** — any workspace slug is viewable by the session. | `_serve_md_reader` | Acceptable single-user; revisit if multi-user | ⬜ open (accepted for single-user) |
| **SEC-LOW-6** | 🟡 | **Daily-brief cron runs unattended** with the same broad perms. | `ui/run-daily-brief.sh` | Wrapper now restates the quarantine inline (CLIs may not load `CLAUDE.md` headless) and relies on the tightened deny-list. | 🟢 mitigated (via CRIT-1) |
| SEC-OK-1 | ✅ | CSRF / DNS-rebinding on the local server (Host allowlist + per-session token + Origin check, no CORS, path-traversal guard) | `ui/server.py`, `tests/smoke.py` | — | mitigated (Unreleased) |

**Remediation — landed 2026-06-16 (was the documented order):** (1) CRIT-2 — renderer scheme allow-list +
nonce CSP; (2) HIGH-3 — dropped `Bash(node *)`, hardened the deny-list; (3) CRIT-1 — quarantine policy +
per-prompt banners + hardened unattended brief. All guarded by new `tests/smoke.py` checks. **Remaining
security work:** SEC-MED-5 (per-slug auth) is accepted for the single-user model; revisit at multi-user.

### Competitive read (vs. GitHub peers)

SPIDER uniquely **combines** four things no peer does together: the end-to-end pipeline, real interview
prep + mock drills, the warm-network referral mapper (no scraping — mines the `Connections.csv` you
already exported), and explicit honesty gates. It **lacks** four table-stakes items, tracked in the
backlog: traction/community, a live-preview résumé builder, **DOCX/JSON export** (only Markdown→PDF today —
P2 #19), and real job aggregation (P2 #17). Peers referenced: Reactive-Resume (~35k★), AIHawk (~30k★),
Resume-Matcher (~9k★), OpenResume (~8.6k★), JobSpy (~3.6k★).

### Path to a production *product* (beyond the v1.0 local tool)

The panels converged on a phased path — don't jump straight to SaaS:

- **v1.0 — trustworthy local tool (closest).** Land the security fixes above, then the remaining gate:
  one real end-to-end run on real data. Add DOCX/JSON-Resume export, a published demo, push `ci.yml`.
- **v1.5 — engine independence + packaging.** Embed the **Claude Agent SDK** so output quality is
  reproducible instead of "whatever CLI you have"; package via `pipx`/`npx` (later Tauri); add **eval
  tests** that score sample outputs so prompt edits can't silently regress; structured logging.
- **v2.0 — product.** Multi-user/auth, an optional hosted mode (which reintroduces the whole
  exfiltration surface at scale — treat as a fresh security review), Windows scheduling parity, and a
  legal review (LinkedIn ToS, résumé-data handling; the "AI applicant" ethics are already covered by the
  honesty gates).

---

## The 6 signals behind the backlog (every research panel, independently)

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

## P1 — top 15 (highest impact × honest fit) — *5 shipped (v0.3.0), 10 pending*

| # | Feature | What it is | Why (signal) | Effort | Status |
|---|---|---|---|---|---|
| 1 | **Warm-Network Mapper + Contact Finder** | From the `Connections.csv` in the LinkedIn export, surface warm contacts at each target company; identify likely recruiter/HM; rank by referral reachability | Referrals 35×; "Insider Connections" is Jobright's marquee paid feature; all 5 panels | M | 🟢 v0.3.0 |
| 2 | **Networking CRM** | Track contacts, last-touch, coffee-chat status, dormant-thread nudges, thank-yous | Relationships rank #1; "dormant referral conversations" | M | ⚪ |
| 3 | **Explainable Job Match Score (0–100)** | Transparent composite per JD (skills/seniority/comp/keyword/excitement) **with reasoning** | Table stakes (Jobright, OphyAI, Resume-Matcher) | S–M | 🟢 v0.3.0 |
| 4 | **Achievement-Mining Interview** | Conversational, one-question-at-a-time intake that extracts quantified wins into the bullet DB | Highest-value technique across blogs | M | ⚪ |
| 5 | **Interactive "Interview Me" Drill** | Live text drill: ask → wait → score → swap stories → ratchet difficulty | Recurs everywhere; current drill is static | M | ⚪ |
| 6 | **De-Genericizer / "Sounds-Human" Gate** | Score any résumé/cover/outreach for AI-tells; rewrite in the user's real voice before sending | #1 recruiter complaint; 80% of HMs view obvious AI letters negatively | M | ⚪ |
| 7 | **Salary Negotiation Studio** | Comp → leveling band (P25/50/75, base vs equity) → counter scripts + objection drills | Discrete high-ROI step others monetize | S | ⚪ |
| 8 | **Application Answer Sheet** | Reusable **varied** honest answers to common app questions (why-us, EEO, work-auth, salary, screeners) to copy-paste | The honest substitute for paywalled autofill; identical answers are a top tell | S | 🟢 v0.3.0 |
| 9 | **Daily Briefing Mode** | ~20-min daily scan + rank + 3 actions, alongside weekly maintenance | Aakash OS signature; market cadence | S | 🟢 v0.3.0 |
| 10 | **Standing Job-Match Feed** | Scheduled re-search → ranked, deduped, **verified + fit-scored** feed | #1 stickiness driver (Jobright/Sorce) | M | ⚪ |
| 11 | **Coffee-Chat / Info-Interview Kit** | Sub-400-char request scripts referencing the person's real content, 20-min ask, 70/30 agenda, 24h thank-you | Pre-engagement lifts acceptance to 40–50%; <400 chars = 22% reply lift | S | ⚪ |
| 12 | **Ghost-Detector + Follow-Up Engine** | Per-app aging timers → "follow up vs move on" nudges with drafted, spaced messages | Ghosting at a 3-year high | S | 🟢 v0.3.0 |
| 13 | **JD → Résumé Diff View** | Side-by-side "what the JD asks vs what your résumé shows," exact missing phrases highlighted | Concrete; recurs in guides | S | ⚪ |
| 14 | **Résumé PDF Parser Intake** | Extract structured fields from an existing résumé PDF to seed the master résumé | Smooths onboarding; #1 bug class in OSS tools | M | ⚪ |
| 15 | **Personal-Brand Content Engine** | Honest post drafts mined from the bullet DB (wins/learnings/build-in-public), 80/20, 3–5/wk | Active brands get 47% more inbound, 8× engagement | M | ⚪ |

**Up next (post-1.0):** the highest-leverage pending P1 items cluster in the **relationship + interactivity**
layers the research ranked first — #2 Networking CRM, #4 Achievement-Mining Interview, #5 interactive
"Interview Me" drill, #6 De-Genericizer, #7 Salary Negotiation Studio. These come *after* the v1.0 gate
(one real run); the project freezes scope for 1.0 rather than adding surface.

## P2 — next 15 (planned)

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
