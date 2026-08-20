# Frontend remaining work

Snapshot from backlog review of [open GitHub issues](https://github.com/TheQuintet/macrocrypto-ai/issues?q=sort%3Aupdated-desc+is%3Aissue+state%3Aopen+) on **20 August 2026**. Use this for planning, not as a substitute for the issue tracker.

Related: [project scope](./project-scope.md), [user stories dependency map](./user-stories-dependency-map.md), frontend conventions in `AGENTS.md`.

## How the issues are structured

The tracker is layered like this:

1. **Epics** — product areas ([#328](https://github.com/TheQuintet/macrocrypto-ai/issues/328) Dashboard, [#326](https://github.com/TheQuintet/macrocrypto-ai/issues/326) BTC Forecasting, [#329](https://github.com/TheQuintet/macrocrypto-ai/issues/329) Alert System, [#330](https://github.com/TheQuintet/macrocrypto-ai/issues/330) Correlation & Regimes, [#331](https://github.com/TheQuintet/macrocrypto-ai/issues/331) Export, [#332](https://github.com/TheQuintet/macrocrypto-ai/issues/332) Methodology, plus design/infra epics).
2. **Stories** — persona + capability, with IDs:
   - **T1–T9** — BTC trader (predictions, price, alerts)
   - **A1–A5** — investment analyst (correlations, export, regimes, methodology, event impact)
   - **S1–S3** — any user (macro indicators, public API, economic calendar)
3. **Tasks** — numbered children such as `T1.8`, `A3.11`, `S3.6`, tagged `[FRONTEND]` / `[BACKEND]` / `[TESTING]`.
4. **Labels** — `frontend` plus persona (`btc trader`, `investment analyst`, `any user`), owning service (`ai-service`, `alerts-service`, `data-service`), and sprint (`sprint-5`).

Sprint 5 tagged frontend is mostly **carryover**: S1.7–S1.9, A3.9–A3.14, A4.6. Most of the 83 frontend issues are **unscheduled**. The two concrete dashboard tickets (not generated story slices) are [#508](https://github.com/TheQuintet/macrocrypto-ai/issues/508) and [#510](https://github.com/TheQuintet/macrocrypto-ai/issues/510).

## Things to remember

- **83 open issues** are labeled `frontend`. Most are thin slices of the same screen (tooltip, summary box, then a separate “make it mobile” ticket), not 83 independent features.
- **Do not implement mobile-responsiveness or unit/UI tests as standalone work.** They are acceptance criteria on the real components below.
- **24h and 7d prediction UI is one chart with a toggle**, not two stacks of components (T1.11 and T2.8 are the same control).
- **T7.7 is duplicated** (`#152` and `#153`). Close one when implementing alert CRUD.
- Color-coding for macro indicators (**S1.8**) is already in `MacroIndicators`. Do not rebuild it.
- Price cards, live stream status, OHLC candlesticks, zoom/interval switchers, and the indicators **snapshot grid** are done. Do not rebuild those.
- Alerts **route exists** (`/alerts`) but is **not in the sidebar**. Local mock list only.
- `/forecasts` is placeholders (`ChartPlaceholder` + skeletons). Dashboard “Macro regime” card is a skeleton.
- Forecast on the dashboard (**#508**) needs a design choice: extend the price chart vs a separate card. Real history (**#507**, backend) matters if history and forecast must join on one axis.
- Time range picker already **fetches** more data; the chart viewport does not **show** the full range (**#510**). Users will expect picking 90d to show 90 days.
- Much of the remaining UI is **blocked or mock-only** until APIs exist (predictions, calendar, regimes, alerts service, export).
- Sprints are **1 week**. PR review has been a velocity drag; estimates below are engineer-time, not calendar with review lag.

## Estimate (one frontend engineer, APIs available)

| Scope | What you finish | Effort |
|--------|-----------------|--------|
| Sprint-shaped now | `#510`, `#508`, S1 leftover, A3 regimes | ~1.5–2.5 weeks |
| Capstone-useful product | Above + real `/forecasts` + real alerts CRUD | ~4–6 weeks |
| Close every FE ticket | Full trader + analyst surfaces | ~8–12 weeks (10–16 if closing tickets one-by-one) |

Ticket count overstates work. Story-level implementation is the 8–12 week number. Two frontend people in parallel (forecasts vs alerts/calendar) can cut calendar time toward ~6–8 weeks for the full set, not in half, because shared chart/layout/review still serialize.

## What the app already has

Vite + React + TypeScript under `frontend/`. Routes in `App.tsx`:

| Route | Page | Status |
|--------|------|--------|
| `/` | `DashboardPage` | Live/spot price, change, OHLC chart, pan/zoom, time range, macro indicators. Regime + forecast not wired. |
| `/macro` | `MacroPage` | Same indicators query. |
| `/forecasts` | `ForecastsPage` | Placeholder chart/cards. |
| `/alerts` | `AlertsPage` | Client-only draft list. |
| *(none)* | Methodology | No page yet. |

State: Zustand for preferences/theme/ephemeral UI (including shared time range); TanStack Query for server data. Types in `src/types/`. Components grouped under `layout/`, `dashboard/price|controls|viewport|lib/`, `timeRange/`, `alerts/`, `charts/`, ShadCN in `ui/`.

---

## Remaining work by page

Check off when it is done. Tests and mobile layout are AC on each item. `[x]` = already in the app.

Sidebar (`AppSidebar`): add **Alerts** when that page is real; add **Methodology** if it becomes its own route.

### Dashboard — `/` (`DashboardPage`)

Glance view: live price, chart, regime, indicators, optional forecast snippet.

**Already there**

- [x] `BtcPriceCard`, `PriceChangeCard`, day stats, stream status
- [x] `PriceChart` (OHLC), zoom / interval switchers, pan viewport
- [x] `TimeRangePicker` (fetches history)
- [x] `MacroIndicators` snapshot grid (including color-coding)

**Still missing**

- [ ] Chart shows the selected time range, not only one screen of candles (`#510`)
- [ ] AI forecast on this page (`#508`) — overlay on the price chart **or** a small card that reuses Forecasts’ `PredictionChart`
- [ ] `RegimeCard` — replace the skeleton with current regime (`#240`)

### Macro — `/macro` (`MacroPage`)

Deeper macro context. Today it is only the same indicator cards as the dashboard.

**Already there**

- [x] `MacroIndicators` snapshot (same component as dashboard)

**Still missing — indicators & regimes (Sprint 5 frontend)**

- [ ] `IndicatorHistory` — open an indicator → historical series (`#269`)
- [ ] `RegimePerformance` (`#238`)
- [ ] `RegimeTimeline` (`#239`)
- [ ] `SimilarPeriods` (`#241`)
- [ ] Regime export (`#242`; can use `ExportModal`)

**Still missing — calendar, events, correlations, export (later; not Sprint 5 frontend)**

Calendar (S3; backend `#294`–`#298` is in this sprint)

- [ ] `EconomicCalendar` — upcoming events (`S3.6`; can also cover T9.8)
- [ ] `EventDetailsModal`
- [ ] `EventHistory`
- [ ] `TimezoneSelector`

Event impact (A5)

- [ ] `EventImpactPanel` — filters, impact chart, export

Correlations (A1)

- [ ] `CorrelationHeatmap`
- [ ] `RollingCorrelationChart`
- [ ] `CorrelationInsights`

Export (A2) — modal opened from this page, not its own route

- [ ] `ExportModal` — progress, download notifications, history

### Forecasts — `/forecasts` (`ForecastsPage`)

**Already there**

- [x] Page shell with placeholder chart and confidence skeletons

**Still missing** (replace placeholders)

- [ ] `PredictionChart` — one chart for 24h **and** 7d, path, high/low, tooltips, confidence band, legend
- [ ] `PredictionSummary` — direction, expected range, key levels, confidence copy
- [ ] `ConfidenceSelector`
- [ ] `RecommendationCard` — horizon toggle, accuracy snippet, dismiss
- [ ] `AccuracyPanel` — trend, predicted vs actual, market-condition breakdown
- [ ] `AccuracyDetailsModal`

### Alerts — `/alerts` (`AlertsPage`)

Route exists; **not in the sidebar**. Local mock list only.

**Already there**

- [x] `AlertsEmptyState`, `AlertsList`, `AlertListItem` (client-only drafts)

**Still missing**

- [ ] Put Alerts in the sidebar
- [ ] Real CRUD (`AlertForm`) — price-level (T7), prediction-change (T8), macro-event (T9) as **types**, not three apps (`#152` / `#153` duplicate)
- [ ] `AlertPreview`
- [ ] `AlertHistory`
- [ ] `NotificationFeed` (or `AppToaster`)
- [ ] `MacroEventSubscriptions`

### Methodology — no page yet

New route (e.g. `/methodology`) plus a sidebar item.

- [ ] `MethodologyPage` — content, model performance metrics, search, FAQ (`#255`, Sprint 5), citations

## Suggested build order (by page)

1. **Dashboard** — range fit (`#510`), then forecast snippet (`#508`), then `RegimeCard`.
2. **Macro** — `IndicatorHistory` + regime block (timeline / performance / similar).
3. **Forecasts** — fill the placeholders.
4. **Alerts** — real CRUD + sidebar.
5. **Macro (later)** — calendar, event impact, correlations, export.
6. **Methodology** — new page.

**Must-ship for a useful capstone UI:** steps 1–4. Calendar, correlations, export, and methodology stay on Macro / a new page until you get to them.
