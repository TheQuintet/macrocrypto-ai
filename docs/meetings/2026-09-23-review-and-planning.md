# Review, Refinement & Planning — 23 Sep 2026

Weekly Capstone Scrum sync: data-pipeline status, AI-service handoff, forecast and regime-analysis demo, a decision to stop investment-analyst work, deployment options, and how to shape the recording.

| | |
|---|---|
| **Date** | Wed 23 Sep 2026 (Slot B) |
| **Type** | Review + Refinement + Planning |
| **Sprint** | Submission push — Richard’s estimate ~70%. About one to two weeks left. Energy goes to the API Gateway, the forecast, and real frontend data |
| **Attendees** | Sid Ahmed Mahieddine, Loredana Lungu, Kingson Emma-Ochu, Mael Taye Deneke, Richard Owusu |
| **Facilitator** | Loredana Lungu (Scrum Master) |
| **Product Owner** | Sid Ahmed Mahieddine |

Loredana dropped briefly and rejoined: she was in the meeting on another Zoom account and could not approve screen share until she switched.

---

## Key outcomes

- **Mael** is on the **sixth stage** of the data-preparation pipeline. **Feature engineering** and the **80-10-10** train / validation / test split (from the feature-engineering doc) are done. He is in **feature scaling and transforming**, building the final **ML-ready** dataset from CSV aggregates. Target: that dataset **by 24 Sep**, if Richard’s feedback comes quickly. **AI service integration** is the step after that, then a pass on missing API Gateway endpoints.
- Training data is drawn from three tables: **BTC price**, **BTC dominance**, and **macro indicators**. Macro history is uneven: much of it is **FRED**, and some series needed archives or CSV because providers lack backfill. **Richard** helped navigate APIs (including sources that are outdated or not historical).
- **Alert service** is missing pieces Loredana already flagged, including **notifications**. Mael will pick those up after the pipeline. He expects the gap to be hours, not days, once Loredana sends a **summary of missing data and alert endpoints**.
- The **API Gateway** currently exposes about **11 data-service** and **27 alert-service** endpoints (**38** total). It does not yet cover the AI pipeline. **Richard** called Gateway integration the bottleneck: if it fails, there is nothing to submit.
- **Sid** has an **abstraction layer** that trains and retrains **six ML models** the same way, plus an **evaluation engine** using the metrics from Dr. Robert’s last feedback. It publishes the best model and still reports the others. CSV and chart export exist but are lower priority than orchestration. For capacity, Sid described **12 models** in the deploy: **six for the 24-hour horizon** and **six for the 7-day horizon** (two Prophet, two XGBoost, two LightGBM on each horizon), retrained on those two cadences.
- **Kingson** demoed the **forecast** page (Loredana had already improved it). **Loredana** demoed **regime analysis** (three tabs, many PRs merged). BTC-trader frontend sub-issues are implemented. On-screen data is still **mocked**. A **T1** backend task is still open, and Loredana is unsure how it connects to the UI.
- **Richard** (~**70%** overall): data services are largely in place aside from remaining ML work; frontend progress is real; the remaining cost is **integration**. **This week and next** should close most of what will be submitted.
- **Scope:** **stop investment-analyst work** for the submission. Richard’s reason: the Dr. Robert discussion was about **prediction**, that persona was not part of it, and about **40** frontend sub-issues are still open while the backend for them already exists. Sid agreed to **lowest priority**. Frontend focus becomes **BTC trader** and shared behaviour, especially the **forecast**. Already-built regime screens are analyst-oriented; the team did not decide in this meeting to move them onto the forecast page.
- **Deployment:** **Render** free tier will not work (512 MB, cold starts, training memory). Sid and Mael: ship a **single Docker Compose** bundle, measure memory on local training before locking a host, and look at **free tiers in parallel** (**Vercel** or **Railway**). Sid’s retraining window is about the **last 180 days** (250 would cost more); **Mael would not confirm 180**. After Mael left, **Kingson**, **Richard**, and **Loredana** agreed to **proceed with Vercel**, with a paid plan for a few months if the free tier cannot hold the app.
- **Documentation:** Mael will produce the **required-document checklist** from the earlier software-engineering project (user journey, stories, functional and non-functional requirements) and check it against what exists. Richard will **correct existing docs** where scope changed, not rewrite from scratch. Sid wants a revision that also covers **UML**, **why patterns were chosen**, **domain-driven design / bounded contexts**, and the **testing method**. Loredana’s view: do not duplicate the agile board; put the effort on design and testing (rubric section she identified as **4.4**). The evaluator will read **code, docs, and the board**.
- **Architecture compromise to explain in that design:** services **share one database server** so the team can finish inside the time limit. The written design should still describe the intended production shape (a database server per service, smaller schemas). Sid’s rule of thumb: a microservice should own about **six or seven tables**; some current services own more.
- **Presentation:** **15–20 minutes** (Kingson; Loredana had guessed about 10). Cover frontend, backend, AI, ML, and a short look at the **task board**. Loredana said the recording should **show an ID to the camera**. Richard will **structure** the outline. People present the parts they worked on; Kingson can cover **frontend**.
- **Sid** will review the frontend and send **feedback tonight**, including a short explanation of **regime analysis** and how an investment analyst would use it. He had not expected this much UI, because progress was not posted in the channels.
- **Mael** asked the team to **reply quickly** when he posts in the group, and not to assume who is doing what.

