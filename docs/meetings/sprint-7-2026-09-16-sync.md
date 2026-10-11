# Weekly Capstone Sync — 16 Sep 2026

Weekly Capstone Scrum sync: status on the ML data aggregation, the retraining design, the PR review backlog, and the plan to the submission window. No demo or board review took place. This is the first write-up for this session.

| | |
|---|---|
| **Date** | Wed 16 Sep 2026 |
| **Type** | Weekly sync (status and planning; no demo or review) |
| **Sprint** | Sprint 7 (board: 15–21 Sep). Two sprints remain, about 15 days to the submission window |
| **Attendees** | Sid Ahmed Mahieddine, Kingson Emma-Ochu, Mael Taye Deneke (joined about 20 minutes late) |
| **Not present** | Loredana Lungu, Richard Owusu |
| **Facilitator** | Loredana Lungu (Scrum Master), absent. Sid Ahmed led the discussion |
| **Product Owner** | Sid Ahmed Mahieddine |

---

## Key outcomes

- **Training data** is nearly aggregated. Mael reports more than 90% of the work is done. Remaining work is verification, confirming with Richard that each source is an authoritative source of truth, and checking that the CSV files can be cited as sources.
- **Data coverage is the main risk.** Some APIs changed, some series only cover three or five years, and some sources are published monthly, quarterly, or annually. Mael is pulling archived CSVs to lengthen history. Intersecting BTC price, BTC dominance, and macro indicators may leave roughly **2,000–3,000 rows**. Richard had asked for a minimum of **1,800** records, and Mael wants that minimum confirmed.
- **ML design (Sid):** three model families (Prophet, LightGBM, XGBoost), each trained two ways (fresh, and from the previous trained model). That gives six models per prediction horizon. The same design applies to the **24-hour** and **7-day** horizons. A comparison engine picks the best prediction and shows the other five for reference. Evaluation uses a back-testing technique and the metrics from Dr. Robert's feedback. The name of the back-testing technique was not recalled in the meeting.
- **Implementation status (Sid):** Prophet is implemented in both training variants. The other models are not yet implemented. Sid expects Mael to extend them by following the Prophet steps, with AI assistance.
- **Retraining window:** Sid configured retraining on the **past 180 days** (about six months). Mael said he can work with that, but Sid asked him to confirm the window against the agreed feature list.
- **Export:** chart export (PDF, PNG, CSV) is implemented and mostly considered closed.
- **Testing gap:** only unit tests exist. Integration and smoke tests still need all services running and communicating.
- **PR review backlog:** Sid's stacked PR series is about **50 PRs**. Mael has reviewed **8** and has **42** left. Mael asked for smaller, more granular PRs, which he says are easier to review.
- **Frontend:** Kingson reports the BTC-trader work is almost done and has about **four PRs** waiting for review and approval. Sid set the priority: **BTC-trader issues and user stories first**.
- **Submission window:** Sid's target is early October (5 Oct, possibly 6 Oct). Kingson's plan is to wrap up by the end of September and start recording the presentation at the start of October. Sid also plans a revision of documentation, software design, code, and tests during the second half of September.
- **Capstone deliverables** (Sid's question): working software, tests, CI/CD, deployment, and software design. Kingson's view is that any working minimum viable version is acceptable.

---

## Progress by area

| Area | Owner | Status |
|------|-------|--------|
| Training data (BTC price, BTC dominance, macro indicators) | Mael | More than 90% aggregated. Verification, source-of-truth confirmation with Richard, and archived CSV work still open |
| Feature list for models | Mael, Richard | Feature engineering done for Prophet. Sid thinks the feature list differs from what was agreed with Richard; Mael to check |
| Model orchestration and evaluation | Sid | Common path for three model families and two training methods. Prophet done in both variants. XGBoost and LightGBM not yet implemented |
| Retraining configuration | Sid | Set to 180 days. Not yet confirmed by Mael |
| Export (chart, PDF, PNG, CSV) | Sid | Implemented, mostly closed |
| Integration and smoke tests | Unassigned | Not started. Only unit tests exist |
| BTC-trader frontend | Kingson | Almost done. About four PRs waiting for review and approval |
| PR review (Sid's stacked series) | Mael | 8 of about 50 PRs reviewed. 42 remaining |
| Design docs | Mael, Sid | API design doc updated by Mael. Feature-engineering doc to be revised for the current models and dataset. Other docs to be updated alongside implementation |
| AI service and data integration | Mael | Handed to Mael by Sid. Starts after the dataset is ready |
| Presentation | Team | Each member to present their part. Planning to start during the coming days |

---

## Decisions

| Topic | Decision |
|-------|----------|
| **Frontend priority** | BTC-trader issues and user stories come first (Sid's instruction to Kingson) |
| **AI service integration** | Sid hands the integration of the AI service with the data service to Mael |
| **Stacked PRs** | Sid keeps the stack together so that AI-driven changes apply across all PRs at once. Mael reviews the stack. Not a formal team decision |
| **Data work before ML work** | Mael proposed finishing data work and joining the ML models from Friday 18 Sep, after he has learned the retraining process. Sid asked him to understand that process first. Not formally confirmed |
| **Shared database** | Sid asked whether to split the database so each model owns one. Mael agreed it is possible but wants to finish first. No decision was made |
| **Submission target** | Early October (5 Oct, possibly 6 Oct). Presentation recording to start at the start of October. Not formally agreed |

---

## Action items

| Owner | Action | Target | Status |
|-------|--------|--------|--------|
| Mael | Finish data aggregation and verification (BTC price, BTC dominance, macro indicators) | Tonight (16 Sep), then about two days | Open |
| Mael | Create a local branch, merge Sid's PR series, ask AI to explain the retraining flow, and check how many days of history are used | Before starting ML work | Open |
| Mael | Check the implemented feature list against what was agreed with Richard | Not stated | Open |
| Mael | Review the stacked PRs (42 remaining) | Not stated | Open |
| Mael | Start ML models from Friday, extending the non-Prophet models by following the Prophet pattern | From Fri 18 Sep (proposed) | Open |
| Mael | Revise the feature-engineering doc and update the API design doc | Not stated | Open |
| Mael | Integrate the dataset with the AI service and the data service | After dataset and models | Open |
| Richard | Confirm that the data sources are sources of truth and that the 1,800-record minimum is acceptable | Not stated | Open |
| Sid | Revise documentation, software design, code, and tests | Second half of September | Open |
| Sid | Confirm the retraining window and the back-testing technique in the design | Not stated | Open |
| Kingson | Prioritise BTC-trader issues and user stories | Ongoing | Open |
| Kingson | Get the about four open PRs reviewed and merged | Not stated | Open |
| Loredana | Review and approve Kingson's open PRs (absent from this session) | Not stated | Open |
| Team | Start planning which member presents which section of the project | Coming days | Open |
| Team | Reply in the channel and keep in touch | Ongoing | Open |

---

## Open questions

- Should the shared database be split so each model owns its own database, or kept as is for the submission? (unclear in transcript: discussed, no decision)
- Is the agreed feature list the same as the one Sid implemented? Sid thinks it may differ. (unclear in transcript)
- What is the confirmed retraining window: 180 days (Sid) or something else? Mael did not confirm 180 days. (unclear in transcript)
- Who owns integration and smoke tests? (unclear in transcript: not assigned)
- Which items does Kingson mean by "S3" and "A3" on the board? (unclear in transcript)
- Did Kingson say "MVP" or another term when he described the minimum deliverable? The transcript reads "simplest MDT version". (unclear in transcript)
- Is the submission date 5 Oct, or 5 Oct "or ahead, maybe six"? (unclear in transcript)

---

## Notes

- Source: Zoom transcript, Weekly Capstone Scrum meeting, **Wed 16 Sep 2026**. Transcript file: (file: Weekly Capstone Scrum meeting_ Transcript (7).txt, not committed).
- Speech-to-text aliases in the room: "Lori" or "Laurie" (Loredana), "Profit" (Prophet), "PTC" (BTC), "Frey" (FRED), "Kingson Son" or "Kingson Sun" (Kingson), "Mahil" or "Mai" (Mael), "Richard" (Richard Owusu).
- Personal and non-project remarks, audio trouble, and academic-program items were left out.
- Previous documented session: [23 Sep 2026 Review, Refinement & Planning](./sprint-8-2026-09-23-review-and-planning.md). The 9 Sep write-up is [sprint-6](./sprint-6-2026-09-09-review-and-planning.md).

---

## Next meeting

Wed 23 Sep 2026 — see [recurring sync schedule](../team-roles.md#recurring-meetings-through-14-oct-2026).
