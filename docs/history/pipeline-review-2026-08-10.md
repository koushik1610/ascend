# Résumé pipeline review, 2026-08-10

A four-step résumé system was proposed for adoption into Ascend: an ATS diagnostic, a recruiter
keyword scan, an XYZ bullet rewrite, and a LaTeX assembly step. This is the review, the verdict per
step, and what actually shipped.

**Short version.** Three of the four steps already existed in Ascend, in most cases more strictly than
proposed. One of them, taken literally, would have broken the system's core rule. The fourth, LaTeX,
was a real gap and is now the default renderer. Two small pieces of rigor from the proposal were worth
taking and were taken.

---

## Step 1, the ATS diagnostic: already covered, two ideas worth taking

`prompts/02-resume-audit.md` already produced every section the proposal asked for.

| Proposed | Where it already lived |
|---|---|
| ATS-killers (tables, columns, headers, graphics, fonts, dates) | §2 ATS pass/fail, checked against `reference/ats-and-keywords.md` |
| Section-by-section weakest line | §3 the 6-second scan, plus §6 bullet rewrites |
| Missing signals for the target role | §4 keyword gap table, plus §5 trend leverage |
| Top 5 fixes ranked, with a before and after | §7 prioritized fix list, §6 shows before to after |

Ascend's version also carries a 0 to 100 parseability score with a transparent rationale, a knockout-risk
check (years, certs, work authorization), and honest-gap handling, none of which the proposal had.

**Taken:** two rules that were genuinely absent.
1. **Quote the user's actual line verbatim, and do not soften.** The audit could previously satisfy its
   own spec while saying "your summary is weak." It now has to print the sentence.
2. **Keep parse failures and content failures apart.** They have different fixes and different
   urgency, and most people only think about the second. Fixing the first is cheaper and comes first.

Both went into `prompts/02-resume-audit.md`, and `prompts/03-master-resume.md` now inherits them by
reference, because the folded audit inside Phase 3 is the default path and the standalone Phase 2
artifact only exists on request. The rules are stated once and pointed at, not copied.

## Step 2, the recruiter keyword scan: already covered, and Ascend's is sounder

`reference/ats-and-keywords.md` already specified the whole method: pull 5 to 10 real current
postings, extract Tier-1 and Tier-2 terms, then mark each one present, missing-but-claimable, or a
true gap. `reference/industry-analysis-framework.md` goes further with weighted frequency, confidence
intervals, segmentation, and a scarcity scan.

One difference matters. The proposal asks a model to recall keyword frequencies "based on pattern
recognition across the live market." That is an unsourced statistical claim generated from memory,
which is the exact failure mode this system exists to prevent. Ascend reads real postings and reports
the sample size. That difference is kept.

**Taken:** the reminder that a differentiating keyword is wasted if it only appears in the skills list.
`reference/ats-and-keywords.md` step 5 now says to place them inside achievement bullets. It
deliberately **points at** the existing scarcity scan for identifying those terms rather than
describing a second method, because a first draft of this change did introduce that duplication and it
was removed.

## Step 3, the XYZ bullet rewrite: already covered, and the literal version breaks the system

`reference/resume-writing-rules.md` already binds every one of the proposal's six rules: the formula
itself, strong verbs with no "responsible for", a measured outcome, never fabricating a number, one to
two lines per bullet, JD vocabulary matched once, and filler cut. The banned-vocabulary list is
mechanically enforced by `tools/lint_artifacts.py`, so it is a gate rather than a suggestion.

**Not taken, deliberately: "rewrite every bullet in my experience section."**

Ascend is built on **selection, not invention**. Once `master-resume.md` is locked, per-job résumés
select, reorder, and trim locked bullets. They never reword one and never add one. A job that needs a
bullet that does not exist produces a MASTER GAP note, and the fix is to change the master
deliberately and re-lock it, not to write new prose per application.

Per-job rewriting is precisely how drift and fabrication enter: twenty applications become twenty
slightly different claims about the same work, and no one can say which one is true. Rewriting has a
correct home in Ascend already, and it is Phase 3, where the master is built or amended, under the
bullet-quality gate and the honesty policy.

The one rule from this step worth underlining is the proposal's own rule 2: ask rather than fabricate a
number. Ascend already states it in `reference/number-and-honesty-policy.md` and enforces the
retracted-claims half of it in the linter.

## Step 4, LaTeX: a real gap, now the default

