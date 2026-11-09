# Ascend 3.0 — comparative analysis and what shipped

**Date:** 2026-11-05 · **Method:** feature comparison against other open-source career-operations
modules, then a three-member council review (coding/systems · AI-agent-security · technical
recruiter) of the integrated flow. Every mechanical claim below was verified by running the code,
not by reading it.

The headline: **the two most valuable changes were not on the original candidate list.** The
comparison surfaced five plausible features; the review found that one of them was already 70% built
and pointed at the wrong artifact, that a sixth problem nobody had proposed outranked three of the
five, and that the system's inbound ingest path was actively laundering hidden content into
clean-looking prose.

---

## 1. What the comparison actually found

The peer module is a Claude Code job-search framework: 14 slash commands, 6 portal-search skills,
~19 Python tools, with a documented personal funnel of 69 applications → 20 first interviews → 1
offer. Its genuinely distinctive ideas, and Ascend's position on each:

| Their idea | Ascend before | Verdict |
|---|---|---|
| Deterministic posting integrity gate (hidden text, invisible characters, instruction-shaped lines) | Instruction-level quarantine only | **Adopted, narrowed** |
| PDF text-layer + layout verification after render | Page-count check only | **Adopted, narrowed** |
| Portal registry with a uniform search contract, `enabled:` flag, auto-discovery | Company-board polling by slug + LinkedIn result cards | **Deferred** — see §4 |
| Language deal-breaker with structured handling | Nothing | **Adopted, narrowed** |
| `/upskill` gap heatmap + study plan | Per-job gaps recorded, never aggregated | **Adopted, cut to a counter** |
| `robots_check.py` gating a browser-header curl retry | No curl at all | **Rejected** — see §5 |
| `/add-template` user-supplied résumé templates | Locked LaTeX template | **Rejected** — see §5 |
| Notion sync | Navigator + hub, offline | **Rejected** — outbound channel for workspace data |

**On the portal list specifically**, since it was the most visible thing: the shipped boards are
Danish-market (Jobindex, Jobnet, Akademikernes Jobbank, Jobdanmark), so the list does not transfer.
The two country-agnostic ones are a LinkedIn scraper the repo itself labels "personal use only —
automated access is against LinkedIn's Terms of Service", and one remote-tech aggregator. The
transferable asset is the *pattern*, not the list.

**Where Ascend was already ahead:** `/ascend linkedin-search` drives the user's *own logged-in
browser*, reads result cards only, and asks permission first — a better posture than unauthenticated
scraping. All personal output lives under a gitignored `workspace/`, where the peer writes the
profile into tracked files and warns that a fork is always public. And Ascend's outbound honesty
gates (`lint_artifacts.py`, 10 categories; `grade_run.py`; the locked master) have no counterpart.

---

## 2. The two findings that outranked the candidate list

### 2.1 The ingest path laundered hidden content

`finder.clean()` and `gmail_sync._strip_html()` both did, in effect:

```python
s = html.unescape(s)              # &#8203; becomes a real zero-width space
s = re.sub(r"<[^>]+>", " ", s)    # removes the wrapper, KEEPS the hidden text
```

Verified against the real module: a `<div style="display:none">` payload, a `font-size:0` span, a
U+200B inside a word, and a sentence spelled in the U+E0000 tag block all survived — and came out
**indistinguishable from the visible job description**, because the only thing removed was the
evidence that they were hidden. The ordering was the bug.

The honest framing is not primarily security. The commonest source of these characters is a JD
drafted in Word and pasted into a portal, and the cost is a plain triage bug:
`prefilter.keyword_overlap` matches by literal substring, so `"Pyt​hon"` does not contain
`"python"` and `re.sub(r"\s+", " ")` does not strip U+200B because Python's `\s` does not match it. A
posting the user is well matched to therefore scored lower, sorted lower, and was never scored.

**The outbound half was broken too, independently.** `lint_artifacts._symbol_glyphs` gated on
Unicode categories `So`/`Co`. Verified: U+200B, U+00AD, U+FEFF and the whole tag block are all `Cf`,
so the check returned `[]` for a name containing a zero-width space — and `render_resume.tex_escape`
passed `Cf` straight through into the `.tex`. Invisible text could ship *inside a submitted PDF*,
which `reference/ats-and-keywords.md` itself calls worse than an unmatched résumé. That file also
claimed "The LaTeX template cannot produce hidden text", which was false as written; it is now
corrected and both gates exist.

