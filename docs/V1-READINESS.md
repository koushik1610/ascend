# Ascend: v1.0 Readiness Review (council, 2026-06-28)

Full LLM council, 10 personas across 3 groups (engineering/systems/delivery · security/privacy/compliance ·
product/market/skeptics), anonymous peer-vote, priority verdict. This report supersedes the optimistic
"one checkbox away" framing in [`ROADMAP.md` → Path to v1.0](ROADMAP.md); reconcile that section against this.

## Verdict: do not tag v1.0 yet

The project has thoroughly hardened the **periphery** (server CSRF/XSS, deny-lists, CI, the résumé builder)
and never validated the **center**: the core pipeline has not been run end-to-end on real data even once, by
its own Known Limitations. Two independent groups reached the same conclusion. The honest move is to **tag
v0.5.0 now** (it captures the rebrand + builder + security hardening), do the real runs and the items below,
then earn v1.0. Estimated ~1 week of focused work.

Vote weight is noted as ●●● (raised by all three groups), ●● (two), ● (one).

---

## P0: blocks v1.0

1. **Release mechanics are unfinished; nothing is on `main`.** ●●
   `main` HEAD still ships S.P.I.D.E.R. (old banner, `/spider`, CI badge → `koushik1610/spider`). The rebrand,
   résumé builder, and banner live only on unmerged branches. The version badge says **v0.4.0**, the CHANGELOG
   is still `[Unreleased]`, and there is no tag. DoD items ⑥/⑦ are unmet.
   **Action:** merge the work to `main` (fold in or delete the stale `rebrand/ascend` + `feat/resume-builder`
   branches), confirm CI green on `main`, bump the badge + convert the CHANGELOG block to a dated release, then tag.

2. **The only proof artifact contradicts the shipped product.** ●●
   `examples/sample-run/` is the README's headline "see a full run" link and the *only* end-to-end evidence.
   It is frozen at the v0.1 architecture: 8-file job folders (the eager ~100-file behavior v0.2 killed), a
   standalone `resume-audit.md` (now folded into Phase 3), **no `resume.json`, no rendered PDF** (the entire
   v0.4 résumé-builder feature is invisible), and its README claims "5 jobs / all 8 files." A first-time
   visitor clicks the one "see it" link and sees an older, more bloated product than the README sells.
   **Action:** regenerate the sample against the current pipeline (3-file CORE packs, deep-prep for one job
   only, audit folded in, a 15+ queue, at least one `resume.json` + sample PDF) and fix its README file-tour.

3. **The "one real run" gate is under-specified and under-scoped.** ●●●
   DoD ① says "one real run, archived as proof, honesty gates verified" but defines no pass/fail rubric, no
   sign-off, and the archive is (correctly) gitignored personal data, so the gate is self-certified and
   unfalsifiable. One run by the author, on the author's data, on macOS, tests one happy path. It does not
   exercise: a no-résumé cold start (README promises this), a non-tech field, Windows/WSL, the free-tier CLI
   path, or the resume-after-interruption flow.
   **Action:** redefine the gate as **2–3 real runs** spanning (a) with-résumé tech, (b) no-résumé or
   non-tech, (c) one resume-after-interruption, each archived (redacted run-log) with an explicit honesty-gate
   spot-check and a recorded sign-off in the CHANGELOG/ROADMAP.

4. **The agent's Bash security boundary is an enumerable deny-list with trivial bypasses.** ●● *(verified against source)*
   `.claude/settings.json` denies specific interpreters (`node`, `python3 -c`, …) but not `bash -c`, `sh -c`,
   `env`, `xargs`, `find -exec`, or **`python3 <script.py>`**. With pre-approved `Write(workspace/**)`, an
   injected job page can write a script under `workspace/` and run it via any unlisted interpreter, defeating
   the "no RCE / no exfil under injection" property that *gates the 1.0 tag*. Broad all-domain `WebFetch`
   remains a live exfil channel constrained only by judgment, not capability. Separately,
   `.claude/settings.local.json` re-broadens to `Bash(python3 *)` on the author's machine, so the documented
   "real run" would execute under a defeated threat model.
   **Action:** convert Bash to **allow-list-only** for v1.0; drop wildcard `Bash(mkdir *)`; add a negative
   smoke test that a bypass (`bash -c`, `python3 file.py`) is blocked; remove `Bash(python3 *)` from local
   settings before the proof run. *(The renderer XSS fix SEC-CRIT-2, the injection-quarantine banners
   SEC-CRIT-1, the CSRF/rebind defenses, and the résumé builder's DOM-text rendering were all verified to
   still hold post-rename.)*

