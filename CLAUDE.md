# Claude Code — MacroCrypto AI

Follow `AGENTS.md` for shared agent conventions. Cursor-specific detail: `.cursor/rules/`.

## When working in `frontend/`

You are a frontend engineer on the Vite + React + TypeScript app.

### Must follow

- `@/` import alias; match existing `frontend/src` patterns.
- **Zustand** for UI/preferences (`*Store.ts`); **TanStack Query** for server/API data (`api/` + `use*Query` / `use*Mutation`); **React Router** for pages (not Zustand).
- TypeScript file naming: PascalCase components/pages, camelCase hooks/modules; co-located `*.test.ts(x)`.
- ShadCN (`components/ui`) + Tailwind tokens; do not replace the UI stack.
- Before finishing: from `frontend/`, `npm run lint`, `npm run typecheck`, and `npm test` pass.
- **Testing names:** **unit** = Vitest under `src/`; **UI integration** = Playwright in `frontend/e2e/ui-integration/`; **E2E** = Playwright in `frontend/e2e/system/` (APIs/services when available). Run `npm run test:ui-integration`, `npm run test:e2e:system`, or `npm run test:e2e` (install browsers once via `npx playwright install chromium`).
- **Act helpers:** unit tests use co-located `*.testHelpers.ts(x)`; UI integration uses `*.specHelpers.ts`. Specs should call named act/expect helpers (arrange → act → assert), not repeat raw locators. Use Testing Library `act()` for non-UI store updates in unit tests.
- High cohesion / low coupling; SOLID + careful DRY; pure helpers where practical; no drive-by refactors.

### Avoid

- Putting remote data in Zustand or local toggles in Query.
- Kebab-case app modules (except generated `components/ui/*`).
- New CSS frameworks, Redux, or unrelated large refactors.
- Mixing strategies: UI integration/E2E specs under `src/`, or running Playwright via Vitest.
