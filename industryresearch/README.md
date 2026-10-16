# industryresearch/

Shared phrasing references, one per industry and domain, built by Phase 26
([`../prompts/26-industry-language.md`](../prompts/26-industry-language.md)).

```
industryresearch/<industry>/<domain>/industry-language.md
```

Each file describes how people at a target level in one field write about their work: what strong
profiles do, bullet templates, level vocabulary (IC and leadership), a verb bank, noun phrases, keyword
clusters with honest counts, and rewrite rules Ascend applies. It is **phrasing guidance only**. Facts
about a user always come from that user's own evidence.

## Slugs

Two lowercase slugs, letters and digits only. The intake proposes them and the user confirms.

| Field | industry | domain |
|---|---|---|
| Cloud security engineering | `tech` | `cloudsecurity` |
| Investigative journalism | `media` | `journalism` |
| Investment banking | `finance` | `investmentbanking` |
| Product design | `tech` | `productdesign` |

Pick the pair another person in the same field would pick, so the reference gets reused.

## Freshness

```
python3 tools/industry_research.py status <industry> <domain>   # FRESH | STALE | MISSING | UNDATED
python3 tools/industry_research.py list
```

Every run checks. A file whose `**Built:**` stamp is in the current calendar month is reused. Anything
older, missing, or undated is rebuilt. Git history keeps earlier versions.

## Privacy (absolute)

These files are shared and may be committed to a public repo, so they hold no personal data:

- no names, handles, photos, or profile URLs
- no employer named next to an individual's career path or tenure (employer types only)
- phrases are short fragments or patterns, never a copied bullet
- nothing about the person running Ascend. Their mapping goes in `workspace/<name>/industry-fit.md`

## Shipped

| Path | Built | Sample |
|---|---|---|
| [`tech/cloudsecurity/industry-language.md`](tech/cloudsecurity/industry-language.md) | 2026-10-16 | 49 profiles + 1 posting |
