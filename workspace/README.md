# workspace/ — your private output lives here (never committed)

Everything Ascend generates about **you** lands in `workspace/<your-name>/` and is
ignored by git (see the repo `.gitignore`). Your LinkedIn export, your resume, your master
resume, your job folders, and the two HTML dashboards are all personal data — they stay on
your machine and are never pushed to GitHub.

When you run the system (see the repo `README.md`), the orchestrator creates:

```
workspace/<your-name>/
├── inputs/                      # YOU drop these in
│   ├── linkedin-export/         # your downloaded LinkedIn data (unzipped)
│   └── current-resume.(pdf|md|docx)
├── linkedin-analysis.html       # Phase 1 output — open in a browser
├── resume-audit.md              # Phase 2 output
├── master-resume.md             # Phase 3 output (your bullet database)
├── job-queue.md                 # Phase 4 output — 15+ ranked jobs
├── interview-packet/            # Phase 6 output — cross-job prep
├── jobs/                        # Phase 5 output — one folder per job (8 files each)
│   ├── 01-<company>-<role>/
│   └── ...
└── start-here.html              # Phase 7 output — your navigator. OPEN THIS FIRST.
```

To start a fresh run for a different person, create a new `workspace/<name>/` — runs never
collide. Delete a workspace folder to wipe that person's data entirely.
