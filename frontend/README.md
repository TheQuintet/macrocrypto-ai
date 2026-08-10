# MacroCrypto AI — Frontend

Vite + React + TypeScript app for the MacroCrypto AI dashboard UI.

Stack: **React**, **TypeScript**, **Vite**, **Tailwind CSS**, **ShadCN UI**, **Zustand**, **TanStack Query**, **Recharts**, **Vitest**.

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
| `npm run prepare` | Enable Husky (`cd .. && husky frontend/.husky`) — usually via `npm install` |

These match the `scripts` block in `package.json`.

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
| `src/components/` | Shared UI; `components/ui/` = ShadCN primitives |
| `src/pages/` | Route-level screens (`*Page.tsx`) |
| `src/dashboard/` | Dashboard / chart feature modules |
| `src/lib/` | Shared helpers (`queryClient`, `utils`) |
| `src/constants/` | Static config (e.g. navigation) |
| `src/test/` | Vitest setup |
| `src/alerts/`, `src/utils/` | Reserved / placeholders |

Naming: PascalCase for components and pages, camelCase for hooks and modules. Co-located tests use `*.test.ts(x)`; helpers use `*.testHelpers.ts(x)`. Leave `components/ui/*` as ShadCN generates them.

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
