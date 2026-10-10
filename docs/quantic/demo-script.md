# Capstone demo — speaking script (team)

**Single place for everyone’s lines.** Each presenter edits **their segment(s)** below by **8 Oct**. **Loredana** merges sections into one continuous narrative and finalizes the recording plan (total **15–20 min**).

| Role | Person |
|------|--------|
| Merge scripts & recording plan | **Loredana Lungu** (SM) |
| Facilitate recording | **Loredana Lungu** (SM) |

References: [demo-prep run-of-show](./demo-prep.md#agreed-run-of-show-18-min) · [7 Oct meeting](../meetings/2026-10-07-final-demo-planning.md) · [#752](https://github.com/TheQuintet/macrocrypto-ai/issues/752)

**Deploy URL:** https://macrocrypto-ai.lgloredanaelena.workers.dev/

**Recording:** Sat **10 Oct 2026** ~**18:00** (Zoom — Loredana). All five on camera for the full session.

**Key links (show on camera when relevant):**

| | |
|--|--|
| Repo | https://github.com/TheQuintet/macrocrypto-ai |
| Team Workflow board | https://github.com/orgs/TheQuintet/projects/6 |
| All Work (overview) | https://github.com/orgs/TheQuintet/projects/6/views/6 |
| Capstone sprints (×3) | [Sprint 1](https://github.com/orgs/TheQuintet/projects/6/views/18) · [Sprint 2](https://github.com/orgs/TheQuintet/projects/6/views/19) · [Sprint 3](https://github.com/orgs/TheQuintet/projects/6/views/20) — [deliverables §4](./deliverables.md#4-agile-task-board) |
| Domain Slack | `#mc-frontend`, `#mc-backend`, `#mc-ml-model`, `#mc-software-design` (async — no daily meeting) |
| Sprint 2 retro board | https://github.com/orgs/TheQuintet/projects/6/views/10 |
| Roadmap | https://github.com/orgs/TheQuintet/projects/6/views/5 |
| Design docs | https://github.com/TheQuintet/macrocrypto-ai/tree/main/docs/design |
| Testing doc | https://github.com/TheQuintet/macrocrypto-ai/blob/main/docs/test%20documents/local-and-ci-cd-tests.md |
| Meeting notes | https://github.com/TheQuintet/macrocrypto-ai/tree/main/docs/meetings |

---

## Storyline rules (agreed 7 Oct)

- **One continuous story** — each handoff should sound like the next beat, not a new presentation.
- **Personas:** frame features for the **BTC trader** and **investment analyst** where it helps.
- **3–4 minutes** per block, as timed in the [recording plan](#recording-plan-19-min-total). Keep the whole recording **under 20 min**.
- **Deployed app** on screen for live demos; **alerts use dummy data** — say that clearly on camera.
- **Quantic:** every member speaks; show **government ID** (name + photo legible). Kingson opens, then everyone shows their ID in one round: name and role.

---

## Recording plan (~19 min total)

| Order | ~Time | Running total | Who | Segment in this doc |
|-------|-------|---------------|-----|---------------------|
| 1 | ~0:45 | 0:45 | **Kingson** | [Opening & welcome](#1-kingson--opening--welcome-045) |
| 2 | ~1:15 | 2:00 | **All** | [Intros & IDs](#all-members--intros--ids-quantic): Kingson → Loredana → Richard → Mael → Sid; name + role, hold ID (~15 s each) |
| 3 | ~3:30 | 5:30 | **Sid** | [Problem, product & AI service](#2-sid--problem-product--ai-service-330) |
| 4 | ~3:30 | 9:00 | **Mael** | [Architecture & platform](#3-mael--architecture--platform-330) |
| 5 | ~3:00 | 12:00 | **Richard** | [Data gathering & preprocessing](#4-richard--data-gathering--preprocessing-300) |
| 6 | ~3:00 | 15:00 | **Loredana** | [Scrum process & alerts](#5-loredana--scrum-process--alerts-300) |
| 7 | ~4:00 | 19:00 | **Kingson** | [Dashboard, forecast & close](#6-kingson--dashboard-forecast--closing-demo-400) |

About **1 min of buffer** under the 20-min limit for handoffs and screen switches.

**Loredana — merged plan:** _combined transitions, dry-run notes_

- **Kingson (10 Oct):** updated script placed in segments 1 and 6. At ~140 wpm, segment 1 reads in **~0:45** and segment 6 in **~4:00**.
- **Order change (9 Oct):** Kingson's opening comes first, then the ID round, then Sid. His opening already names everyone's role, so the ID round can be just name + role. Optionally, Kingson can drop the teammate list from his opening to avoid repeating it.

---

## 1. Kingson — opening & welcome (~0:45)

**Must cover:** welcome; the problem in one breath; what MacroCrypto AI does; hand off to the ID round.

_Kingson’s script (updated 10 Oct). Lines in [brackets] are on-screen actions; everything else is spoken._

> Hey everyone, welcome! I’m Kingson, and we’re The Quintet. Bitcoin doesn’t move on its own. Rates, inflation, the whole economy push on it, and most tools only show you the price. So we built MacroCrypto AI. It puts the economy right next to the market and uses AI to forecast what’s next. Five of us built it. Before we show you how it works, let’s each introduce ourselves!

---

## All members — intros & IDs (Quantic)

Comes **right after Kingson’s opening** (~1:15 total). Each person says their **name** and **capstone role**, plus an optional short line about themselves, and **holds their ID** for ~10–15 s (name and photo legible).

Intro order: **Kingson → Loredana → Richard → Mael → Sid**. Sid goes last so his intro leads straight into his segment.

### Kingson Emma-Ochu (Frontend)

- **Intro line:** “I’m Kingson, frontend engineer.” _(ID up)_ — then “Loredana, over to you!”
- **ID on camera:** ☐

### Loredana Lungu (Scrum Master / frontend)

- **Intro line:** “Hi, I’m Loredana Lungu, Scrum Master and Frontend Lead.” _(hold ID)_ — then “Richard, over to you!”
- **ID on camera:** ☐

### Richard Owusu (ML / frontend)

- **Intro line:** “I’m Richard Owusu, ML and frontend engineer.” _(ID up)_ — then “Mael, over to you!”
- **ID on camera:** ☐

<details>
<summary><strong>Suggestions</strong></summary>

- “I’m Richard — ML and frontend. I focused on data gathering and preprocessing research, model evaluation literature, and keeping our ML story grounded in evidence the analyst persona can trust.”

</details>

### Mael Taye Deneke (Backend / code owner)

- **Intro line:** “I’m Mael Taye Deneke, code owner and lead backend developer.” _(ID up)_ — then “Sid, over to you!”
- **ID on camera:** ☐

<details>
<summary><strong>Suggestions</strong></summary>

- “I’m Mael, code owner for the backend. I implemented our core platform services, wired the AI service through the API Gateway, and set up CI/CD and automated tests for the services I own.”

</details>

### Sid Ahmed Mahieddine (Product Owner)

- **Intro line:** “I’m Sid Ahmed Mahieddine, Product Owner.” _(ID up)_ — then “Let’s start with the problem.”
- **ID on camera:** ☐

<details>
<summary><strong>Suggestions</strong></summary>

- “I’m Sid, Product Owner. I own product direction and led the AI service — multi-model forecasting, champion selection, and the data pipeline work that feeds those models.”

</details>

---

## 2. Sid — problem, product & AI service (~3:30)

**Must cover:** origin of the idea; problem; solution; high-level overview; **AI service** (prefer **one slide**: six models, champion selection, scheduled correlation analysis).

- **First line:**
- **Screen:** _(slide and/or deployed home — list what you’ll share)_
- **Talking points:**
  - Problem / solution / value
  - **AI service:** 6 models, how champion is chosen, correlation analysis on a schedule
  - What the trader vs analyst gets from predictions (high level)
- **Handoff to Mael:** “Mael made that architecture real — Gateway, services, messaging, cache, and the pipelines you’ll see in production. Mael, over to you!”

<details>
<summary><strong>Suggestions</strong></summary>

- **First line:** “Bitcoin doesn’t move in a vacuum — inflation, rates, and growth matter — so we built MacroCrypto AI to pair live BTC data with macro features and ML forecasts.”
- **Screen:** one slide (6 model names/types) + optional deployed home page.
- **Talking points:**
  - **Problem:** fragmented tools; predictions without macro narrative (trader pain) and manual merges (analyst pain).
  - **Solution:** event-driven backend + React dashboard; **13 macro-style features** feed forecasting (demo may show 9 if that’s what deploy has — call it out if needed).
  - **AI service:** train/compare **six models**; pick a **champion** on horizons like **24h and 7d**; run **scheduled correlation** so analysts see macro–BTC relationships over time.
  - **Trader** gets short-horizon forecast + confidence; **analyst** gets traceable inputs and correlation story.
- **Handoff:** “Mael made that architecture real — Gateway, services, messaging, cache, and the pipelines you’ll see in production.”

</details>

---

## 3. Mael — architecture & platform (~3:30)

**Must cover:** architecture and tech stack; **the services you implemented**; **RabbitMQ**; **Redis** caching; **testing and CI/CD**; **current and future architecture** diagrams.

- **Screen:** current architecture diagram, future architecture diagram, CI/CD run or screenshot

**Script** _([brackets] are on-screen actions; everything else is spoken)_

> I’m Mael, the code owner and lead backend developer.
>
> I was responsible for implementing the core platform services, including the **Data Service, Alert Service, API Gateway, and the integration with the AI Service**. I also worked on exposing the backend functionality through the API Gateway so that the frontend has a consistent entry point to the system.

**Current architecture**

> At a high level, our platform consists of **PostgreSQL with TimescaleDB, the Data Service, Alert Service, AI Service, API Gateway, Redis, RabbitMQ, and the frontend**.
>
> Let me briefly explain the responsibility of each component.
>
> **Data Service** is primarily responsible for collecting and processing our **Bitcoin and macroeconomic data**.
>
> **Alert Service** is responsible for managing alerts and notifications. For example, users can be notified when a Bitcoin price, prediction, or macroeconomic indicator crosses a defined threshold.
>
> **AI Service** is the analytical component of the platform, responsible for **prediction, correlation, and analysis** of the data collected by the system.
>
> These services are built using **FastAPI** and are exposed through the **API Gateway**.
>
> The **API Gateway** acts as the single entry point for the frontend. It provides a consistent interface to the backend services and handles communication between the frontend and the underlying services.
>
> For performance, we use **Redis as a caching layer**, with configurable TTLs so that frequently requested data can be served quickly while still allowing the cache to expire and refresh.
>
> We also use **RabbitMQ as our message-queuing platform** for asynchronous communication, particularly between the Data Service and Alert Service. It also allows alert events to be propagated when a configured trigger is fired.
>
> So, this is what our **current implementation** looks like.

**[Show current architecture diagram]**

**Future architecture**

> Our intention is not to stop at the capstone. We designed the architecture with future expansion in mind, and our plan is to extend the application with additional capabilities and services beyond the current implementation.

**[Show future architecture diagram]**

**Testing and quality assurance**

> From a quality perspective, we have implemented testing at several levels.
>
> We use **unit testing, integration testing, end-to-end testing, and full system-stack testing**.
>
> **Frontend:** we use Vitest and Playwright. **Backend:** we use Pytest. **System-level testing:** we use a Docker-based environment to simulate the complete application stack and verify that the services work together correctly.

**CI/CD pipeline**

> Finally, I’ll show the **CI/CD pipeline in action**, where these automated checks are executed as part of our development workflow.

**[Show CI/CD video or screenshot]**

- **If something fails live:** _(one line + fallback screen)_
- **Backup:** pre-recorded segment if connectivity fails
- **Handoff to Richard:** “Richard dug into where our data comes from and how we clean it before it ever reaches Sid’s models. Richard, over to you!”

---

## 4. Richard — data gathering & preprocessing (~3:00)

**Must cover:** data gathering and preprocessing **research** (sources, cleaning, features path toward ML).

- **First line:**
- **Screen:** _(docs, diagrams, or repo paths — specify)_
- **Talking points:**
  - Where macro / market data comes from
  - Preprocessing choices and why they matter for the models
  - Link to Sid’s AI segment without repeating model details
- **Handoff to Loredana:** “Loredana will show how we delivered this as a team in Scrum, then how a trader gets alerts in the UI. Loredana, over to you!”

<details>
<summary><strong>Suggestions</strong></summary>

- **First line:** “Good forecasts start with trustworthy data — we combine **market** and **macro** sources, then normalize them into features the AI service can consume.”
- **Screen:** README architecture table; data-service docs; any preprocessing / feature-table notes; optional FRED + exchange source callout.
- **Talking points:**
  - **BTC:** exchange/API collection (e.g. Binance path via data-service) for OHLCV and live price.
  - **Macro:** FRED-style indicators (CPI, rates, employment, etc.) — analyst persona cares about **provenance** and refresh cadence.
  - **Preprocessing:** alignment to **hourly** (or consistent) resolution for ML; handling missing values; building the **feature set** (up to 13 indicators) — research-backed choices, not ad hoc columns.
  - **Bridge to Sid:** “That feature table is what the six-model comparison and champion logic consume — I’ll stay out of model math since Sid covered it.”
- **Handoff:** “Loredana will show how we delivered this as a team in Scrum, then how a trader gets **alerts** in the UI.”

</details>

---

## 5. Loredana — scrum process & alerts (~3:00)

**Must cover:** Scrum process — roles, sprints, meeting notes, retro; **no daily standup** (team Slack decision — domain channels only); **frontend alerts** on deploy (**dummy data** — state on camera).

- **Screen:** [All Work](https://github.com/orgs/TheQuintet/projects/6/views/6) → Sprint [1](https://github.com/orgs/TheQuintet/projects/6/views/18) / [2](https://github.com/orgs/TheQuintet/projects/6/views/19) / [3](https://github.com/orgs/TheQuintet/projects/6/views/20) → [Sprint 2 retro board](https://github.com/orgs/TheQuintet/projects/6/views/10); `docs/meetings/`; deployed app — Alerts + notification bell

**Script** _([brackets] are on-screen actions; everything else is spoken)_

**[All Work view, Team Workflow board]**

> Thanks, Richard. Good data and good models only matter if five people can ship them together, so here's how we worked.
>
> Our roles were clear from day one. Sid was Product Owner and owned the backlog. I was Scrum Master. Mael was code owner for the backend, and Kingson, Richard and I shared the frontend.

**[Click Sprint 1 → Sprint 2 → Sprint 3 views]**

> We worked in nine sprints over the project. For the capstone, we grouped them into the three sprints Quantic asks for, and each one is a saved view on this GitHub board. You can see what we committed to and what we delivered.
>
> Early on, after a Slack discussion, we decided not to hold a daily standup. We had a weekly sync instead, plus async updates in domain channels for frontend, backend, the ML model and software design. Each discussion happens where that work lives.
>
> That choice had a cost. Focus got better, but some of us felt we saw less of the other areas. We made up for it with the weekly sync, the board and written notes.

**[Open docs/meetings]**

> Every meeting has notes in the repo.

**[Open Sprint 2 retro board]**

> In Sprint 2 we ran a full retrospective, with items on this board and written notes from 5 August. Later sprints had only a one-to-two-hour sync, so we dealt with blockers live in that meeting and recorded the improvements in the notes and on the board.
>
> Every piece of work followed the same path: a user story on the board, then a pull request, a review and CI. On the frontend, CI runs linting, type checks, unit tests and Playwright end-to-end tests.

**[Switch to deployed app → Alerts]**

> Now, alerts. **For this recording we're using dummy alert data**, so you can see the experience without waiting for a real market trigger.

**[Price tab → create a price alert]**

> A trader can set a price alert, for example Bitcoin crossing above a threshold.

**[Macro tab, Prediction tab]**

> There are also macro alerts, like a CPI release, and prediction alerts for when the model's outlook changes.

**[Open notification bell]**

> When a rule fires, the alert shows up here in the notification bell in real time. The trader doesn't have to watch the screen all day, and the analyst won't miss a macro event.
>
> That's how we built it. Kingson will now tie it all together with the live dashboard, the charts and the forecast traders use every day. Kingson, over to you!

- **If alerts fail:** _(fallback line)_ show alert UI mock or PR screenshot + board story marked Done.

---

## 6. Kingson — live demo & close (~4:00)

**Must cover:** the live deploy URL walkthrough (dashboard, macro, regime, forecasts, calendar); **Alerts** only as a one-line callback to Loredana’s segment; closing line.

**Click path (deploy URL):** Dashboard → Macro Economy → Regime analysis → Forecasts → Economic calendar → back to Dashboard.

- **Dashboard:** live BTC price with 24h and 7d change; macro regime card with confidence and reason; next 24-hour forecast with 85% band; BTC price chart from 30d to 1y.
- **Macro Economy:** inflation, rates, jobs, GDP, money supply and the dollar on one timeline with BTC; hover tooltips on what each move means for BTC.
- **Regime analysis:** Performance and Similar periods — a comparison, not a prediction.
- **Forecasts:** 24h to 7d; 70% to 95% confidence; the accuracy card with the model’s own track record.
- **Economic calendar:** filter by High impact; open an event; subscribe.
- **Alerts:** one-line callback only — “as Loredana showed you…” — so we don’t repeat her segment.
- **Close:**

> That’s MacroCrypto AI: the live price, the economy behind it, and an AI forecast that shows its track record. Built with React and TypeScript, an event-driven backend, and unit, integration and E2E tests. Five people, one goal. Thanks for watching!

- **If API fails:** _(one line; 9 macro indicators OK if 13 unavailable)_ — e.g. “Backend is slow — here’s the same view from our staging recording,” or show CI + merged PR.

---

## Global fallbacks (Loredana maintains for recording)

| Flow | If it breaks on camera, say | Show instead |
|------|-----------------------------|--------------|
| Forecast / prediction | “Prediction service is warming up — we validated this flow in CI and locally.” | Forecast PR / screenshot |
| Alerts | “We’re using **dummy alert data** for this demo.” | Board or backup clip |
| Notifications | “Notification delivery is async — here’s the inbox with a test event.” | Inbox screenshot |
| Macro / BTC load | “We’re showing **nine** stable indicators on this deploy.” | Full set on local recording |
| Deploy / health | “Health check timed out — architecture and tests are in the repo.” | **Green CI** in GitHub |

---

## Status

- [ ] Each member completed their segment(s) and intro above (**due 8 Oct**)
- [ ] Loredana merged one narrative + recording plan (**15–20 min**)
- [ ] Noted in [#752](https://github.com/TheQuintet/macrocrypto-ai/issues/752) or Slack
