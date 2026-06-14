# Phase 4 — Job Search → `job-queue.md`

**Goal:** find **at least 15 real, currently-live jobs** matched to the user's profile and targeting,
rank them, and write a ranked queue with a per-job application plan. This is the spine the per-job
folders (Phase 5) are built from.

**Read first:** `workspace/<name>/intake.md`, `master-resume.md` (§2 summaries, §4 skills),
`resume-audit.md` (keyword set), `../templates/job-queue-template.md`,
`../reference/ats-and-keywords.md`.

---

## Find the jobs (live web research)
Use web search/fetch to find **15+ currently-open postings** that fit the user's roles, seniority,
location/work-mode, and company/industry targets from `intake.md`. Cast across:
- The user's named target companies (check their careers pages / ATS portals directly).
- Company *types* the user named (e.g., "Series B fintech," "AI-native startups," "FAANG-adjacent").
- Aggregators and ATS hosts (LinkedIn Jobs, the company Greenhouse/Lever/Ashby/Workday boards).
- Adjacent titles the user is qualified for but didn't name (surface 2–3 — sometimes the best fit is a
  title they didn't think to search).

For each posting capture: company, exact title, level, req ID + link, comp (if posted),
location/work-mode, ATS in use, and a **link-status field** (see the gate below). If you cannot reach
15 candidates in the user's exact lane, widen by one ring (adjacent titles, adjacent locations,
adjacent company tier) and say you did.

### Link-verification gate (be honest — do not assert verification you didn't perform)
Many job boards block automated fetches, paginate behind JavaScript, and rot within days. You **cannot
reliably confirm** a posting is open just because it appeared in a search result. So:
- For each link, **actually fetch it** and record the real outcome: `✅ verified-live` (fetched, 200,
  posting content present), `⚠ unverified` (couldn't fetch / blocked / JS-gated — link may still be
  good), or `✖ dead` (404/expired — drop or replace it).
- **Never count an `⚠ unverified` link as "verified."** Report two numbers: total candidates and the
  subset independently link-verified.
- Mark every entry with its status and the fetch date. Tell the user plainly: postings rot fast, so
  they must re-open each link before applying (the per-job `application-log.md` checklist enforces this).
- **Do not invent req IDs or links.** If you can't find a real URL for a role, describe the role and
  where to search for it, marked `⚠ find-the-link`, rather than fabricating one.

## Rank them
Score each on a transparent formula and order the queue by it:
`evidence fit (does the master resume prove the JD's asks?) × level match × comp × location feasibility
× shortlist probability`. State the formula and each job's rough score rationale. The #1 job should be
the highest (fit × feasibility), not just the highest comp.

## Write `job-queue.md` to the template
Per `../templates/job-queue-template.md`, each entry gets:
- The metadata block (req/link/level/comp/location/ATS).
- **Why it ranks here** (1–3 sentences).
- **Resume delta** — which master-resume bullets to lead with and any per-job emphasis (this is the
  pre-approved selection Phase 5 applies; cite master entry IDs).
- **Talking points** (3–5), **expected interview questions**, **gaps & honest handling**.
- Application logistics (ATS quirks, referral angle, anything to resolve in the recruiter screen).

Also write, at the top of the file:
- A **pre-application blockers** list (things to do before applying to anything — e.g., fix the
  resume's top ATS issue, apply the LinkedIn next-steps, run a referral sweep, ship any portfolio
  artifact the JDs reward).
- A **watch list** of jobs deliberately *not* pursued yet, with the trigger to revisit.
- A cross-cutting **interview-prep note** (coding-round reality across the set, set-piece designs to
  rehearse, the user's universal stat lines).

## Honesty & numbers
- Rank on real fit; if the user is under-qualified for a posting, say so and either drop it or mark it
  a stretch with honest handling. Never pad the count with jobs they can't credibly pursue.
- Apply the sanitization rule from `intake.md` to anything that will appear on a sendable surface.

## Verify
- ≥15 candidate entries, each with a link-status (`✅ verified-live` / `⚠ unverified` / `⚠ find-the-link`)
  and a real rank rationale. Report the count split: *N candidates, M independently link-verified.*
- No fabricated req IDs or URLs.
- Every "resume delta" cites master-resume entry IDs that actually exist.
- Locations/work-modes match the user's stated constraints (or are flagged as a stretch).

## Checkpoint
Give the user the ranked top 5 with one-line rationales, the **count split** (candidates vs.
link-verified), and the pre-application blockers. Be honest that unverified links must be re-opened
before applying. Let them re-order, drop, or add targets before Phase 5 builds the folders.