**Sid named CI/CD** as a topic for this meeting. The group did not discuss it.

---

## Decisions

| Topic | Decision |
|-------|----------|
| **Submission scope** | **Prediction and the BTC trader.** **Investment analyst** work is **out** for this submission (lowest priority / future). Do not keep those open issues in the active push |
| **Regime analysis** | Treated as **analyst-oriented**, not core forecast. Explanation and feedback come from Sid **tonight**. No decision to relocate the page |
| **Frontend variables** | **Richard** aligns indicator and BTC fields with the **ML dataset** the team already chose |
| **Data pipeline** | Feature engineering and **80-10-10** split are done. ML-ready dataset targeted for **24 Sep**, then **AI service** integration |
| **API Gateway** | **First-class risk.** ~**38** endpoints today (11 data + 27 alert). Frontend sends a **report of endpoints that work, are missing, or are buggy** so Mael can revise quickly. Loredana’s summary of missing notification and data APIs comes first |
| **Models** | Use Sid’s orchestration and evaluation path (best model published, others reported). Capacity planning assumes **12** models and retraining every **24 hours** and **7 days** |
| **Shared database** | **Keep the shared database server** for the submission. Document the production vision (database per service) and why the team stopped short of it |
| **Deployment** | **Not Render.** Package as **one Docker Compose** app. **Vercel** is the choice Kingson, Richard, and Loredana locked after Mael left; paid months are acceptable if needed. Mael still measures real training memory and checks free tiers (**Vercel** or **Railway**) |
| **Retraining history** | Sid plans on about **180 days**. Mael did not confirm that figure |
| **Documentation** | **Mael** owns the checklist. **Richard** updates existing docs to match what was built. **Loredana, Mael, and Sid** revise so code, docs, and the board agree. Stories can stay on the board; design, patterns, UML, DDD, and the testing method still need a pass |
| **Presentation** | **15–20 minutes.** Richard drafts the structure. Speakers cover the work they did. Show ID on camera |
| **Communication** | Reply when Mael posts. Put frontend questions in the topic channel instead of holding them for the weekly sync |

---

## Sprint review

| Area | Owner | Status |
|------|-------|--------|
| **Data preparation** | Mael (Richard advising) | Feature engineering and **80-10-10** split **done**. Scaling, transforms, and the final dataset **in progress** (CSV work). ML-ready set targeted **24 Sep** |
| **AI service** | Sid implemented; Mael integrates | Abstraction over six models, evaluation engine, lower-priority CSV/chart export. Integration **not started** |
| **API Gateway** | Mael | **~38 endpoints.** AI and some frontend needs **not exposed**. **Bottleneck** |
| **Alert notifications** | Mael | **Missing** — Loredana flagged them. Short follow-up after the pipeline |
| **BTC trader frontend** | Loredana / Kingson | **Sub-issues implemented.** Demoed forecast. Still **mocked**. **T6** still open, mainly **integration** with the backend (unit tests already land with each PR) |
| **T1** | Backend | **Still open.** Frontend connection unclear |
| **Regime analysis** | Loredana | **Merged** (three tabs). Purpose still unclear to frontend and to Richard. Analyst-oriented |
| **A1 — macro correlation / export** | Frontend | **Still open** on the board (“implement macro correlation analysis”, “export BTC and macro correlation”). Loredana believes an **export API** already exists |
| **Investment analyst frontend** | — | **~40 sub-issues open.** **Stopped** for submission. Backend for them is largely already there |
| **Design docs** | Mael (checklist), team (revision) | Foundation exists in `docs/`. Needs a checklist and a revision, not a from-scratch rewrite |
| **Deployment** | Team | **Vercel** chosen by Kingson, Richard, and Loredana. Render rejected. Docker Compose bundle. Memory still to be measured |
| **CI/CD** | — | **Not discussed** |

