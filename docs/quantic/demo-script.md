# Capstone demo — speaking script (team)

**Single place for everyone’s lines.** Each presenter edits **their segment(s)** below by **8 Oct**. **Loredana** merges sections into one continuous narrative and finalizes the recording plan (total **15–20 min**).

| Role | Person |
|------|--------|
| Merge scripts & recording plan | **Loredana Lungu** (SM) |
| Facilitate recording | **Loredana Lungu** (SM) |

References: [demo-prep run-of-show](./demo-prep.md#agreed-run-of-show-18-min) · [7 Oct meeting](../meetings/2026-10-07-final-demo-planning.md) · [#752](https://github.com/TheQuintet/macrocrypto-ai/issues/752)

**Deploy URL (fill when ready):** _TBD_

**Recording:** Sat **10 Oct 2026** ~**18:00** (Zoom — Loredana). All five on camera for the full session.

---

## Storyline rules (agreed 7 Oct)

- **One continuous story** — each handoff should sound like the next beat, not a new presentation.
- **Personas:** frame features for the **BTC trader** and **investment analyst** where it helps.
- **~4 minutes** per block below (flex slightly; stay within **15–20 min** overall).
- **Deployed app** on screen for live demos; **alerts use dummy data** — say that clearly on camera.
- **Quantic:** every member speaks; show **government ID** (name + photo legible). Batch IDs + short intros at the start is fine.

---

## Recording plan (~18 min content + IDs)

| # | ~Time | Who | Segment in this doc |
|---|-------|-----|---------------------|
| 0 | ~1:30 | **All** | [Intros & IDs](#all-members--intros--ids-quantic) |
| 1 | ~4:00 | **Kingson** | [Opening & welcome](#1-kingson--opening--welcome-400) |
| 2 | ~4:00 | **Sid** | [Problem, product & AI service](#2-sid--problem-product--ai-service-400) |
| 3 | ~4:00 | **Mael** | [Architecture & platform](#3-mael--architecture--platform-400) |
| 4 | ~4:00 | **Richard** | [Data gathering & preprocessing](#4-richard--data-gathering--preprocessing-400) |
| 5 | ~4:00 | **Loredana** | [Scrum process & alerts](#5-loredana--scrum-process--alerts-400) |
| 6 | ~4:00 | **Kingson** | [Dashboard, forecast & close](#6-kingson--dashboard-forecast--closing-demo-400) |

**Loredana — merged plan (fill after 8 Oct):** _timing adjustments, combined transitions, dry-run notes_

---

## All members — intros & IDs (Quantic)

Each person: **name**, **capstone role**, **one sentence** on what you built → **hold ID** ~10–15 s (name and photo legible).

Suggested intro order (same as speaking flow): Kingson → Sid → Mael → Richard → Loredana.

### Kingson Emma-Ochu (Frontend)

- **Intro line:**
- **ID on camera:** ☐

<details>
<summary><strong>Suggestions</strong> (adapt — do not read verbatim)</summary>

- “I’m Kingson — frontend. I built the dashboard forecast experience: linking forecast from the dashboard, the forecast page, accuracy chart, and detail views traders use for 24-hour decisions.”

</details>

### Sid Ahmed Mahieddine (Product Owner)

- **Intro line:**
- **ID on camera:** ☐

<details>
<summary><strong>Suggestions</strong></summary>

- “I’m Sid, Product Owner. I own product direction and led the AI service — multi-model forecasting, champion selection, and the data pipeline work that feeds those models.”

</details>

### Mael Taye Deneke (Backend / code owner)

- **Intro line:**
- **ID on camera:** ☐

<details>
<summary><strong>Suggestions</strong></summary>

- “I’m Mael, code owner for the backend. I implemented our core platform services, wired the AI service through the API Gateway, and set up CI/CD and automated tests for the services I own.”

</details>

### Richard Owusu (ML / frontend)

- **Intro line:**
- **ID on camera:** ☐

<details>
<summary><strong>Suggestions</strong></summary>

- “I’m Richard — ML and frontend. I focused on data gathering and preprocessing research, model evaluation literature, and keeping our ML story grounded in evidence the analyst persona can trust.”

</details>

### Loredana Lungu (Scrum Master / frontend)

- **Intro line:**
- **ID on camera:** ☐

<details>
<summary><strong>Suggestions</strong></summary>

- “I’m Loredana — Scrum Master and frontend. I run our Agile ceremonies, maintain meeting notes, and built macro indicator UI, alerts integration, E2E tests, and our deployment path for the demo.”

</details>

---

## 1. Kingson — opening & welcome (~4:00)

**Must cover:** welcome; team + product in one sentence; set up the problem the capstone solves; hand off to Sid.

- **First line:**
- **Talking points:**
  - Hook for **MacroCrypto AI** (BTC + macro context)
  - Mention both personas briefly if natural
- **Handoff to Sid:**

<details>
<summary><strong>Suggestions</strong></summary>

- **First line:** “Welcome — we’re The Quintet, and this is **MacroCrypto AI**: one place for Bitcoin price, macroeconomic context, forecasts, and alerts.”
- **Talking points:**
  - **BTC trader** checks price in one app and macro in another — easy to miss *why* BTC moved.
  - **Investment analyst** spends time merging FRED-style series with market data for reports.
  - We built a single dashboard so both personas see BTC + macro + predictions together.
  - Today we’ll walk from the idea → platform → data → how we worked → live product.
- **Handoff:** “Sid shaped the product vision and the AI engine — he’ll connect the problem to what our models actually do.”

</details>

---

## 2. Sid — problem, product & AI service (~4:00)

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

## 3. Mael — architecture & platform (~4:00)

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
- **Screen:** deploy URL health; GitHub Actions; `docs/design/` (C4 / microservices / software design MD + SVG folder).
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

## 4. Richard — data gathering & preprocessing (~4:00)

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

## 5. Loredana — scrum process & alerts (~4:00)

**Must cover:** Scrum process — board, sprints, meeting notes, retro; **frontend alerts** on deploy (**dummy data** — state on camera).

- **First line:**
- **Screen:** GitHub board (≥3 sprints, retro visible); deployed app — alerts + notifications
- **Talking points:**
  - PO / SM / code owner; how the team worked in sprints
  - PRs, CI, meeting notes in repo
  - Create or show alert flow; **explicit dummy-data disclaimer**
- **Click path (alerts):**
  1.
  2.
- **If alerts fail:** _(fallback line)_
- **Handoff to Kingson:**

<details>
<summary><strong>Suggestions</strong></summary>

- **First line:** “We ran this capstone like a real product team — sprints, a visible board, and notes every week — while shipping a React dashboard on top of Mael’s Gateway.”
- **Screen:** GitHub Projects/board URL; `docs/meetings/` (e.g. this 7 Oct plan); open **Alerts** on deploy + notification bell/inbox.
- **Talking points:**
  - **Roles:** Sid PO, you SM, Mael code owner; frontend split across Kingson, you, Richard where relevant.
  - **Process:** user stories → PRs → review → CI; link **retro** column or doc; ≥3 sprints for graders.
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

- **First line:**
- **Screen:** deploy URL — dashboard, price chart, forecast page / accuracy view
- **Click path:**
  1.
  2.
  3.
- **Talking points:**
  - BTC trader journey on dashboard + forecast
  - Forecast accuracy / details if time
- **If API fails:** _(one line; 9 macro indicators OK if 13 unavailable)_
- **Closing line:**

<details>
<summary><strong>Suggestions</strong></summary>

- **First line:** “This is what the **BTC trader** sees day to day — live price, macro context, and a forecast they can act on.”
- **Click path (example — replace with real routes):**
  1. Open **Dashboard** — BTC price, 24h change, connection/status if shown.
  2. Scroll **macro indicator cards** (API-driven; mention if showing 9 vs 13).
  3. Open **Forecast** — prediction chart, horizon (24h/7d), **accuracy** or details view you shipped.
  4. Optional: quick link from dashboard card to forecast (your merged work).
- **Talking points:**
  - Real-time or near–real-time price stream vs static mock.
  - Macro cards answer “**why** is BTC moving?” for the trader; analyst can sanity-check against known indicators.
  - Forecast + confidence / accuracy card supports entry timing without leaving the app.
- **If API fails:** “Backend is slow — here’s the same view from our staging recording” or show CI + merged PR.
- **Closing line:** “Thanks for watching — MacroCrypto AI unifies BTC, macro data, ML forecasts, and alerts. Repo and deploy link are in our README; questions welcome.”

</details>

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