5. **Beta surfaces sit inside the advertised v1.0 feature set.** ●●
   The README presents `/ascendui`, the scheduled daily brief, `network`, `answers`, `today`, and `prep` as
   first-class, with the *(beta)* tag only on `/ascendui`. The status banner admits these are "not proven
   end-to-end." SemVer 1.0 is a stability promise; shipping it with a beta tax on roughly half the headline
   commands breaks that promise.
   **Action:** either prove the on-demand ops with real runs and drop the caveat, or explicitly scope it in
   the lede/badge: "the `/ascend` text pipeline is 1.0; the UI, scheduling, and on-demand ops are 1.0-beta."

---

## P1: should-fix before v1.0

- **Smoke tests assert plumbing, not the value claim.** ●● The suite proves the server compiles, the renderer
  sanitizes, the PDF has text. None touch the honesty gates or selection-not-invention, which the README calls
  the core feature. **Action:** add an automated honesty check (the committed sample's résumé DELTA LOG has no
  fiction; no internal-number leak), codifying the grep the sample already documents. Full eval tests stay v1.5.
- **Demo GIF slot is empty.** ● `README.md` still holds the `<!-- DEMO -->` placeholder; `assets/` has no
  `demo.gif`. For a private→public launch with zero traction, the 10–15s "it runs" clip is the highest-leverage
  conversion asset. **Action:** record and commit it before going public.
- **CI must be green on the remote, not just locally.** ● `tests/smoke.py` passes locally (verified), but DoD
  ④ means a real GitHub Actions run is green. Confirm the workflow runs on `main`. (Note: the Actions badge can
  only render once the repo is **public**.)
- **The one-page PDF guarantee is advisory, not enforced.** ● `Create PDF` is `window.print()`; a `.pagewarn`
  banner is shown but nothing blocks a 2-page export, while the README sells "one-page ATS-safe PDF" as a hard
  property. **Action:** enforce one-page (scale/refuse on overflow) or soften the copy, and add a page-count
  assertion to the smoke suite.
- **`/resume-builder` is served with no CSP and no token gate.** ● It returns HTML before the `/api/` token
  check and parses arbitrary résumé JSON. Lower risk (DOM-text rendering), but it's the one served page with
  zero CSP. **Action:** add the same `default-src 'none'`-style CSP the `/view` route uses.
- **The unattended daily-brief is the riskiest, least-tested surface.** ● Untrusted fetched content → pre-approved
  Bash/Write/WebFetch, no human gate, relying on the prompt to restate quarantine inline because headless CLIs
  may not load `CLAUDE.md`. **Action:** default the scheduled brief **OFF** for v1.0 (opt-in, with a loud
  "beta, runs unattended" notice at schedule time).
- **README slightly over-promises the gitignore CSV backstop.** ● It says LinkedIn CSVs are blocked "anywhere
  in the tree," but the rule enumerates specific filenames; a renamed export is only caught by the `workspace/*`
  rule (which does hold). **Action:** soften the claim or broaden the ignore.
- **CI depends on an unpinned `node`.** ● `ci.yml` runs `node --check` with no `setup-node`, and the project's
  own deny-list bans `node`. **Action:** pin `actions/setup-node` or replace with a Python-based JS check.

---

## P2: post-v1.0 (correctly deferred; do not reopen 1.0 scope)

- Table-stakes feature gaps already in the backlog: **DOCX export** (#19), **official ATS job aggregation**
  via Greenhouse/Lever/Ashby JSON + RSS (#17). Don't block 1.0.
- The relationship + interactivity layer the research ranked first (Networking CRM #2, Achievement-Mining
  Interview #4, interactive "Interview Me" drill #5, De-Genericizer #6, Salary Negotiation Studio #7). These
  are the strongest *next* bets, after the 1.0 gate. Scope freeze is correct.
- Maintenance debt, acceptable for 1.0: the hand-rolled `/view` Markdown renderer, the run-order string
  triplicated across three files (held in sync by a smoke test).
- Accepted single-user risks, log them explicitly: SEC-MED-4 (token in page DOM), SEC-MED-5 (no per-slug auth
  on `/view`).
- The author's real workspace still has a stale `.spider-state.json`; use a clean workspace for the proof run.

---

## Dissenting view

The roadmap's optimistic read: the `/ascend` text pipeline is genuinely complete, and the author can do the
real runs quickly. If those runs pass, most P0s collapse within days, so "one checkbox away" is nearly true in
effort even if wrong in framing. The council majority holds the line anyway: tagging 1.0 before the runs, a
fixed sample, and an enforced (not enumerated) security boundary is a stability claim the project cannot yet
back. Security work on a pipeline nobody has run end-to-end is a vault around an untested engine.

## What "good" (a real v1.0) looks like

Merged to `main` and tagged · 2–3 archived real runs across the P0-3 gate cases with honesty spot-checks ·
a regenerated sample matching the shipped architecture (incl. `resume.json` + a PDF) · Bash allow-list-only
with a negative smoke test · beta surfaces proven or fenced in the lede · CI green on the remote · demo GIF
live. That is roughly a week of focused work.