Board figures Loredana scrolled past during the demo included **73%**, **76%**, **71%**, and **94%**. Richard’s cross-cutting estimate is **~70%**.

---

## Refinement

| Item | Outcome | Ready for sprint? |
|------|---------|-------------------|
| Investment analyst frontend (~40 open sub-issues) | **Stop.** Treat as future work so it stops pulling the weekly sync backwards | Yes (scope cut) |
| Regime analysis page | Keep the demoed UI for now. Sid explains it tonight. Relocation into Forecast was **not** decided | Needs Sid’s note |
| Indicator / BTC fields vs ML dataset | Richard adjusts variables so the UI matches the dataset | Yes |
| Missing gateway / alert / data endpoints | Loredana writes the summary; Mael implements after the dataset | Yes |
| T6 | Kingson reviews again. Open items are mostly **backend integration**, not missing UI unit tests | Yes |
| A1 correlation and export | Still open on the frontend; confirm the export API with Mael | Yes |
| Document checklist | Mael, from the concentration-project list, compared with the repo | Yes |
| Existing design docs | Richard double-checks and corrects drift. Sid’s gap list: UML (class, sequence, activity, use case, deployment, architecture), pattern rationale (orchestrator, observer), DDD and bounded contexts, functional and non-functional requirements, testing method | Yes |
| Shared-database decision | Write it into the design as a **time-box choice**, with the per-service database as the vision | Yes |
| Deploy target | Vercel, Docker Compose, measure memory. 180-day window unconfirmed | Yes |

---

## Sprint planning — next focus

| Focus | Owner | Notes |
|-------|-------|-------|
| **ML-ready dataset** | Mael, with Richard’s feedback | By **24 Sep** if feedback is fast |
| **Integrate dataset with Sid’s models** | Mael | After the dataset. Training and retraining, then Gateway updates |
| **Required-document checklist** | Mael | Deliver and check off what exists vs what must be written |
| **Missing endpoint summary** | Loredana | Data and alert gaps, including notifications, plus which Gateway routes work, are missing, or are buggy |
| **Frontend on real data** | Loredana | Replace mocks. Integration is the open testing gap |
| **T6 review** | Kingson | Look again at remaining trader frontend |
| **Frontend feedback and regime examples** | Sid | **Tonight** |
| **Correct existing docs to match the build** | Richard | Initial project docs, adjusted for scope changes |
| **Design revision** | Loredana, Mael, Sid | Code, docs, and board tell the same story |
| **Free-tier / memory check** | Mael | Alongside training. Sid and Mael still want a measured choice; the others already picked **Vercel** |
| **Presentation outline** | Richard | 15–20 minutes: frontend, backend, AI, ML, task board. Who speaks follows who did the work |
| **Frontend portion of the recording** | Kingson | He can cover frontend parts |

**Out of this push**

- Remaining **investment analyst** frontend
- Chart-style analyst tools Sid named as out of the BTC trader path (for example Bollinger Bands, support and resistance)
- Sid’s other program (a separate multi-week cohort). Mael cut that topic off

---

## Action items

