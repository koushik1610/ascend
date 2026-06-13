# ATS, Keywords & Screening Intelligence (2026)

How application screening actually works now, and how the system makes a resume/profile survive it.
Field-agnostic — the *method* is universal; the *keywords* come from the user's target roles.

## How screening works in 2026
- **~98% of large employers run an ATS;** a large share of resumes never reach a human. Getting past
  the filter is a precondition, not the whole game.
- **The big shift is LLM/semantic screening.** Tier-1 employers have largely moved from Boolean
  keyword matching to AI evaluation that judges *intent, depth, and scope* — it can tell "used X" from
  "owned and scaled the X that did Y." Consequences:
  - Keyword **stuffing is detectable and penalized.** Keyword **coverage in context** still wins:
    15–25 role-relevant terms embedded in achievement bullets (contextualized mentions rank ~40%
    higher than skills-list-only).
  - Semantic screeners reward a **coherent narrative**: title trajectory, growing scope, and
    consistency between the summary, the bullets, the skills, and the LinkedIn profile.
  - **AI-generated-sounding text is a flag.** Uniform bullet rhythm and generic phrasing read as slop
    to both AI and humans. Specific nouns, real numbers, and varied sentences are the antidote.
- **Recruiter search is the other half.** Recruiters filter by exact job title and endorsed skills
  before any match runs — so the **headline/title and skills must contain the *searched* terms**, not
  vanity titles.
- **Knockout questions** (years of experience, certifications, work authorization, location) are hard
  gates. An expired cert claimed as active fails verification; an unanswered required filter loses.

## ATS families (observed behaviors)
| ATS | Notes |
|---|---|
| **Workday** | Strictest parser. Single column, standard headings, no tables/text-boxes. Expect a re-enter-your-resume form; keep a plain-text copy. |
| **Greenhouse** | Clean parser; recruiters review in arrival order — **apply early**. Custom questions carry real weight. |
| **Lever / Ashby** | Modern parsers, lighter keyword dependence, human review sooner. |
| **Eightfold / AI-matching layers** | Match against the *whole* profile — LinkedIn and resume must agree, or discrepancies hurt the match score. |
| **Proprietary (big tech)** | Heavy semantic ranking + recruiter search. Exact-phrase title/skill matches in the headline/summary materially improve recall. |

## Building the keyword set (per user)
1. Take the user's target roles/titles from `intake.md`.
2. Pull 5–10 real, current postings for those roles. Extract the terms that repeat across them: the
   **Tier-1** keywords (in nearly every posting — must appear, verbatim, in context) and **Tier-2**
   keywords (differentiating, lower-competition — high signal where the user has them).
3. Cross-check against the user's evidence (resume + LinkedIn): mark each keyword **present**,
   **missing-but-claimable** (evidence exists, resume doesn't say it — fix at the master-resume source),
   or **true gap** (cannot honestly claim — honest handling).
4. Distribute the claimable keywords across achievement bullets in context — never a stuffed list.

## Formatting rules (parser-safe)
- Single column. Standard headings (Summary, Experience, Skills, Education). No tables, text boxes,
  icons, headers/footers, graphics. PDF unless the portal demands DOCX.
- Two pages is correct for 10+ years; page 1 carries the strongest material (screeners weight it).
- Standard dates (`Feb 2022 – Present`); legal company name where verification matters.
- One master resume + a per-application keyword pass beats maintaining many divergent versions — which
  is exactly the SPIDER model (master resume → select per job).

## Field note
For non-ATS-heavy paths (small companies, referral-first, creative fields with portfolio review), the
keyword discipline still helps recruiter search and LinkedIn findability, but the portfolio/work-sample
and the referral matter more — weight effort accordingly (the job folder's `interview-prep.md` says
which reality applies per target).
