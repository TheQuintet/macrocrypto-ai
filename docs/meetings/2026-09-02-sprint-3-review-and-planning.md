# Review, Refinement & Planning — 2 Sep 2026

Weekly Capstone Scrum sync: alerts and macro UI progress, API Gateway status, economic calendar demo, AI service planning (Prophet), and Dr. Robert meeting preparation.

| | |
|---|---|
| **Date** | Wed 2 Sep 2026 (Slot B) |
| **Type** | Review + Refinement + Planning |
| **Sprint** | Sprint 3 — alerts, frontend, API Gateway; AI / prediction work (T8) moving into sprint |
| **Attendees** | Sid Ahmed Mahieddine, Loredana Lungu, Kingson Emma-Ochu, Mael Taye Deneke, Richard Owusu |
| **Facilitator** | Loredana Lungu (Scrum Master) |
| **Product Owner** | Sid Ahmed Mahieddine |

---

## Key outcomes

- **S1 (alerts) is closed** — the team celebrated completing the first user story.
- **Loredana** demoed the alerts system: price alerts, notifications, and UI for creating and managing alerts. Macro events UI was updated for consistency (breadcrumb titles, pop-up designs). Remaining work includes preview fixes and moving some tasks to in progress.
- **Kingson** demoed an economic calendar; it should become a **child of Macro Indicators** in front-end navigation (data is currently hard-coded).
- **Mael** reported the **API Gateway** exposes **34 endpoints** (10 data service, 24 alert service). Loredana will review and merge Mael's two API Gateway PRs.
- **AI service:** Sid outlined a **Prophet**-based prediction model with **10 features** (5 BTC, 5 macro), retraining every **24 hours**, using time-series data per Dr. Robert's feedback. T8 prediction sub-issues move to the current sprint.
- **Capstone focus:** Prioritize **BTC trader** persona features for submission; investment-analyst scope is secondary. Overall progress estimated at **~50–60%** (varies by whether documentation, code, and AI are counted).
- **Dr. Robert meeting:** Sid prepares slides and leads; team members cover frontend (Loredana), backend (Mael), and AI (Sid). Send a consolidated email on AI implementation ahead of the meeting.

---

## Decisions