### 2.2 Arrival time: the board's publish date was fetched and thrown away

`reference/ats-and-keywords.md` states it outright — *"recruiters review in arrival order — apply
early."* Nothing acted on it, because nothing could: `finder.normalize()` received
`updated_at` / `createdAt` / `publishedAt` / `published_on` / `releasedDate` from the five boards and
captured none of them. The only date stored was `first_seen` — *when Ascend looked*. On a fresh
workspace that makes every posting one day old, including a 90-day-old requisition with 400
applicants already in it.

This was also a regression against the prompt it replaced: `prompts/14-ats-aggregation.md` names
`updated_at` and `createdAt` explicitly and uses them for staleness. The deterministic path that
superseded it dropped the capability.

---

## 3. What shipped

| # | Change | Where |
|---|---|---|
| 1 | **`tools/_untrusted.py`** — de-smuggle untrusted text: hidden elements removed *with their content* before tags are flattened, every `Cf` code point stripped, tag-block runs decoded then removed so the payload can be quoted, NFKC fold. Wired into `finder.clean`, `gmail_sync._strip_html`, and `jobqueue.servable_text` (the last seam before the model), always **before** the character budget. | 4 call sites |
| 2 | **`Cf` added to the `scan` gate** and `tex_escape` now strips invisibles | `lint_artifacts.py`, `render_resume.py` |
| 3 | **`posted_on` captured from all five boards**, with `age_days`, freshness as the queue tie-break (unknown age sorts last, never first), and a daily-brief line that names a requisition's age | `finder.py`, `jobqueue.py`, `13-daily-briefing.md` |
| 4 | **PDF text-layer verification** — the ToUnicode extractor moved out of `tests/smoke.py` into the tool, so it runs on the user's own résumé; plus `--verify-text <pdf>` for the Overleaf path | `render_resume.py` |
| 5 | **Language gate** — declared-only, routed through the existing required/preferred/mentioned classifier | `00-orchestrator.md`, `profile-brief.template.md`, `04-job-search.md` |
| 6 | **`jobqueue.py gaps`** — a counter over gaps already stored, reported at ≥3 occurrences | `jobqueue.py`, `20-weekly-review.md` |
| 7 | **Pre-existing red test fixed** — a hardcoded `applied_on` fell outside `GUARD_DAYS=60` on 2026-10-31 and had been red since | `tests/test_pipeline.py` |
| 8 | **Unit-suite glob widened** to `test_v[0-9]*_*.py`; it matched only `test_v2_*`, so any later suite would have run green locally and never been gated | `tests/smoke.py` |

### Design decisions worth recording

**The de-smuggler is a module, not a command.** `.claude/settings.json` pins a Bash entry by path
prefix and places **no constraint on the arguments** — the weakness `_paths.py` exists to contain. A
`posting_guard.py` with an allow-list entry, taking untrusted text or a URL on argv, would turn an
allow-listed entry into a primitive that attacker-influenced content can aim. And a scanner the model
is *told* to run is itself an instruction-level control, which is the class of defence it exists to
replace. Called from inside the tools, it needs no cooperation and no new permission.

**No instruction-shaped-line or homoglyph detection.** A posting for an SSH administrator says
"SSH"; nearly every posting says "please submit your resume as a PDF"; "Яндекс" is a company. Removal
of invisible characters has no false-positive cost, so it is unconditional. Heuristic *flagging*
does, so it stays with the quarantine, where a human reads the quoted text.

**ToUnicode presence is context, never the assertion.** Demonstrated on the committed sample: a PDF
can carry a CMap for every font and still have glyphs that extract as garbage, and a wrong CMap entry
maps cleanly to the wrong character. The assertions are literal-substring: the contact details must
appear as literal text. The check **reports and does not block** — a false positive that refuses to
produce a PDF the night before a deadline is worse than the bug.

