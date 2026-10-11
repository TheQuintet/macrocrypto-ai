# Weekly Capstone Sync — 19 Aug 2026

Weekly Capstone Scrum sync: alert service status, front-end demo (BTC/USD dashboard, candlesticks, macro cards), PR and sub-issue closing conventions, scope and user roles, and open questions waiting on Dr. Robert.

| | |
|---|---|
| **Date** | Wed 19 Aug 2026 |
| **Type** | Weekly sync (demo + status + board review; partial retro) |
| **Sprint** | Sprint 3 (board: 18–24 Aug) |
| **Attendees** | Sid Ahmed Mahieddine, Loredana Lungu, Mael Taye Deneke, Richard Owusu (Mael left before the end) |
| **Absent** | Kingson Emma-Ochu |
| **Facilitator** | Loredana Lungu (Scrum Master) |
| **Product Owner** | Sid Ahmed Mahieddine |

---

## Key outcomes

- **Alert service** is functionally close to done (Mael estimated about 85%). Sid will fix test failures caused by record ordering in the T8 and T9 tests (the alert table must be created before tables that reference it). Mael will review the code again and make improvements before merging.
- **Data service** is considered complete. Some optional data-service and macro-event sub-issues remain on the board.
- **Remaining back-end work** is the API Gateway and the ML model. Sid will start the API Gateway that evening. Mael hopes to finish it this sprint. Sid plans to focus the next month on the ML model and software design.
- **Front end:** Loredana demoed the BTC/USD dashboard price widget (live updates over a WebSocket, currently on mock data), a candlestick prototype, and the macro indicator cards built by Richard. Front-end unit tests are not closed yet because the charts are still missing.
- **Front-end data path:** the front end must call the API Gateway, not the back-end services directly. Loredana had wired one test call straight to a service; she will switch to the gateway through a configuration variable that is not committed.
- **Dr. Robert** has not replied yet. The reply decides two things: whether user accounts and login are required, and whether deployment must handle scaling and circuit breakers or Docker Compose is enough.
- **Process:** the team agreed on how PRs should close sub-issues, reviewed the stacked-PR workflow, and agreed that Richard will pair with Loredana on the front end from 20 Aug.

---

## Progress by area

| Area | Owner | Status |
|------|-------|--------|
| Alert service | Sid (build), Mael (review) | About 85% functional; T8/T9 test-ordering fix pending; Mael to review and improve, then merge |
| Data service | Mael | Considered done; test coverage was about 79–80% on the last measurement; optional sub-issues remain |
| Other services' tests | Team | Several failing; Mael proposed this sprint focus on data/alert cleanup and test coverage |
| API Gateway | Sid (starting), Mael (target: finish this sprint) | Starting; ownership of the remaining work is not fully clear |
| ML / AI model | Sid | Not started in this sprint; main focus for the following month |
| BTC/USD dashboard (front end) | Loredana | Live price widget demoed on mock data; still to switch to the gateway |
| Candlestick chart | Loredana | Prototype demoed; not yet decided as the final chart |
| Macro indicator cards | Richard | Three cards demoed; front-end unit tests still on mock data |
| Front-end unit tests | Loredana | Not closed; waiting on charts |
| Economic calendar / macro events (optional) | Mael (optional) | Optional sub-issues on Fed-style events; no commitment |
| Software design diagrams | Team | Large workload; planned for the coming month |
| Deployment | Team | Waiting on Dr. Robert (Docker Compose vs. scaling/circuit breaker) |
| User accounts and authentication | Team | Pending Dr. Robert; likely to be dropped if not required |

---

## Decisions

