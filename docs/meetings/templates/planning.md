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

### Submission push — Planning (combined with review and refinement) — 23 Sep 2026

| | |
|---|---|
| **Date** | Wed 23 Sep 2026 |
| **Attendees** | Sid Ahmed Mahieddine, Loredana Lungu, Kingson Emma-Ochu, Mael Taye Deneke, Richard Owusu |
| **Sprint goal** | Finish the BTC trader path for submission: ML-ready data into the AI service, real frontend data, Gateway integration, design-doc checklist, Vercel, and the recording |
| **Full notes** | [2026-09-23 Review, Refinement & Planning](../sprint-8-2026-09-23-review-and-planning.md) |

**Stories / focus selected**

| Story / focus | Owner | Notes |
|---------------|-------|-------|
| ML-ready dataset, then AI service | Mael (Richard feedback) | Dataset by 24 Sep if feedback is fast; then Sid’s model orchestration |
| Missing endpoints and real data | Loredana | Summary of data and alert gaps; wire the UI off mocks |
| T6 remaining frontend | Kingson | Review again; integration is what is still open |
| Document checklist and doc corrections | Mael / Richard | Checklist from the earlier project list; edit existing docs where scope changed |
| Design revision | Loredana, Mael, Sid | UML, pattern rationale, DDD, testing method; code, docs, and board agree |
| Presentation outline | Richard | 15–20 minutes; speakers cover the work they did |
| Investment analyst UI | Team | Stop for this submission |
| Deploy | Team | Not Render. Vercel, one Docker Compose app; measure training memory |

**Notes**

- About 70% complete; API Gateway integration is the bottleneck (~38 endpoints today)
- Sid owes frontend and regime feedback the evening of 23 Sep
- CI/CD was named and not discussed

---

### Next sprint — Planning (combined with review and refinement) — 9 Sep 2026

| | |
|---|---|
| **Date** | Wed 9 Sep 2026 |
| **Attendees** | Sid Ahmed Mahieddine, Loredana Lungu, Kingson Emma-Ochu, Mael Taye Deneke, Owusu Richard |
| **Sprint goal** | Close out S3 calendar and T9 alert history; A3 frontend; unblock AI via Gateway merge and documented ML model choice |
| **Full notes** | [2026-09-09 Review, Refinement & Planning](../sprint-6-2026-09-09-review-and-planning.md) |

**Stories / focus selected**

| Story / focus | Owner | Notes |
|---------------|-------|-------|
| A3 — frontend stories | Sid adds to sprint; Kingson / team | Historical BTC patterns across macro regimes |
| S3 — economic calendar cleanup | Kingson | Verify AC, close done tickets; history/table view if needed |
| T9 — Alert history (#172) | Kingson | Current sprint |
| T8 — Prediction alerts UI | Richard / Loredana | Review PR; notifications optional follow-up |
| API Gateway merge | Loredana | Unblock Mael |
| AI service / ML model | Sid / Mael / Richard | Justification doc; Prophet dual-retrain or multi-model if time |

**Notes**

- Alert preview (#189) deferred to backlog
- ML decision requires shared simulation code on real pre-processed data

---

### Current sprint — Planning (combined with review and refinement) — 26 Aug 2026

| | |
|---|---|
| **Date** | Wed 26 Aug 2026 |
| **Attendees** | Sid Ahmed Mahieddine, Loredana Lungu, Kingson Emma-Ochu (joined later) |
| **Sprint goal** | Alerts and frontend alert issues; API-gateway integration. Macro / ML / remaining AI work deferred to September |
| **Full notes** | [2026-08-26 Review, Refinement & Planning](../sprint-4-2026-08-26-review-and-planning.md) |

**Stories / focus selected**

| Story / focus | Owner | Notes |
|---------------|-------|-------|
| Alerts and frontend alert issues | Richard | Richard implemented alerts; connect to the service and test integration ASAP |
| API gateway completion | Sid | Needed for joint frontend / backend validation |
| API contract alignment | Sid + Loredana | Parameters, URLs, response shape, pagination, data format |
| Macro-indicator charts and history | Loredana | Loredana implemented charts and historical views; pagination / historical structure still open |
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
| **Full notes** | [2026-08-05 Retrospective, Review, Refinement & Planning](../sprint-1-2026-08-05-retrospective.md) |

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
| **Full notes** | [2026-07-29 Refinement & Planning](../pre-sprint-1-2026-07-29-refinement-and-planning.md) |

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