| Owner | Action | Status |
|-------|--------|--------|
| Mael | Finish scaling and the **ML-ready dataset** by **24 Sep**, if Richard’s feedback arrives in time | ⏳ Open |
| Mael | **Integrate that dataset with the AI service** (Sid’s training / retraining orchestration) | ⏳ Open |
| Mael | Publish a **documentation checklist** from the earlier software-engineering deliverables and mark what this repo already has | ⏳ Open |
| Mael | After the pipeline, add the **missing alert and data endpoints** from Loredana’s summary (notifications included) and extend the Gateway | ⏳ Open |
| Mael | Look up a **free deployment tier** in parallel and judge it against measured training memory | ⏳ Open |
| Richard | Give Mael **dataset feedback** so the 24 Sep target holds | ⏳ Open |
| Richard | **Align frontend indicator and BTC variables** with the ML dataset | ⏳ Open |
| Richard | **Double-check existing project docs** and correct them where the scope changed | ⏳ Open |
| Richard | **Structure the 15–20 minute presentation** (frontend, backend, AI, ML, task board) | ⏳ Open |
| Loredana | Send the **summary of data the UI needs** and of **missing or buggy endpoints** | ⏳ Open |
| Loredana | **Integrate the frontend with the backend** so screens show real data | ⏳ Open |
| Loredana | Keep **T6** and related trader issues honest on the board: unit tests exist; what remains is integration | ⏳ Open |
| Kingson | **Review T6** again | ⏳ Open |
| Kingson | Cover **frontend** in the recording | ⏳ Open |
| Sid | **Frontend feedback tonight**, including regime analysis and the investment-analyst point of view | ⏳ Open |
| Sid | Take part in the **design-doc revision** (UML, pattern rationale, DDD, testing method) | ⏳ Open |
| Team | Leave **investment-analyst** issues out of the submission push and say so on the board | ⏳ Open |
| Team | **Deploy on Vercel** as a single Docker Compose app; fall back to a short paid plan if the free tier cannot run training | ⏳ Open |
| Team | **Reply promptly** when Mael posts in the group | ⏳ Open |

---

## Discussion notes

### Mael — pipeline, APIs, and the Gateway

The last seven to ten days were spent chasing data. Some APIs are stale, some have no history, and coverage differs by indicator. Richard helped choose sources. Collected rows are aggregated for training from **BTC price**, **BTC dominance**, and **macro indicators**.

Mael is still working in CSV files, so this stage does not yet change the frontend. The sequence he described: finish the ML-ready set, hook it to the AI service Sid already opened, then update the Gateway (38 endpoints today, no AI pipeline). He asked Sid not to repeat the very large PR stack; reviewing it took heavy use of AI. Sid said that push was the last of that size. He had front-loaded the AI work so Mael could do the data integration, and he asked Mael to understand the orchestration before using AI to go deeper in that code.

Loredana had already pointed at unimplemented notifications. Mael wants one summary from her rather than rediscovering gaps, and he thinks the missing services are a small change once the dataset is out of the way.

### Sid — models and the shared database

The AI service is built so one orchestration path trains and retrains six models and an evaluation step ranks them with Dr. Robert’s metrics. Export features are secondary. Memory planning has to assume twelve models and regular retraining, which is why Render’s free tier is out.

On architecture, Sid was explicit: what is running is not a finished event-driven, database-per-service design. Sharing one database server was a time decision. The submission should still include a design that states that vision, the patterns (orchestrator, observer), and why the team shipped the smaller version.

### Frontend demo

Kingson showed the forecast page. Loredana showed regime analysis and said she is listing every data field the UI needs. She considers the BTC-trader frontend sub-issues done, with **T1** still open on the backend.

Mael had not reviewed the UI closely. Richard’s read: indicators and BTC variables are represented, but some fields must change to match the ML dataset. He would not judge the forecast chart until model output exists. On regime analysis he, Loredana, and Kingson all said the screen was built from the issues without a solid shared picture of the user. Loredana thinks it serves an analyst, not a trader. Sid agreed it is extra analysis (chart-style work such as Bollinger Bands and support or resistance sits with the analyst persona; the trader path is the basic 24-hour prediction). He will send examples tonight rather than use the sync for that tutorial, and he asked that the next questions go to the topic channel.

Sid offered the frontend team a choice to continue the investment-analyst stories. That was before Richard’s recommendation to stop. Loredana asked the group to stop the persona discussion and name concrete work: documentation, deployment, and real data, with about a week left. She asked Sid to take documentation because Mael is on the backend, Richard on the dataset and model, Kingson on finishing the analysis UI, and she on integration.

### What “documentation” means here

Sid was not asking only for code comments. He wants the path from personas, stories, and functional and non-functional requirements through design, evolution, maintenance, deployment, and testing, written in Markdown or PDF, plus UML. He also said the team had not spelled out domain-driven design and bounded contexts.

Loredana asked not to frame that as people forgetting. She walked the repo docs (scope, personas, structure, design) and the Quantic rubric. Her question on the story list: the board already is that list, unlike the first concentration project. She wants the writing time on design and testing. Sid’s answer: listing stories is better if someone does it; if not, the board is enough; design still has to be refined, including the testing method. He also said he has already added documentation and wants the team to read it. Responsibility is shared, via a checklist (personas, stories, and so on).

