# Capstone demo prep

Operational guide for **[§5 Video presentation](./deliverables.md#5-video-presentation)** only.

| | |
|---|---|
| **Submission checklist (all 5 deliverables)** | **[Deliverables](./deliverables.md)** — URLs, status, requirements, [pre-submission checklist](./deliverables.md#pre-submission-checklist) |
| **Issue tracker** | [#752](https://github.com/TheQuintet/macrocrypto-ai/issues/752) — tick **recording** boxes here or in this file (keep in sync) |
| **Speaking script** | [demo-script.md](./demo-script.md) — Loredana merges sections into one narrative |
| **Last planning sync** | [7 Oct 2026 meeting notes](../meetings/post-sprint-9-2026-10-07-final-demo-planning.md) |

**On camera:** screen-share from [Deliverables](./deliverables.md) (§1 repo · §2 deploy · §3 design/testing · §4 board + [Sprint 1–3](./deliverables.md#4-agile-task-board)). Process detail (async Slack, retro): [Agile & sprints](../project-workflow.md).

---

## Schedule (team)

| Event | When |
|-------|------|
| **Code freeze** | Thu **8 Oct 2026** — integration complete; no dev on recording day |
| **Recording** | Sat **10 Oct 2026**, ~**18:00** (TZ TBD) — Loredana sends Zoom invite |
| **Submission** | **Sunday** after recording (exact deadline/TZ TBD) |

---

## Content & format (Quantic rules)

- **15–20 minutes** · **one `.mp4`** on **Google Drive** (anyone with the link can view)
- **All 5** on camera, **each speaks**, show **government ID** (name + photo legible)
- **Screen share** the **deployed** app ([§2 URL](./deliverables.md#2-deployed-application)); BTC trader + prediction scope
- **Not** a PowerPoint of separate clips, PDF, or ZIP
- **One teammate** submits on Quantic dashboard + signed Group Project Agreement
- Tell **one continuous storyline** (~**4 min** per segment); dummy data for **alerts** only — say so on camera

Details: [§5 requirements](./deliverables.md#5-video-presentation) · [Presentation standards](./policies.md#presentation-standards)

---

## Recording prerequisites

Finish **[Deliverables §1–§4](./deliverables.md#mandatory-submissions)** before rehearsing. Additional **video-only** prep:

- [x] **Deploy host (frontend)** — **Cloudflare Workers** (free plan, `frontend/wrangler.jsonc`); live at the [§2 URL](./deliverables.md#2-deployed-application) with simulated data. Vercel was dropped (Hobby plan can't deploy from a private org repo)
- [ ] **Deploy host (backend)** — one **Hetzner Cloud VM** (4 vCPU, 8–16 GB RAM, Ubuntu 24.04) running **Docker Compose** with the prod override, behind nginx/TLS on `api.<domain>`. See [deployment platform analysis](../guides/deployment-platform-analysis.md#deployment-of-the-backend)
- [ ] **Live API connection** — `VITE_API_GATEWAY_BASE_URL` set on the Worker and redeployed; `CORS_ALLOW_ORIGINS` set on the VM; site shows live data instead of simulated data. If not done by recording day, say on camera that the data is simulated
- [x] **Deploy account owner** — **Loredana** (Cloudflare); post confirmation in `#capstone-project-group`
- [ ] **Smoke test on deploy** — `https://api.<domain>/health` returns OK; `docker compose ps` shows all containers healthy; **CI pipelines green** (show pipelines on camera; full post-deploy smoke not required)
- [x] **Google Drive / recording owner** — Loredana (Zoom record → Drive link; anyone with link can view)
- [ ] **Quantic submitter** — one person named for dashboard + Group Agreement
- [ ] **Scripts** — each member fills [demo-script.md](./demo-script.md) by **8 Oct**; **Loredana** merges and builds the recording plan
  - Provided: **Kingson** ✅, **Loredana** ✅, **Mael** ✅ · Not provided: **Sid** ❌ · Pending: **Richard**

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
- [ ] Final `.mp4` on Drive; update [§5 URL](./deliverables.md#5-video-presentation) on Deliverables
- [ ] Quantic dashboard submit + Group Agreement
- [ ] **No repo changes after submit** unless Quantic (Katie) approves

Close **#752** when recording tasks above are done and **[Deliverables](./deliverables.md)** is complete.
