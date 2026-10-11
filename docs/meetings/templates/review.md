# Meeting Notes — Sprint Review

Sprint review notes: demo completed work, gather feedback, review progress.

---

## Template

### Sprint _N_ — Review

| | |
|---|---|
| **Date** | _TBD_ |
| **Attendees** | _TBD_ |
| **Sprint** | _N_ |
| **Sprint goal** | _TBD_ |

**Completed stories**

| Story | Owner | Demo notes |
|-------|-------|------------|
|       |       |            |

**Stories not completed**

| Story | Owner | Reason |
|-------|-------|--------|
|       |       |        |

**Stakeholder feedback**

- _TBD_

**Next sprint preview**

- _TBD_

**Notes**

- 

---

## Sessions

### Review (combined with refinement and planning) — 26 Aug 2026

| | |
|---|---|
| **Date** | Wed 26 Aug 2026 |
| **Attendees** | Sid Ahmed Mahieddine, Loredana Lungu, Kingson Emma-Ochu (joined later) |
| **Sprint** | Current sprint (alerts and frontend) |
| **Full notes** | [2026-08-26 Review, Refinement & Planning](../sprint-4-2026-08-26-review-and-planning.md) |

**Progress by area**

| Area | Owner | Status |
|------|-------|--------|
| Dashboard / price chart | Loredana | Candlesticks replace the line view; 24-hour vs seven-day controls still to be documented |
| Macro-indicator charts and history | Loredana | Color-coded cards, historical graph/table; Loredana implemented and demoed |
| Indicator / price data | Loredana (frontend) | Backend connections for macro indicators and BTC/USD; pagination and historical shape remain |
| Alerts | Richard | Richard implemented alerts; frontend alert work continues |
| API gateway | Sid | Still in progress — needed for joint frontend / backend validation |

**Feedback**

- Sid praised the visual design, especially color use
- Table beneath the chart approved
- Clearer business requirements needed for historical candlestick timeframes
- Responsive bugs remain (e.g. combo-box values appearing away from the control on mobile)

**Next sprint preview**

- This sprint: alerts + frontend alerts + API-gateway integration
- September: remaining macro indicators, ML model, AI service, indicator rationale

---

### Sprint 2 — Review (combined with retro, refinement, planning) — 5 Aug 2026

| | |
|---|---|
| **Date** | Wed 5 Aug 2026 |
| **Attendees** | Team |
| **Sprint** | 2 |
| **Full notes** | [2026-08-05 Retrospective, Review, Refinement & Planning](../sprint-1-2026-08-05-retrospective.md) |

**Progress by area**

| Area | Status |
|------|--------|
| Backend | Good progress; several features implemented; moving in the right direction |
| Frontend | Configuration work progressing; more visible UI work needed |

**Feedback**

- Seeing working screens would improve team motivation and frontend/backend collaboration

**Sprint 3 preview**

- Carry over unfinished Sprint 2 work; speed up PR reviews — see [Sprint 3 planning notes](./planning.md#sprint-3--planning-combined-with-retro-review-refinement--5-aug-2026)

---

### Review (combined with refinement and planning) — 2 Sep 2026

| | |
|---|---|
| **Date** | Wed 2 Sep 2026 |
| **Attendees** | Sid Ahmed Mahieddine, Loredana Lungu, Kingson Emma-Ochu, Mael Taye Deneke, Richard Owusu |
| **Sprint** | Current sprint — alerts, API Gateway, AI / prediction (T8) |
| **Full notes** | [2026-09-02 Review, Refinement & Planning](../sprint-5-2026-09-02-review-and-planning.md) |

**Progress by area**

| Area | Owner | Status |
|------|-------|--------|
| Alerts (S1) | Richard / Loredana | Closed — price alerts, notifications, create/manage UI |
| Receive alerts from BTC (T7) | Loredana | In progress — due Friday |
| Macro events UI | Loredana | Breadcrumb and pop-up consistency; notifications planned |
| Economic calendar | Kingson | Demoed; place under Macro Indicators |
| API Gateway | Mael | 34 endpoints; two PRs awaiting merge |
| AI / prediction (T8) | Sid | Prophet model; sub-issues moving to sprint |

**Feedback**

- Prioritize BTC trader persona for Capstone submission
- Future PRs should include testing and mobile responsiveness together
- Keep implementations simple; document extras for later

**Next sprint preview**

- Finish T7 by Friday; merge API Gateway PRs
- T8 prediction work and Dr. Robert AI meeting prep
- Kingson: calendar navigation and macro notifications

---

### Review (combined with refinement and planning) — 9 Sep 2026

| | |
|---|---|
| **Date** | Wed 9 Sep 2026 |
| **Attendees** | Sid Ahmed Mahieddine, Loredana Lungu, Kingson Emma-Ochu, Mael Taye Deneke, Owusu Richard |
| **Sprint** | Sprint 3 — frontend near complete; AI blocked on model/naming |
| **Full notes** | [2026-09-09 Review, Refinement & Planning](../sprint-6-2026-09-09-review-and-planning.md) |

**Progress by area**

| Area | Owner | Status |
|------|-------|--------|
| Macro subscription UI | Team | Closed |
| T8 prediction alerts UI | Richard | PR open |
| S3 economic calendar | Kingson | Merged; demoed |
| T9 alert history (#172) | Kingson | In sprint |
| API Gateway | Mael | Awaiting Loredana review |
| AI / ML model | Sid / Richard / Mael | Debate; justification pending |

**Feedback**

- Document ML choices with literature and metrics for capstone
- Remove console.logs from frontend PRs before merge

**Next sprint preview**

- A3 and S3 frontend stories; Gateway merge; ML implementation path

---

### Review (combined with refinement and planning) — 23 Sep 2026

| | |
|---|---|
| **Date** | Wed 23 Sep 2026 |
| **Attendees** | Sid Ahmed Mahieddine, Loredana Lungu, Kingson Emma-Ochu, Mael Taye Deneke, Richard Owusu |
| **Sprint** | Submission push — ~70% complete; Gateway integration, real data, docs, and the recording |
| **Full notes** | [2026-09-23 Review, Refinement & Planning](../sprint-8-2026-09-23-review-and-planning.md) |

**Progress by area**

| Area | Owner | Status |
|------|-------|--------|
| Data preparation | Mael | Feature engineering and 80-10-10 split done; scaling and final dataset in progress |
| Forecast UI | Kingson / Loredana | BTC trader sub-issues demoed; data still mocked |
| Regime analysis | Loredana | Demoed; analyst-oriented; purpose still unclear |
| API Gateway | Mael | ~38 endpoints; integration is the bottleneck |
| Investment analyst UI | Team | Stopped for this submission |
| Deploy | Team | Not Render; Vercel and one Docker Compose app |

**Feedback**

- Show real backend data on trader screens
- Sid to explain regime analysis and review the UI the evening of the sync
- Reply when progress is posted; do not leave investment-analyst issues in the active push

**Next sprint preview**

- ML-ready data into the AI service, Gateway integration, design-doc checklist, Vercel, and the 15–20 minute recording

---

_Add dated review notes below as sprints progress._
