# Retrospective, Review, Refinement & Planning — 5 Aug 2026

Combined session: retrospective, sprint review, backlog refinement, and sprint planning in one sync.

| | |
|---|---|
| **Date** | Wed 5 Aug 2026 (Slot B) |
| **Type** | Retrospective + Review + Refinement + Planning |
| **Attendees** | Team (everyone participated in the retro) |
| **Facilitator** | Loredana Lungu (Scrum Master) |
| **Product Owner** | Sid Ahmed Mahieddine |
| **Retro board** | [MacroCrypto AI Team Retrospective](https://github.com/orgs/TheQuintet/projects/4) |

---

## Key outcomes

- Main theme: **improve collaboration, raise development velocity, and remove the PR review bottleneck**.
- PR reviews were identified as the single biggest drag on sprint velocity — reviews depend on too few people and time zones delay merges.
- Backend progress is solid; frontend needs more visible UI work.
- No new scope this sprint — finish the existing backlog first.
- The team found this more structured format (four ceremonies, clear ownership) more productive than previous meetings.

---

## Retrospective

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
| Share UI designs and prototypes earlier | Frontend team (Loredana, Kingson) | Next sprint |
| Improve PR review workflow and reduce review bottlenecks | Team leads (Sid, Mael) | Next sprint |
| Investigate GitHub settings for requesting multiple reviewers on PRs | Team | Next sprint |
| Centralize documentation and discussions (e.g. GitHub Discussions) | Team | Next sprint |
| Focus on completing current sprint work before creating additional issues | Everyone | Ongoing |
| Prepare and group retro items before each retro to make discussion efficient | Loredana | Before next retro |

---

## Sprint review

| Area | Status |
|------|--------|
| **Backend** | Good progress overall; several features implemented; the team agreed backend is moving in the right direction |
| **Frontend** | Configuration work progressing; more visible UI work needed — working screens would improve team motivation and collaboration |

---

## Refinement

The team agreed refinement should clarify existing work rather than introduce new features.

| Item | Outcome |
|------|---------|
| New issues | Avoid creating many new issues while previous sprint work is unfinished |
| Current backlog | Continue completing it before expanding scope |
| Refinement focus | Clarify existing work; no new features pulled in |

---

## Sprint planning

The team discussed whether the current sprint goals are achievable and agreed they are — **if**:

- PR reviews become faster.
- AI tools are used where appropriate.
- Members work more in parallel instead of completing issues strictly one at a time.

No new scope was added; the sprint continues with the existing backlog.

---

## Decisions

| Topic | Decision |
|-------|----------|
| **Sprint scope** | Continue the existing sprint backlog before adding new work |
| **PR reviews** | Make reviews faster and distribute review responsibility by area (frontend / backend) |
| **Communication** | Improve daily communication using Agile practices (daily updates, visible blockers) |
| **Collaboration** | Keep strengthening frontend ↔ backend collaboration |
| **Retro prep** | Prepare retrospective items before each retro and group similar topics in advance |

---

## Sprint metrics

| Metric | Value |
|--------|-------|
| Stories completed | _not tracked in this session_ |
| Velocity | _not tracked — PR review latency identified as the limiting factor_ |
| Blockers | PR review turnaround (highest priority) |

---

## Carried over

Agenda items planned for this session that were not covered — carry to the next sync:

- [ ] **Auth system** — decide which authentication approach to use for the app (options, trade-offs, recommendation)
- [ ] **Turborepo** — discuss whether/how to adopt Turborepo for the monorepo (fit with current `frontend/` + `services/` layout, pros/cons)

---

## Key takeaways

- Noticeable technical progress, particularly on the backend.
- Collaboration is improving and roles are becoming clearer.
- The largest obstacle is the PR review process, which directly affects sprint velocity.
- Stronger Agile habits — daily updates, documentation, preparation, and distributed ownership — are expected to improve productivity in future sprints.

---

## Notes

- Retro items were captured on the [Team Retrospective](https://github.com/orgs/TheQuintet/projects/4) board during the session; outcomes copied here.
- Previous session: [29 Jul 2026 Refinement & Planning](./2026-07-29-refinement-and-planning.md).

---

## Next meeting

See [recurring sync schedule](../team-roles.md#recurring-meetings-through-14-oct-2026) — next sync **Wed 12 Aug 2026, Slot B**.
