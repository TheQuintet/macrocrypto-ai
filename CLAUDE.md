# Claude Code — MacroCrypto AI

Follow `AGENTS.md` for shared agent conventions. Cursor-specific detail: `.cursor/rules/`.

## When working in `frontend/`

You are a frontend engineer on the Vite + React + TypeScript app.

### Must follow

- `@/` import alias; match existing `frontend/src` patterns.
- **Zustand** for UI/preferences (`*Store.ts`); **TanStack Query** for server/API data (`api/` + `use*Query` / `use*Mutation`).
- TypeScript file naming: PascalCase components/pages, camelCase hooks/modules; co-located `*.test.ts(x)`.
- ShadCN (`components/ui`) + Tailwind tokens; do not replace the UI stack.
- Before finishing: from `frontend/`, `npm run lint`, `npm run typecheck`, and `npm test` pass.
- High cohesion / low coupling; SOLID + careful DRY; pure helpers where practical; no drive-by refactors.

### Avoid

- Putting remote data in Zustand or local toggles in Query.
- Kebab-case app modules (except generated `components/ui/*`).
- New CSS frameworks, Redux, or unrelated large refactors.
