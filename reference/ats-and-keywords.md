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
- **Recruiter search is the other half, and for most applicants it is the whole game.** Most ATS
  deployments do not auto-reject on content. They store every application and recruiters query them
  like a database: title, keywords, experience range. A résumé that does not contain the searched
  strings is not rejected, it is never surfaced. So the **headline/title and skills must contain the
  *searched* terms**, not vanity titles.
- **Match the posting's exact title in the headline.** Jobscan's analysis of 2.5M applications found
  résumés carrying the target job title were interviewed at about 10.6x the rate of those that did
  not. That is a vendor's correlational data, not an experiment, but the mechanism behind it is real:
  a title filter is a string match, and "Product Lead" does not match "Senior Product Manager." The
  per-job résumé's headline (`basics.label`) therefore starts with the posting's title **verbatim**.
  The honesty line: the headline states the role being applied for. Position titles under Experience
  stay exactly as held and are never renamed to match. `tools/lint_artifacts.py` checks the headline
  against the `JD title (verbatim):` line in the job's Delta Log (the `title` category).
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
5. **Place the differentiators in bullets, not just the skills line.** The *identification* of
   rare-but-in-demand terms is not done here. It is the **scarcity / white-space scan** in
   `industry-analysis-framework.md` (step 5 and the Demand-Scarcity quadrant it outputs). Do not
   re-derive it, and do not produce a second list from recall about "what the market wants" - an
   unsourced frequency claim is the kind of confident invention this system exists to prevent. Take
   that scan's output, keep the terms the user can honestly claim, and make sure **each one lands
   inside an achievement bullet**. A differentiating keyword sitting only in the skills list is the
   most common way real leverage gets wasted.

## Formatting rules (parser-safe)
- Single column. Standard headings (Summary, Experience, Skills, Education). No tables, text boxes,
  icons, headers/footers, graphics. Name and contact details go in the body: many parsers skip
  header/footer regions, so a name placed there leaves the record with no candidate attached.
- **No icons or emoji anywhere**, including the contact line. A phone glyph reaches the parser as an
  unknown code point or nothing. The linter flags any symbol glyph in `resume.json` (`scan`).
- **Never hide keywords** (white text, 1pt text, a pasted JD). AI-assisted screeners and the parse
  preview both expose it, and a flagged résumé is worse than an unmatched one. The LaTeX template
  cannot produce hidden text, which is one reason it is the default path.
- **PDF or DOCX.** A text-based PDF from the LaTeX template parses fine in current ATS. DOCX is the
  lower-risk upload when the portal asks for Word, or when its autofill preview mangles the PDF
  (common with older Taleo and iCIMS deployments). The test is the same for both: after upload, check
  the portal's parsed fields. If they are wrong, re-upload the other format. `08-export-pdf.md` builds
  the DOCX from the same source.
- Two pages is correct for 10+ years; page 1 carries the strongest material (screeners weight it).
- **One date format, everywhere: `Mon YYYY – Mon YYYY` / `Mon YYYY – Present`.** An ATS computes
  total experience from these ranges, and mixing `Jan 2019`, `2019-01`, and `January '19` across roles
  can make it compute the wrong total. Two-digit years give it nothing to compute from. The linter
  flags mixed or unparseable work dates (`scan`). Legal company name where verification matters.
- One master resume + a per-application keyword pass beats maintaining many divergent versions — which
  is exactly the Ascend model (master resume → select per job).

## Field note
For non-ATS-heavy paths (small companies, referral-first, creative fields with portfolio review), the
keyword discipline still helps recruiter search and LinkedIn findability, but the portfolio/work-sample
and the referral matter more — weight effort accordingly (the job folder's `interview-prep.md` says
which reality applies per target).
