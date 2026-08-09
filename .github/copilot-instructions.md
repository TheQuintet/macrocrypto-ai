# GitHub Copilot — repository instructions

Follow `AGENTS.md` for shared MacroCrypto AI agent conventions.

## Defaults

- Prefer small, focused diffs that match existing code.
- Frontend app lives under `frontend/` (Vite + React + TypeScript).
- When editing `frontend/**/*.{ts,tsx}`, also follow `.github/instructions/frontend.instructions.md`.

## Quality

Do not leave frontend changes with failing `npm run lint`, `npm run typecheck`, or `npm test` (run from `frontend/`).
