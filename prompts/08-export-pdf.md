# Export → ATS-safe PDF (for a job's resume.md / signal.md)

**Goal:** turn a tailored `resume.md` (or `signal.md`) into a clean, ATS-safe **PDF** the user can
actually submit — without making them figure out Markdown→PDF themselves. This closes the system's
biggest manual dead-end.

**When:** run per job right after its `resume.md` is finalized (or on request: "export the Acme
resume"). Also works for `signal.md`.

---

## Method A — print-to-PDF (default; zero install, works everywhere)
1. Convert the Markdown to simple HTML and drop it into a copy of
   `../templates/resume-print.template.html` as `<main id="doc">…</main>`:
   - `# Name` → `<h1>`, the contact line → `<p class="contact">`, `## Section` → `<h2>`,
     role line → `<h3>Company — Title <span class="meta">dates · location</span></h3>`,
     bullets → `<ul><li>…</li></ul>`, the summary → `<p class="summary">`.
   - No tables, no columns, no graphics — the template is already single-column and ATS-safe.
2. Save it next to the resume as `<name>-resume-<company-role>.print.html` in the job folder.
3. Tell the user: **open that file in a browser and press Cmd/Ctrl-P → "Save as PDF"** (set margins to
   Default, "Background graphics" off). Name it `<Name>-Resume-<Company>.pdf`.
4. Sanity-check: 1–2 pages, single column, standard font, selectable text (not an image), no clipped
   content.

## Method B — pandoc (one command, if the user has it / wants automation)
If `pandoc` + a PDF engine are available:
```
pandoc resume.md -o "<Name>-Resume-<Company>.pdf" \
  -V geometry:margin=0.6in -V fontsize=10.5pt -V mainfont="Calibri" --pdf-engine=weasyprint
```
(Use `wkhtmltopdf` or `--pdf-engine=tectonic`/`xelatex` if weasyprint isn't installed; xelatex needs
the `--variable` font present.) Verify the same checklist as Method A.

## Method C — headless Chrome (fully scripted, if Node/Chrome present)
Render the print HTML from Method A and print it headless:
```
chrome --headless --disable-gpu --print-to-pdf="<Name>-Resume-<Company>.pdf" \
  --no-pdf-header-footer "<file>.print.html"
```

---

## Honesty & format
- The PDF must be **single column, standard headings, selectable text, ≤2 pages, certs honest**
  (no "Active" unless true). Re-run the number-policy grep on the final text — the export must not
  reintroduce any sanitized internal number.
- Filename convention: `<Name>-Resume-<Company>.pdf` (recruiters search download folders).

## Checkpoint
Tell the user which method you used, where the file is, and the 2-click save step if Method A. Remind
them to **eyeball the PDF** before submitting (the one manual verification that always matters).
