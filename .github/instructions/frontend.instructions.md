---
applyTo: "frontend/**/*.{ts,tsx}"
---

# Frontend conventions (Copilot)

Apply when working under `frontend/`. Same standards as `AGENTS.md` and `.cursor/rules/`.

## Persona

- Implement Vite + React + TypeScript using existing patterns and the `@/` alias.
- Do not add parallel CSS/state frameworks or alternate folder trees.
- Finish only when `npm run lint`, `npm run typecheck`, and `npm test` pass from `frontend/`.
- **Testing names:** **unit** (Vitest, `src/`); **UI integration** (Playwright, `frontend/e2e/ui-integration/`); **E2E** (Playwright, `frontend/e2e/system/`). Use `npm run test:ui-integration`, `npm run test:e2e:system`, or `npm run test:e2e`.
- **Act helpers:** unit → `*.testHelpers.ts(x)`; UI integration → `*.specHelpers.ts`. Named act/expect helpers; specs stay arrange → act → assert. Wrap non-UI Zustand updates in Testing Library `act()`.

## State

- Zustand (`src/stores/*Store.ts`): preferences, modals, theme, ephemeral UI — not page routing.
- TanStack Query (`src/api/*` + `use*Query` / `use*Mutation` hooks): server fetch/cache/mutations.
- Never store API payloads in Zustand; never use Query for local-only toggles; use React Router for pages.
- Explicit generics on `useQuery` / `useMutation`; API modules own keys + fetchers.

## Structure & naming

- Layout: `api/`, `hooks/`, `stores/`, `components/` (+ `ui/` ShadCN), `pages/`, feature dirs, `lib/`, `test/`.
- UI integration: `frontend/e2e/ui-integration/` only (Playwright) — not under `src/`, not Vitest.
- E2E: `frontend/e2e/system/` only (Playwright; API/service-backed).
- Components/pages: `PascalCase.tsx` matching export.
- Hooks: `useSomething.ts`; modules: `camelCase.ts`.
- Unit tests: `*.test.ts(x)` next to source; helpers: `*.testHelpers.ts(x)`.
- UI integration helpers: `*.specHelpers.ts` next to `*.spec.ts`.
- Leave `components/ui/*` as ShadCN generates them.

## UI & gates

- ShadCN primitives + Tailwind theme tokens; compose classes with `cn()`.
- No unjustified `any`; do not disable ESLint to hide issues.
- Update co-located Vitest tests when unit behavior changes.
- UI integration and E2E are not on pre-commit; still run `test:e2e` for flow changes.

## Clean design

- High cohesion / low coupling; composition over inheritance.
- SOLID for modules/hooks/props; FP purity/totality/composition for helpers.
- DRY only for real shared rules; early returns; no drive-by refactors.
