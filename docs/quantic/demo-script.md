# Capstone demo — speaking script (team)

**Single place for everyone’s lines.** Each presenter edits **their segment(s)** below by **8 Oct**. **Loredana** merges sections into one continuous narrative and finalizes the recording plan (total **15–20 min**).

| Role | Person |
|------|--------|
| Merge scripts & recording plan | **Loredana Lungu** (SM) |
| Facilitate recording | **Loredana Lungu** (SM) |

References: [demo-prep run-of-show](./demo-prep.md#agreed-run-of-show-18-min) · [7 Oct meeting](../meetings/post-sprint-9-2026-10-07-final-demo-planning.md) · [#752](https://github.com/TheQuintet/macrocrypto-ai/issues/752)

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

- **Kingson (9 Oct):** script received and placed in segments 1 and 6. At ~140 wpm, segment 1 reads in **~0:45** and segment 6 in **~4:00**.
- **Order change (9 Oct):** Kingson's opening comes first, then the ID round, then Sid. His opening already names everyone's role, so the ID round can be just name + role. Optionally, Kingson can drop the teammate list from his opening to avoid repeating it.

---

## 1. Kingson — opening & welcome (~0:45)

**Must cover:** welcome; team + product in one sentence; set up the problem the capstone solves; hand off to the ID round.

_Kingson’s script (9 Oct). Lines in [brackets] are on-screen actions; everything else is spoken._

**[Dashboard, top of page, cursor still]**

> Hi, I’m Kingson Emma-Ochu, a frontend engineer on The Quintet. My teammates are Sid Ahmed Mahieddine, our Product Owner; Loredana Lungu, our Scrum Master; Mael Taye Deneke, who owns the backend; and Richard Owusu, who works on frontend and machine learning. This is MacroCrypto AI.
>
> Here’s the problem. A Bitcoin trader watches the price on one site and the economy on another, and has to put the two together in their head. We put them on one screen, so you can see why Bitcoin is moving, not just what it’s doing.

- **Handoff to the ID round:** _not in Kingson’s script — add one line, e.g._ “Before we show you how it works, let’s each introduce ourselves.”

---

## All members — intros & IDs (Quantic)

Comes **right after Kingson’s opening** (~1:15 total). Each person says their **name** and **capstone role**, plus an optional short line about themselves, and **holds their ID** for ~10–15 s (name and photo legible).

Intro order: **Kingson → Loredana → Richard → Mael → Sid**. Sid goes last so his intro leads straight into his segment.

### Kingson Emma-Ochu (Frontend)

- **Intro line:** “Hi, I’m Kingson Emma-Ochu, a frontend engineer on The Quintet.” _(his full opening also introduces the whole team — see [segment 1](#1-kingson--opening--welcome-045))_
- **ID on camera:** ☐

### Loredana Lungu (Scrum Master / frontend)

- **Intro line:**
- **ID on camera:** ☐

<details>
<summary><strong>Suggestions</strong></summary>

- “I’m Loredana — Scrum Master and frontend. I run our Agile ceremonies, maintain meeting notes, and built macro indicator UI, alerts integration, E2E tests, and our deployment path for the demo.”

</details>

### Richard Owusu (ML / frontend)

- **Intro line:**
- **ID on camera:** ☐

<details>
<summary><strong>Suggestions</strong></summary>

- “I’m Richard — ML and frontend. I focused on data gathering and preprocessing research, model evaluation literature, and keeping our ML story grounded in evidence the analyst persona can trust.”

</details>

### Mael Taye Deneke (Backend / code owner)

- **Intro line:**
- **ID on camera:** ☐

<details>
<summary><strong>Suggestions</strong></summary>

- “I’m Mael, code owner for the backend. I implemented our core platform services, wired the AI service through the API Gateway, and set up CI/CD and automated tests for the services I own.”

</details>

### Sid Ahmed Mahieddine (Product Owner)

- **Intro line:**
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
- **Handoff to Mael:**

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

**Must cover:** architecture and tech stack; **three services** you implemented; **RabbitMQ**; **Redis** caching; **CI/CD** and test automation; link to **software design docs** (single MD + SVG UML; current and future architecture).

- **First line:**
- **Screen:** deploy URL, diagram, CI status, repo path to design doc
- **Talking points:**
  - End-to-end flow (Gateway, data, AI, alerts — as you built it)
  - RabbitMQ and Redis roles
  - CI/CD and automated tests (show green pipeline if useful)
  - Point to design doc — do not read it aloud
- **If something fails live:** _(one line + fallback screen)_
- **Backup:** pre-recorded segment if connectivity fails
- **Handoff to Richard:**

<details>
<summary><strong>Suggestions</strong></summary>

- **First line:** “Under the hood we use **microservices** so ingestion, alerts, and AI can scale independently — all exposed through one **API Gateway**.”
- **Screen:** deploy URL health; GitHub Actions; [docs/design/](https://github.com/TheQuintet/macrocrypto-ai/tree/main/docs/design) and [testing doc](https://github.com/TheQuintet/macrocrypto-ai/blob/main/docs/test%20documents/local-and-ci-cd-tests.md) (C4 / microservices / ADRs; consolidated software-design MD + SVG when ready).
- **Talking points:**
  - **Three services you own:** e.g. **data-service** (BTC + macro collection/APIs), **alert-service** (rules + notifications), **api-gateway** (single entry for the frontend) — adjust to what you actually present.
  - **RabbitMQ:** collectors publish events; services stay decoupled ([ADR-001](../design/adr/ADR-001-use-rabbitmq.md)).
  - **Redis:** cache hot reads (e.g. prices/indicators) to keep the dashboard responsive.
  - **TimescaleDB/Postgres** for history; **MLflow** for model artifacts where relevant.
  - **CI/CD:** PR checks, service tests, coverage goals — show a green run instead of re-running every test on camera.
  - **Design doc:** one Markdown index linking SVG diagrams; **current** deploy vs **future** scale-out — 30 seconds pointing at repo paths.
- **If fail:** “The deploy health check is flaky — here’s the same flow in our diagram and CI proof.”
- **Handoff:** “Richard dug into where our data comes from and how we clean it before it ever reaches Sid’s models.”

</details>

---

## 4. Richard — data gathering & preprocessing (~3:00)

**Must cover:** data gathering and preprocessing **research** (sources, cleaning, features path toward ML).

- **First line:**
- **Screen:** _(docs, diagrams, or repo paths — specify)_
- **Talking points:**
  - Where macro / market data comes from
  - Preprocessing choices and why they matter for the models
  - Link to Sid’s AI segment without repeating model details
- **Handoff to Loredana:**

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

**Must cover:** Scrum process — board, sprints, meeting notes, retro; **no daily standup** (team Slack discussion — domain channels only); **frontend alerts** on deploy (**dummy data** — state on camera).

- **First line:**
- **Screen:** [All Work](https://github.com/orgs/TheQuintet/projects/6/views/6) + [Sprint 1](https://github.com/orgs/TheQuintet/projects/6/views/18) / [2](https://github.com/orgs/TheQuintet/projects/6/views/19) / [3](https://github.com/orgs/TheQuintet/projects/6/views/20) + Sprint 2 retro; deployed app — alerts + notifications
- **Talking points:**
  - PO / SM / code owner; weekly sync + GitHub boards (not a daily meeting)
  - Async updates in `#mc-frontend`, `#mc-backend`, `#mc-ml-model`, `#mc-software-design`
  - PRs, CI, meeting notes in repo
  - Create or show alert flow; **explicit dummy-data disclaimer**
- **Click path (alerts):**
  1.
  2.
- **If alerts fail:** _(fallback line)_
- **Handoff to Kingson:**

<details>
<summary><strong>Suggestions</strong></summary>

- **First line:** “We ran this capstone with **sprints and boards**, but after a **Slack discussion** we agreed **not** to do a daily standup — live or required offline posts — we use **domain Slack** and the **weekly sync** instead.”
- **Screen:** [All Work](https://github.com/orgs/TheQuintet/projects/6/views/6) + board sprints [1](https://github.com/orgs/TheQuintet/projects/6/views/18) · [2](https://github.com/orgs/TheQuintet/projects/6/views/19) · [3](https://github.com/orgs/TheQuintet/projects/6/views/20) + [Sprint 2 retro board](https://github.com/orgs/TheQuintet/projects/6/views/10); [5 Aug retro notes](https://github.com/TheQuintet/macrocrypto-ai/blob/main/docs/meetings/sprint-1-2026-08-05-retrospective.md); [docs/meetings/](https://github.com/TheQuintet/macrocrypto-ai/tree/main/docs/meetings); open **Alerts** on deploy + notification bell/inbox.
- **Talking points:**
  - **Roles:** Sid PO, you SM, Mael code owner; frontend split across Kingson, you, Richard where relevant.
  - **Slack by domain:** `#mc-frontend`, `#mc-backend`, `#mc-ml-model`, `#mc-software-design` — discuss work where it lives; `#capstone-project-group` for whole-team items.
  - **Retro:** **Sprint 2 (5 Aug)** — full retro with items on the [retro board](https://github.com/orgs/TheQuintet/projects/6/views/10) and written notes. **Later sprints** — our weekly sync is only **1–2 hours**, so we **discussed emergent blockers live** in the meeting instead of maintaining a retro board every sprint; improvements are in **meeting notes** and the workflow board.
  - **Honest process note:** domain Slack improved focus but some members felt **less visibility**; we compensated with **weekly Capstone sync**, the **GitHub board**, and **PR/meeting notes**.
  - **Board for graders:** day-to-day work is **[All Work](https://github.com/orgs/TheQuintet/projects/6/views/6)** on Team Workflow #6 (sprints on the project **Sprint** field — we did not use GitHub Issues milestones). Capstone **three sprint boards** are saved views: [Sprint 1](https://github.com/orgs/TheQuintet/projects/6/views/18), [Sprint 2](https://github.com/orgs/TheQuintet/projects/6/views/19), [Sprint 3](https://github.com/orgs/TheQuintet/projects/6/views/20).
  - **Process:** user stories → PRs → review → CI.
  - **Engineering quality:** frontend lint/typecheck/unit tests + Playwright E2E; backend CI on services.
  - **Alerts demo:** “For this recording we’re using **dummy alert data** so you can see the UX without waiting on live triggers.”
- **Click path (example — replace with deploy routes):**
  1. Navigate to **Alerts** in the sidebar.
  2. Create or open a **price alert** (threshold above/below).
  3. Show **notification** (toast or inbox) firing from that dummy rule.
- **If fail:** show alert UI mock or PR screenshot + board story marked Done.
- **Handoff:** “Kingson will tie it together with the **live dashboard**, charts, and **forecast** traders use day to day.”

</details>

---

## 6. Kingson — dashboard, forecast & closing demo (~4:00)

**Must cover:** dashboard, charts, **forecast**; **closing live demo** on deploy URL (live backend data — not dummy).

_Kingson’s script (9 Oct). Lines in [brackets] are on-screen actions; everything else is spoken._

**Click path (deploy URL):** Dashboard → Macro Economy → Regime analysis → Forecasts → Economic calendar → Alerts → back to Dashboard.

**[Hover the “Live” indicator under the price]**

> This is the dashboard. The Bitcoin price is live. It streams over a WebSocket, and this indicator shows the connection status and when the last update came in. Next to it are the 24-hour and 7-day moves.

**[Point at the Macro regime card]**

> This card is the macro regime. Our service reads the latest Federal Reserve data and classifies the current backdrop, for example rising rates, high inflation or growth. It shows a confidence meter and a plain-English reason, so you know whether that backdrop has historically helped or hurt Bitcoin.

**[Scroll to the Forecast card, then the price chart. Switch the interval, then the time range]**

> Below that is the AI model’s outlook for the next day, and an interactive candlestick chart where you can change the interval and the time window.

**[Sidebar → Macro Economy. Hover the % change on an indicator card]**

> Under Macro Economy are the indicators that matter: inflation, interest rates, unemployment, GDP, money supply and the dollar. Hover over any change and it tells you what that move usually means for Bitcoin. Rising rates, for example, usually mean tighter liquidity, which has been a headwind.

**[Scroll to the combined chart and hover across it]**

> This is my favourite view. Bitcoin and the macro indicators share one timeline. Each series starts at 100 so different units fit on one scale, and when you hover, the price and the economy line up bar by bar.

**[Sidebar → Regime analysis. Click through the Performance, Timeline and Similar periods tabs]**

> Regime analysis goes deeper. It shows how Bitcoin performed in each kind of backdrop and a timeline of those regimes over the years. Similar periods finds the last times the economy looked like it does today and shows what Bitcoin did next. It’s a comparison, not a prediction, and we label it that way.

**[Sidebar → Forecasts. Switch 24h to 7d, then change the confidence level]**

> Forecasts shows the model’s 24-hour and 7-day predictions, with a confidence band around the price range it expects. Underneath is what I think matters most: forecast accuracy. We check past predictions against the real price, so you can see how much to trust the model before you rely on it.

**[Sidebar → Economic calendar. Click one event to open its details]**

> The economic calendar shows upcoming Fed decisions, CPI releases, jobs reports and GDP. You can filter by impact, switch time zones, and subscribe to an event straight from here.

**[Sidebar → Alerts. Click through the Price, Macro and Prediction tabs, then open the notification bell]**

> All of that feeds into alerts. You can set price alerts, macro event alerts and prediction alerts, and they arrive in this notification bell in real time.

**[Back to Dashboard]**

> So that’s MacroCrypto AI: live price, the economy behind it, and an AI forecast that shows its track record, all in one place. It’s built with React and TypeScript on an event-driven backend, and it’s covered by unit, UI-integration and end-to-end tests. Thanks for watching, from me and the rest of The Quintet.

- **If API fails:** _(one line; 9 macro indicators OK if 13 unavailable)_ — e.g. “Backend is slow — here’s the same view from our staging recording,” or show CI + merged PR.
- **Merge notes (Loredana):**
  - The **Alerts** beat overlaps [segment 5](#5-loredana--scrum-process--alerts-300). Either keep it as a one-line callback (“as Loredana showed…”) or drop it here.
  - If alerts stay in this segment, add the **dummy-data** disclaimer from the [storyline rules](#storyline-rules-agreed-7-oct).

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
