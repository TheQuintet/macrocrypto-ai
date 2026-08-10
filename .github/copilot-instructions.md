# GitHub Copilot — repository instructions

Follow `AGENTS.md` for shared MacroCrypto AI agent conventions.

## Defaults

- Prefer small, focused diffs that match existing code.
- Frontend app lives under `frontend/` (Vite + React + TypeScript).
- When editing `frontend/**/*.{ts,tsx}`, also follow `.github/instructions/frontend.instructions.md`.

## Quality

Do not leave frontend changes with failing `npm run lint`, `npm run typecheck`, or `npm test` (run from `frontend/`).
**UI integration** (`frontend/e2e/ui-integration/`) and **E2E** (`frontend/e2e/system/`) use Playwright and are separate from Vitest **unit** tests. Prefer `npm run test:ui-integration` / `npm run test:e2e:system`, or `npm run test:e2e` for both.
Use act helpers: unit `*.testHelpers.ts(x)`, UI integration `*.specHelpers.ts` — named act/expect helpers; specs as arrange → act → assert.