**The text check found a real defect in the committed sample.** The Chrome/HTML fallback path emits a
PDF whose text layer contains `ﬁ`, so `remote-first` extracts as `remote-ﬁrst` and a recruiter's
search for "first" misses it, plus 8 glyphs with no usable ToUnicode entry. The LaTeX path disables
ligatures and is regression-tested; the fallback was not. Now reported with the word named.

**Honesty limit, stated rather than papered over.** This covers the **tool-mediated** ingest paths —
board polling, Gmail, and every row served through `jobqueue.candidates`, whatever wrote it. Where a
prompt has the model WebFetch a posting directly (Phase 4, engine B), the content is in context before
any Python could run. No tool can sit in front of a WebFetch result. That is an argument for routing
ingestion through the tools, not for skipping this.

---

## 4. Deferred: query-based discovery across aggregators

The gap is real — `finder.py` polls **company boards by slug** and `14-ats-aggregation.md` says "for
each target company", so the user must already know which companies to watch. But the proposed shape
does not fit:

- The five supported ATSs publish **per-company board** endpoints, not cross-company search. A
  "uniform search contract" over them is a contract with no implementations.
- Real keyless search APIs are a different, smaller set, and **this container's network is
  restricted** — endpoints could not be verified live, and the available search results were
  third-party listings rather than the boards' own documentation. Shipping a hardcoded endpoint list
  that was never tested is exactly the unverified external claim this repo refuses elsewhere.
- Per the recruiter: for the common case of a mid-level candidate outside the US, the gap is **source
  coverage for their market**, not query mode. Adding keyword search across the same five boards
  returns more of the same narrow slice. And posting supply is not the binding constraint — the
  applicant-to-requisition ratio is, and the levers that move it are a warm path and arrival speed.
  Arrival speed is what §2.2 fixed.
- Deriving an endpoint to call from fetched content would violate the untrusted-content policy
  outright.

**If this is built later:** a `feeds[]` array beside the existing `boards[]` in `sources.json`, with
the host list a **literal dict in the source** (never read from a workspace file, or a config file
becomes an SSRF knob), `enabled: false` by default, two portals maximum, and the user verifying each
endpoint where their network is open. The ongoing cost is the real cost: five board schemas already
need maintenance, and unofficial aggregator APIs break more often and more quietly —
`fetch_board` returns `None` on any exception, so breakage shows up as a silent zero.

---

## 5. Rejected, with reasons

- **`robots_check.py`.** Its entire purpose is to decide whether a browser-header **curl** retry past
  a bot-filtering firewall is permissible. Ascend deny-lists `curl` — which is the one
  general-purpose outbound-POST primitive in that list, and therefore the highest-value thing an
  injected posting could ask for. Adopting the guard means adding the capability it guards. Net loss.
- **User-supplied résumé templates.** All layout lives in one locked template with exactly one content
  marker, and the renderer emits macro calls only, so a render cannot reintroduce a table or a column.
  A user template is the single change that makes that false — and it breaks the ligature guarantee
  the new text-layer check depends on. If variation is wanted, expose *parameters* (a font from a
  pinned ATS-safe list, margins within the stated floors), never a template file.
- **The estimation technique for numbers you don't have** (carried over from an earlier comparison): a
  conservative invention is still an invention, and one the user has to defend in an interview.
- **A gap heatmap with hour estimates.** An hour estimate for learning something is a fabricated
  number. Beyond that, a study plan is the most comfortable-feeling work in a job search: it looks
  like progress, it is entirely within the candidate's control, and it displaces applying. Shipped as
  a counter that names one recurring gap at ≥3 occurrences and stops.

---

## 6. Verification

- `python3 tests/smoke.py` → all pass, including the newly-globbed `test_untrusted.py` (23 tests)
- `python3 tools/grade_run.py examples/sample-run` → `GRADE: PASS`
- `python3 tools/lint_artifacts.py examples/sample-run` → 7 files, 0 findings, CLEAN
- Every new gate was reverted to its broken state and **observed to fail** before being called done:
  disabling hidden-element removal and the `Cf` category turned 4 tests red.
- No TeX engine in this container, so the LaTeX render path's text layer is covered by CI
  (`ASCEND_REQUIRE_TEX=1`), not by a local run. The `--verify-text` path was exercised against the
  committed sample PDF.