This was the genuinely additive part. Ascend rendered only through an HTML builder printed by a
Chrome-class engine. A LaTeX path gives a portable `.tex` artifact that compiles on Overleaf with no
local install, and it removes the browser from the critical path.

**Shipped:**
- `templates/resume-latex.template.tex`, a locked single-column layout carrying the same typography floors as
  the HTML builder: 0.5in margins, 10pt body, 12pt headings, 1.15 leading.
- `tools/render_resume.py`, which populates the template by emitting macro calls only. It never emits
  raw formatting, so a render cannot reintroduce a table, a column, or a text box.
- The tool enforces the page budget and fails on overflow instead of shipping a silent two-pager.
- The `.tex` is written even with no TeX engine present, so the fallback is always "compile on
  Overleaf," never "you get nothing."
- The HTML builder stays as the fallback and as the interactive path behind `/ascendui`.

**The proposed template was not used as given.** It sets `margin=1cm`, which is 0.39in and below
Ascend's 0.5in floor, and it is shaped for an academic CV (GPA, relevant coursework, publications,
academic projects) rather than a senior industry résumé. The layout was rebuilt to Ascend's existing
locked standard so the two renderers produce the same document.

### Two ATS bugs found by compiling, not by reading

Both were invisible until a PDF was compiled and its text extracted back out through the font's
ToUnicode tables, which is what an ATS does.

1. **The fi ligature had no ToUnicode mapping.** "first" extracted as "rst" and "fintech" as "ntech".
   Every keyword containing fi or fl was invisible to a parser. Fixed by disabling common ligatures,
   per engine: `DisableLigatures` under pdfTeX, `Ligatures=NoCommon` under XeTeX.
2. **Math-mode glyphs had no ToUnicode mapping either.** The separator and the arrow in "0 to 1"
   extracted as unmapped glyphs. All math mode was removed from the renderer's output.

`tests/smoke.py` now has a regression test that compiles the committed sample, extracts its text
through the ToUnicode CMaps, and asserts that "first" and "fintech" survive. That is the test that
would have caught either bug, and it is there so a future font change cannot quietly undo the fix.

### Security note

LaTeX's `\write18` would make a document into a command execution primitive, and résumé content can
trace back to a fetched job posting. The renderer escapes backslashes so no macro can be injected
through content, and it also passes `-no-shell-escape` to the pdfTeX family, so the boundary does not
depend on the escaping being perfect. tectonic disables shell escape by default.

---

## Duplication audit

The point of this pass was to add without making any step do work another step already owns.

| Concern | Result |
|---|---|
| Keyword set derived more than once | No. Derived once in Phase 3 into master §4. Phases 4, 5, and 14 reuse it, and `CLAUDE.md` states the rule. |
| Writing rules restated per prompt | No. They live once in `reference/resume-writing-rules.md`. Sixteen files reference it, none copy it. |
| Two homes for rare-keyword analysis | Was introduced by this change, then removed. `industry-analysis-framework.md` §5 is the only home, and `ats-and-keywords.md` points at it. |
| Audit rigor rules copied into Phase 3 | No. Phase 3 references the rules in Phase 2. |
| Two renderers meaning two layouts | No. Both render the same locked typography, stated in both templates and in `resume-writing-rules.md`. |
| Phase run order duplicated | Unchanged and still asserted by `tests/smoke.py` across `00-orchestrator.md`, `CLAUDE.md`, and `ascendui.md`. |
| Dead cross-references from the new files | None. The smoke suite's cross-reference test passes. |

**No phase was added.** The export step already existed; it gained a default path and kept its
fallback. The pipeline is still `1 → 3 → 4 → 6 → 5 → 7` with the same on-demand ops.

## Verification

- `python3 tests/smoke.py`: **168 checks, all passing**, including 19 new LaTeX checks.
- Compiled and text-extracted three real documents: the committed fictional sample, a dense
  senior-engineer per-job résumé, and a two-page master. One page, two pages, and one page
  respectively, all with clean extraction and no unmapped glyphs.
- Rendered output inspected visually, not only asserted on.

## Open items

- The arrow character now renders as `->` rather than an arrow glyph. That is the deliberate trade for
  clean extraction. If it ever matters visually, the fix is a real font glyph with a ToUnicode entry,
  never a return to math mode.
- The committed sample still ships the HTML-rendered PDF. Regenerating it through LaTeX would make the
  showcase match the documented default, and is worth doing as its own change.
