# examples/

This folder is intentionally light — **no real personal data ships in this repo** (that's the whole
privacy model; see the root `.gitignore`).

## The proof case
S.P.I.D.E.R. was extracted from a real, end-to-end run the author did on their own job search:
a LinkedIn-export analysis, a master resume built by selection, a ranked queue of 12 live roles, and
12 per-job folders (8 files each = 96 files) plus a cross-job interview packet. That run is what the
templates and prompts in this repo encode. The author's actual documents are **not** included — they
live in a private workspace and are gitignored.

## What a real run looks like
After you run the pipeline (see the root `README.md`), your `workspace/<name>/` will contain the
structure described in `workspace/README.md`:

```
linkedin-analysis.html   resume-audit.md   master-resume.md   job-queue.md
interview-packet/        jobs/<NN-company-role>/ (×15+, 8 files each)   start-here.html
```

## Want a sanitized sample?
If you'd like a fully fictional, end-to-end sample workspace (a made-up "Jordan Rivera, Senior Product
Designer") committed here for reference, open an issue or generate one yourself: run the pipeline with
invented intake answers and a placeholder resume, then copy the result here with all names fictional.
Keep anything in `examples/` 100% fictional — never a real person's data.
