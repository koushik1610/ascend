# Export → ATS-safe PDF (the résumé builder)

**Goal:** turn a tailored `resume.md` (or the master resume) into a clean, ATS-safe **PDF** the user
can submit — in the locked builder layout, fitted to one page. This closes the system's biggest manual
dead-end.

**When:** automatically, per job, right after a `resume.md` is finalized in Phase 5; for the master
public résumé in Phase 3; or on request (`/ascend export <company>`, `/ascend build-resume`).

**One renderer.** Everything goes through `../templates/resume-builder.template.html` (the locked,
single-column, ATS-safe layout). There is no separate print template anymore.

---

## Step 1 — resume.md → resume.json (JSON Resume schema)
Parse the finalized `resume.md` into `resume.json` next to it, using the builder's data model
(JSON Resume-based):

```json
{
  "basics":   { "name": "", "label": "<target role>", "email": "", "phone": "",
                "location": "City, ST", "url": "<portfolio/linkedin>", "summary": "" },
  "work":     [ { "company": "", "position": "", "location": "", "dates": "Mon YYYY - Present",
                  "highlights": ["bullet", "bullet"] } ],
  "projects": [ { "name": "", "role": "", "dates": "", "description": "" } ],
  "education":[ { "institution": "", "studyType": "", "location": "", "dates": "" } ],
  "skills":   [ "skill", "skill" ]
}
```

Use **public/sanitized** values only (per `../reference/number-and-honesty-policy.md`). Honor the
**one-page content budget** in `../reference/resume-writing-rules.md` — if the selected bullets exceed
it, cut by JD-relevance before rendering, never shrink type. Re-run the number-policy grep over
`resume.json` before rendering: it must not reintroduce any sanitized internal number.

## Step 2 — fill the builder template
Copy `../templates/resume-builder.template.html` into the job folder as
`<name>-resume-<company-role>.html` and replace the empty data island with the JSON from Step 1:

```html
<script type="application/json" id="resume-data">
{ ...resume.json... }
</script>
```

Everything else in the template stays untouched.

## Step 3 — render the PDF (automatic)
Render headless via the already-trusted server (no extra permissions needed):

```
python3 ui/server.py --render "<path>/<name>-resume-<company-role>.html" \
  --out "<path>/<Name>-Resume-<Company>.pdf"
```

It detects a Chrome-class engine and prints to PDF using the template's print CSS (résumé only,
single column, selectable text). **Fallback:** if it reports no engine found, tell the user to open the
filled `.html` in a browser and press **Cmd/Ctrl-P → Save as PDF** (Background graphics off) — same
output, two clicks. The standalone builder's **Create PDF** button does exactly this.

---

## Optional — DOCX export (`/ascend export-docx <company>`)
Some ATS portals and recruiters still ask for a Word file. The PDF is the default and the one to submit
when you can; produce a `.docx` only on request, from the **same finalized `resume.md`** so the two never
drift.

1. Strip the leading Delta-Log HTML comment (everything in `<!-- … -->`) — only the résumé body converts.
2. Convert with the allow-listed `pandoc`:
   ```bash
   pandoc "<path>/resume.body.md" -o "<path>/<Name>-Resume-<Company>.docx"
   ```
   (Write the body to a temp `resume.body.md` under the same folder first; `pandoc` is the only
   converter in the Bash allow-list — never shell out to anything else.)
3. **ATS-safe DOCX rules:** single column, standard heading styles, no text boxes / tables / images,
   no headers/footers. pandoc's default reference doc satisfies this; don't pass a custom template that
   adds columns or graphics.
4. Re-run the number-policy grep over the `.docx`'s source body — a DOCX is sendable, so public/sanitized
   values only, same as the PDF. Filename: `<Name>-Resume-<Company>.docx`.
5. Tell the user the `.docx` is a convenience copy and the PDF remains the preferred submission; eyeball
   both. (Generated `*.docx` is gitignored as personal output.)

---

## Honesty & format checklist (always)
- **Typography (best practices — always):** classic ATS-safe font (Calibri/Arial/Helvetica/Times New
  Roman), body **10–12pt (10pt floor)**, section headings **12–14pt**, margins **0.5–1in (0.5in floor)**,
  line spacing **1.15–1.5 (1.15 floor)**, consistent sizing, bold/italics sparingly. These are the locked
  defaults in the builder CSS; see `../reference/resume-writing-rules.md → Typography & layout`. To fit
  one page, trim content to the budget — never render below the font/margin/spacing floors.
- Single column, standard headings, selectable text (not an image), certs honest (no "Active" unless
  true).
- **Per-job résumé: one page.** Master public résumé: ≤ 2 pages.
- Filename: `<Name>-Resume-<Company>.pdf` (recruiters search download folders).
- The render must not reintroduce any sanitized internal number (grep the final `resume.json`).
- **Lint gate before rendering:** `python3 tools/lint_artifacts.py <the resume.md and resume.json>`
  (plus `--config workspace/<name>/lint-config.json` if it exists) → **0 findings**. This is the
  mechanical form of the language rules above — don't render a PDF from text that fails it.

## Verify
- The `.html` opens with the form prefilled and the preview showing the résumé.
- The PDF exists, is the expected page count, and its text copies out in order (the ATS parse test:
  paste into plain text, confirm name → titles → dates → bullets read top-to-bottom).

## Checkpoint
Tell the user where the `resume.json`, filled `.html`, and `.pdf` are, and whether it auto-rendered or
needs the two-click save. Remind them to **eyeball the PDF** before submitting (the one manual
verification that always matters).
