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

## Honesty & format checklist (always)
- Single column, standard headings, selectable text (not an image), certs honest (no "Active" unless
  true).
- **Per-job résumé: one page.** Master public résumé: ≤ 2 pages.
- Filename: `<Name>-Resume-<Company>.pdf` (recruiters search download folders).
- The render must not reintroduce any sanitized internal number (grep the final `resume.json`).

## Verify
- The `.html` opens with the form prefilled and the preview showing the résumé.
- The PDF exists, is the expected page count, and its text copies out in order (the ATS parse test:
  paste into plain text, confirm name → titles → dates → bullets read top-to-bottom).

## Checkpoint
Tell the user where the `resume.json`, filled `.html`, and `.pdf` are, and whether it auto-rendered or
needs the two-click save. Remind them to **eyeball the PDF** before submitting (the one manual
verification that always matters).
