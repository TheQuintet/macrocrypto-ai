# Frontend remaining work

Snapshot from backlog review of [open GitHub issues](https://github.com/TheQuintet/macrocrypto-ai/issues?q=sort%3Aupdated-desc+is%3Aissue+state%3Aopen+) on **20 August 2026**. Use this for planning, not as a substitute for the issue tracker.

Related: [project scope](./project-scope.md), [user stories dependency map](./user-stories-dependency-map.md), frontend conventions in `AGENTS.md`.

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

## How the issue tracker is structured

278 open issues total. Layers:

1. **Epics** — Dashboard (`#328`), BTC Forecasting (`#326`), Alert System (`#329`), Correlation & Regimes (`#330`), Export (`#331`), Methodology (`#332`), plus design/infra.
2. **Stories** — **T1–T9** BTC trader, **A1–A5** investment analyst, **S1–S3** any user.
3. **Tasks** — numbered children (`T1.8`, `A3.11`, `S3.6`) tagged `[FRONTEND]` / `[BACKEND]` / `[TESTING]`.
4. **Labels** — `frontend`, persona, owning service, sprint.

Sprint 5 tagged frontend is mostly **carryover**: S1.7–S1.9, A3.9–A3.14, A4.6. Most of the 83 frontend issues are **unscheduled**. The two concrete dashboard tickets (not generated story slices) are [#508](https://github.com/TheQuintet/macrocrypto-ai/issues/508) and [#510](https://github.com/TheQuintet/macrocrypto-ai/issues/510).

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

### New — dashboard / macro

| Component | Purpose |
|-----------|---------|
| `RegimeCard` | Current regime on the dashboard (`#240`). |
| `RegimePerformance` | How BTC behaved in this regime (`#238`). |
| `RegimeTimeline` | Historical regimes on a time axis (`#239`). |
| `SimilarPeriods` | Similar-period suggestions (`#241`). |
| Regime export | Export regime data (`#242`) — can live in `ExportModal`. |
| `IndicatorHistory` | Drill-down / chart of historical indicator values (`#269`). |

### New — forecasts (also reused on dashboard for `#508`)

| Component | Purpose |
|-----------|---------|
| `PredictionChart` | One chart for 24h **and** 7d: projected path, high/low, tooltips, confidence band, legend, CI in tooltip. |
| `PredictionSummary` | Direction, expected range, key levels, confidence copy. |
| `ConfidenceSelector` | Confidence level shown on the chart. |
| `RecommendationCard` | Trade recommendation, horizon toggle, accuracy snippet, dismiss/acknowledge. |
| `AccuracyPanel` | Accuracy summary, trend chart, predicted vs actual, market-condition breakdown. |
| `AccuracyDetailsModal` | “View details”. |

### New — alerts (beyond list CRUD)

| Component | Purpose |
|-----------|---------|
| `AlertForm` / `AlertPreview` | Create/edit + preview. |
| `AlertHistory` | Shared history for all alert types. |
| `NotificationFeed` (or `AppToaster`) | In-app notifications. |
| `MacroEventSubscriptions` | Subscribe to upcoming events. |

### New — economic calendar & event impact

| Component | Purpose |
|-----------|---------|
| `EconomicCalendar` | Upcoming events (`S3.6`); can also cover T9.8. |
| `EventDetailsModal` | Event detail. |
| `EventHistory` | Past events. |
| `TimezoneSelector` | Event times in a chosen zone. |
| `EventImpactPanel` | Impact analysis, event-type + date filters, impact chart, export. |

### New — analyst: correlations, export, methodology

| Component | Purpose |
|-----------|---------|
| `CorrelationHeatmap` | BTC–macro correlation matrix. |
| `RollingCorrelationChart` | Rolling correlations. |
| `CorrelationInsights` | Written insights. |
| `ExportModal` | Start export, progress, download notifications, history (correlation + charts; PNG/PDF is backend). |
| `MethodologyPage` | New route: methodology, model metrics, search, FAQ, citations. |

## Suggested build order

1. `ChartPanViewport` / range fit, then forecast overlay or `PredictionChart` on the dashboard.
2. `RegimeCard` + timeline / performance / similar periods.
3. `IndicatorHistory`.
4. Fill `ForecastsPage` (chart, summary, confidence, recommendations, accuracy).
5. Real `AlertForm` / history / notifications; add Alerts to the sidebar.
6. `EconomicCalendar` + details / history / timezone, then event impact.
7. Correlations, export modal, methodology page.

**Must-ship for a useful capstone UI:** steps 1–5. Calendar, correlations, export, and methodology are separate surfaces that do not exist in the app yet.