| Topic | Decision |
|-------|----------|
| **Front-end data source** | Front end calls the API Gateway, never back-end services directly; the API switch is a configuration variable, not committed |
| **Sub-issue closing** | Put `closes #<sub-issue>` in the commit title and in the PR description, so GitHub closes the sub-issue and the link survives branch deletion |
| **Stacked PRs** | Accepted as the way to split large work; review oldest first; approve and merge the last PR in the stack |
| **Alert service completion** | Treat the alert service as done once Sid's failing tests pass and Mael's review is complete; whoever finishes the last change merges |
| **Sprint focus (back end)** | Mael proposed dedicating this sprint to modifying the data and alert services and raising test coverage; the team agreed |
| **Local tests before PRs** | Mael strongly advised running tests locally before opening a PR, relying on CI on push as a second check |
| **Macro indicators placement** | Macro indicators sit on the same page as BTC views, so both are visible together; investment-analyst-specific features (such as data export) are a later item |
| **User roles** | Two user types (BTC trader, investment analyst) plus a shared default role; shared sub-issues were consolidated under the default role |
| **Authentication / accounts** | Not built unless Dr. Robert requires accounts; otherwise a simple view switch satisfies the business requirements |
| **Scope** | Scope was reduced to the minimum after two team members left; the focus is the event-driven architecture and the ML model, using public BTC and macro data |
| **Richard on front end** | Richard collaborates with Loredana on the front end from 20 Aug instead of the back end, since Kingson is unavailable |
| **Daily status Slack channel** | Stays optional; not being enforced |

---

## Action items

| Owner | Action | Target | Status |
|-------|--------|--------|--------|
| Sid | Fix record-ordering in T8/T9 tests so all tests pass; then hand over to Mael for review | 19 Aug (evening) | Open |
| Sid | Start the API Gateway work | 19 Aug (evening) | Open |
| Mael | Review the alert service code again, make improvements, then merge | This sprint | Open |
| Mael | Review optional data-service and macro-event sub-issues; implement those that are feasible | This sprint | Open |
| Mael | Move completed sub-issues from "In review" to "Done"; use `closes #<id>` in commit titles and PR descriptions from now on | Ongoing | Open |
| Loredana | Switch the front end from direct service calls to the API Gateway via a configuration variable | Next sync (20 Aug) | Open |
| Loredana | Close finished sub-issues still in review (one she missed to check) | Next sync (20 Aug) | Open |
| Loredana | Finish charts, then unit tests on mock data; close the front-end story after that | After charts | Open |
| Loredana | Define user-role rules and where unit vs. integration tests belong | Next sync (20 Aug) | Open |
| Sid | Chase Dr. Robert's reply on accounts/authentication and deployment requirements | Ongoing | Open |
| Sid | Draft a strategy for issue creation: when to create issues, labels, and how to organize them | Next sync (20 Aug) | Open |
| Richard | Work with Loredana on the front end, replacing Kingson's planned collaboration | From 20 Aug | Open |
| Sid | Remind Mael of the `closes` convention if needed | Next sync | Open |

---

## Open questions

- **Dr. Robert reply:** Does the project need user accounts and login? Does deployment need scaling and circuit breakers, or is Docker Compose enough? (No reply as of the session.)
- **Sprint label:** Some sub-issues were tagged "Sprint 5" on the board during the session, while this write-up follows the board's Sprint 3 (18–24 Aug). (unclear in transcript)
- **API Gateway ownership:** Both Sid and Mael said they would work on it this sprint; who owns which part is not stated. (unclear in transcript)
- **Mael's sprint commitments:** Sid asked whether Mael had picked up sprint issues; Mael's reply was not clear. (unclear in transcript)
- **Issue creation rules:** Sid wants a strategy; Loredana proposed that she stops creating issues and asks others to create them when needed. No decision recorded.
- **Front-end integration test / API endpoint item:** Loredana raised a question about an integration-test and API-endpoint sub-issue for real-time BTC price updates. (unclear in transcript)
- **Retro:** A retro was intended but was mostly folded into the discussion; no formal retro items were recorded. (unclear in transcript)

---

## Notes

- Source: Zoom transcript of the Weekly Capstone Scrum meeting, 19 Aug 2026.
- Next session: Thursday 20 Aug 2026, evening (planning and front-end/back-end alignment).
- Previous session: [Sprint 2 review and sprint planning, 5 Aug 2026](./sprint-1-2026-08-05-retrospective.md).
