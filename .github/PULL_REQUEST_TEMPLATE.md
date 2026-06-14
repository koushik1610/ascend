## What this changes

<!-- one-paragraph summary -->

## Checklist
- [ ] **No personal data committed** — `git status` shows nothing personal; ran `git check-ignore` on a
      sample `workspace/…` path (it's ignored) and on the system files I touched (they're tracked).
- [ ] If I touched a **dashboard template**: extracted the JSON block and `JSON.parse`'d it ✓, and
      `node --check`'d the render `<script>` ✓.
- [ ] If I touched **`.gitignore`**: verified it still ignores personal data AND still tracks system files.
- [ ] Preserves the principles: honesty gates · selection-not-invention · self-contained offline
      dashboards · field-agnostic · person-agnostic.
- [ ] Updated `CHANGELOG.md` under "Unreleased."

## Notes for reviewers
<!-- anything tricky, trade-offs, follow-ups -->
