# Review, Refinement & Planning — 9 Sep 2026

Weekly Capstone Scrum sync: sprint board review, macro and prediction frontend progress, economic calendar demo, API Gateway merge backlog, and extended discussion on ML model choice (Prophet vs LightGBM vs XGBoost), feature selection, and AI service naming.

| | |
|---|---|
| **Date** | Wed 9 Sep 2026 (Slot B) |
| **Type** | Review + Refinement + Planning |
| **Sprint** | Sprint 3 carryover into next iteration — frontend largely complete; AI backend blocked on model and naming decisions |
| **Attendees** | Sid Ahmed Mahieddine, Loredana Lungu, Kingson Emma-Ochu, Mael Taye Deneke, Owusu Richard |
| **Facilitator** | Loredana Lungu (Scrum Master) |
| **Product Owner** | Sid Ahmed Mahieddine |

---

## Key outcomes

- The **previous sprint under-delivered** partly because Loredana had limited availability (family); she asked the team whether she had been a blocker for Richard and Kingson.
- **Macro event subscription / calendar management UI** work is **closed**; related demo items were finished after the last session.
- **Richard** opened a PR for **prediction alert management UI** (T8); **notifications** may land in a follow-up PR. **Alert preview (#189)** stays in the **backlog** — too complex for MVP from a backend perspective.
- **Kingson** merged the **economic calendar**; live demo showed month navigation, timezone selection, event types, and alert modals. Most **S3** frontend tickets appear implemented — Kingson to **double-check and close** completed items after Sid moves them into the current sprint.
- **Issue #172** — **implement alert history view** (parent **T9**) — moved to the **current sprint** and assigned to Kingson.
- **Mael** is **waiting on API Gateway review/merge confirmation** from Loredana before continuing backend AI tasks; AI sub-issues remain **in progress** until the team agrees on **model choice** and **service naming** (AI vs ML).
- **Next sprint frontend focus:** **A3** and **S3** stories — Sid to add all related frontend issues to the sprint by end of session week.
- **ML model:** Long team discussion — **no final lock-in** in this meeting. Sid advocates **Prophet** for capstone timeline plus **two retraining strategies** (fresh vs continue from previous checkpoint) per Dr. Robert. **Richard** shared **simulated comparisons** of Prophet, **LightGBM**, and **XGBoost** with literature backing and proposed **variable set** refinements. Agreement direction: decisions must be **substantiated with research and metrics**; Richard will **share simulation code** for the team to run on real pre-processed data; optionally support **multiple models** via an **abstraction layer** if time allows.

---

## Decisions

| Topic | Decision |
|-------|----------|
| **Alert preview (#189)** | **Defer to backlog** — not MVP; backend complexity too high for current timeline |
| **Prediction alert PR (Richard)** | Loredana reviews; **remove console.logs** before merge |
| **T8 / Richard scope** | Credit Richard’s participation in **model research and Slack discussions** in meeting notes; Prophet is referenced in backend sub-issues |
| **T9 — Alert history (#172)** | In **current sprint**; Kingson owns |
| **S3 — Economic calendar** | Most UI items treated as **done** pending Kingson’s verification; **event history table view** (upcoming vs historical, name/date/impact, prior values) may still need work |
| **Next sprint FE priority** | **A3** and **S3** frontend stories added to sprint (Sid) |
| **API Gateway** | Loredana to **prioritize review/merge** so Mael can proceed |
| **ML model (interim)** | **Proceed with documented rationale** — capstone allows a mature, feasible model; Dr. Robert expects **research-backed justification**, not “initial plan only” |
| **Retraining (Prophet path)** | If Prophet is chosen, implement **two training modes**: train from scratch vs retrain from previous model (Dr. Robert request) |
| **Alternative models** | Richard’s **LightGBM / XGBoost** findings stay on the table; team may integrate **all three** after **real-data preprocessing** if schedule allows |
| **Feature variables** | Richard’s selection uses **correlation analysis** and **literature**; not identical to the earlier 10-feature list (e.g. adds **equity**, **VIX**; differs on **Fed funds**, **DXY**, **global M2**, **BTC dominance**, **active addresses**, **volume**) — align and document before implementation |
| **AI service naming** | Clarify **“AI service” vs “ML service”** in docs and architecture; substantiate naming for Dr. Robert |

---

## Sprint review

| Area | Owner | Status |
|------|-------|--------|
| **Macro event subscription UI** | Loredana / team | **Closed** |
| **T8 — Prediction alerts (UI)** | Richard | PR open — prediction alert creation; notifications optional second PR |
| **T8 — Alert preview** | Richard | **Backlog** (#189) |
| **T7 / T6 — BTC alerts & related FE** | Loredana | **Nearly complete** |
| **T9 — Alert history (#172)** | Kingson | **In sprint** — in progress |
| **S3 — Economic calendar** | Kingson | **Merged** — demoed; verify and close sub-tasks; history/table view TBD |
| **API Gateway** | Mael | Implemented; **blocked on Loredana review/testing** |
| **AI backend (T1 / T8 sub-issues)** | Sid / Mael | **Blocked** — model and naming agreement; Sid resumes AI work after personal distraction |
| **ML model research** | Richard | Simulations + literature shared; code to be shared in group |
| **Model tooling note** | Mael | Using **Prophet 1.4**; newer Prophet release noted for upgrade consideration |

---

## Refinement

| Item | Outcome | Ready for sprint? |
|------|---------|-------------------|
| Richard prediction alert PR | Review, drop console.logs, merge | Yes |
| Kingson — verify S3 tickets | Close completed; fix light-mode combobox styling if needed | Yes |
| Kingson — calendar history / table view | Clarify AC with Loredana (async call or recording OK) | Yes |
| Sid — add **A3** + **S3** FE stories to sprint | By end of week | Yes |
| Loredana — API Gateway PRs | Unblock Mael | Yes |
| ML model decision + justification doc | Richard shares code; team runs on real data; write rationale for submission | **Blocked — urgent** |
| AI vs ML service naming | Document in architecture / capstone materials | Yes |
| View historical BTC patterns across macro regimes (**A3**) | Backend largely done; FE focus next sprint | Yes |
| Optional: model abstraction layer | Sid / Mael — swap models without rewriting pipeline | If time |

---

## Sprint planning — next focus

| Focus | Owner | Notes |
|-------|-------|-------|
| **A3** frontend stories | Kingson / Richard / Loredana | Sid adds issues to current sprint |
| **S3** cleanup — economic calendar | Kingson | Verify AC, close done tickets; history view if missing |
| **T9 — Alert history (#172)** | Kingson | Complete in current sprint |
| **Close T8** (frontend) | Richard / Loredana | After PR merge; notifications as needed |
| **API Gateway merge + validation** | Loredana / Mael | Unblocks AI integration testing |
| **AI service implementation** | Sid / Mael | Prophet + dual retrain **or** multi-model path after team decision |
| **ML justification for capstone** | Richard + Sid | Literature, metrics, feature list aligned with Dr. Robert expectations |
| **Share Richard simulation code** | Richard | Team reproduces on pre-processed production data |

**Out of immediate sprint**

- **Alert preview (#189)** full implementation
- Final decision on using **three models in production** vs **one** — depends on preprocessing progress and remaining capstone time

---

## Action items

| Owner | Action | Status |
|-------|--------|--------|
| Loredana | Review Richard’s **prediction alert** PR; ensure **no console.logs** | ⏳ Open |
| Loredana | **Review and merge API Gateway** work to unblock Mael | ⏳ Open |
| Richard | **Share Python simulation code** (Prophet / LightGBM / XGBoost) in the group | ⏳ Open |
| Richard | Split or extend work: **notifications** PR if not in current PR | ⏳ Open |
| Kingson | **Verify S3** sub-issues; close completed; implement **history/table view** if gaps remain | ⏳ Open |
| Kingson | Continue **#172** alert history view | ⏳ Open |
| Sid | Add **A3** and **S3** **frontend** stories to the **current sprint** | ⏳ Open |
| Sid | Resume **AI service** work; implement agreed model path + **dual retraining** if Prophet | ⏳ Open |
| Sid / team | Produce **written model and feature justification** (literature + metrics) for capstone and Dr. Robert | ⏳ Open |
| Mael | Proceed with AI backend tasks once **model**, **naming**, and **Gateway** are unblocked | ⏳ Blocked |
| Team | Align on **AI service vs ML service** naming in docs | ⏳ Open |

---

## Discussion notes

### Sprint velocity and board hygiene

Loredana walked the GitHub board by assignee. Richard’s macro subscription stories are closed. Several T8 items remain in progress. The team discussed moving issues between sprints on the project board (e.g. #172 into the current sprint).

### Richard — T8 UI and PR quality

Richard’s PR covers prediction alert creation; notifications may follow. Loredana flagged **console.log** usage with simulated API switching — remove before merge. **Alert preview** deferred: UI is feasible but backend simulation/preview is not MVP.

### Mael — Gateway and AI blocker

Mael completed API Gateway implementation and is waiting on team confirmation. Backend AI tasks cannot finish until the team agrees on **which model(s)** to implement and how to **justify** the **AI service** name after Dr. Robert’s ML vs AI comment.

### Kingson — Economic calendar demo

Kingson demoed calendar month view, timezone handling, filters, and navigation to alerts. Loredana noted a possible **light-mode combobox** styling bug. **Historical events** may need a **table view** (search, recurrence, prior values) beyond calendar visualization — Kingson to confirm against story AC asynchronously.

### Frontend status

Aside from prediction-dependent UI, frontend progress is strong on T6, T7, and calendar work. **A3** (historical BTC patterns across macro regimes) is the main upcoming frontend theme once Sid adds stories.

### ML model debate (Prophet vs gradient boosting)

Richard ran **simulated data** experiments comparing **Prophet**, **LightGBM**, and **XGBoost**, citing literature that tree-based models often handle **macro shocks** and **non-linear** relationships well. Sid emphasized **capstone deadline**, prior **Prophet** communication with Dr. Robert, and **macro seasonality** arguments for Prophet. The team discussed:

- **Two Prophet training modes** (fresh vs warm-start retrain) as required experimentation
- Richard’s simulations used **simplified data** — next step is **real preprocessing** and shared code
- Possible **multi-model AI service** and **abstraction layer** (Mael agreed architecturally)
- **Feature selection**: correlation screening, redundancy removal, literature for five macro/on-chain choices; reconcile with earlier 10-feature documentation
- **Kingson** and **Richard** stressed: whatever model wins, **peer-reviewed justification** must appear in the submission

The meeting ended with alignment on **evidence-based documentation** rather than a single verbal vote; implementation proceeds once code is shared and preprocessing catches up.

### Quantic specializations (pre-meeting)

Sid and Loredana briefly discussed completing **Quantic specializations** before the capstone deadline; remaining concentration work uses **exams and SmartCases** rather than new projects.

---

## Key takeaways

- **Frontend** is ahead of **AI backend**; Gateway merge and **model/naming decisions** are the critical path.
- **Richard** delivered meaningful **ML research** and **T8 UI** work; **alert preview** is explicitly out of MVP.
- **Kingson** should **close out S3** and finish **T9 alert history** while the AI team unblocks Mael and Sid.
- **Capstone credibility** requires a **written, literature-backed ML rationale** — whether the team ships Prophet only or multiple models.

---

## Notes

- Source: Zoom transcript — Weekly Capstone Scrum meeting (9 Sep 2026).
- Previous session: [2 Sep 2026 Review, Refinement & Planning](./2026-09-02-sprint-3-review-and-planning.md).
- Related: [4 Sep 2026 Dr. Robert checkpoint](./2026-09-04-sprint-3-dr-robert-steele-checkpoint.md) · Capstone criteria: [Quantic grading](../quantic/grading.md) · [Deliverables](../quantic/deliverables.md).

---

## Next meeting

See [recurring sync schedule](../team-roles.md#recurring-meetings-through-14-oct-2026) — next documented session: [23 Sep 2026 Review, Refinement & Planning](./2026-09-23-sprint-3-review-and-planning.md). The 16 Sep sync has no write-up in this folder.
