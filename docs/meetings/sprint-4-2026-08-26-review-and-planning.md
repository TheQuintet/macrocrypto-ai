# Review, Refinement & Planning — 26 Aug 2026

Combined session: dashboard demo and review, product-scope refinement, current-sprint planning, integration, and deployment.

| | |
|---|---|
| **Date** | Wed 26 Aug 2026 (Slot B) |
| **Type** | Review + Refinement + Planning |
| **Sprint** | Sprint 4 (board: 25–31 Aug) — current sprint (alerts and frontend) — ML / remaining AI work deferred to September |
| **Attendees** | Sid Ahmed Mahieddine, Loredana Lungu, Kingson Emma-Ochu (joined later) |
| **Also expected** | Mael Taye Deneke — connectivity risk; recording to be shared. Richard Owusu implemented alerts (attendance was not confirmed in the source notes). |
| **Facilitator** | Loredana Lungu (Scrum Master) |
| **Product Owner** | Sid Ahmed Mahieddine |

---

## Key outcomes

- The chart is for **prediction analysis**, not trading execution. Twenty-four-hour and seven-day intervals are enough for the current solution.
- The dashboard uses **candlesticks** (line view dropped). Users should be able to choose **24-hour** or **seven-day** candles on the same one-year chart, with historical navigation via extra data fetching.
- **Work delivered:** **Richard** implemented **alerts**. **Loredana** implemented **macro-indicator charts and history** (color-coded cards, graph/table historical views; demoed in this session).
- **This sprint:** alerts (Richard) and remaining frontend alert issues. **September:** remaining macro-indicator work, ML model, AI service, indicator rationale, and a broader project review.
- Front-end alert work should connect to the **API gateway** as soon as possible so request parameters, URLs, response shape, pagination, and data format can be validated together.
- **Vercel** is the preferred first deployment; Amazon is available but more complex. The team still decides the platform together. Plan: a simple working deploy now, plus a diagram of a more complete production architecture later.

---

## Decisions

| Topic | Decision |
|-------|----------|
| **Product scope** | Support **prediction analysis**, not trading execution |
| **Candlestick intervals** | **24-hour** and **seven-day** are sufficient; finer intervals need more compute and are not a current priority |
| **Chart presentation** | **Candlesticks only** — the former line view is not needed |
| **Chart controls** | Separate controls for 24-hour vs seven-day candles so the same one-year view can re-render at either interval; keep full-year view and historical navigation |
| **Current sprint** | **Alerts** and **frontend alert issues** only — keep essential work in the limited timeline |
| **Deferred to September** | Macro indicators (remaining), ML model / AI engineering, indicator rationale, remaining AI service work, broader project review |
| **Indicator feature set** | Minimum of **five BTC indicators** and **five macroeconomic / US-dollar indicators**; document them in project stories (not only Slack) |
| **Story discipline** | Sprint stories should be closed for modification; new requirements go in as **feature requests** so the capstone can finish |
| **Integration** | Connect frontend alerts to the API gateway early; align request parameters, endpoint URLs, response structure, pagination, and data format |
| **Transparency** | Show the indicators used for model training in the UI so users can compare values with official sources |
| **Initial deployment** | **Vercel** preferred for speed; Amazon account with credit is more complex. Final platform is a **team decision** |
| **Deployment approach** | Ship a **simple working deployment** first; document a more complete production architecture (scalability and availability) in a design / UML diagram |
| **Fallback plan** (if needed) | Simplify the product, avoid authentication features, and prioritize the ML model |

---

## Sprint review

Loredana demonstrated the latest dashboard, including the **macro-indicator charts and history** she implemented. Sid asked about Bitcoin trading research; Loredana’s observations were about chart usage — BTC traders may lean on daily / broader-market views more than the shorter time frames common in Forex.

