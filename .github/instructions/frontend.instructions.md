---
applyTo: "frontend/**/*.{ts,tsx}"
---

# Frontend conventions (Copilot)

Apply when working under `frontend/`. Same standards as `AGENTS.md` and `.cursor/rules/`.

## Persona

- Implement Vite + React + TypeScript using existing patterns and the `@/` alias.
- Do not add parallel CSS/state frameworks or alternate folder trees.
- Finish only when `npm run lint`, `npm run typecheck`, and `npm test` pass from `frontend/`.

## State

- Zustand (`src/stores/*Store.ts`): preferences, modals, theme, ephemeral UI.
- TanStack Query (`src/api/*` + `use*Query` / `use*Mutation` hooks): server fetch/cache/mutations.
- Never store API payloads in Zustand; never use Query for local-only toggles.
- Explicit generics on `useQuery` / `useMutation`; API modules own keys + fetchers.

## Structure & naming

- Layout: `api/`, `hooks/`, `stores/`, `components/` (+ `ui/` ShadCN), `pages/`, feature dirs, `lib/`, `test/`.
- Components/pages: `PascalCase.tsx` matching export.
- Hooks: `useSomething.ts`; modules: `camelCase.ts`.
- Tests: `*.test.ts(x)`; helpers: `*.testHelpers.ts(x)`.
- Leave `components/ui/*` as ShadCN generates them.

## UI & gates

- ShadCN primitives + Tailwind theme tokens; compose classes with `cn()`.
- No unjustified `any`; do not disable ESLint to hide issues.
- Update co-located Vitest tests when behavior changes.

## Clean design

- High cohesion / low coupling; composition over inheritance.
- SOLID for modules/hooks/props; FP purity/totality/composition for helpers.
- DRY only for real shared rules; early returns; no drive-by refactors.
