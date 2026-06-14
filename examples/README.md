# examples/

> ⚠️ **Never put a real person's data in `examples/`.** Real runs go in `workspace/` (gitignored).
> The committed sample under `examples/sample-run/` is 100% fictional. If you generate your own sample
> here, make every name, number, company, and link invented — `examples/` is committed, so anything
> real here would be published.

This folder ships one **fictional worked example** so you can see real-shaped output without running
the pipeline — otherwise **no real personal data ships in this repo** (that's the whole privacy model;
see the root `.gitignore`).

## `sample-run/` — a complete fictional run
A made-up candidate (**Jordan Rivera, Senior Product Designer** — deliberately non-engineering, to show
the system works beyond software roles). It contains a filled `linkedin-analysis.html`, a resume audit,
a master resume, a 5-job queue, an interview packet, two full per-job folders (8 files each), and a
`start-here.html` navigator — exactly the structure your own `workspace/<name>/` will have. Open
`examples/sample-run/start-here.html` in a browser to tour it. Everything in it is invented.

## The proof case
S.P.I.D.E.R. was extracted from a real, end-to-end run the author did on their own job search:
a LinkedIn-export analysis, a master resume built by selection, a ranked queue of live roles, and
per-job folders (8 files each) plus a cross-job interview packet. That run is what the templates and
prompts in this repo encode. The author's actual documents are **not** included — they live in a
private workspace and are gitignored. The committed `sample-run/` is a fictional re-creation of that
shape.