| Area | Owner | Status |
|------|-------|--------|
| **Dashboard / price chart** | Loredana | Candlesticks replace the former line view. Granularity still changes with historical range (including current one-year behaviour). Pagination, scrolling, and the split between historical-range selection and candlestick-size still need clearer requirements in the issue |
| **Macro-indicator charts and history** | Loredana | Color-coded cards (colors reused on the macro-indicators page). Demo covered mocked data, tooltips, influence, indicator lines, filtering, and historical values in graph and table form |
| **Indicator data** | Loredana (frontend) | Indicators can have periodicities from roughly **15 days to six months**. Table beneath the chart approved. Macro-indicator and BTC/USD price data already connect to the backend; remaining work is pagination and historical indicator shape |
| **Alerts** | Richard | Richard implemented alerts; Loredana’s mentorship was credited with supporting that progress |
| **Responsive frontend** | Loredana | Bugs remain, including combo-box values appearing away from the control on mobile |
| **API gateway** | Sid | Still in progress — needed before the team can validate frontend requests and backend responses together |
| **Richard’s mobile changes** | Richard | Related issue stayed open pending completion of the broader macro-indicator graph |

---

## Refinement

The team asked for clearer **business and UX** context when stories enter a sprint. Issues are highly interdependent; new requirements should not reopen in-sprint stories.

| Item | Outcome | Ready for sprint? |
|------|---------|-------------------|
| Selectable 24-hour and seven-day candlesticks | Sid documents the requirement and adds implementation guidance on the relevant issue | Yes (requirements / issue update) |
| Historical candlestick timeframes | Sid reviews issue comments and clarifies display behaviour vs historical-range selection | Yes (requirements) |
| Five BTC + five macro / USD indicators | Add to project stories so they are visible outside Slack | Yes (documentation) |
| Alerts + frontend alert issues | Richard owns alerts; connect to the API gateway and test as soon as possible | Yes |
| Indicator color-coding | Carry color-coding logic and related unit tests into sprint work | Partial (this / next sprint) |
| Historical indicator data | Loredana implemented macro-indicator charts and history; remaining backend concerns are pagination and historical structure | Partial |
| Macro-indicator graph (remaining) | Loredana continues remaining graph work and backend wiring | Carry / September |
| Macro indicators in different colors for BTC Trader | Next sprint | Next sprint |
| ML feature selection, model construction, 10-fold cross-validation | Discuss in September; remaining AI service work then | Deferred |
| Deployment platform | Team decides; Vercel preferred for the first deploy | Later (simple deploy first) |

---

## Sprint planning — current sprint

Narrow the sprint to foundational work that still fits the timeline.

| Focus | Owner | Notes |
|-------|-------|-------|
| Alerts and frontend alert issues | Richard | Richard implemented alerts; connect to the appropriate service and test integration as soon as possible |
| API gateway completion | Sid | Needed so frontend and backend can validate requests and responses together |
| API contract alignment | Sid + Loredana | Request parameters, endpoint URLs, response structure, pagination, data format |
| Indicator color-coding | TBD (source notes: “meeting participant”) | Include color-coding logic |
| Indicator unit tests | TBD (source notes: “meeting participant”) | Carry over into this sprint |
| Macro-indicator charts and history | Loredana | Loredana implemented the charts and historical views; remaining pagination / historical structure still open |
| Frontend support tasks | Kingson (with Loredana) | Kingson picks ready frontend tasks he can support or complete |
| Sprint-story review | Team | Review stories from a business and UX perspective before or during planning |

**Out of this sprint (September or later)**

- Remaining macro-indicator graph and backend wiring
- Macro-indicator colors for BTC Trader (next sprint)
- ML model construction, feature selection, evaluation (e.g. tenfold cross-validation)
- Remaining AI service work, indicator rationale, broader project review
- Production deployment architecture diagram (record the idea; discuss again only if needed)

---

## Action items

| Owner | Action | Status |
|-------|--------|--------|
| Sid | Provide Mael with the meeting recording after the session | ⏳ Open |
| Sid | Review relevant issue comments and add implementation guidance for candlestick timeframes and display behaviour | ⏳ Open |
| Sid | Document the requirement for selectable 24-hour and seven-day candlestick views on the relevant issue | ⏳ Open |
| Sid | Add the selected five BTC indicators and five macroeconomic / US-dollar indicators to the relevant project stories | ⏳ Open |
| Sid | Complete the API gateway so the team can validate frontend requests and backend responses together | ⏳ Open |
| Sid + Loredana | Align API request parameters, endpoint URLs, response structure, pagination, and data format during integration | ⏳ Open |
| Richard | Continue alerts work; connect frontend alert work to the appropriate service and test the integration as soon as possible | ⏳ Open |
| Loredana | Continue macro-indicator charts and history (pagination and remaining historical structure) | ⏳ Open |
| Loredana | Complete the remaining macro-indicator graph implementation and connect the display to backend data | ⏳ Open |
| Loredana | Create a prompt to evaluate the repository against Quantic’s capstone criteria | ⏳ Open |
| Kingson | Coordinate with Loredana to select frontend tasks he can support or complete | ⏳ Open |
| TBD | Implement color-coding logic for indicators | ⏳ Open |
| TBD | Carry over unit tests for indicators into the sprint work | ⏳ Open |
| TBD | Implement macro indicators in different colors for BTC Trader in the next sprint | ⏳ Open |
| Team | Review sprint stories from the business and UX perspective before or during sprint planning | ⏳ Open |
| Team | Discuss feature selection, ML-model construction, and evaluation methods such as tenfold cross-validation (September) | ⏳ Open |
| Team | Complete remaining AI service work in September | ⏳ Open |
| Team | Decide the deployment platform collectively | ⏳ Open |
| Team | Create a simple initial deployment and document the more complex production architecture in a diagram | ⏳ Open |

