# Setup — for people who don't live in a terminal

Ascend runs inside **Claude Code**, a tool you drive by typing in plain English. You don't need
to be a programmer, but there are a few one-time setup steps. Take them slowly; you only do this once.

> Honest heads-up: this does require installing a developer tool and a Claude subscription, and a full
> run takes a while and uses tokens. If that's not for you, that's OK — but if you can follow these
> steps, the rest is just answering questions in chat.

---

## Step 1 — Install Claude Code (~10 min)
Follow Anthropic's official guide: **https://docs.claude.com/en/docs/claude-code**. You'll need a
Claude account with access (Pro/Max subscription or API billing). When it's installed, you can open a
terminal, go to a folder, and type `claude` to start it.

## Step 2 — Get this repo onto your computer
Option A (graphical, easiest): on the repo's GitHub page, click the green **Code** button → **Download
ZIP** → unzip it. Remember where it landed (e.g., your `Downloads` folder).

Option B (terminal): `git clone https://github.com/koushik1610/ascend.git`

## Step 3 — Download your LinkedIn data (request now — it can take up to a day)
On LinkedIn: **Me → Settings & Privacy → Data Privacy → Get a copy of your data → "The works" →
Request archive.** LinkedIn emails you a `.zip` (often in minutes, sometimes up to 24h).
**Download it and unzip it.** Inside is a folder full of `.csv` files — that folder is what Ascend
reads. You can start Ascend before it arrives; it'll do a lighter first pass and you add the export
later.

## Step 4 — Find your folder paths (the one fiddly bit)
Ascend will ask "where is your LinkedIn export folder?" and "where is your resume?" It wants the
**path** (the address of the file/folder on your computer). Easy ways to get it:

- **macOS:** drag the folder (or file) from Finder **into the terminal window** — the full path
  appears. Or right-click → hold **Option** → "Copy … as Pathname."
- **Windows:** in File Explorer, hold **Shift** + right-click the folder → "Copy as path." (If you're
  using WSL/Git Bash, paths look like `/mnt/c/Users/You/Downloads/…`.)
- **Linux:** right-click → "Copy" usually copies the path, or drag into the terminal.

You don't have to get this perfect — if a path is wrong, Ascend will tell you and ask again.

## Step 5 — Start it
In your terminal, go into the unzipped `ascend` folder and run `claude`. Then type:

```
/ascend
```

…or just say **"Run Ascend."** Answer its questions (your name, those two folder paths, the jobs you
want, where you'll work). Then let it run. It pauses to check in with you after each step — you stay in
control, and you can stop anytime and pick up later.

## Step 6 — Open your dashboard
When it's done it tells you to open **`workspace/<your-name>/start-here.html`**. Double-click it; it
opens in your browser. That's your home base.

---

## Windows note
Claude Code and these shell-style steps work most smoothly under **WSL** (Windows Subsystem for Linux)
or **Git Bash**. Plain PowerShell mostly works too, but if something looks off, WSL/Git Bash is the
recommended path. Folder paths under WSL look like `/mnt/c/Users/You/...`.

## If you get stuck
- "It can't find my LinkedIn folder" → you probably gave the path to the `.zip` instead of the
  **unzipped folder**. Unzip it first, then give the folder path.
- "Nothing's happening" → a full run is long (1–3+ hours) and does live research; it's working, not
  frozen. Ask it "where are you in the pipeline?" anytime.
- "I want to try it cheaply first" → tell it: *"Run Ascend but only Phase 1"* (just the LinkedIn
  analysis), or *"only find 3 jobs and build 1 folder."*
- Still stuck → open an issue on the repo (see the main `README.md`).

## Privacy, in one line
Everything about you is written into `workspace/<your-name>/`, which is **ignored by git** — it never
leaves your computer and is never uploaded. The dashboards even say so at the top.
