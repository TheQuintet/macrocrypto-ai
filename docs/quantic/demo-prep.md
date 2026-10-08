# Capstone demo prep

**User story:** As a team, we want one compliant Capstone demo video that meets Quantic rules.

Check boxes on **[#752](https://github.com/TheQuintet/macrocrypto-ai/issues/752)** or in this file (keep in sync).

**Last planning sync:** [7 Oct 2026 meeting notes](../meetings/2026-10-07-final-demo-planning.md).

---

## Key links (repo, board, docs)

Use these on camera during the demo and in the README / [deliverables](./deliverables.md) checklist.

| Resource | Link |
|----------|------|
| **GitHub repository** | [TheQuintet/macrocrypto-ai](https://github.com/TheQuintet/macrocrypto-ai) |
| **Team Workflow board** | [GitHub Project #6](https://github.com/orgs/TheQuintet/projects/6) — planning, sprints, roadmap |
| **Three sprints (capstone)** | [Sprint 1 / milestone 1](https://github.com/TheQuintet/macrocrypto-ai/milestone/1) · [Sprint 2 / milestone 2](https://github.com/TheQuintet/macrocrypto-ai/milestone/2) · [Sprint 3 / milestone 3](https://github.com/TheQuintet/macrocrypto-ai/milestone/3) — show these on camera (focused scope vs full board) |
| **Current sprint** | [Current sprint view](https://github.com/orgs/TheQuintet/projects/6/views/7) |
| **Sprint planning** | [Team Planning](https://github.com/orgs/TheQuintet/projects/6/views/1) |
| **Sprint 2 retro (evidence)** | [Retro board view](https://github.com/orgs/TheQuintet/projects/6/views/10) + [5 Aug 2026 notes](../meetings/2026-08-05-retrospective.md) — full retro with board items; later sprints: improvements in [meeting notes](../meetings/) |
| **Sprint milestones** | [GitHub Milestones](https://github.com/TheQuintet/macrocrypto-ai/milestones) |
| **Async coordination** | Domain Slack: `#mc-frontend`, `#mc-backend`, `#mc-ml-model`, `#mc-software-design` — **no daily standup**; whole-team `#capstone-project-group` |
| **Design documentation** | [Software design & architecture](../design/README.md) (`docs/design/`) |
| **Testing documentation** | [Local and CI/CD testing](../test%20documents/local-and-ci-cd-tests.md) |
| **Meeting notes (Scrum)** | [docs/meetings/](../meetings/) |

Full board list: [Project workflow — Project resources](../project-workflow.md#project-resources).

---

## Schedule (team)

| Milestone | When |
|-----------|------|
| **Code freeze** | Thu **8 Oct 2026** — integration complete; no dev on recording day |
| **Recording** | Sat **10 Oct 2026**, ~**18:00** (TZ TBD) — Loredana sends Zoom invite |
| **Submission** | **Sunday** after recording (exact deadline/TZ TBD) |

---

## Content & format (Quantic rules)

- **15–20 minutes** · **one `.mp4`** on **Google Drive** (anyone with the link can view)
- **All 5** on camera, **each speaks**, show **government ID** (name + photo legible)
- **Screen share** the **deployed** app; BTC trader + prediction scope
- **Not** a PowerPoint of separate clips, PDF, or ZIP
- **One teammate** submits on Quantic dashboard + signed Group Project Agreement
- Tell **one continuous storyline** (~**4 min** per segment); dummy data for **alerts** only — say so on camera

[policies](./policies.md#presentation-standards) · [deliverables](./deliverables.md)

---

## Prerequisites (before rehearsing or recording)

- [ ] **Deploy host** — **Vercel** (primary); env vars set (Mael + Sid + Loredana). Fallback: Railway or Render (paid tier if memory-limited)
- [x] **Deploy account owner** — **Loredana** (Vercel); post confirmation in `#capstone-project-group`
- [ ] **Deploy URL** — public link works; in README + [deliverables](./deliverables.md)
- [ ] **Smoke test** — health endpoints on deploy; **CI pipelines green** (show pipelines on camera; full post-deploy smoke not required)
- [ ] **Documents** — [design](../design/README.md) + [testing](../test%20documents/local-and-ci-cd-tests.md) docs linked from README (consolidated software-design MD + SVG UML when ready — [7 Oct decisions](../meetings/2026-10-07-final-demo-planning.md))
- [ ] **Board & grader** — [Team Workflow board](https://github.com/orgs/TheQuintet/projects/6) (+ [Sprint 2 retro](https://github.com/orgs/TheQuintet/projects/6/views/10)) in README; ≥3 sprints visible; explain retro approach per [project workflow](../project-workflow.md#retrospective); `quantic-grader` invited (Sid)
- [x] **Google Drive / recording owner** — Loredana (Zoom record → Drive link; anyone with link can view)
- [ ] **Quantic submitter** — one person named for dashboard + Group Agreement
- [ ] **Scripts** — each member fills their section in [demo-script.md](./demo-script.md) by **8 Oct**; **Loredana** merges the team’s scripts into one narrative and builds the recording plan from what is provided

---

## Agreed run-of-show (~18 min)

| # | ~Time | Who | Focus |
|---|-------|-----|--------|
| 1 | ~4:00 | **Kingson** | Opening, welcome, handoff into story |
| 2 | ~4:00 | **Sid** | Origin, problem, solution, overview; **AI service** (6 models, champion, correlation job) |
| 3 | ~4:00 | **Mael** | Architecture, stack, 3 services, RabbitMQ, Redis, CI/CD, link to software design docs |
| 4 | ~4:00 | **Richard** | Data gathering and preprocessing research |
| 5 | ~4:00 | **Loredana** | Scrum (board, sprints, notes, retro) + **frontend alerts** (dummy data called out) |
| 6 | ~4:00 | **Kingson** | Dashboard, charts, forecast, **closing live demo** on deploy URL |

Plus **intros + government IDs** per Quantic rules (typically at the start of the recording).

- [x] Run-of-show order agreed (**7 Oct 2026**)
- [ ] Merged script and recording plan match run-of-show ([demo-script.md](./demo-script.md)) — **Loredana**, after member sections are in by **8 Oct**

---

## Rehearse each block (optional tick as you prep)

- [ ] Intros + IDs — all
- [ ] Opening — Kingson
- [ ] Problem, product & AI service — Sid
- [ ] Architecture & platform — Mael
- [ ] Data & preprocessing — Richard
- [ ] Agile process & alerts — Loredana
- [ ] Dashboard, forecast & close — Kingson

---

## Record

- [ ] Zoom scheduled **Sat 10 Oct ~18:00** — all 5 confirmed (Loredana)
- [ ] Deploy live; alerts use dummy data with on-camera disclaimer
- [ ] Optional dry run timed (15–20 min)
- [ ] Mael backup pre-record for his segment (connectivity fallback)
- [ ] Final `.mp4` on Drive; link in README / deliverables
- [ ] Quantic dashboard submit + Group Agreement
- [ ] **No repo changes after submit** unless Quantic (Katie) approves

Close **#752** when all boxes above are done.