Items marked **TBD** were recorded in the source notes as “meeting participant” without a named owner.

---

## Discussion notes

### Attendance, connectivity, and meeting plan

The group checked audio, attendance, and internet reliability. Mael might miss the call because of poor connectivity, so Sid asked for his notes and questions and planned to send the recording afterward. Loredana proposed demoing the latest macro-indicator work, reviewing backend progress, and holding a retrospective if time allowed. A full retro was not captured in these notes.

### Trading perspectives and time frames

Sid asked what research Loredana had done on Bitcoin trading techniques. Loredana said her observations were about chart usage: Bitcoin traders may emphasize daily, broader-market views rather than the shorter time frames often used in Forex analysis.

### Dashboard view changes

Loredana showed the updated dashboard with candlesticks instead of the former line view. Sid agreed the line view was not needed. The team also discussed Richard’s mobile changes and why that issue stayed open until the broader macro-indicator graph is done.

### Macro-indicator design and demonstration

Loredana demonstrated the **macro-indicator charts and history** she implemented: color-coded cards (the same colors are reused on the macro-indicators page), mocked indicator data, tooltips, influence information, indicator lines, filtering, and historical values in graph and table formats.

### Candlestick timeframes and historical navigation

Loredana showed how candlestick granularity changes across historical ranges, including current one-year behaviour. Sid proposed letting users choose **24-hour** or **seven-day** candles while keeping the full-year view and supporting historical navigation through additional data fetching.

### Chart controls and user perspectives

The team discussed pagination, scrolling, and the difference between historical-range selection and candlestick-size settings. They converged on **separate controls** for 24-hour and seven-day candles so users can re-render the same one-year chart at either interval.

### Prediction scope and computing constraints

The chart supports **prediction analysis**, not trading execution. Twenty-four-hour and seven-day predictions are enough for the current solution; more granular intervals would need extra computing power and are not a current priority.

### Chart presentation and indicator data

Sid praised the visual design, especially the colors. The line chart is dropped in favor of candlesticks. Participants approved the table under the chart. Indicators can have periodicities from roughly 15 days to six months.

### Responsive frontend issues and requirements clarification

Loredana reported responsive bugs, including combo-box values appearing away from the control on mobile. She asked for clearer business-oriented requirements for historical candlestick timeframes. Sid agreed to review and update the relevant issue with guidance.

### MVP prioritization

Keep issue history organized and retain MVP value. Broader implementation depends on available time.

### Progress on alerts and team support

Prioritize and document only essential work in the remaining timeline. **Richard implemented alerts**; Loredana’s mentorship was credited with supporting his rapid improvement. **Loredana implemented the macro-indicator charts and history** shown in the demo.

### Team availability and development progress

Kingson rejoined, apologized for his absence, and received support from the team. Participants shared progress and discussed continuing collaboration when Kingson is ready.

### Front-end understanding and user experience

Sid asked Loredana to explain her understanding of the project, its purpose, and the needs of BTC traders and investment analysts. The discussion focused on UX and gaps in frontend requirements, especially for the more technical investment-analyst persona.

### Story scope and sprint discipline

Loredana’s main difficulty is that project issues are highly interdependent. She asked for more business-context reviews when stories enter a sprint, and argued that sprint stories should be closed for modification — new requirements should be recorded as feature requests so the capstone can move toward completion.

### ML features and front-end transparency

