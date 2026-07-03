# workspace/ — your private output lives here (never committed)

Everything Ascend generates about **you** lands in `workspace/<your-name>/` and is
ignored by git (see the repo `.gitignore`). Your LinkedIn export, your resume, your master
resume, your job folders, and the two HTML dashboards are all personal data — they stay on
your machine and are never pushed to GitHub.

When you run the system (see the repo `README.md`), the orchestrator creates:

```
workspace/<your-name>/
├── intake.md                    # the run's source of truth (from the intake interview)
├── .ascend-state.json           # run manifest — makes the run resumable
├── inputs/                      # YOU drop these in
│   ├── linkedin-export/         # your downloaded LinkedIn data (unzipped)
│   └── current-resume.(pdf|md|docx)
├── linkedin-analysis.html       # Phase 1 — open in a browser
├── master-resume.md             # Phase 3 — your bullet database (ATS/keyword audit folded in)
├── resume.json + a master PDF   # Phase 3 — the public master résumé (builder-rendered, one page)
├── job-queue.md                 # Phase 4 — 15+ ranked jobs, each with a Fit Score + link status
├── interview-packet/            # Phase 6 — thin cross-job prep (enriched on demand)
├── jobs/                        # Phase 5 — CORE apply pack per committed job (top 3–5):
│   ├── 01-<company>-<role>/     #   resume.md · outreach.md · application-log.md
│   │                            #   (+ resume.json + one-page PDF; deep prep added on demand
│   └── ...                      #    when a screen books — see "Ascend prep <NN>")
└── start-here.html              # Phase 7 — your navigator. OPEN THIS FIRST.
```

On-demand outputs land here too as you use them: `network-map.md`, `answer-bank.md`,
`daily-briefing.md`, and each job's deep-prep files.

To start a fresh run for a different person, create a new `workspace/<name>/` — runs never
collide. Delete a workspace folder to wipe that person's data entirely.
