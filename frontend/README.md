# MacroCrypto AI — Frontend

Vite + React + TypeScript app for the MacroCrypto AI dashboard UI.

Stack: **React**, **TypeScript**, **Vite**, **React Router**, **Tailwind CSS**, **ShadCN UI**, **Zustand**, **TanStack Query**, **Recharts**, **Vitest**, **Playwright**.

## Prerequisites

- **Node.js** 20+ (LTS recommended)
- **npm** (comes with Node)

Work from the `frontend/` directory for all commands below.

## Setup

```bash
cd frontend
npm install
```

`npm install` runs the `prepare` script, which enables **Husky** git hooks from `frontend/.husky` (see [Pre-commit hooks](#pre-commit-hooks)).

### Start the app

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser. Vite hot-reloads as you edit files under `src/`.

To stop the server, press `Ctrl+C` in the terminal.

### Connect to the API Gateway

Start the backend services from the repository root:

```bash
docker compose up -d api-gateway
```

Then configure the frontend:

```bash
cp .env.example .env.local
```

Set this value in `.env.local`:

```dotenv
VITE_API_GATEWAY_BASE_URL=http://localhost:8000
```

All data and alert HTTP requests then use the gateway. Leave the value empty
for a frontend-only run with simulated data. `VITE_API_BASE_URL` and
`VITE_ALERT_API_BASE_URL` remain available only for direct downstream-service
development; the gateway URL takes precedence when both are set.

## Scripts

| Command | What it does |
|---------|----------------|
| `npm run dev` | Start the Vite dev server ([http://localhost:3000](http://localhost:3000)) |
| `npm run build` | Typecheck (`tsc -b`) then production build |
| `npm run preview` | Preview the production build locally |
| `npm run typecheck` | TypeScript project build with `--noEmit` |
| `npm run lint` | ESLint over the frontend package |
| `npm run lint:fix` | ESLint with `--fix` |
| `npm test` | Vitest unit tests (`vitest run`) |
| `npm run test:e2e` | All Playwright projects (UI integration + E2E), headless |
| `npm run test:ui-integration` | Playwright UI integration only (`e2e/ui-integration/`), headless |
| `npm run test:e2e:system` | Playwright E2E only (`e2e/system/`), headless |
| `npm run test:ui-integration:headed` | UI integration with visible browser + slow-mo |
| `npm run test:e2e:headed` | All Playwright projects, visible browser + slow-mo |
| `npm run test:e2e:ui` | Playwright interactive UI mode |
| `npm run prepare` | Enable Husky (`cd .. && husky frontend/.husky`) — usually via `npm install` |

These match the `scripts` block in `package.json`.

### UI integration & E2E (Playwright)

First-time machine setup (installs browser binaries used by Playwright):

```bash
npx playwright install chromium
```

```bash
npm run test:ui-integration   # FE-only browser flows (headless)
npm run test:e2e:system       # API/service-backed journeys (when specs exist)
npm run test:e2e              # both Playwright projects (headless)
```

**Watch the browser (clicks + UI):**

```bash
npm run test:ui-integration:headed   # opens Chromium; slows actions via config when --headed
npm run test:e2e:headed              # same for all Playwright projects
npm run test:e2e:ui                  # Playwright UI mode — pick/debug tests interactively
```

- **Headed** (`--headed`) shows the real browser window. Slow-mo is applied in `playwright.config.ts` for headed runs (there is no `--slow-mo` CLI flag).
- **UI mode** (`--ui`) opens Playwright’s test runner UI to step through specs, time-travel, and inspect actions.

Default CI/local `test:e2e` stays **headless** (faster, no window).

**Testing names we use:**

| Kind | Meaning | Location |
|------|---------|----------|
| Unit | Isolated component/store/helper tests | Co-located under `src/` (Vitest) |
| UI integration | Real-browser FE flows (no backend required) | `e2e/ui-integration/` (Playwright) |
| E2E | Full journeys including APIs/services when available | `e2e/system/` (Playwright) |

UI integration and E2E share Playwright but live in **separate folders** — a **different strategy** from unit tests. Do not put Playwright specs in `src/` or run them with `npm test`. They are **not** part of the Husky pre-commit hook (too slow for every commit); run them locally or in CI when touching user flows.

Prefer **act helpers**: unit tests use co-located `*.testHelpers.ts(x)`; UI integration uses `*.specHelpers.ts`. Specs should call named act/expect helpers (arrange → act → assert) instead of repeating locators.

## Pre-commit hooks

Husky is turned on automatically when you run `npm install` (via the `prepare` script). No separate hook install step is required.

When you commit, if any files under `frontend/` are staged, the hook runs:

1. `npm run lint`
2. `npm run typecheck`
3. `npm test`

Commits that do not touch `frontend/` skip these checks. Fix failures rather than bypassing the hook.

## Folder overview

Source lives in `src/` (`@/` alias → `src/`).

| Path | Purpose |
|------|---------|
| `src/api/` | Query keys, fetchers, API types |
| `src/hooks/` | React hooks, including TanStack Query wrappers |
| `src/stores/` | Zustand stores (client/UI state) |
| `src/components/` | Shared UI grouped by domain (`layout/`, `alerts/`, `timeRange/`, `dashboard/`, …); `components/ui/` = ShadCN primitives |
| `src/types/` | Shared domain / API TypeScript types (`@/types/...`) |
| `src/pages/` | Route-level screens (`*Page.tsx`) |
| `src/lib/` | Shared helpers (`queryClient`, `utils`) |
| `src/constants/` | Static config (e.g. navigation) |
| `src/test/` | Vitest setup |
| `src/alerts/`, `src/utils/` | Reserved / placeholders |
| `e2e/ui-integration/` | Playwright **UI integration** specs (`*.spec.ts`) + `*.specHelpers.ts` |
| `e2e/system/` | Playwright **E2E** specs (API/service-backed; add when ready) |

Naming: **one function component per file** (PascalCase name = export); group related UI in camelCase folders under `components/` (nest when a domain grows, e.g. `dashboard/controls/`). **Shared types** in `src/types/`. CamelCase for hooks and modules. Co-located tests use `*.test.ts(x)`; helpers use `*.testHelpers.ts(x)`. Leave `components/ui/*` as ShadCN generates them.

## Routing

Client-side routes (React Router):

| Path | Page |
|------|------|
| `/` | Dashboard |
| `/macro` | Macro indicators |
| `/forecasts` | Forecasts |
| `/alerts` | Alerts |

Sidebar and header alerts use router `Link`s. Shared UI preferences (theme, time range, sidebar) stay in Zustand — not used as the page router.

## State ownership

Keep **client UI state** and **server/API state** separate.

| Concern | Tool | Where |
|---------|------|--------|
| Preferences, modals, theme, ephemeral UI | **Zustand** | `src/stores/*Store.ts` |
| Fetch, cache, mutations | **TanStack Query** | `src/api/*` + `src/hooks/use*Query.ts` / `use*Mutation.ts` |

- Do **not** put remote lists or API payloads in Zustand.
- Do **not** use Query for purely local UI toggles.
- API modules own query keys and fetchers; hooks wrap `useQuery` / `useMutation` (prefer explicit generics).
- Prefer Zustand selectors over subscribing to the whole store.

Example preferences store: `src/stores/preferencesStore.ts`.  
Example query pattern: `src/api/btcPriceHistory.ts` + `src/hooks/useBtcPriceHistoryQuery.ts`.