| Topic | Decision |
|-------|----------|
| **Capstone persona** | Prioritize **BTC trader** features over investment-analyst features for the submission |
| **Economic calendar** | Place under **Macro Indicators** in navigation; keep implementation simple; low priority vs core deliverables |
| **Calendar user story** | Economic calendar remains a **separate user story** from macro-event notifications |
| **PR expectations** | Future PRs should include **testing and mobile responsiveness** — can be combined in one PR rather than split |
| **AI algorithm** | Use **Prophet** (Meta) for time-series prediction with 10 features (5 BTC + 5 macro indicators) |
| **Model retraining** | Retrain every **24 hours** |
| **Training data** | Use **time-series data** for model training (per Dr. Robert's feedback), not holdout-only approaches |
| **Dr. Robert communication** | Send a **consolidated email** focused on **AI-related questions** and implementation plan; Sid prepares slides and leads the meeting |
| **Post-submission work** | Use the week after deliverable submission to refine the live version and improve user-journey documentation |
| **Implementation simplicity** | Keep implementations simple; document additional features for later review |

---

## Sprint review

| Area | Owner | Status |
|------|-------|--------|
| **Alerts (S1)** | Richard / Loredana | **Closed** — price alerts, notifications, create/manage UI delivered |
| **Macro events UI** | Loredana | Breadcrumb titles, updated pop-ups, macro events table aligned with price alerts; macro-event notifications planned |
| **Receive alerts from BTC (T7)** | Loredana | In progress — target finish **Friday** |
| **Economic calendar** | Kingson | Demoed; hard-coded data; needs navigation placement under Macro Indicators |
| **Notifications + macro implementation** | Kingson | Assigned by Loredana |
| **API Gateway** | Mael | **34 endpoints** live (10 data, 24 alert); two PRs awaiting Loredana's review and merge |
| **Alert service** | Sid | Completed; sub-issues moving to current sprint |
| **AI / prediction (T8)** | Sid | Prophet model planned; sub-issues to move to current sprint; implementation doc and Dr. Robert email due tonight |
| **Preview functionality** | Loredana | Issues identified — remaining fix work |

---

## Refinement

| Item | Outcome | Ready for sprint? |
|------|---------|-------------------|
| Economic calendar under Macro Indicators | Kingson implements navigation placement | Yes |
| Macro-event notifications | Separate from calendar; Kingson continues macro work | Yes |
| T7 — Receive alerts from BTC | Loredana finishes by Friday | Yes (in sprint) |
| T8 — Prediction sub-issues | Sid moves to current sprint tonight | Yes |
| API Gateway PRs | Loredana reviews and merges Mael's two PRs | Yes |
| AI implementation plan | Sid shares document tonight (Prophet, features, retraining) | Yes |
| Dr. Robert meeting prep | Sid prepares slides; team ready for domain-specific Q&A | Yes |
| Capstone scope definition | Sid helps team define objectives and scope in next meeting | Next meeting |
| User journey documentation | Deferred — use AI to help generate journey maps post-submission | Later |

---

## Sprint planning — current sprint

| Focus | Owner | Notes |
|-------|-------|-------|
| Finish T7 — Receive alerts from BTC | Loredana | Due **Friday** |
| Review and merge API Gateway PRs | Loredana | Mael's two PRs |
| Economic calendar navigation | Kingson | Child of Macro Indicators in FE nav |
| Notifications + macro implementation | Kingson | Assigned in session |
| Move T8 prediction sub-issues to sprint | Sid | By tonight |
| AI model implementation plan | Sid | Document + email Dr. Robert tonight |
| Dr. Robert meeting slides | Sid | Focus on AI service specifics |
| Capstone scope / objectives | Sid + team | Define in next meeting |

**Out of immediate sprint (post-submission or later)**

- Refine live deployment and user-journey documentation
- Investment-analyst persona features
- Full economic calendar with live data (beyond hard-coded demo)

---

## Action items

| Owner | Action | Status |
|-------|--------|--------|
| Kingson | Implement the economic calendar as a child of Macro Indicators in front-end navigation | ⏳ Open |
| Loredana | Finish T7 — "Receive alerts from BTC" — by **Friday** | ⏳ Open |
| Loredana | Review and merge Mael's two API Gateway PRs | ⏳ Open |
| Sid | Move T8 prediction sub-issues from the previous sprint to the current sprint by **tonight** | ⏳ Open |
| Sid | Prepare and share an AI model implementation plan tonight (Prophet, features, retraining strategy) and email Dr. Robert with progress and questions | ⏳ Open |
| Sid | Prepare a brief slide presentation for the Dr. Robert meeting, focusing on AI service specifics | ⏳ Open |
| Sid | Help the team define Capstone objectives and scope in the next meeting | ⏳ Open |
| Team | Be prepared for Dr. Robert's questions — Sid (AI), Mael (backend), Loredana (frontend) | ⏳ Open |

---

## Discussion notes

### Alerts system progress

The team celebrated closing **S1**. Loredana presented the alerts implementation: price alerts, a notifications system, and UI for creating and managing alerts. Some tasks still need to move to in progress, and preview functionality has open issues.

### Macro events UI updates

Loredana walked through macro events and price alerts table changes for UI consistency — titles moved to the breadcrumb, updated pop-up designs. Macro-event notifications are planned. Sid confirmed the economic calendar should be a separate user story.

### Sprint task review and PR discipline

Kingson was assigned notifications and macro implementation. Sid confirmed alert service work is complete and will move related sub-issues to the current sprint. Loredana asked that future PRs include testing and mobile responsiveness together. Sid advised keeping implementations simple and documenting extra features for later.

### API Gateway status

Mael reported **34 endpoints** on the API Gateway (10 data service, 24 alert service) and asked Loredana to review for gaps that might affect AI functionality or user story coverage.

### AI model — Prophet and time series

Mael raised Dr. Robert's feedback on using time-series data instead of holdout-only training. Sid outlined **Prophet** with 10 features (5 BTC, 5 macro), retraining every 24 hours. Sid will share an implementation document and email Dr. Robert with progress and next steps.

### Capstone resources and rubric

The team reviewed Capstone resources via the concentration dashboard and discussed rubric requirements for a top score — software design, testing documentation, CI/CD, and going above minimum requirements. They agreed to email Dr. Robert ahead of the meeting about AI model performance, recommendation accuracy, risk calculations, and related AI sub-issues.

### Dr. Robert meeting preparation

Sid will present AI service progress: entry price calculation, recommendation engine, and threshold monitoring. The team will focus on delivery targets and architectural decisions rather than a long written pre-read. Owusu suggested prepared questions to make the most of limited time. They agreed on a consolidated AI-focused email; a second meeting with Dr. Robert is already scheduled.

### Economic calendar demo

Kingson demoed the economic calendar. Loredana asked for it under Macro Indicators and noted hard-coded data. Sid suggested refining the live version and user-journey docs in the week after deliverable submission.

### Project progress and Capstone prioritization

Completion estimates ranged from 20% to 60% depending on what is counted. Richard suggested focusing Capstone deliverables on the **BTC trader** persona. The team planned the Dr. Robert meeting with Sid leading slides and domain experts ready for questions.

---

## Key takeaways

- **S1 closed** — alerts are delivered; **T7** (receive alerts from BTC) is the immediate frontend priority (due Friday).
- **API Gateway** is substantially complete (34 endpoints); merge Mael's PRs and connect remaining frontend work.
- **AI is the critical next phase** — Prophet model, T8 in sprint, Dr. Robert meeting prep tonight.
- **Capstone submission:** focus on **BTC trader** core functionality; keep calendar and polish for post-submission.
- Project is roughly **50–60% complete** — AI service and documentation remain the largest gaps.

---

## Notes

- Source: Zoom AI meeting summary and action items (2 Sep 2026).
- Previous session: [26 Aug 2026 Review, Refinement & Planning](./2026-08-26-sprint-3-review-and-planning.md).
- Capstone criteria: [Quantic grading](../quantic/grading.md) · [Deliverables](../quantic/deliverables.md).

---

## Next meeting

See [recurring sync schedule](../team-roles.md#recurring-meetings-through-14-oct-2026) — session write-up: [9 Sep 2026 Review, Refinement & Planning](./2026-09-09-sprint-3-review-and-planning.md).
