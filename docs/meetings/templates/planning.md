# Meeting Notes — Planning Sessions

Sprint planning notes: select stories, estimate, assign owners.

---

## Template

### Sprint _N_ — Planning

| | |
|---|---|
| **Date** | _TBD_ |
| **Attendees** | _TBD_ |
| **Sprint goal** | _TBD_ |

**Stories selected**

| Story | Owner | Estimate |
|-------|-------|----------|
| | | |

**Notes**

- 

---

## Sessions

### Current sprint — Planning (combined with review and refinement) — 26 Aug 2026

| | |
|---|---|
| **Date** | Wed 26 Aug 2026 |
| **Attendees** | Sid Ahmed Mahieddine, Loredana Lungu, Kingson Emma-Ochu (joined later) |
| **Sprint goal** | Alerts and frontend alert issues; API-gateway integration. Macro / ML / remaining AI work deferred to September |
| **Full notes** | [2026-08-26 Review, Refinement & Planning](../2026-08-26-review-and-planning.md) |

**Stories / focus selected**

| Story / focus | Owner | Notes |
|---------------|-------|-------|
| Alerts and frontend alert issues | Loredana | Connect to the service and test integration ASAP |
| API gateway completion | Sid | Needed for joint frontend / backend validation |
| API contract alignment | Sid + Loredana | Parameters, URLs, response shape, pagination, data format |
| Historical indicator data | Loredana | Pagination / historical structure still open |
| Indicator color-coding and unit tests | TBD | Carry into this sprint |
| Frontend support tasks | Kingson (with Loredana) | Pick ready frontend work |

**Notes**

- Prediction analysis is in scope; trading execution is not
- Candlesticks only; selectable 24-hour and seven-day intervals
- Vercel preferred for the first deploy; team still decides the platform

---

### Sprint 3 — Planning (combined with retro, review, refinement) — 5 Aug 2026

| | |
|---|---|
| **Date** | Wed 5 Aug 2026 |
| **Attendees** | Team |
| **Sprint goal** | Finish the Sprint 2 carryover — no new scope added |
| **Full notes** | [2026-08-05 Retrospective, Review, Refinement & Planning](../2026-08-05-retrospective.md) |

**Stories selected**

| Story / focus | Owner | Notes |
|---------------|-------|-------|
| Sprint 2 carryover | Current assignees | No new issues pulled in until carried-over work is done |

**Notes**

- Sprint 2 closed in this session; unfinished work rolled into Sprint 3 (Kanban-style carryover)
- Sprint 3 is achievable if PR reviews get faster, AI tools are used where appropriate, and members work in parallel instead of one issue at a time
- PR review turnaround is the limiting factor on velocity

---

### Sprint 2 — Planning (combined with refinement) — 29 Jul 2026

| | |
|---|---|
| **Date** | Wed 29 Jul 2026 |
| **Attendees** | Team |
| **Sprint goal** | Advance Sprint 2 work with 1-week cadence; frontend as capacity allows (Loredana leads; Kingson limited); backend microservices refactor on track |
| **Full notes** | [2026-07-29 Refinement & Planning](../2026-07-29-refinement-and-planning.md) |

**Stories / focus selected**

| Story / focus | Owner | Notes |
|---------------|-------|-------|
| Frontend architecture setup (new issue) | Loredana → Sid creates ticket | Blocks component work |
| Frontend tasks (capacity-based) | Loredana (+ Kingson later) | Unfinished rolls to next sprint |
| Frontend WebSockets | — | Keep in sprint; do not work yet |
| Microservices refactor | Mael | Confirmed this sprint |
| Use case diagram (new issue) | Loredana (Mael supervises) | Sid creates ticket |

**Notes**

- Sprint duration: **1 week**
- Standups: async in **role-specific** Slack channels
- Frontend stack: TypeScript, Vite, ShadCN, Tailwind, TanStack Query, Vitest + Testing Library
