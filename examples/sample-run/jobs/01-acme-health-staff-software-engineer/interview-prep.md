<!-- 🧪 FICTIONAL SAMPLE: invented loop and plan. Study plan for a SOFTWARE ENGINEERING loop. -->

# Interview Prep, Acme Health · Staff Software Engineer, Platform

## 1. Loop structure (fill in after recruiter screen)
- Recruiter screen (30 min): positioning, level, remote policy, comp band. `VERIFY:` round mix.
- Hiring-manager screen (45 min): role thesis, platform philosophy.
- Coding, 2 rounds (45–60 min each): data structures and algorithms.
- System design (60 min): D1 and D2 as anchors.
- Code review or debugging (45 min, `VERIFY:`).
- Values panel (45 min): an engineer from a product team plus a PM.

## 2. Study-areas table (gap-ranked; ~30 h total)
| Topic | Priority | Est. hours |
|---|---|---|
| Coding reps: graphs, intervals, heaps, hash maps (timed, in Go) | P0 | 10 |
| System design reps: deploy pipeline, rate limiter, job scheduler | P0 | 7 |
| D1 deploy-platform walkthrough, 60-sec + probing beats | P0 | 3 |
| Code-review drill: planted-bug PRs (races, timeouts, retries) | P1 | 3 |
| Health ramp: HIPAA basics, audit logging (VERIFY specifics) | P1 | 3 |
| Behavioral S1–S5 reps (esp. S2 influence, S3 conflict) | P1 | 3 |
| Acme Health values re-read + personal "why Acme Health" draft | P2 | 1 |

## 3. Set-pieces to rehearse (draw/do)
- **D1, deploy-platform architecture** (manifest → controller → Kubernetes; Terraform; canary and
  rollback): draw it cold in five minutes.
- **D2, latency work**: the measure → fix → verify loop with real numbers.
- **Coding**: say the brute force first, then the better approach, then test edge cases out loud.

## 4. Gap areas (verbatim handling lines)
- *No manager title:* "I mentor 3–4 engineers and run our design review, and I'm targeting Staff IC
  scope, not management."
- *New to health:* "Audit and access constraints aren't new from PCI work; I'd ramp on your HIPAA
  controls before changing the platform."
- *No ML:* "I've built around a model endpoint; I haven't trained or served models."

## 5. Week-by-week plan
- **Week 1, fundamentals:** 2 coding problems a day; lock D1 and D2 walkthroughs; HIPAA reading.
- **Week 2, design:** one full system design a day, timed; one code-review drill every other day.
- **Week 3, behavioral + mocks:** S1–S5 reps; one mock coding round; one mock system design; refine
  the closer; logistics.

## 6. Day-before checklist
- [ ] 5 stat lines automatic (metrics-cheatsheet.md).
- [ ] Number discipline: never-say list reviewed (codename, raw internals, comp).
- [ ] Closer rehearsed.
- [ ] Acme Health values + JD re-read.
- [ ] Editor and language set up for the coding tool; a whiteboard tool open for design.
- [ ] Logistics: links, time zone (Austin/CT), interviewer names (fill after scheduling), water.
