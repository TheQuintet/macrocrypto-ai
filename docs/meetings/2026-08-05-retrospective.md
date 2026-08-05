# Retrospective, Review, Refinement & Planning — 5 Aug 2026

Combined session: **Sprint 2** retrospective and review, plus refinement and **Sprint 3** planning in one sync.

| | |
|---|---|
| **Date** | Wed 5 Aug 2026 (Slot B) |
| **Type** | Retrospective + Review + Refinement + Planning |
| **Sprint** | Sprint 2 closed → Sprint 3 started |
| **Attendees** | Team (everyone participated in the retro) |
| **Facilitator** | Loredana Lungu (Scrum Master) |
| **Product Owner** | Sid Ahmed Mahieddine |
| **Retro board** | [MacroCrypto AI Team Retrospective](https://github.com/orgs/TheQuintet/projects/4) |

---

## Key outcomes

- Main theme: **improve collaboration, raise development velocity, and remove the PR review bottleneck**.
- Sprint 2 closed and Sprint 3 started; unfinished Sprint 2 work rolls into Sprint 3 (Kanban-style carryover).
- PR reviews were identified as the single biggest drag on sprint velocity — reviews depend on too few people and time zones delay merges.
- Backend progress is solid; frontend needs more visible UI work.
- No new scope in Sprint 3 — finish the carried-over backlog first.
- Turborepo will not be adopted — Docker stays the build and run tooling for the monorepo.
- The team found this more structured format (four ceremonies, clear ownership) more productive than previous meetings.

---

## Retrospective — Sprint 2

### What went well 🟢

**Collaboration**

- Backend collaboration improved significantly.
- Members worked together on software design, frontend/backend integration, and ML discussions.
- Communication between contributors is improving.

**Technical progress**

- Good progress on backend implementation.
- Repository organization and project structure keep improving.
- Members started reviewing each other's work and contributing fixes.

**Team engagement**

- Everyone participated in the retrospective and feedback was constructive.
- The meeting was more structured and productive than previous ones, with clearer ownership of responsibilities.

### What went wrong / to improve 🔴

| # | Topic | Current issues | Ideas discussed |
|---|-------|----------------|-----------------|
| 1 | **PR review process** (highest priority) | Reviews depend on a small number of people; different time zones delay merges; developers wait for reviews before continuing, which slows the sprint considerably | Distribute review responsibility — frontend leads review frontend PRs, backend leads review backend PRs; let knowledgeable members review in their area; improve reviewer assignment so multiple reviewers can be requested; reduce waiting while keeping code quality |
| 2 | **Agile discipline** | Daily updates and blockers are not posted consistently | Post daily updates, record blockers, share planned work even during busy periods, keep work visible — a team habit, not a reporting exercise |
| 3 | **Documentation** | Ideas and discussions are spread across Slack and other channels | Move important discussions into GitHub Discussions (or another central place) so information stays searchable |
| 4 | **UI collaboration** | Frontend mockups and WIP designs are shared too late | Share earlier for faster feedback, better alignment, earlier design decisions, and stronger frontend/backend collaboration |

### What we'll change 🔵

| Action item | Owner | Due date |
|-------------|-------|----------|
| Post daily status updates (Yesterday / Today / Blockers) | Everyone | Daily, from 6 Aug 2026 |
| Add retrospective items throughout the sprint, not only before the meeting | Everyone | Ongoing |
| Share UI designs and prototypes earlier | Frontend team (Loredana, Kingson) | Sprint 3 |
| Improve PR review workflow and reduce review bottlenecks | Team leads (Sid, Mael) | Sprint 3 |
| Investigate GitHub settings for requesting multiple reviewers on PRs | Team | Sprint 3 |
| Centralize documentation and discussions (e.g. GitHub Discussions) | Team | Sprint 3 |
| Focus on completing carried-over Sprint 2 work before creating additional issues | Everyone | Ongoing |
| Prepare and group retro items before each retro to make discussion efficient | Loredana | Before next retro |

---

## Sprint review — Sprint 2

| Area | Status |
|------|--------|
| **Backend** | Good progress overall; several features implemented; the team agreed backend is moving in the right direction |
| **Frontend** | Configuration work progressing; more visible UI work needed — working screens would improve team motivation and collaboration |

---

## Refinement

The team agreed refinement should clarify existing work rather than introduce new features.

| Item | Outcome |
|------|---------|
| New issues | Avoid creating many new issues while Sprint 2 carryover is unfinished |
| Carried-over backlog | Continue completing it before expanding Sprint 3 scope |
| Refinement focus | Clarify existing work; no new features pulled into Sprint 3 |

---

## Sprint planning — Sprint 3

The team discussed whether the Sprint 3 goals are achievable and agreed they are — **if**:

- PR reviews become faster.
- AI tools are used where appropriate.
- Members work more in parallel instead of completing issues strictly one at a time.

No new scope was added; Sprint 3 starts with the Sprint 2 carryover.

---

## Decisions

| Topic | Decision |
|-------|----------|
| **Sprint scope** | Sprint 3 continues the Sprint 2 carryover before adding new work |
| **PR reviews** | Make reviews faster and distribute review responsibility by area (frontend / backend) |
| **Communication** | Improve daily communication using Agile practices (daily updates, visible blockers) |
| **Collaboration** | Keep strengthening frontend ↔ backend collaboration |
| **Retro prep** | Prepare retrospective items before each retro and group similar topics in advance |
| **Monorepo tooling** | **Turborepo will not be adopted** — we use **Docker** for building and running the `frontend/` + `services/` monorepo |

---

## Sprint metrics — Sprint 2

| Metric | Value |
|--------|-------|
| Stories completed | _not tracked in this session_ |
| Velocity | _not tracked — PR review latency identified as the limiting factor_ |
| Blockers | PR review turnaround (highest priority) |

---

## Carried over

Agenda items planned for this session — unchecked items carry to the next sync:

- [ ] **Auth system** — decide which authentication approach to use for the app (options, trade-offs, recommendation)
- [x] **Turborepo** — decided: not adopting it, we stay with Docker (see [Decisions](#decisions))

---

## Key takeaways

- Noticeable technical progress, particularly on the backend.
- Collaboration is improving and roles are becoming clearer.
- The largest obstacle is the PR review process, which directly affects sprint velocity.
- Stronger Agile habits — daily updates, documentation, preparation, and distributed ownership — are expected to improve productivity in future sprints.

---

## Notes

- Retro items were captured on the [Team Retrospective](https://github.com/orgs/TheQuintet/projects/4) board during the session; outcomes copied here.
- Previous session: [29 Jul 2026 Refinement & Planning](./2026-07-29-refinement-and-planning.md) — where Sprint 2 was planned, including the 1-week cadence and Kanban-style carryover rule applied here.

---

## Next meeting

See [recurring sync schedule](../team-roles.md#recurring-meetings-through-14-oct-2026) — next sync **Wed 12 Aug 2026, Slot B**.
