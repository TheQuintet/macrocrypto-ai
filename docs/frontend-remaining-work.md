# Remaining work

Snapshot of **every user story** (T1–T9, A1–A5, S1–S3) against the [GitHub board](https://github.com/TheQuintet/macrocrypto-ai/issues?q=is%3Aissue) and `main` on **23 September 2026**, after [#666](https://github.com/TheQuintet/macrocrypto-ai/pull/666). Use this for planning, not as a substitute for the issue tracker. Capstone deadline: **5 October** ([deliverables](./quantic/deliverables.md)).

Related: [project scope](./project-scope.md), [user stories dependency map](./user-stories-dependency-map.md), frontend conventions in `AGENTS.md`.

Parent story issues stay **OPEN** while any child is open — usually leftover `[TESTING]` tickets. That is why T1–T4, T8, T9, A3, and S3 still look unfinished on the board even though the product surface shipped. The **Product** column below is what you can demo; **Board** is the parent issue.

## How the issues are structured

The tracker is layered like this:

1. **Epics** — product areas ([#328](https://github.com/TheQuintet/macrocrypto-ai/issues/328) Dashboard, [#326](https://github.com/TheQuintet/macrocrypto-ai/issues/326) BTC Forecasting, [#329](https://github.com/TheQuintet/macrocrypto-ai/issues/329) Alert System, [#330](https://github.com/TheQuintet/macrocrypto-ai/issues/330) Correlation & Regimes, [#331](https://github.com/TheQuintet/macrocrypto-ai/issues/331) Export, [#332](https://github.com/TheQuintet/macrocrypto-ai/issues/332) Methodology, plus design/infra epics).
2. **Stories** — persona + capability, with IDs:
   - **T1–T9** — BTC trader (predictions, price, alerts)
   - **A1–A5** — investment analyst (correlations, export, regimes, methodology, event impact)
   - **S1–S3** — any user (macro indicators, public API, economic calendar)
3. **Tasks** — numbered children such as `T5.8`, `A4.3`, `S3.9`, tagged `[FRONTEND]` / `[BACKEND]` / `[TESTING]`.
4. **Labels** — `frontend` plus persona (`btc trader`, `investment analyst`, `any user`), owning service (`ai-service`, `alerts-service`, `data-service`), sprint (`sprint-8` / Sprint 9 carryover), and `future-version` for deferred work.

**38 open** issues are labeled `frontend` (down from 83 in the August snapshot). Most remaining tickets are still thin slices of the same screen (tooltip, then a separate “make it mobile” ticket), not 38 independent features.

Sprint 9 frontend leftover that is still open: **[#508](https://github.com/TheQuintet/macrocrypto-ai/issues/508)** (dashboard forecast), **[#302](https://github.com/TheQuintet/macrocrypto-ai/issues/302)** (timezone selector), **[#188](https://github.com/TheQuintet/macrocrypto-ai/issues/188)** (prediction-alert history). A3.9–A3.14 and the `/forecasts` T1/T2/T3 slices are **closed**.

## All stories

Statuses from the parent issues (`#1`–`#21`) plus remaining children. “Shipped” means the user-facing capability is on `main`. Close the parent when children are done or accepted as out of scope.

### Foundation

| Story | Board | Product | Still open |
|-------|--------|---------|------------|
| **[S1](https://github.com/TheQuintet/macrocrypto-ai/issues/18)** View macroeconomic indicators alongside BTC | Closed | Shipped — dashboard + `/macro` snapshot, history, BTC-impact colors | None |
| **[S2](https://github.com/TheQuintet/macrocrypto-ai/issues/19)** Access BTC predictions and macro data via API | Open (Sprint 9 carryover) | Partial — gateway proxies data + alerts; **does not** proxy AI `/predict/btc` | [#280](https://github.com/TheQuintet/macrocrypto-ai/issues/280) S2.4 CORS/HTTPS; wire predict through the gateway |
| **[S3](https://github.com/TheQuintet/macrocrypto-ai/issues/20)** View economic calendar of upcoming events | Open | Shipped — `/macro/calendar` + details + history | [#302](https://github.com/TheQuintet/macrocrypto-ai/issues/302) S3.9 full timezone AC (Local/UTC already there); [#304](https://github.com/TheQuintet/macrocrypto-ai/issues/304)–[#308](https://github.com/TheQuintet/macrocrypto-ai/issues/308) testing |

### Trader — price and forecasts

| Story | Board | Product | Still open |
|-------|--------|---------|------------|
| **[T4](https://github.com/TheQuintet/macrocrypto-ai/issues/4)** View real-time BTC price updates | Open | Shipped — live cards, stream status, OHLC, range fit (#510) | [#44](https://github.com/TheQuintet/macrocrypto-ai/issues/44) T4.16 API integration tests |
| **[T1](https://github.com/TheQuintet/macrocrypto-ai/issues/1)** View 24-hour BTC price predictions | Open | Shipped on `/forecasts` (same chart as T2/T3) | [#53](https://github.com/TheQuintet/macrocrypto-ai/issues/53) T1.7 trend backend (UI already shows `trend` from the batch); [#60](https://github.com/TheQuintet/macrocrypto-ai/issues/60), [#63](https://github.com/TheQuintet/macrocrypto-ai/issues/63)–[#65](https://github.com/TheQuintet/macrocrypto-ai/issues/65) testing |
| **[T2](https://github.com/TheQuintet/macrocrypto-ai/issues/2)** View 7-day BTC price predictions | Open | Shipped — 7d toggle on the same chart | [#92](https://github.com/TheQuintet/macrocrypto-ai/issues/92), [#94](https://github.com/TheQuintet/macrocrypto-ai/issues/94)–[#96](https://github.com/TheQuintet/macrocrypto-ai/issues/96) testing |
| **[T3](https://github.com/TheQuintet/macrocrypto-ai/issues/3)** View confidence intervals alongside each prediction | Open | Shipped — band, 70/85/95 selector, Low/Moderate/High meter | [#107](https://github.com/TheQuintet/macrocrypto-ai/issues/107)–[#110](https://github.com/TheQuintet/macrocrypto-ai/issues/110) testing |
| **[T5](https://github.com/TheQuintet/macrocrypto-ai/issues/7)** View historical prediction accuracy | Open | **Not built** | FE [#117](https://github.com/TheQuintet/macrocrypto-ai/issues/117)–[#122](https://github.com/TheQuintet/macrocrypto-ai/issues/122); testing [#123](https://github.com/TheQuintet/macrocrypto-ai/issues/123)–[#127](https://github.com/TheQuintet/macrocrypto-ai/issues/127) |
| **[T6](https://github.com/TheQuintet/macrocrypto-ai/issues/8)** View clear trade recommendations | Open | **Not built** — blocked on the engine | BE [#128](https://github.com/TheQuintet/macrocrypto-ai/issues/128)–[#134](https://github.com/TheQuintet/macrocrypto-ai/issues/134) T6.1–T6.7 (Sprint 9); FE [#136](https://github.com/TheQuintet/macrocrypto-ai/issues/136)–[#140](https://github.com/TheQuintet/macrocrypto-ai/issues/140); testing [#141](https://github.com/TheQuintet/macrocrypto-ai/issues/141)–[#145](https://github.com/TheQuintet/macrocrypto-ai/issues/145) |

Cross-cutting, not a story: **[#508](https://github.com/TheQuintet/macrocrypto-ai/issues/508)** surface the forecast on the dashboard (T1/T2 already have a dedicated page).

### Trader — alerts

| Story | Board | Product | Still open |
|-------|--------|---------|------------|
| **[T7](https://github.com/TheQuintet/macrocrypto-ai/issues/9)** Alerts when BTC reaches key price levels | Closed | Shipped — price CRUD, history, notifications | Leftover duplicate [#153](https://github.com/TheQuintet/macrocrypto-ai/issues/153) (close); [#156](https://github.com/TheQuintet/macrocrypto-ai/issues/156) preview is `future-version` |
| **[T8](https://github.com/TheQuintet/macrocrypto-ai/issues/11)** Alerts for significant prediction changes | Open | Shipped — prediction CRUD + `PredictionHistory` | Confirm/close [#188](https://github.com/TheQuintet/macrocrypto-ai/issues/188) T8.9; skip [#189](https://github.com/TheQuintet/macrocrypto-ai/issues/189) `future-version` |
| **[T9](https://github.com/TheQuintet/macrocrypto-ai/issues/10)** Alerts before major economic events | Open | Shipped — subscriptions, calendar, notifications, sent-alert history | No T9.* children left; close the parent |

### Analyst

| Story | Board | Product | Still open |
|-------|--------|---------|------------|
| **[A3](https://github.com/TheQuintet/macrocrypto-ai/issues/15)** Historical BTC patterns across macro regimes | Open | Shipped — dashboard card + `/macro/performance` (performance, timeline, similar periods, CSV) | No A3.* children left; close the parent |
| **[A1](https://github.com/TheQuintet/macrocrypto-ai/issues/13)** BTC–macro correlation analysis | Open | **Not built** | FE [#204](https://github.com/TheQuintet/macrocrypto-ai/issues/204)–[#208](https://github.com/TheQuintet/macrocrypto-ai/issues/208); testing [#209](https://github.com/TheQuintet/macrocrypto-ai/issues/209)–[#213](https://github.com/TheQuintet/macrocrypto-ai/issues/213) |
| **[A2](https://github.com/TheQuintet/macrocrypto-ai/issues/14)** Export BTC and macro correlation data | Open | Partial — regime CSV only; no generic export modal | FE [#220](https://github.com/TheQuintet/macrocrypto-ai/issues/220)–[#224](https://github.com/TheQuintet/macrocrypto-ai/issues/224); testing [#225](https://github.com/TheQuintet/macrocrypto-ai/issues/225)–[#229](https://github.com/TheQuintet/macrocrypto-ai/issues/229) |
| **[A4](https://github.com/TheQuintet/macrocrypto-ai/issues/17)** Methodology behind predictions and correlations | Open | **Not built** (no `/methodology` page) | FE [#252](https://github.com/TheQuintet/macrocrypto-ai/issues/252)–[#257](https://github.com/TheQuintet/macrocrypto-ai/issues/257); testing [#258](https://github.com/TheQuintet/macrocrypto-ai/issues/258)–[#262](https://github.com/TheQuintet/macrocrypto-ai/issues/262) |
| **[A5](https://github.com/TheQuintet/macrocrypto-ai/issues/21)** Historical event impact analysis on BTC | Open | Backend shipped (A5.1–A5.5); **no UI** | FE [#71](https://github.com/TheQuintet/macrocrypto-ai/issues/71)–[#75](https://github.com/TheQuintet/macrocrypto-ai/issues/75); testing [#76](https://github.com/TheQuintet/macrocrypto-ai/issues/76)–[#79](https://github.com/TheQuintet/macrocrypto-ai/issues/79) |

### Not a user story (still on the board)

| Tickets | What |
|---------|------|
| [#583](https://github.com/TheQuintet/macrocrypto-ai/issues/583)–[#585](https://github.com/TheQuintet/macrocrypto-ai/issues/585) D1–D3 | Dataset collection / builder / feature-engineering pipeline (AI service) |

### How to read this for the capstone

**Demoable now:** S1, T4, T1–T3 (UI; live predict 404s until S2 proxies AI), T7–T9, A3, S3.

**Still to build:** T5 (accuracy), T6 (recommendations — needs BE first), A1 (correlations), A4 (methodology), A5 UI (event impact), A2 generic export.

**Board hygiene (no new product):** close T7 `#153`, T8 `#188` if AC holds, T9 and A3 parents; skip `future-version` previews; treat leftover `[TESTING]` as AC on the story, not a second sprint.

## Things to remember

- **Do not implement mobile-responsiveness or unit/UI tests as standalone work.** They are acceptance criteria on the real components below (`A4.8`, `A2.11`, `A1.12`, `A5.10`, `T6.13`, `T5.12`).
- **24h and 7d prediction UI is one chart with a toggle.** T1 and T2 are done that way; do the same for accuracy (T5) and recommendations (T6).
- **[#153](https://github.com/TheQuintet/macrocrypto-ai/issues/153) is a leftover duplicate** of closed [#152](https://github.com/TheQuintet/macrocrypto-ai/issues/152) (price-alert CRUD). Close it; do not rebuild `AlertManagement`.
- **[#189](https://github.com/TheQuintet/macrocrypto-ai/issues/189) and [#156](https://github.com/TheQuintet/macrocrypto-ai/issues/156)** (alert preview) are labeled `future-version`. Skip them for the capstone. [#668](https://github.com/TheQuintet/macrocrypto-ai/pull/668) already dropped the unused prediction preview.
- **[#188](https://github.com/TheQuintet/macrocrypto-ai/issues/188)** still open, but `PredictionHistory` is already on `/alerts` (search, date, horizon, threshold, pagination, export). Confirm AC and close rather than rebuilding.
- **[#302](https://github.com/TheQuintet/macrocrypto-ai/issues/302)** — calendar already has a Local / UTC toggle (`CalendarTimezoneSelect`). Remaining AC is a persisted IANA timezone in user settings applied everywhere. Decide whether that is in scope or close as done-enough.
- Price, indicators, regimes, calendar, alerts CRUD, and the Forecasts chart are **done**. Do not rebuild those pages.
- Forecasts call `GET /api/v1/predict/btc` on the gateway. The gateway does **not** proxy the AI service yet, so a full-stack run **404s** on the forecast half and shows the error state. Candles still load (`/api/v1/btc/price/history`). Routing `/predict/btc` is a **backend** task; the frontend path does not change when it lands.
- Data HTTP goes through `VITE_API_GATEWAY_BASE_URL` only. Empty URL → simulated (badged). Configured URL that fails → error, not a silent fake live reading.
- Sprints are **1 week**. PR review has been a velocity drag; estimates below are engineer-time, not calendar with review lag.

## What shipped since the August snapshot

Closed on the board and on `main`:

| Area | Issues | PR |
|------|--------|----|
| Price chart fits the selected range | [#510](https://github.com/TheQuintet/macrocrypto-ai/issues/510) | [#632](https://github.com/TheQuintet/macrocrypto-ai/pull/632) |
| Current regime card | [#240](https://github.com/TheQuintet/macrocrypto-ai/issues/240) A3.11 | [#624](https://github.com/TheQuintet/macrocrypto-ai/pull/624) |
| Regime performance + timeline | [#238](https://github.com/TheQuintet/macrocrypto-ai/issues/238) A3.9, [#239](https://github.com/TheQuintet/macrocrypto-ai/issues/239) A3.10 | [#628](https://github.com/TheQuintet/macrocrypto-ai/pull/628) |
| Similar periods + regime CSV | [#241](https://github.com/TheQuintet/macrocrypto-ai/issues/241) A3.12, [#242](https://github.com/TheQuintet/macrocrypto-ai/issues/242) A3.13, [#243](https://github.com/TheQuintet/macrocrypto-ai/issues/243) A3.14 | [#634](https://github.com/TheQuintet/macrocrypto-ai/pull/634) |
| Forecasts chart (24h/7d, band, summary, Low/Moderate/High meter) | [#54](https://github.com/TheQuintet/macrocrypto-ai/issues/54)–[#59](https://github.com/TheQuintet/macrocrypto-ai/issues/59), [#86](https://github.com/TheQuintet/macrocrypto-ai/issues/86)–[#91](https://github.com/TheQuintet/macrocrypto-ai/issues/91), [#101](https://github.com/TheQuintet/macrocrypto-ai/issues/101)–[#106](https://github.com/TheQuintet/macrocrypto-ai/issues/106) | [#666](https://github.com/TheQuintet/macrocrypto-ai/pull/666) |
| Economic calendar + details + history | S3.6–S3.8, S3.10, T9.8, T9.10 | [#614](https://github.com/TheQuintet/macrocrypto-ai/pull/614) and follow-ups |
| Alerts in the sidebar, price / prediction / macro CRUD + notifications | T7.*, T8.7–T8.8, T8.11, T9.7, T9.9, T9.11 | [#569](https://github.com/TheQuintet/macrocrypto-ai/pull/569) and follow-ups |
| Indicator history (S1.7–S1.9) | [#269](https://github.com/TheQuintet/macrocrypto-ai/issues/269)–[#271](https://github.com/TheQuintet/macrocrypto-ai/issues/271) | merged |

## Estimate (one frontend engineer)

| Scope | What you finish | Effort |
|--------|-----------------|--------|
| Sprint 9 leftovers | Close `#153`, confirm/close `#188`, decide `#302`, then `#508` | ~2–4 days |
| Capstone-useful next | Above + accuracy (T5) **or** recommendations (T6) **or** methodology (A4) | ~1–2 weeks |
| Close every remaining FE ticket | T5 + T6 + A1 + A2 + A4 + A5 | ~3–5 weeks |

Ticket count still overstates work. Story-level implementation is the 3–5 week number. Skip `future-version` previews and standalone mobile tickets.

## What the app already has

Vite + React + TypeScript under `frontend/`. Routes in `App.tsx`:

| Route | Page | Status |
|--------|------|--------|
| `/` | `DashboardPage` | Live price, change, `RegimeCard`, OHLC chart fit to range, indicator snapshot. No forecast snippet (`#508`). |
| `/macro` | `MacroPage` | Indicator snapshot + BTC chart linked to history (chart + table). |
| `/macro/performance` | `RegimePerformancePage` | Tabs: performance, timeline, similar periods + CSV export. |
| `/macro/calendar` | `CalendarPage` | Upcoming events, list/calendar, details, Local/UTC times. |
| `/macro/notifications` | `EconomicNotificationsPage` | Sent macro-alert history (search, filter, export). |
| `/forecasts` | `ForecastsPage` | Candles, fit, projection, confidence band, Low/Moderate/High meter, 24h/7d. Live forecast 404s until the gateway proxies the AI service. |
| `/alerts` | `AlertsPage` | In the sidebar. Price, prediction, and macro CRUD + history + notification bell. |
| *(none)* | Methodology | No page yet (`#252`). |

State: Zustand for preferences/theme/ephemeral UI; TanStack Query for server data. Types in `src/types/`. Shared HTTP via `apiUrl` / `VITE_API_GATEWAY_BASE_URL`.

---

## Remaining work by page

Check off when it is done. Tests and mobile layout are AC on each item. `[x]` = already in the app. Issue numbers are the **open** board items.

Sidebar (`AppSidebar`): add **Methodology** if it becomes its own route.

### Dashboard — `/` (`DashboardPage`)

**Already there**

- [x] `BtcPriceCard`, `PriceChangeCard`, day stats, stream status
- [x] `PriceChart` (OHLC), zoom / interval, pan viewport, candle tooltip
- [x] Chart shows the selected time range (`#510`)
- [x] `RegimeCard` — current regime, confidence Low/Moderate/High (`#240`)
- [x] `MacroIndicators` snapshot grid (BTC-impact color-coding)

**Still missing**

- [ ] AI forecast on this page ([#508](https://github.com/TheQuintet/macrocrypto-ai/issues/508)) — overlay on the price chart **or** a small card that reuses Forecasts’ `PredictionChart`

### Macro — `/macro` (`MacroPage`)

**Already there**

- [x] Indicator snapshot + linked BTC / history (S1.7–S1.9)
- [x] Daily / Weekly, series filter, simulated vs live

**Still missing on this page** — none for Sprint 9. Later analyst work (event impact, correlations, generic export) can land here or on a sibling route; see sections below.

### Regime analysis — `/macro/performance` (`RegimePerformancePage`)

**Already there** (A3.9–A3.14)

- [x] Performance table/chart
- [x] Timeline
- [x] Similar periods (Today row + historical table, Match = closeness of prints)
- [x] CSV export of visible performance rows
- [x] Mobile layout

**Still missing** — none.

### Calendar — `/macro/calendar` and `/macro/notifications`

**Already there** (S3.6–S3.8, S3.10, T9.8, T9.10)

- [x] `EconomicCalendar`, list/calendar, `EventDetailsDialog`
- [x] Past events / sent-alert history
- [x] Local vs UTC times on the calendar

**Still missing**

- [ ] Full timezone selector AC ([#302](https://github.com/TheQuintet/macrocrypto-ai/issues/302) S3.9) — persisted IANA zone in user settings, applied to every calendar view. Toolbar Local/UTC is already shipped.

### Forecasts — `/forecasts` (`ForecastsPage`)

**Already there** (T1.8–T1.13, T2.7–T2.12, T3.5–T3.10)

- [x] `PredictionChart` — one chart for 24h and 7d, candles, fit, path, band, legend, tooltips
- [x] `PredictionSummary` — direction, change, key levels, range width
- [x] `ConfidenceLevelSelector` and Low / Moderate / High meter
- [x] Horizon toggle

**Still missing** — accuracy and recommendations, not a second chart:

Accuracy (T5)

- [ ] `AccuracyPanel` — trend, predicted vs actual, market-condition breakdown ([#117](https://github.com/TheQuintet/macrocrypto-ai/issues/117)–[#120](https://github.com/TheQuintet/macrocrypto-ai/issues/120))
- [ ] `AccuracyDetailsModal` ([#121](https://github.com/TheQuintet/macrocrypto-ai/issues/121); mobile is [#122](https://github.com/TheQuintet/macrocrypto-ai/issues/122))

Recommendations (T6)

- [ ] `RecommendationCard` — horizon toggle, accuracy snippet, dismiss ([#136](https://github.com/TheQuintet/macrocrypto-ai/issues/136)–[#139](https://github.com/TheQuintet/macrocrypto-ai/issues/139); mobile is [#140](https://github.com/TheQuintet/macrocrypto-ai/issues/140))

Backend: proxy `GET /api/v1/predict/btc` (and later accuracy) through the gateway so the live chart stops 404ing.

### Alerts — `/alerts` (`AlertsPage`)

**Already there**

- [x] In the sidebar
- [x] Price / prediction / macro CRUD, filters, notification bell
- [x] Price and macro history; `PredictionHistory` on the prediction tab
- [x] Economic notifications page for sent macro alerts

**Still missing**

- [ ] Close leftover T7.7 duplicate ([#153](https://github.com/TheQuintet/macrocrypto-ai/issues/153))
- [ ] Confirm and close prediction-alert history ([#188](https://github.com/TheQuintet/macrocrypto-ai/issues/188) T8.9) if AC is met
- [ ] Skip alert preview ([#156](https://github.com/TheQuintet/macrocrypto-ai/issues/156), [#189](https://github.com/TheQuintet/macrocrypto-ai/issues/189) — `future-version`)

### Methodology — no page yet

New route (e.g. `/methodology`) plus a sidebar item. One page covers A4.3–A4.8; do not ship search / FAQ / citations as separate apps.

- [ ] `MethodologyPage` — content ([#252](https://github.com/TheQuintet/macrocrypto-ai/issues/252) A4.3)
- [ ] Model performance metrics ([#253](https://github.com/TheQuintet/macrocrypto-ai/issues/253) A4.4)
- [ ] Search ([#254](https://github.com/TheQuintet/macrocrypto-ai/issues/254) A4.5)
- [ ] FAQ ([#255](https://github.com/TheQuintet/macrocrypto-ai/issues/255) A4.6, Sprint 6 carryover)
- [ ] Citations ([#256](https://github.com/TheQuintet/macrocrypto-ai/issues/256) A4.7; mobile is [#257](https://github.com/TheQuintet/macrocrypto-ai/issues/257))

### Not on a page yet — event impact, correlations, export

These are still open on the board. They are **not** Sprint 9 leftovers. Build each as one surface; fold the mobile/export-notification slices into that PR.

Event impact (A5) — can live on calendar or a Macro tab

- [ ] `EventImpactPanel` — display, filters, chart, export ([#71](https://github.com/TheQuintet/macrocrypto-ai/issues/71)–[#74](https://github.com/TheQuintet/macrocrypto-ai/issues/74); mobile is [#75](https://github.com/TheQuintet/macrocrypto-ai/issues/75))

Correlations (A1)

- [ ] `CorrelationHeatmap` ([#204](https://github.com/TheQuintet/macrocrypto-ai/issues/204) A1.8)
- [ ] `RollingCorrelationChart` ([#205](https://github.com/TheQuintet/macrocrypto-ai/issues/205) A1.9)
- [ ] `CorrelationInsights` ([#206](https://github.com/TheQuintet/macrocrypto-ai/issues/206) A1.10; export is [#207](https://github.com/TheQuintet/macrocrypto-ai/issues/207); mobile is [#208](https://github.com/TheQuintet/macrocrypto-ai/issues/208))

Export (A2) — modal opened from a page, not its own route. Regime CSV is **already** shipped; this is the generic export modal.

- [ ] `ExportModal` — component, progress, download notifications, history ([#220](https://github.com/TheQuintet/macrocrypto-ai/issues/220)–[#223](https://github.com/TheQuintet/macrocrypto-ai/issues/223); mobile is [#224](https://github.com/TheQuintet/macrocrypto-ai/issues/224))

## Suggested build order (by page)

1. **Board hygiene** — close `#153`; confirm `#188`; decide `#302`.
2. **Dashboard** — forecast snippet (`#508`), reusing the Forecasts chart.
3. **Forecasts extras** — accuracy (T5) or recommendations (T6), one surface each.
4. **Methodology** — new page (A4).
5. **Analyst later** — event impact (A5), correlations (A1), generic export (A2).

**Must-ship before 5 October if time is short:** step 1, then `#508`, then whichever of T5 / T6 / A4 you can demo. Event impact, correlations, and the generic export modal can wait if the live forecast, regime analysis, calendar, and alerts already tell the story.

**Backend that unblocks a live demo:** proxy `/api/v1/predict/btc` on the API gateway to the AI service.
