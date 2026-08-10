# Agent instructions — MacroCrypto AI

Shared conventions for AI coding agents (Cursor, Copilot, Claude Code, and others).
Detailed Cursor-only rules live in `.cursor/rules/`. Keep this file and tool-specific mirrors in sync when conventions change.

## Repository

- Monorepo: frontend app under `frontend/` (Vite + React + TypeScript).
- Prefer small, focused diffs that match existing patterns.
- Do not invent parallel frameworks, state libraries, or folder trees.

## Frontend (`frontend/**/*.{ts,tsx}`)

### Stack

- React + TypeScript, Vite, ShadCN UI, Tailwind, Zustand, TanStack Query, Vitest.
- Import alias: `@/` → `frontend/src/`.

### State ownership

| Concern | Tool | Location |
|---------|------|----------|
| Preferences, modals, theme, ephemeral UI | Zustand | `src/stores/*Store.ts` |
| Fetch, cache, mutations | TanStack Query | `src/api/*` + `src/hooks/use*Query.ts` / `use*Mutation.ts` |

- Do not put remote/API data in Zustand.
- Do not use Query for purely local UI toggles.
- API modules own query keys + fetchers; hooks wrap `useQuery` / `useMutation` with explicit generics.

### Folders & naming

| Folder | Use for |
|--------|---------|
| `api/` | Query keys, fetchers, API types |
| `hooks/` | React hooks, including Query wrappers |
| `stores/` | Zustand stores |
| `components/` | Shared UI; `components/ui/` = ShadCN (keep generator names) |
| `pages/` | Route screens (`*Page.tsx`) |
| Feature dirs (e.g. `dashboard/`) | Feature-specific modules |
| `lib/` | Shared helpers |
| `test/` | Vitest setup only |

- Components/pages: PascalCase files matching the export (`TimeRangePicker.tsx`).
- Hooks: camelCase `use*` (`useBtcPriceHistoryQuery.ts`).
- Modules: camelCase (`btcPriceHistory.ts`, `preferencesStore.ts`).
- Tests: co-located `*.test.ts(x)`; helpers: `*.testHelpers.ts(x)`.

### UI & quality gates

- Reuse `@/components/ui/*`; style with Tailwind + theme tokens in `src/index.css`.
- From `frontend/`: `npm run lint`, `npm run typecheck`, and `npm test` must pass.
- Add/update co-located Vitest tests when behavior changes.
- Pre-commit runs lint, typecheck, and tests when `frontend/` is staged — fix failures; do not bypass hooks.

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
