# Generative AI & coding-assistant disclosure

Human-written disclosure for **academic integrity** on this repository. It describes how **The Quintet** used generative AI and AI-assisted development tools while building MacroCrypto AI — **not** the product’s machine-learning models (Prophet, XGBoost, LightGBM in `ai-service`).

Program context: [Policies & Standards](./quantic/policies.md) (Quantic capstone).

**Final:** October 2026 capstone submission.

---

## Summary

We used **coding assistants and agent-style tools** to speed up implementation, exploration, and refactoring across the monorepo (frontend, backend microservices, tests, and repo configuration). **All merged code was reviewed by teammates** via pull requests; authors **owned and understood** what they merged.

For **formal written deliverables** (design & architecture, testing strategy, capstone wiki pages, meeting notes intended for graders), we wrote in **our own words**. Where AI **influenced a decision or outline**, we noted it here — we did **not** take AI output and drop it straight into those documents as if it were our own writing.

---

## Tools we used

| Tool | Type | How we used it on this project |
|------|------|--------------------------------|
| **Cursor** | IDE with inline chat and **Agent** mode | Frontend and full-repo edits; refactors; tests; guided by `.cursor/rules/` |
| **GitHub Copilot** | IDE completion + chat | Inline suggestions while coding; guided by [.github/copilot-instructions.md](../.github/copilot-instructions.md) and [frontend instructions](../.github/instructions/frontend.instructions.md) |
| **Claude Code** | CLI / IDE agent | Same stack conventions as [AGENTS.md](../AGENTS.md) and [CLAUDE.md](../CLAUDE.md) when used by teammates |
| **ChatGPT / Gemini / similar chat UIs** | General-purpose assistants | Architecture brainstorming, debugging hints, draft PR text (rewritten before merge) |
| **MCP integrations in Cursor** | Connected tools (e.g. browser, git hosts) | Development-time inspection and automation only; not part of the deployed product |

We added **shared agent instructions** so different assistants followed the same repo conventions:

| Artifact | Purpose |
|----------|---------|
| [AGENTS.md](../AGENTS.md) | Stack, folders, state ownership, testing strategy for coding agents |
| [CLAUDE.md](../CLAUDE.md) | Claude Code entry point → `AGENTS.md` |
| [.github/copilot-instructions.md](../.github/copilot-instructions.md) | Copilot entry point → `AGENTS.md` |
| [.cursor/rules/](../.cursor/rules/) | Cursor-specific frontend conventions |

These files are **team-authored configuration** for steering assistants; they are not a substitute for this disclosure.

---

## What we used AI for

| Activity | AI assistance | Human responsibility |
|----------|---------------|----------------------|
| **Application code** (React, Python services, Docker, CI) | Scaffolding, boilerplate, refactors, lint/type fixes, test suggestions | Review every diff; run lint, typecheck, and tests; align with our architecture and ADRs |
| **Tests** (Vitest, Playwright, pytest) | Cases, helpers, act/expect patterns | Assert real behavior; match [AGENTS.md](../AGENTS.md) testing conventions |
| **Debugging & exploration** | Error explanations, fix options, comparisons | Reproduce issues; verify fixes; choose options that fit scope |
| **Architecture brainstorming** | Pattern and API options, folder layout ideas | Decisions recorded in ADRs and design docs; final choice by the team |
| **Commit messages & PR text** | Draft wording | Authors edited for accuracy; reviewers validated |
| **Formal design & testing documentation** | Topic lists and structure prompts only | **Manual prose** throughout ([policies](./quantic/policies.md)) |
| **Capstone video script** | Occasional phrasing ideas | [Demo script](./quantic/demo-script.md) adapted and spoken by members — not read word-for-word from AI |

---

## What we did not use AI for

- Submitting **unreviewed** generated code to `main`
- Dropping AI-written paragraphs into design docs, testing docs, or capstone deliverables without rewriting them in our own words
- Replacing **teammate judgment** on security, secrets, licensing, or data handling
- Inventing sprint history, user stories, or task-board work that did not happen

---

## Review, ownership, and attribution

1. **GitHub Flow** — work merged via PR; [Code Owner](./team-roles.md) and peers reviewed ([GITHUB_FLOW.md](../GITHUB_FLOW.md), [CONTRIBUTING.md](../CONTRIBUTING.md)).
2. **Heavy AI on a module** — called out in the PR description when it mattered ([policies — Code attribution](./quantic/policies.md#code-attribution)).
3. **External code** (tutorials, Stack Overflow, libraries) — cited separately from AI; both under academic integrity.

---

## Usage by project area

| Area | Primary owners | How AI was used |
|------|----------------|-----------------|
| **Frontend** (`frontend/`) | Kingson Emma-Ochu, Richard Owusu, Loredana Lungu | Components, hooks, Zustand/TanStack Query, Vitest and Playwright specs; Cursor rules under `.cursor/rules/` |
| **Backend** (`services/`, `shared/`) | Mael Taye Deneke, Sid Ahmed Mahieddine, Richard Owusu | FastAPI services, repositories, Docker/Compose, pytest; Copilot and Agent for boilerplate and refactors |
| **ML / ai-service** | Richard Owusu | Training pipeline code, model configs, features; assistants helped with Python structure; **models, data, and metrics** validated by the team |
| **DevOps / CI** | Mael Taye Deneke, Sid Ahmed Mahieddine | GitHub Actions workflows and coverage gates; snippets suggested by AI, verified by humans |
| **Docs** (`docs/`) | Whole team | Capstone and design docs written manually; AI occasionally suggested outlines or checklists — substantive text is ours |

---

## Per-member summary

| Member | Tools used | Contributions with AI assist |
|--------|------------|------------------------------|
| **Sid Ahmed Mahieddine** | ChatGPT, DeepSeek | Product direction, microservices architecture, backend and DevOps, Docker/Compose |
| **Loredana Lungu** | Cursor (Agent), Claude Code | Frontend architecture, React/TypeScript, agent/repo rules (`.cursor/rules/`, `AGENTS.md` alignment), process and capstone docs; same [AGENTS.md](../AGENTS.md) / [CLAUDE.md](../CLAUDE.md) conventions as the rest of the repo |
| **Mael Taye Deneke** | Cursor, Copilot | Backend services, PR review as Code Owner, CI workflows |
| **Kingson Emma-Ochu** | Copilot, Cursor | Frontend features, UI integration flows |
| **Richard Owusu (Ph.D.)** | Cursor, Copilot, chat UIs | `ai-service` ML pipeline, frontend and alerts-related work, data/analysis scripts |

---

## Influence on written deliverables

| Deliverable | AI influence |
|-------------|--------------|
| [Design & architecture](./design/README.md) | Manual authorship. AI used only for brainstorming (diagram types, section topics). We did not drop AI output into the doc as our own writing. |
| [Testing (local & CI/CD)](./test%20documents/local-and-ci-cd-tests.md) | Manual authorship. AI may have suggested section headings; all descriptions of what we test and how CI runs were written and verified by the team. |
| [Policies & Standards](./quantic/policies.md) | Team reference summarizing Quantic course rules; written manually. |
| **This disclosure** | Written manually; canonical statement of coding-assistant use for this repository. |

---

## Related pages

- [Documentation index](./README.md)
- [Contributing](../CONTRIBUTING.md)
- [Quantic — AI use policy](./quantic/policies.md#ai-use)
- [Quantic — grading](./quantic/grading.md)
- [Quantic — deliverables](./quantic/deliverables.md)
