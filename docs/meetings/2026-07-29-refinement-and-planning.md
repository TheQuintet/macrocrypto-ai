# Refinement & Planning — 29 Jul 2026

Combined backlog refinement and Sprint 2 planning session.

| | |
|---|---|
| **Date** | Wed 29 Jul 2026 |
| **Type** | Refinement + Planning |
| **Sprint** | Sprint 2 (planning) |
| **Attendees** | Team (async/sync alignment) |
| **Facilitator** | Loredana Lungu (Scrum Master) |
| **Product Owner** | Sid Ahmed Mahieddine |

---

## Key outcomes

- Aligned on Agile/Scrum process, sprint structure, and communication norms.
- Reviewed Sprint 2 scope; frontend tasks were deemed over-scoped for the current week given Kingson's limited availability.
- Backend progress confirmed on track — Mael refactoring services into the new microservices architecture.
- Decisions made on frontend tech stack, diagramming approach, and roadmap documentation.

---

## Decisions

| Topic | Decision |
|-------|----------|
| **Sprint duration** | **1-week sprints** to maximize practice and iteration speed |
| **Sprint scope** | Complete as many frontend tasks as possible; unfinished items **roll to the next sprint** (Kanban-style) |
| **Daily coordination** | **No live daily standup.** **Async** updates in domain Slack (`#mc-frontend`, `#mc-backend`, `#mc-ml-model`, `#mc-software-design`) — not only the general channel |
| **Frontend tech stack** | TypeScript, Vite, ShadCN, Tailwind CSS, TanStack Query, Vitest + Testing Library. Redux considered too heavy; **Zod proposed** as the lightweight alternative |
| **Frontend WebSockets** | **Out of scope for now** — keep issues in the sprint but do not work on them (medium priority) |
| **Diagrams** | Start with a **use case diagram**; Loredana creates, Mael supervises; tool TBD (Mermaid, PlantUML, or collaborative web app) |
| **Roadmap dates** | Sid adds start/target dates to epics and features for visibility — **not binding deadlines** |
| **PR process** | **One issue per PR**; linked PRs auto-close issues; blocked items need a comment with reason + flag in daily standup |

---

## Role assignments

| Role / area | Owner | Focus this sprint |
|-------------|-------|-------------------|
| Scrum Master | Loredana | Process alignment, meeting notes, retro facilitation, frontend architecture setup, use case diagram |
| Product Owner | Sid | Sprint/backlog management, roadmap dates, issue creation, backend + testing |
| Backend | Mael | Refactor monolith services into the new microservices architecture |
| Frontend | Loredana + Kingson | Loredana starts immediately; Kingson picks up mid-next-month when capacity eases |
| ML Model | Richard | Owns the ML workstream |

---

## Stories / scope notes (refinement)

| Item | Outcome | Ready for sprint? |
|------|---------|-------------------|
| Frontend architecture / app setup | Description ready (Loredana); waiting on Sid to create the ticket. Architecture doc drafted and shared via Slack | Yes (blocker for FE) |
| Frontend component tasks | Over-scoped for this week (Kingson limited) — pull what Loredana can finish | Partial |
| Frontend WebSocket issues (e.g. T4.8, T4.12) | Keep in sprint; **do not work** yet (medium priority) | Parked |
| Backend microservices refactor | Confirmed on track for Mael | Yes |
| Use case diagram | Waiting on Sid to create the issue so Loredana can start | Yes |

---

## Blockers

| Blocker | Impact | Notes |
|---------|--------|-------|
| Kingson availability | Frontend capacity this month | Overloaded with work/school; expects capacity mid-next-month |
| Frontend architecture setup ticket missing | Blocks component issues | Loredana finished the issue description — waiting on Sid to create the ticket |
| Use case diagram ticket missing | Blocks Loredana from starting diagram work | Waiting on Sid to create the issue |

---

## Pending confirmation

- [x] Frontend architecture document drafted by Loredana → shared via Slack; aligned with Kingson offline in the frontend Slack channel
- [ ] Diagramming tool selection (collaborative web app vs Mermaid/PlantUML)
- [x] Lightweight state-manager alternative to Redux — Loredana researched and proposed **Zod** instead of Redux

---

## Action items

| Owner | Action | Status |
|-------|--------|--------|
| Loredana | Create frontend architecture setup issue (send description to Sid for ticket creation) | ✅ Done (description ready — Sid to create the ticket) |
| Loredana | Draft frontend architecture document; schedule short sync with Kingson | ✅ Done (doc shared via Slack; aligned with Kingson offline in `#frontend`) |
| Loredana | Begin use case diagram (Mael supervises) | ⏸️ Blocked — needs Sid to create the issue |
| Loredana | Prepare retro board (what went well / improvements / action items) for next meeting | ⏳ Open |
| Loredana | Set recurring weekly meeting (Wednesday or Thursday, late evening) | ✅ Done (set 30 Jul 2026) |
| Sid | Create frontend architecture setup issue from Loredana's description | ⏳ Open — **needed so FE setup can start** |
| Sid | Add start/target dates to epics and features for roadmap visibility | ⏳ Open |
| Sid | Create issue for use case diagram in current sprint | ⏳ Open — **needed so Loredana can start** |
| Mael | Refactor previously implemented services into the new microservices architecture | ⏳ Open |
| Kingson | Post daily standup in frontend Slack channel; check in on progress when possible | ⏳ Open |

---

## Next meeting

**Recurring weekly** — set by Loredana on 30 Jul 2026. After a couple of weeks comparing availability, the team locked **Wednesday Slot B** (late evening) through **14 Oct 2026**. Full date list: [Team availability](../team-roles.md#recurring-meetings-through-14-oct-2026).

**Next sync (Wed 5 Aug 2026):** [Retrospective, Review, Refinement & Planning](./2026-08-05-retrospective.md) — both extra agenda items were decided there: **Auth0** for authentication, and no Turborepo (Docker stays).
