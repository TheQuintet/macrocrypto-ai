# Agent instructions — MacroCrypto AI

Shared conventions for AI coding agents (Cursor, Copilot, Claude Code, and others).
Detailed Cursor-only rules live in `.cursor/rules/`. Keep this file and tool-specific mirrors in sync when conventions change.

## Repository

- Monorepo: frontend app under `frontend/` (Vite + React + TypeScript).
- Prefer small, focused diffs that match existing patterns.
- Do not invent parallel frameworks, state libraries, or folder trees.

## Frontend (`frontend/**/*.{ts,tsx}`)

### Stack

- React + TypeScript, Vite, React Router, ShadCN UI, Tailwind, Zustand, TanStack Query, Vitest, Playwright.
- Import alias: `@/` → `frontend/src/`.

### State ownership

| Concern | Tool | Location |
|---------|------|----------|
| Preferences, modals, theme, ephemeral UI | Zustand | `src/stores/*Store.ts` |
| Fetch, cache, mutations | TanStack Query | `src/api/*` + `src/hooks/use*Query.ts` / `use*Mutation.ts` |

- Do not put remote/API data in Zustand.
- Do not use Query for purely local UI toggles.
- Do not use Zustand as the page router — use React Router.
- API modules own query keys + fetchers; hooks wrap `useQuery` / `useMutation` with explicit generics.

### Folders & naming

| Folder | Use for |
|--------|---------|
| `api/` | Query keys, fetchers (not shared type definitions) |
| `hooks/` | React hooks, including Query wrappers |
| `stores/` | Zustand stores |
| `components/` | Shared UI in grouped folders (`layout/`, `alerts/`, `dashboard/`, …); `components/ui/` = ShadCN (keep generator names) |
| `pages/` | Route screens (`*Page.tsx`) |
| `types/` | Shared domain / API types only (`@/types/...`) |
| `lib/` | Shared helpers |
| `test/` | Vitest setup only |
| `e2e/ui-integration/` | Playwright **UI integration** (FE-only browser flows) |
| `e2e/system/` | Playwright **E2E** (journeys with APIs/services when available) |

**Shared types (required):**
- Put all shared domain and API types under `src/types/` (camelCase files, e.g. `types/chart.ts`, `types/alerts.ts`, `types/btcPriceHistory.ts`).
- Import them via `@/types/...`. Do **not** declare or export shared types from `api/`, `stores/`, `hooks/`, `constants/`, or components.
- Local non-exported `Props` types may stay in the component file.
- Runtime values (constants, functions, stores) stay in their domain folders; only type aliases/interfaces belong in `types/`.

**Component structure (required):**
- **One function component per file** — single primary export; file name matches the component (`AlertListItem.tsx` → `export function AlertListItem`). Do not nest extra function components in the same file; extract them.
- **Group related components in camelCase subfolders** under `components/` (e.g. `components/alerts/`, `components/timeRange/`). Nest further when a domain grows (`dashboard/price/`, `dashboard/controls/`, `dashboard/viewport/`, `dashboard/lib/`).
- Do **not** use one-folder-per-component with `index.tsx`. Exception: ShadCN `components/ui/*` as generated.
- Pages: PascalCase `*Page.tsx` under `pages/`.
- Hooks: camelCase `use*` (`useBtcPriceHistoryQuery.ts`).
- Modules: camelCase (`btcPriceHistory.ts`, `preferencesStore.ts`).
- Unit tests: co-located `*.test.ts(x)`; helpers: `*.testHelpers.ts(x)`.
- UI integration & E2E specs: **only** under `frontend/e2e/` (Playwright) — never under `src/`, never run via Vitest.
- UI integration helpers: co-located `*.specHelpers.ts` next to the `*.spec.ts` (same act-helper style as unit tests).

### Testing strategy

| Kind | Tool | Location | Purpose |
|------|------|----------|---------|
| Unit / component | Vitest + Testing Library | Co-located under `src/` (`*.test.ts(x)`) | Isolated component/store/helper behavior |
| UI integration | Playwright | `frontend/e2e/ui-integration/` | Real-browser FE flows without requiring backend |
| E2E | Playwright | `frontend/e2e/system/` | Full user journeys that include APIs/services when those exist |

Use these names going forward. Keep strategies separate: do not mix Playwright into `src/` or Vitest; do not use Vitest for browser UI integration or E2E.

### Test helpers (act style)

Prefer small named helpers so specs read as arrange → act → assert, not raw locator/DOM detail.

| Kind | Spec | Helpers |
|------|------|---------|
| Unit | `*.test.ts(x)` next to source | co-located `*.testHelpers.ts(x)` |
| UI integration | `e2e/ui-integration/*.spec.ts` | co-located `*.specHelpers.ts` |

- **Act helpers** name the user action (`selectTimeRange`, `clickSidebarNav`); **expect helpers** name the outcome (`expectRangeSelected`, `expectRoute`).
- Unit: Testing Library `userEvent` / `act()` when updating stores outside the UI; wrap store updates in `act()`.
- UI integration: same helper style with Playwright `page` APIs — do not inline repeated `getByRole` / URL checks in every test.
- Reuse shared app constants (`routes`, `pageCopy`) from helpers instead of hardcoding path/label strings.

Examples: `TimeRangePicker.testHelpers.tsx`, `e2e/ui-integration/routing.specHelpers.ts`.

### UI & quality gates

- Reuse `@/components/ui/*`; style with Tailwind + theme tokens in `src/index.css`.
- From `frontend/`: `npm run lint`, `npm run typecheck`, and `npm test` must pass.
- Add/update co-located Vitest tests when unit-level behavior changes.
- UI integration: `npm run test:ui-integration`. E2E (system): `npm run test:e2e:system`. All Playwright: `npm run test:e2e` (first-time: `npx playwright install chromium`).
- To watch clicks/UI locally: `npm run test:ui-integration:headed`, `npm run test:e2e:headed`, or interactive `npm run test:e2e:ui`.
- UI integration and E2E are **not** on the Husky pre-commit hook (too slow); pre-commit runs lint, typecheck, and unit tests when `frontend/` is staged — fix failures; do not bypass hooks.

### Design principles

- High cohesion, low coupling; prefer composition over inheritance.
- SOLID for modules/hooks/props (SRP, OCP, LSP, ISP, DIP) — use GoF patterns only when they clearly fit.
- FP habits for helpers: purity, totality, composition, laziness; immutable state updates.
- DRY carefully; early returns; clear domain names; no drive-by refactors.

## Tool-specific config

| Tool | Config |
|------|--------|
| Cursor | `.cursor/rules/*.mdc` |
| GitHub Copilot | `.github/copilot-instructions.md` + `.github/instructions/*.instructions.md` |
| Claude Code | `CLAUDE.md` |
| Shared agents | this `AGENTS.md` |
