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

State: Zustand for preferences/theme/ephemeral UI (including shared time range); TanStack Query for server data. Types in `src/types/`. Components grouped under `layout/`, `dashboard/price|controls|viewport|lib/`, `timeRange/`, `alerts/`, `charts/`, ShadCN in `ui/`.

---

## Remaining work by component

Tests and mobile layout are AC on each item, not listed here.

### Extend existing

**`ChartPanViewport` + `PriceChart`**  
Fit the visible window to the selected time range (`#510`). Zoom should start from that density, not a fixed candle width.

**`TimeRangePicker`**  
Already drives fetch; it must also drive what the chart shows (with `#510`).

**`PriceChart` / `PriceCandlestickChart` (or overlay)**  
Optional path for `#508`: history continuing into a 24h projected path + uncertainty band, visually distinct from actuals.

**Dashboard “Macro regime” card** (skeleton in `DashboardPage`)  
Replace with current regime (name, period, short explanation).

**`MacroIndicators`**  
Color-coding is done. Still missing historical access (open an indicator → series / past values).

**`AlertsList` / `AlertListItem` / `AlertsPage`**  
Replace local drafts with real CRUD; rule preview; alert history; in-app notifications. Cover price-level (T7), prediction-change (T8), and macro-event subscriptions (T9) as **one management UI with types**, not three apps.

**`AppSidebar` / `sidebarNavItems`**  
Add Alerts. Add nav for any new first-class pages (calendar, correlations, methodology, export).

**`ForecastsPage`**  
Replace placeholders with the forecast components below.

**`MacroPage`**  
Beyond the indicator grid: host or link regime timeline, calendar, correlations, event impact.

### Missing — dashboard / macro

Check off when the component exists in the app.

- [ ] `RegimeCard` — current regime on the dashboard (`#240`)
- [ ] `RegimePerformance` — how BTC behaved in this regime (`#238`)
- [ ] `RegimeTimeline` — historical regimes on a time axis (`#239`)
- [ ] `SimilarPeriods` — similar-period suggestions (`#241`)
- [ ] Regime export — export regime data (`#242`); can live in `ExportModal`
- [ ] `IndicatorHistory` — drill-down / chart of historical indicator values (`#269`)

### Missing — forecasts (also reused on dashboard for `#508`)

Check off when the component exists in the app.

- [ ] `PredictionChart` — one chart for 24h **and** 7d: projected path, high/low, tooltips, confidence band, legend, CI in tooltip
- [ ] `PredictionSummary` — direction, expected range, key levels, confidence copy
- [ ] `ConfidenceSelector` — confidence level shown on the chart
- [ ] `RecommendationCard` — trade recommendation, horizon toggle, accuracy snippet, dismiss/acknowledge
- [ ] `AccuracyPanel` — accuracy summary, trend chart, predicted vs actual, market-condition breakdown
- [ ] `AccuracyDetailsModal` — “View details”

### Missing — alerts (beyond list CRUD)

Check off when the component exists in the app.

- [ ] `AlertForm` / `AlertPreview` — create/edit + preview
- [ ] `AlertHistory` — shared history for all alert types
- [ ] `NotificationFeed` (or `AppToaster`) — in-app notifications
- [ ] `MacroEventSubscriptions` — subscribe to upcoming events

### Missing — economic calendar & event impact

Not in the app today (no route, no components). Not Sprint 5 frontend — S3 calendar **backend** is in this sprint (`#294`–`#298`). Check off when each piece exists.

- [ ] `EconomicCalendar` — upcoming events (`S3.6`); can also cover T9.8
- [ ] `EventDetailsModal` — event detail
- [ ] `EventHistory` — past events
- [ ] `TimezoneSelector` — event times in a chosen zone
- [ ] `EventImpactPanel` — impact analysis, event-type + date filters, impact chart, export (`A5`)

### Missing — analyst: correlations, export, methodology

Check off when the component exists in the app.

- [ ] `CorrelationHeatmap` — BTC–macro correlation matrix
- [ ] `RollingCorrelationChart` — rolling correlations
- [ ] `CorrelationInsights` — written insights
- [ ] `ExportModal` — start export, progress, download notifications, history (correlation + charts; PNG/PDF is backend)
- [ ] `MethodologyPage` — new route: methodology, model metrics, search, FAQ, citations

## Suggested build order

1. `ChartPanViewport` / range fit, then forecast overlay or `PredictionChart` on the dashboard.
2. `RegimeCard` + timeline / performance / similar periods.
3. `IndicatorHistory`.
4. Fill `ForecastsPage` (chart, summary, confidence, recommendations, accuracy).
5. Real `AlertForm` / history / notifications; add Alerts to the sidebar.
6. `EconomicCalendar` + details / history / timezone, then event impact.
7. Correlations, export modal, methodology page.

**Must-ship for a useful capstone UI:** steps 1–5. Calendar, correlations, export, and methodology are separate surfaces that do not exist in the app yet.
