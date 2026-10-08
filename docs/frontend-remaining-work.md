# Remaining work

Snapshot of **every user story** (T1–T9, A1–A5, S1–S3) against the [Team Workflow project board](https://github.com/orgs/TheQuintet/projects/6) (project **#6**) and `main` on **8 October 2026**, after Sprint 11 ([#695](https://github.com/TheQuintet/macrocrypto-ai/pull/695) dashboard forecast, [#693](https://github.com/TheQuintet/macrocrypto-ai/pull/693) forecast accuracy). Use this for planning, not as a substitute for the issue tracker. Capstone submission deadline was **5 October** ([deliverables](./quantic/deliverables.md)).

Related: [project scope](./project-scope.md), [user stories dependency map](./user-stories-dependency-map.md), frontend conventions in `AGENTS.md`.

Parent story issues stay **OPEN** while any child is open — usually leftover `[TESTING]` tickets or one deferred child. That is why T1–T5, T8, A3, and A4 still look unfinished on the board even though most of the product surface shipped. The **Product** column below is what you can demo; **Board** is the parent issue.

## Board snapshot (8 Oct)

On [project #6](https://github.com/orgs/TheQuintet/projects/6?query=sort%3Aupdated-desc+state%3Aopen), **Status** columns are Backlog → Ready → In progress → In review → Done.

| Metric | Count |
|--------|------:|
| Open issues labeled `frontend` | **28** |
| Of those, labeled `future-version` (out of active scope) | **12** |
| **Active frontend backlog** (open, not `future-version`) | **16** |
| Active FE items in **Backlog** on project #6 | **16** (none in Ready / In progress / In review) |

Sprint 11 frontend closures on the board (Done): **[#508](https://github.com/TheQuintet/macrocrypto-ai/issues/508)** (dashboard forecast), **[#302](https://github.com/TheQuintet/macrocrypto-ai/issues/302)** (calendar timezone), **[#188](https://github.com/TheQuintet/macrocrypto-ai/issues/188)** (prediction-alert history), **[#153](https://github.com/TheQuintet/macrocrypto-ai/issues/153)** (duplicate T7.7), **T5.7–T5.12** ([#117](https://github.com/TheQuintet/macrocrypto-ai/issues/117)–[#122](https://github.com/TheQuintet/macrocrypto-ai/issues/122)). Parent stories **[S3](https://github.com/TheQuintet/macrocrypto-ai/issues/20)** and **[T9](https://github.com/TheQuintet/macrocrypto-ai/issues/10)** are **closed** on the issue tracker.

## How the issues are structured

The tracker is layered like this:

1. **Epics** — product areas ([#328](https://github.com/TheQuintet/macrocrypto-ai/issues/328) Dashboard, [#326](https://github.com/TheQuintet/macrocrypto-ai/issues/326) BTC Forecasting, [#329](https://github.com/TheQuintet/macrocrypto-ai/issues/329) Alert System, [#330](https://github.com/TheQuintet/macrocrypto-ai/issues/330) Correlation & Regimes, [#331](https://github.com/TheQuintet/macrocrypto-ai/issues/331) Export, [#332](https://github.com/TheQuintet/macrocrypto-ai/issues/332) Methodology, plus design/infra epics).
2. **Stories** — persona + capability, with IDs:
   - **T1–T9** — BTC trader (predictions, price, alerts)
   - **A1–A5** — investment analyst (correlations, export, regimes, methodology, event impact)
   - **S1–S3** — any user (macro indicators, public API, economic calendar)
3. **Tasks** — numbered children such as `T5.8`, `A4.3`, `S3.9`, tagged `[FRONTEND]` / `[BACKEND]` / `[TESTING]`.
4. **Labels** — `frontend` plus persona (`btc trader`, `investment analyst`, `any user`), owning service (`ai-service`, `alerts-service`, `data-service`), sprint carryover, and `future-version` for deferred work.

Most remaining tickets are still thin slices of the same screen (export notification, then a separate “make it mobile” ticket), not 16 independent features.

## All stories

Statuses from the parent issues (`#1`–`#21`) plus remaining children. “Shipped” means the user-facing capability is on `main`. Close the parent when children are done or accepted as out of scope.

### Foundation

| Story | Board | Product | Still open |
|-------|--------|---------|------------|
| **[S1](https://github.com/TheQuintet/macrocrypto-ai/issues/18)** View macroeconomic indicators alongside BTC | Closed | Shipped — dashboard + `/macro` snapshot, history, BTC-impact colors | None |
| **[S2](https://github.com/TheQuintet/macrocrypto-ai/issues/19)** Access BTC predictions and macro data via API | Open (Sprint 10 carryover) | Partial — gateway proxies data + alerts; **does not** expose live `GET /api/v1/predict/btc` (predictions router still commented out) | [#280](https://github.com/TheQuintet/macrocrypto-ai/issues/280) S2.4 CORS/HTTPS; wire predict + performance through the gateway |
| **[S3](https://github.com/TheQuintet/macrocrypto-ai/issues/20)** View economic calendar of upcoming events | Closed | Shipped — `/macro/calendar` + details + history + timezone selector ([#302](https://github.com/TheQuintet/macrocrypto-ai/issues/302)) | None (S3 testing [#304](https://github.com/TheQuintet/macrocrypto-ai/issues/304)–[#308](https://github.com/TheQuintet/macrocrypto-ai/issues/308) closed) |

### Trader — price and forecasts

| Story | Board | Product | Still open |
|-------|--------|---------|------------|
| **[T4](https://github.com/TheQuintet/macrocrypto-ai/issues/4)** View real-time BTC price updates | Open | Shipped — live cards, stream status, OHLC, range fit (#510) | Leftover `[TESTING]` only; T4.16 [#44](https://github.com/TheQuintet/macrocrypto-ai/issues/44) **closed** |
| **[T1](https://github.com/TheQuintet/macrocrypto-ai/issues/1)** View 24-hour BTC price predictions | Open | Shipped on `/forecasts` + dashboard 24h card (#508) | [#53](https://github.com/TheQuintet/macrocrypto-ai/issues/53) T1.7 trend backend; [#60](https://github.com/TheQuintet/macrocrypto-ai/issues/60), [#64](https://github.com/TheQuintet/macrocrypto-ai/issues/64)–[#65](https://github.com/TheQuintet/macrocrypto-ai/issues/65) testing ([#63](https://github.com/TheQuintet/macrocrypto-ai/issues/63) UI tests **closed**) |
| **[T2](https://github.com/TheQuintet/macrocrypto-ai/issues/2)** View 7-day BTC price predictions | Open | Shipped — 7d toggle on the same chart | [#92](https://github.com/TheQuintet/macrocrypto-ai/issues/92), [#96](https://github.com/TheQuintet/macrocrypto-ai/issues/96) testing ([#94](https://github.com/TheQuintet/macrocrypto-ai/issues/94)–[#95](https://github.com/TheQuintet/macrocrypto-ai/issues/95) **closed**) |
| **[T3](https://github.com/TheQuintet/macrocrypto-ai/issues/3)** View confidence intervals alongside each prediction | Open | Shipped — band, 70/85/95 selector, Low/Moderate/High meter | [#107](https://github.com/TheQuintet/macrocrypto-ai/issues/107)–[#110](https://github.com/TheQuintet/macrocrypto-ai/issues/110) testing ([#109](https://github.com/TheQuintet/macrocrypto-ai/issues/109) UI tests **closed**) |
| **[T5](https://github.com/TheQuintet/macrocrypto-ai/issues/7)** View historical prediction accuracy | Open | Shipped — `PredictionAccuracyCard` on `/forecasts` (#693); BE metrics on `main` | FE **closed** ([#117](https://github.com/TheQuintet/macrocrypto-ai/issues/117)–[#122](https://github.com/TheQuintet/macrocrypto-ai/issues/122)); testing [#123](https://github.com/TheQuintet/macrocrypto-ai/issues/123)–[#127](https://github.com/TheQuintet/macrocrypto-ai/issues/127) ([#125](https://github.com/TheQuintet/macrocrypto-ai/issues/125)–[#126](https://github.com/TheQuintet/macrocrypto-ai/issues/126) **closed**) |
| **[T6](https://github.com/TheQuintet/macrocrypto-ai/issues/8)** View clear trade recommendations | Open (`future-version` on parent) | **Deferred** — not in capstone scope | BE/FE T6.* including [#136](https://github.com/TheQuintet/macrocrypto-ai/issues/136)–[#140](https://github.com/TheQuintet/macrocrypto-ai/issues/140) labeled `future-version` |

Dashboard forecast **[#508](https://github.com/TheQuintet/macrocrypto-ai/issues/508)** is **closed** ([#695](https://github.com/TheQuintet/macrocrypto-ai/pull/695)).

### Trader — alerts

| Story | Board | Product | Still open |
|-------|--------|---------|------------|
| **[T7](https://github.com/TheQuintet/macrocrypto-ai/issues/9)** Alerts when BTC reaches key price levels | Closed | Shipped — price CRUD, history, notifications | [#156](https://github.com/TheQuintet/macrocrypto-ai/issues/156) preview is `future-version`; [#153](https://github.com/TheQuintet/macrocrypto-ai/issues/153) duplicate **closed** |
| **[T8](https://github.com/TheQuintet/macrocrypto-ai/issues/11)** Alerts for significant prediction changes | Open | Shipped — prediction CRUD + `PredictionHistory` | [#188](https://github.com/TheQuintet/macrocrypto-ai/issues/188) **closed**; skip [#189](https://github.com/TheQuintet/macrocrypto-ai/issues/189) `future-version`; **close parent** |
| **[T9](https://github.com/TheQuintet/macrocrypto-ai/issues/10)** Alerts before major economic events | Closed | Shipped — subscriptions, calendar, notifications, sent-alert history | None |

### Analyst

| Story | Board | Product | Still open |
|-------|--------|---------|------------|
| **[A3](https://github.com/TheQuintet/macrocrypto-ai/issues/15)** Historical BTC patterns across macro regimes | Open | Shipped — dashboard card + `/macro/performance` (performance, timeline, similar periods, CSV) | No A3.* children left; **close parent** |
| **[A1](https://github.com/TheQuintet/macrocrypto-ai/issues/13)** BTC–macro correlation analysis | Open | **Not built** | FE [#204](https://github.com/TheQuintet/macrocrypto-ai/issues/204)–[#208](https://github.com/TheQuintet/macrocrypto-ai/issues/208); testing [#209](https://github.com/TheQuintet/macrocrypto-ai/issues/209)–[#213](https://github.com/TheQuintet/macrocrypto-ai/issues/213) |
| **[A2](https://github.com/TheQuintet/macrocrypto-ai/issues/14)** Export BTC and macro correlation data | Open | Partial — regime CSV only; no generic export modal | FE [#220](https://github.com/TheQuintet/macrocrypto-ai/issues/220)–[#224](https://github.com/TheQuintet/macrocrypto-ai/issues/224); testing [#225](https://github.com/TheQuintet/macrocrypto-ai/issues/225)–[#229](https://github.com/TheQuintet/macrocrypto-ai/issues/229) |
| **[A4](https://github.com/TheQuintet/macrocrypto-ai/issues/17)** Methodology behind predictions and correlations | Open | **Not built** (no `/methodology` page) | Active FE: [#253](https://github.com/TheQuintet/macrocrypto-ai/issues/253) A4.4 metrics only; A4.3 / A4.5–A4.8 ([#252](https://github.com/TheQuintet/macrocrypto-ai/issues/252), [#254](https://github.com/TheQuintet/macrocrypto-ai/issues/254)–[#257](https://github.com/TheQuintet/macrocrypto-ai/issues/257)) are `future-version`; testing [#258](https://github.com/TheQuintet/macrocrypto-ai/issues/258)–[#262](https://github.com/TheQuintet/macrocrypto-ai/issues/262) |
| **[A5](https://github.com/TheQuintet/macrocrypto-ai/issues/21)** Historical event impact analysis on BTC | Open | Backend shipped (A5.1–A5.5); **no UI** | FE [#71](https://github.com/TheQuintet/macrocrypto-ai/issues/71)–[#75](https://github.com/TheQuintet/macrocrypto-ai/issues/75); testing [#76](https://github.com/TheQuintet/macrocrypto-ai/issues/76)–[#79](https://github.com/TheQuintet/macrocrypto-ai/issues/79) |

### Not a user story (still on the board)

| Tickets | What |
|---------|------|
| [#583](https://github.com/TheQuintet/macrocrypto-ai/issues/583)–[#585](https://github.com/TheQuintet/macrocrypto-ai/issues/585) D1–D3 | Dataset collection / builder / feature-engineering pipeline (AI service) |

### How to read this post-capstone

**Demoable on `main`:** S1, S3, T4, T1–T3 (UI; live predict/accuracy **404** until S2 wires the gateway), T5 accuracy UI (simulated when no gateway), T7–T9, A3, dashboard forecast (#508).

**Active frontend backlog (16 tickets):** A1 correlations ([#204](https://github.com/TheQuintet/macrocrypto-ai/issues/204)–[#208](https://github.com/TheQuintet/macrocrypto-ai/issues/208)), A2 generic export ([#220](https://github.com/TheQuintet/macrocrypto-ai/issues/220)–[#224](https://github.com/TheQuintet/macrocrypto-ai/issues/224)), A5 event impact UI ([#71](https://github.com/TheQuintet/macrocrypto-ai/issues/71)–[#75](https://github.com/TheQuintet/macrocrypto-ai/issues/75)), A4.4 model metrics ([#253](https://github.com/TheQuintet/macrocrypto-ai/issues/253)).

**Deferred (`future-version`):** T6 recommendations, alert previews ([#156](https://github.com/TheQuintet/macrocrypto-ai/issues/156), [#189](https://github.com/TheQuintet/macrocrypto-ai/issues/189)), most A4 methodology page slices ([#252](https://github.com/TheQuintet/macrocrypto-ai/issues/252), [#254](https://github.com/TheQuintet/macrocrypto-ai/issues/254)–[#257](https://github.com/TheQuintet/macrocrypto-ai/issues/257)).

**Board hygiene (no new product):** close **T8**, **A3**, and forecast parents **T1–T5** when testing is accepted or explicitly out of scope; skip `future-version` children.

## Things to remember

- **Do not implement mobile-responsiveness or unit/UI tests as standalone work.** They are acceptance criteria on the real components below (`A1.12`, `A2.11`, `A5.10`, and closed T5.12).
- **24h and 7d prediction UI is one chart with a toggle.** T1 and T2 share that pattern; T5 accuracy uses the same horizon control on `/forecasts`.
- **[#189](https://github.com/TheQuintet/macrocrypto-ai/issues/189) and [#156](https://github.com/TheQuintet/macrocrypto-ai/issues/156)** (alert preview) are `future-version`. [#668](https://github.com/TheQuintet/macrocrypto-ai/pull/668) already dropped the unused prediction preview.
- **[#302](https://github.com/TheQuintet/macrocrypto-ai/issues/302)** (S3.9 timezone selector) is **closed** on the board and on `main`.
- Price, indicators, regimes, calendar, alerts CRUD, dashboard forecast, Forecasts chart + accuracy card are **done**. Do not rebuild those surfaces.
- Forecasts call `GET /api/v1/predict/btc` and `GET /api/v1/performance/btc` through `VITE_API_GATEWAY_BASE_URL`. The gateway **does not** yet route those paths to the AI service (predictions module commented out), so a full-stack run **404s** on live forecast/accuracy and shows error or simulated states. Candles still load (`/api/v1/btc/price/history`). Routing predict + performance is a **backend** task; frontend paths stay the same when it lands.
- Empty `VITE_API_GATEWAY_BASE_URL` → simulated (badged). Configured URL that fails → error, not a silent fake live reading.
- Sprints are **1 week**. PR review has been a velocity drag; estimates below are engineer-time, not calendar with review lag.

## What shipped since the 23 Sep snapshot

Closed on the board and on `main`:

| Area | Issues | PR |
|------|--------|----|
| Dashboard 24h forecast card | [#508](https://github.com/TheQuintet/macrocrypto-ai/issues/508) | [#695](https://github.com/TheQuintet/macrocrypto-ai/pull/695) |
| Forecast accuracy card (T5 FE) | [#117](https://github.com/TheQuintet/macrocrypto-ai/issues/117)–[#122](https://github.com/TheQuintet/macrocrypto-ai/issues/122) | [#693](https://github.com/TheQuintet/macrocrypto-ai/pull/693) |
| Calendar timezone selector | [#302](https://github.com/TheQuintet/macrocrypto-ai/issues/302) | (Sprint 11) |
| Alert / board hygiene | [#153](https://github.com/TheQuintet/macrocrypto-ai/issues/153), [#188](https://github.com/TheQuintet/macrocrypto-ai/issues/188) | — |
| Playwright system E2E vs live gateway | — | [#718](https://github.com/TheQuintet/macrocrypto-ai/pull/718) |

Earlier August–September deliveries (price range fit, regime analysis, Forecasts chart, calendar, alerts) are unchanged — see git history around [#666](https://github.com/TheQuintet/macrocrypto-ai/pull/666), [#614](https://github.com/TheQuintet/macrocrypto-ai/pull/614), [#569](https://github.com/TheQuintet/macrocrypto-ai/pull/569).

## Estimate (one frontend engineer)

| Scope | What you finish | Effort |
|--------|-----------------|--------|
| Board hygiene only | Close T8, A3, T1–T5 parents after testing sign-off | ~0.5–1 day |
| Next product slice | One of: event impact (A5), correlations (A1), or generic export (A2) | ~1–2 weeks each |
| Close all **16** active FE tickets | A1 + A2 + A5 + A4.4 | ~2–4 weeks |

Ticket count still overstates work if you build one surface per story and fold mobile/export slices into the same PR. Ignore the **12** `future-version` frontend issues unless the PO reopens them.

## What the app already has

Vite + React + TypeScript under `frontend/`. Routes in `App.tsx`:

| Route | Page | Status |
|--------|------|--------|
| `/` | `DashboardPage` | Live price, change, `RegimeCard`, **24h `DashboardForecastCard`**, OHLC chart fit to range, indicator snapshot. |
| `/macro` | `MacroPage` | Indicator snapshot + BTC chart linked to history (chart + table). |
| `/macro/performance` | `RegimePerformancePage` | Tabs: performance, timeline, similar periods + CSV export. |
| `/macro/calendar` | `CalendarPage` | Upcoming events, list/calendar, details, timezone selector. |
| `/macro/notifications` | `EconomicNotificationsPage` | Sent macro-alert history (search, filter, export). |
| `/forecasts` | `ForecastsPage` | Candles, fit, projection, confidence band, Low/Moderate/High meter, 24h/7d, **`PredictionAccuracyCard`**. Live forecast/accuracy 404 until the gateway proxies the AI service. |
| `/alerts` | `AlertsPage` | In the sidebar. Price, prediction, and macro CRUD + history + notification bell. |
| *(none)* | Methodology | No page yet (A4.3+ deferred; only A4.4 metrics ticket open). |

State: Zustand for preferences/theme/ephemeral UI; TanStack Query for server data. Types in `src/types/`. Shared HTTP via `apiUrl` / `VITE_API_GATEWAY_BASE_URL`.

---

## Remaining work by page

Check off when it is done. Tests and mobile layout are AC on each item. `[x]` = already in the app. Issue numbers are **open** board items unless noted.

Sidebar (`AppSidebar`): add **Methodology** when A4.3 lands (currently `future-version`).

### Dashboard — `/` (`DashboardPage`)

**Already there**

- [x] `BtcPriceCard`, `PriceChangeCard`, day stats, stream status
- [x] `PriceChart` (OHLC), zoom / interval, pan viewport, candle tooltip
- [x] Chart shows the selected time range (`#510`)
- [x] `RegimeCard` — current regime, confidence Low/Moderate/High (`#240`)
- [x] `MacroIndicators` snapshot grid (BTC-impact color-coding)
- [x] `DashboardForecastCard` — next-24h outlook ([#508](https://github.com/TheQuintet/macrocrypto-ai/issues/508) / [#695](https://github.com/TheQuintet/macrocrypto-ai/pull/695))

**Still missing**

- None for the current Sprint 11 scope.

### Macro — `/macro` (`MacroPage`)

**Already there**

- [x] Indicator snapshot + linked BTC / history (S1.7–S1.9)
- [x] Daily / Weekly, series filter, simulated vs live

**Still missing on this page** — none for shipped stories. Analyst work (event impact, correlations, generic export) can land here or on a sibling route; see sections below.

### Regime analysis — `/macro/performance` (`RegimePerformancePage`)

**Already there** (A3.9–A3.14)

- [x] Performance table/chart
- [x] Timeline
- [x] Similar periods (Today row + historical table, Match = closeness of prints)
- [x] CSV export of visible performance rows
- [x] Mobile layout

**Still missing** — none.

### Calendar — `/macro/calendar` and `/macro/notifications`

**Already there** (S3.6–S3.8, S3.10, T9.8, T9.10, S3.9)

- [x] `EconomicCalendar`, list/calendar, `EventDetailsDialog`
- [x] Past events / sent-alert history
- [x] Timezone selector ([#302](https://github.com/TheQuintet/macrocrypto-ai/issues/302))

**Still missing**

- None on the frontend.

### Forecasts — `/forecasts` (`ForecastsPage`)

**Already there** (T1.8–T1.13, T2.7–T2.12, T3.5–T3.10, T5.7–T5.12)

- [x] `PredictionChart` — one chart for 24h and 7d, candles, fit, path, band, legend, tooltips
- [x] `PredictionSummary` — direction, change, key levels, range width
- [x] `ConfidenceLevelSelector` and Low / Moderate / High meter
- [x] Horizon toggle
- [x] `PredictionAccuracyCard` — trend, predicted vs actual, market breakdown, details modal ([#117](https://github.com/TheQuintet/macrocrypto-ai/issues/117)–[#122](https://github.com/TheQuintet/macrocrypto-ai/issues/122) / [#693](https://github.com/TheQuintet/macrocrypto-ai/pull/693))

**Still missing**

- [ ] Trade recommendations (T6) — **`future-version`**; do not start unless PO reopens.

Backend: proxy `GET /api/v1/predict/btc` and `GET /api/v1/performance/btc` through the gateway so live forecast + accuracy stop 404ing.

### Alerts — `/alerts` (`AlertsPage`)

**Already there**

- [x] In the sidebar
- [x] Price / prediction / macro CRUD, filters, notification bell
- [x] Price and macro history; `PredictionHistory` on the prediction tab
- [x] Economic notifications page for sent macro alerts

**Still missing**

- [ ] Skip alert preview ([#156](https://github.com/TheQuintet/macrocrypto-ai/issues/156), [#189](https://github.com/TheQuintet/macrocrypto-ai/issues/189) — `future-version`)
- [ ] Close parent **[T8](https://github.com/TheQuintet/macrocrypto-ai/issues/11)** on the board (product shipped; [#188](https://github.com/TheQuintet/macrocrypto-ai/issues/188) closed)

### Methodology — no page yet

Most A4 frontend tasks are **`future-version`**. Only **A4.4** is in the active backlog — likely a component to embed once a methodology route exists.

- [ ] `MethodologyPage` and content ([#252](https://github.com/TheQuintet/macrocrypto-ai/issues/252) A4.3 — `future-version`)
- [ ] Model performance metrics ([#253](https://github.com/TheQuintet/macrocrypto-ai/issues/253) A4.4 — **active**)
- [ ] Search ([#254](https://github.com/TheQuintet/macrocrypto-ai/issues/254) A4.5 — `future-version`)
- [ ] FAQ ([#255](https://github.com/TheQuintet/macrocrypto-ai/issues/255) A4.6 — `future-version`)
- [ ] Citations ([#256](https://github.com/TheQuintet/macrocrypto-ai/issues/256) A4.7 — `future-version`; mobile [#257](https://github.com/TheQuintet/macrocrypto-ai/issues/257) — `future-version`)

### Not on a page yet — event impact, correlations, export

These are the **16** active frontend tickets on project #6 (all **Backlog**). Build each as one surface; fold mobile/export slices into that PR.

Event impact (A5) — can live on calendar or a Macro tab

- [ ] `EventImpactPanel` — display, filters, chart, export ([#71](https://github.com/TheQuintet/macrocrypto-ai/issues/71)–[#74](https://github.com/TheQuintet/macrocrypto-ai/issues/74); mobile is [#75](https://github.com/TheQuintet/macrocrypto-ai/issues/75))

Correlations (A1)

- [ ] `CorrelationHeatmap` ([#204](https://github.com/TheQuintet/macrocrypto-ai/issues/204) A1.8)
- [ ] `RollingCorrelationChart` ([#205](https://github.com/TheQuintet/macrocrypto-ai/issues/205) A1.9)
- [ ] `CorrelationInsights` ([#206](https://github.com/TheQuintet/macrocrypto-ai/issues/206) A1.10; export is [#207](https://github.com/TheQuintet/macrocrypto-ai/issues/207); mobile is [#208](https://github.com/TheQuintet/macrocrypto-ai/issues/208))

Export (A2) — modal opened from a page, not its own route. Regime CSV is **already** shipped; this is the generic export modal.

- [ ] `ExportModal` — component, progress, download notifications, history ([#220](https://github.com/TheQuintet/macrocrypto-ai/issues/220)–[#223](https://github.com/TheQuintet/macrocrypto-ai/issues/223); mobile is [#224](https://github.com/TheQuintet/macrocrypto-ai/issues/224))

## Suggested build order (by page)

1. **Board hygiene** — close **T8**, **A3**, and **T1–T5** parents when testing is signed off or waived.
2. **Backend unblock** — gateway routes for `/api/v1/predict/btc` and `/api/v1/performance/btc` (S2).
3. **Analyst surfaces** — pick one vertical slice: event impact (A5), correlations (A1), or generic export (A2).
4. **Methodology** — only if PO pulls A4.3+ out of `future-version`; until then, **A4.4** alone has no natural home.

**If time is short:** hygiene + gateway routing give the strongest demo lift (live forecast + accuracy on pages already built). A1 / A2 / A5 are net-new UI and can follow after capstone.
