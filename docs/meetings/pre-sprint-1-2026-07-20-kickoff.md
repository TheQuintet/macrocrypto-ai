# Capstone Kickoff — 20 Jul 2026

| | |
|---|---|
| **Date** | Mon 20 Jul 2026 (20:00–21:32, GMT+3) |
| **Type** | Kickoff |
| **Sprint** | Pre-Sprint 1 (before board Sprint 1 starts 4 Aug) |
| **Attendees** | Loredana Lungu, Sid, Kingson, Mael, Richard |
| **Facilitator** | Loredana Lungu (Scrum Master) |
| **Product Owner** | Sid Ahmed Mahieddine |

---

## Key outcomes

- First full-team session. The team went through the working process, roles, channels and the GitHub repo, docs and board. No sprint has started.
- Sid summarised the project scope: predict BTC price by linking crypto market data with macro-economic indicators, because BTC is traded in USD.
- Sid proposed a microservices architecture (three services, RabbitMQ). Docker-based infrastructure and data integration make up the Sprint 1 foundation.
- Quantic grading expects a deployed, working application with a URL, design and testing documents, and an agile task board. Loredana keeps the supporting documentation in the repo's Docs folder.
- The next session will be a refinement of the backlog, with sprint planning after it.

---

## Decisions

| Topic | Decision |
|-------|----------|
| **Team roles** | Defined and agreed (documented in the Docs folder). Loredana: Scrum Master, facilitator and documentation owner. Sid: Product Owner (scope, milestones, issues, board). Mael: full-stack; a code-owner role was mentioned (unclear, see Open questions). Kingson: frontend (primary) and full-stack (secondary). Richard: testing and documentation support (suggested). |
| **Meeting cadence** | Whole team meets together for decisions, about once a week, not daily. Day-to-day coordination is asynchronous. |
| **Next session** | Refinement first (review backlog tasks, brainstorm, clarify), then sprint planning. Proposed for the weekend (25–26 Jul), not yet fixed. |
| **Working model** | Any member can take over another member's task when blocked. Blockers are raised as early as possible. Team aims to deliver what it commits to in each sprint. |
| **Slack channels** | Separate channels per domain: frontend, backend, ML model (Sid's proposal, agreed in principle). Members outside a domain join read-only to keep history. Loredana creates the channels. Project links are pinned in Slack. |
| **Code and task platform** | GitHub for code, docs, Issues, milestones and the project board. Branch naming, PR, review and merge rules will be written into the docs. |
| **Definition of done** | Proposed by Loredana: merged work includes testing, has no known bugs, and includes unit tests on the frontend (not full coverage). Kingson responded positively; treat as provisional until written into the docs. |
| **Architecture** | Microservices, stated by Sid as already picked. Current plan is three services with RabbitMQ. Team confirmation not explicit. |
| **Infrastructure** | Docker-based setup. Infrastructure and data integration are Sprint 1 foundation items. |
| **Sprint length** | Proposed by Sid: 1-week sprints to start, revisited later (possibly 2 weeks). Not confirmed. |
| **Sprint 1 scope** | Proposed foundation: infrastructure (Docker, data integration) and three platform-user user stories from Sid. Real-time BTC price view and update treated as a user story with backend and frontend parts. Final scope not agreed. |
| **Documentation** | Quantic-facing docs in the repo Docs folder (team roles, meeting templates, availability, deliverables). Meeting recordings are linked in the docs for reference. Anyone can ask for a recording to be left out. |
| **Availability** | Tracked in Notion. Each member shares availability week by week. |
| **Meeting access** | Use a Zoom passcode for future meetings instead of manually admitting participants. |

---

## Action items

| Owner | Action | Target | Status |
|-------|--------|--------|--------|
| Loredana | Create Slack channels for frontend, backend and ML model | Not set | Open |
| Loredana | Write the GitHub workflow into the docs: branch naming, PR, review, merge, and board columns | Not set | Open |
| Loredana | Add the proposed definition of done (testing, frontend unit tests) to the docs | Not set | Open |
| Loredana | Replace Kingson's email in the team roles, and send future invitations to both addresses | Next invitation | Open |
| Loredana | Set up availability tracking in Notion | Not set | Open |
| Loredana | Schedule the refinement session for the weekend, update the calendar, and sync offline | Sat 25 or Sun 26 Jul | Open |
| Loredana | Send the action-item summary to the team | After this meeting | Open |
| Loredana | Put the recording link for each meeting in the docs | After each meeting | Open |
| Loredana and Kingson | Brainstorm the frontend architecture setup together, offline | Later this week | Open |
| Sid | Share the initial Sprint 1 plan with related issues for team review | Before refinement | Open |
| Sid | Structure the sprint plan along a chronological framework (scope, user stories, requirements, technology, tools), as Richard suggested | Not set | Open |
| Sid | Push the team roles and other docs from the local worktree to the shared repo (implied, not explicitly assigned) | Not set | Open |
| All | Clone the repo, set up the project locally (including Docker), and review the docs and board | Within the week | Open |
| All | Share availability for the coming weeks in Notion | Not set | Open |

---

## Open questions

- Sprint 1 final scope: which of the three platform-user stories and infrastructure items enter Sprint 1 (pending Sid's plan).
- Sprint length: 1 week to start was proposed. No explicit decision (unclear in transcript).
- Architecture: whether the team formally confirmed microservices, the number of services, and RabbitMQ (unclear in transcript; Loredana asked, and the answer given was indirect).
- Sid's role statement mentioned a scrum-master role and a code-owner role for Mael (unclear in transcript). Loredana is Scrum Master in all other statements.
- Milestones: Loredana wants a date-based, user-facing view. Who adds dates and when is not stated (unclear in transcript).
- Binance was mentioned in connection with the real-time BTC price story, but its role as a data source is not confirmed (unclear in transcript).
- GitHub board columns: Loredana's order (Ready, In progress, In review, Done) and Kingson's personal board differ. Final column set not agreed.
- The sprint-start feedback ("what I did yesterday, what I did today, blockers") may be a daily async update or retrospective input (unclear in transcript).
- Richard's area: testing was suggested by Loredana, and research and documentation by Kingson. Richard's ML or other ownership is not stated (unclear in transcript).
- Mael proposed a tenfold cross-validation evaluation for the ML model, similar to a previous project. Not decided.
- Frontend architecture direction is not decided.