Richard connected Sid’s emphasis on five indicators to the idea that those indicators would be used by the ML model and should therefore appear in the frontend. Sid explained that the project predicts BTC prices from BTC and macroeconomic data, with five indicators from each domain as the minimum feature set.

### Documenting requirements and planning model work

The five indicators were not visible in the stories; Sid agreed they should be documented there rather than only in Slack. The team had prioritized alerts and data ingestion before deeper discussion of feature selection, model evaluation, and software design.

### Transparency and user trust

Showing the indicators used for model training would make the relationship between the model and the UI more transparent. Users could compare displayed values with official sources, which would help establish confidence in the application.

### Sprint priorities and September planning

Document the issues being addressed, manage available time, and narrow the current sprint to foundational work. Alerts and frontend alert issues are in; macro indicators, ML model work, AI engineering, indicator rationale, and a broader project review move to September.

### Sprint board review and work items

Loredana asked how to move work items into progress; the team considered board settings and possible label-related limitations. They reviewed work on indicator tests, color-coding, historical indicator data, macro event subscriptions, pull requests, and significant prediction-change alerts, and identified additional macro-indicator color work for the next sprint.

### Front-end and API gateway integration

Sid and Loredana discussed whether frontend alert work should connect immediately to the API gateway or use a temporary API. They favored early integration to catch mismatches in request parameters, endpoint URLs, response formats, pagination, and data structures.

### Existing data connections and gateway completion

Loredana reported successful backend connections for macro-indicator data and BTC/USD price data. Remaining concerns are pagination and structuring historical indicator data, while Sid works toward completing the API gateway for coordinated frontend and backend validation.

### Team pressure and sprint alignment

The team reiterated the need to synchronize frontend and backend implementations. Loredana encouraged a sustainable, learning-oriented approach. Sid explained that schedule pressure was meant to surface issues early and preserve time for planning.

### Fallback plan and team coordination

Loredana invited Kingson to take on ready tasks. Sid raised two discussion topics: capstone feedback and the unresolved email to Robert. The fallback plan is to simplify the product, avoid authentication features, and prioritize the ML model. Kingson should coordinate with Loredana on frontend work.

### Capstone feedback and novelty expectations

Sid and Loredana reviewed capstone feedback, including criteria-based AI assessment and concerns about novelty. Sid contrasted a typical student project with this team’s concept, which he considered potentially differentiated through combined macroeconomic and market data, plus later expansion of indicators and model capabilities.

### Quantic criteria and remaining technical requirements

Loredana committed to a private AI-based check of the repository against Quantic’s capstone requirements. Sid reported that the current implementation appears to satisfy the documented requirements, with the ML model, results, and performance metrics remaining as the principal technical gaps.

### Deployment platform and architecture

Options included Vercel and the Amazon account with available credit. Amazon is more complex; Vercel would likely be faster. The final platform decision stays with the team. Sid proposed a simple working deployment now and a design / UML diagram later covering a more complete production setup (scalability and availability). The team agreed to record that idea for later and to schedule another discussion only if needed.

---

## Key takeaways

- Prediction analysis is in scope; trading execution is not.
- Chart: candlesticks only, with user-selectable **24-hour** and **seven-day** intervals on the one-year view.
- **Richard** delivered **alerts**; **Loredana** delivered **macro-indicator charts and history**.
- This sprint is alerts + frontend alerts + API-gateway integration; ML and remaining AI work wait until September.
- Document the five BTC and five macro / USD indicators in stories, and show them in the UI for transparency.
- Prefer a simple Vercel-first deploy; keep a production-architecture diagram for later.

---

## Notes

- Source: meeting summary, action items, and discussion transcript provided after the session (26 Aug 2026).
- Previous documented session: [5 Aug 2026 Retrospective, Review, Refinement & Planning](./sprint-1-2026-08-05-retrospective.md). Recurring Slot B also ran on 12 Aug and 19 Aug; those sessions are not written up in `docs/meetings/` yet.
- Capstone criteria: [Quantic grading](../quantic/grading.md) · [Deliverables](../quantic/deliverables.md).

---

## Next meeting

See [recurring sync schedule](../team-roles.md#recurring-meetings-through-14-oct-2026) — session write-up: [2 Sep 2026 Review, Refinement & Planning](./sprint-5-2026-09-02-review-and-planning.md).