Mael stopped the loop. He will take the concentration-project outline (user journey, stories, requirements, board) and produce the list. Loredana accepted. Richard’s earlier point stands next to that: start from documents the team already wrote and edit them where the product changed.

Near the end Mael restated his deliveries: the document list, the dataset with Richard, then AI integration, plus Loredana’s endpoint summary if it arrives.

### Richard — what to submit

Richard did not want another meeting that leaves the investment-analyst issues open. His proposal, which Sid accepted:

1. Put energy on the **API Gateway** until integration works.
2. **Do not add the investment analyst** now.
3. Spend the saved time on the **forecast**.
4. Mael finishes data preparation (dataset by tomorrow at his current pace), then training and retraining, and passes through the Gateway.
5. Frontend reports which endpoints work.
6. Loredana, Mael, and Sid revise documentation because the evaluator reads code, docs, and the board.
7. Start the **speaking parts** for the recording (how long the frontend gets, the six models, the data work, the custom Agile process, the testing method).

He put the project at about **70%**, with this week and next week as the window to finish the majority.

### Deployment

Kingson ruled out Render’s free plan on memory and startup time. Sid agreed: twelve models and scheduled retraining will not fit, and the free plan will not do. He wants a single Docker Compose deploy, local memory measured first, and a host chosen after that. He floated Vercel or Railway. Mael agreed Render is out, agreed with measuring during training, and still wants a **tentative free-tier option now** so the decision is not left to the end of next week. He would not commit to Sid’s 180-day retraining window in the meeting.

Loredana brought deployment back after Mael had left, citing about one week. Kingson chose Vercel and said a paid plan for a few months is acceptable. Richard agreed. Loredana closed it: deployment, documentation, and the presentation are the remaining frames, **investment analysis stops**, Kingson rechecks T6, and she owns frontend–backend integration.

### Presentation

Richard asked whether a duration exists. Kingson first thought it might be undocumented; Loredana guessed about ten minutes; Kingson then said **15–20**. Richard will plan inside that: backend, frontend, AI, ML, and a glimpse of the task board. Loredana added that the recording should show an ID to the camera. Speaking roles follow the work: Kingson and Loredana can cover frontend parts. The transcript ends while Richard is still on that split.

### Communication

Sid said he had not expected the frontend progress because nobody reported it, and that he had avoided asking so it would not feel like pressure. He can now review stories against the UI and comment on layout. Mael, before leaving, asked for fast replies in the group: do not assume work is happening, and do not assume it is not. Kingson’s last ask to Sid was the same as Sid’s commitment: feedback tonight.

---

## Key takeaways

- The submission is the **BTC trader and the forecast**. **Investment-analyst** frontend stops here.
- **Mael’s** dataset is close. The risky step is **Gateway integration** of that data, Sid’s models, and the screens that are still mocked.
- **Twelve-model** retraining is why **Render** is out. **Vercel** plus a **Docker Compose** bundle is the working plan; memory still has to be measured, and **180 days** is not agreed.
- Docs need a **checklist and a revision** of what is already in the repo, including the shared-database decision. Mael owns the list.
- The recording is **15–20 minutes**. Sid owes frontend and regime feedback **tonight**.

---

## Notes

- Source: Zoom transcript, Weekly Capstone Scrum meeting, **Wed 23 Sep 2026**. The file ends mid-sentence while Richard is dividing presentation ownership (`Weekly Capstone Scrum meeting_ Transcript (1).txt`).
- Speech-to-text aliases used in the room: Laurie/Lori (Loredana), Mayo/Mai (Mael), Versailles (Vercel), Freight (FRED), AT1010 (80-10-10), PTC/BTT (BTC).
- An earlier Zoom AI summary added items the transcript does not support: Fisher scaling, a CI/CD repair task, a 5 Oct date spoken in the room, Quantic concentration plans, and a finished speaker assignment (Loredana on Scrum process, Sid on backend and AI). Those are not in this write-up.
- Previous documented session: [9 Sep 2026 Review, Refinement & Planning](./2026-09-09-review-and-planning.md). The 16 Sep sync has no write-up in this folder.
- Related: [4 Sep 2026 Dr. Robert checkpoint](./2026-09-04-dr-robert-steele-checkpoint.md) · Capstone criteria: [Quantic grading](../quantic/grading.md) · [Deliverables](../quantic/deliverables.md).

---

## Next meeting

Wed 30 Sep 2026 (Slot B) — see [recurring sync schedule](../team-roles.md#recurring-meetings-through-14-oct-2026).
