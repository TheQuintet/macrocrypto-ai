# Agile & Sprints

How we manage MacroCrypto AI using GitHub Issues and Projects (Team Workflow board). We do **not** use GitHub Issues milestones on the repo.

We follow **Agile** with at least **three sprints** during the capstone. All tasks and user stories must be tracked on the **GitHub Project boards**.

**Workflow cycle:**

```
PLAN → ASSIGN → WORK → REVIEW → TRACK → CLOSE → RETROSPECT
```

---

## Ceremonies

Sprint **review** and **retrospective** are different ceremonies. We do not run a formal live review — there is not enough overlapping time — so review is **offline**. Retrospective stays on the weekly sync when scheduled.

Write-ups: [29 Jul refinement and planning](./meetings/2026-07-29-refinement-and-planning.md) · [5 Aug retrospective, review, refinement, and planning](./meetings/2026-08-05-retrospective.md) · [26 Aug review, refinement, and planning](./meetings/2026-08-26-review-and-planning.md) · [2 Sep review, refinement, and planning](./meetings/2026-09-02-review-and-planning.md) · [9 Sep review, refinement, and planning](./meetings/2026-09-09-review-and-planning.md) · [23 Sep review, refinement, and planning](./meetings/2026-09-23-review-and-planning.md). Blank formats: [meetings/templates/](./meetings/templates/).

### Sprint planning

Select stories, estimate, and assign owners. Product Owner prioritizes; the team commits to the sprint goal.

### Backlog refinement

Clarify stories and acceptance criteria before they enter a sprint.

### Coordination without daily standup (domain Slack)

We **did not run a daily standup** — no live meeting and **no required offline/async** “every day” standup posts either.

In `#capstone-project-group` the team had a **Slack discussion** (including poll feedback) and **agreed** that daily standups were not workable across time zones and were **not something we would enforce in Slack**. People use **private domain channels** for normal work conversation when needed, not a fixed daily template.

**Scrum Master note:** Without any daily standup, the textbook SM routine (facilitate a daily ceremony, chase everyone each morning) was **hard to maintain** for **Loredana Lungu** (Scrum Master). The role shifted to **weekly Capstone sync**, **GitHub board** hygiene, meeting notes, and blockers in Slack when they appear — see [Scrum Master role](./team-roles.md#mandatory-agile-roles).

| Channel | Domain |
|---------|--------|
| `#mc-frontend` | Dashboard, UI, client integration |
| `#mc-backend` | Services, Gateway, data pipeline, deploy |
| `#mc-ml-model` | AI/ML service, features, model research |
| `#mc-software-design` | Architecture, patterns, design docs, UML |

Use the channel that matches your work for questions and progress when you have something to share. `#capstone-project-group` is for whole-team announcements and decisions.

**Trade-off:** some members felt **less visibility** into what others were doing when conversation was split by domain. Mitigations we used: weekly Capstone sync (see [team availability](./team-roles.md#recurring-meetings-through-14-oct-2026)), GitHub board status, PR notifications, and meeting notes in `docs/meetings/`.

If you have a blocker, add the `blocked` label to the relevant issue and mention it in the relevant domain channel or `#capstone-project-group`.

### Sprint review

There is no scheduled live demo. After each sprint (or when useful), every team member:

- [ ] Pull latest `main` and run the app locally (or use the shared environment if one is available)
- [ ] Explore the new/changed behaviour yourself
- [ ] Check completed work on the [Sprint work board](https://github.com/orgs/TheQuintet/projects/6/views/7)
- [ ] Flag issues or feedback in Slack or on the relevant GitHub issue

### Retrospective

We treat **retrospective** and **review** as separate ceremonies in principle. Our weekly Capstone sync is only **1–2 hours**, so we often combine review, refinement, and planning in one session (see [Ceremonies](#ceremonies)).

**Sprint 2 (5 Aug 2026)** — we ran a **full retrospective** in that slot. The team added **what went well / improvements / action items** on the GitHub retro board during the meeting, and published a write-up in [5 Aug 2026 retrospective, review, refinement, and planning](./meetings/2026-08-05-retrospective.md). For grading and demos, use the [Sprint 2 retro board view](https://github.com/orgs/TheQuintet/projects/6/views/10) together with those notes.

**Later sprints** — we still improved every week, but we **did not keep filling a separate retro board each sprint**. With limited meeting time, we **prioritized live discussion of emergent issues** (integration, PR bottlenecks, scope) over spending part of the sync maintaining retro columns. Outcomes and action items live in the [weekly meeting notes](./meetings/) and on the [Team Workflow board](https://github.com/orgs/TheQuintet/projects/6).

| Question | Purpose |
|----------|---------|
| What went well? | Celebrate successes |
| What went wrong? | Identify problems |
| What can we improve? | Changes for next sprint |
| What should we stop doing? | Remove bad habits |
| What should we start doing? | Add good practices |

---

## Project resources

| Resource | Purpose | How often |
|----------|---------|-----------|
| [GitHub Issues](https://github.com/TheQuintet/macrocrypto-ai/issues) | Track tasks and bugs | Daily |
| [MacroCrypto AI Team Workflow](https://github.com/orgs/TheQuintet/projects/6) | Single org project — planning, sprints, roadmap, retro views | Daily |
| [All Work](https://github.com/orgs/TheQuintet/projects/6/views/6) | Primary overview — issues/PRs across sprints (main board we used) | Daily |
| [Current sprint](https://github.com/orgs/TheQuintet/projects/6/views/7) | In-sprint tasks and status | As you work |
| [Team Planning](https://github.com/orgs/TheQuintet/projects/6/views/1) | Sprint/backlog planning and ceremony prep | Weekly |
| [Sprint 2 retro board](https://github.com/orgs/TheQuintet/projects/6/views/10) | Retro items from our **5 Aug 2026** full retro (see [notes](./meetings/2026-08-05-retrospective.md)) | Reference |
| [Roadmap](https://github.com/orgs/TheQuintet/projects/6/views/5) | Epics, features, and longer-term visibility | Weekly |
| [GitHub Labels](https://github.com/TheQuintet/macrocrypto-ai/labels) | Prioritize and categorize | As needed |
| [Pull Requests](https://github.com/TheQuintet/macrocrypto-ai/pulls?q=sort%3Aupdated-desc+is%3Apr+state%3Aopen+) | Code review | Daily |
| Branch protection | Enforce quality | Always |

**Rule:** If it is not on a board or in `docs/meetings/`, it is not officially tracked. Use **Current sprint** for in-sprint status; **Team Planning** for refinement/planning; **Sprint 2 retro board** (+ [5 Aug notes](./meetings/2026-08-05-retrospective.md)) for formal retro evidence; **Roadmap** for epics and longer-term visibility. Later process improvements are in meeting notes — see [Retrospective](#retrospective).

---

## Board columns

| Column | Purpose |
|--------|---------|
| **Backlog** | Ideas that need refinement |
| **To Do** | Tasks ready to be worked on |
| **In Progress** | Tasks currently being worked on |
| **Review** | Tasks in pull request / code review |
| **Done** | Completed and merged |

**Board flow:** New items land in **Backlog** until refined. **To Do** holds sprint-ready work — no extra column needed. During refinement or planning, move issues from Backlog → To Do when they are ready to be picked up.

### How tasks move

| Action | From → To | Who |
|--------|-----------|-----|
| Issue is ready for sprint | Backlog → To Do | Team lead |
| Developer starts working | To Do → In Progress | Developer |
| Developer opens PR | In Progress → Review | Developer |
| PR is approved and merged | Review → Done | Developer |
| Issue is closed | Done → (closed) | Developer |

---

When blocked, add the `blocked` label to the issue ([labels](https://github.com/TheQuintet/macrocrypto-ai/labels)), note the blocker in a comment, and flag it in the relevant **domain Slack channel**. The [Scrum Master](./team-roles.md) helps clear blockers.

---

## Developer workflow

1. **Start day** — check assigned issues on the [Current sprint](https://github.com/orgs/TheQuintet/projects/6/views/7) view; `git pull origin main`
2. **Work on issue** — move to In Progress; branch `feature/issue-name`; commit and push regularly
3. **Async update** — post progress / blockers in the matching domain Slack channel (`#mc-frontend`, `#mc-backend`, `#mc-ml-model`, `#mc-software-design`); label blocked issues
4. **Open PR** — move issue to Review; request review from a teammate
5. **Review PRs** — review teammate PRs; approve or request changes; merge when approved
6. **End day** — update board status; close issues when done

Code changes follow [GitHub Flow](../GITHUB_FLOW.md). See also [Contributing](../CONTRIBUTING.md).

### Code review process

1. **Author** — move issue to Review; add PR description; request reviewer
2. **Reviewer** — check quality; run tests if needed; approve or request changes
3. **Author** — address feedback; push updates; request re-review
4. **Merge** — squash and merge; move issue to Done; close issue

---

## Communication

| Tool | Purpose |
|------|---------|
| Slack `#mc-frontend`, `#mc-backend`, `#mc-ml-model`, `#mc-software-design` | Domain async updates and technical discussion |
| Slack `#capstone-project-group` | Whole-team announcements, decisions, blockers that cross domains |
| Email / WhatsApp | See [team-roles.md](./team-roles.md#communication) |
| GitHub Issues | Task discussions |
| PR comments | Code discussions |

---

## Sprint requirements (capstone)

- Complete **at least 3 sprints** during the capstone.
- Each sprint needs a clear **goal**, **planned stories/tasks**, and a **review** of what was completed.
- [Product Owner](./team-roles.md) prioritizes; [Scrum Master](./team-roles.md) facilitates.

---

## Sprint checklist

### Before sprint starts

- [ ] Create issues for the sprint
- [ ] Assign tasks to team members
- [ ] Move issues to To Do
- [ ] Share board link with team
- [ ] Agree which domain Slack channel each member uses (`#mc-frontend`, `#mc-backend`, `#mc-ml-model`, `#mc-software-design`)

### During sprint

- [ ] Keep the sprint board current
- [ ] Review PRs promptly
- [ ] Label blocked issues and communicate blockers in the relevant domain channel
- [ ] Post async progress in your domain Slack channel when you have meaningful updates

### After sprint ends

- [ ] Review completed work
- [ ] Demo new features
- [ ] Conduct retrospective
- [ ] Plan next sprint

---

## Sprint log

**Capstone grading:** submit **three sprint URLs** on the project board — [All Work — Sprint 1](https://github.com/orgs/TheQuintet/projects/6/views/6?query=sprint%3A%22Sprint%201%22), [Sprint 2](https://github.com/orgs/TheQuintet/projects/6/views/6?query=sprint%3A%22Sprint%202%22), [Sprint 3](https://github.com/orgs/TheQuintet/projects/6/views/6?query=sprint%3A%22Sprint%203%22). Day-to-day tracking used **[All Work](https://github.com/orgs/TheQuintet/projects/6/views/6)** on [Team Workflow #6](https://github.com/orgs/TheQuintet/projects/6). Details: [Deliverables §4](./quantic/deliverables.md#4-agile-task-board).

### Sprint 1 — Foundation (Weeks 1–2)

| | |
|---|---|
| **Board URL (capstone)** | [All Work — Sprint 1](https://github.com/orgs/TheQuintet/projects/6/views/6?query=sprint%3A%22Sprint%201%22) |
| **Dates** | _TBD_ |
| **Sprint goal** | Infrastructure foundation — Docker, data ingestion, messaging |
| **Product Owner** | _TBD_ |
| **Scrum Master** | _TBD_ |

**Planned work**

- [ ] Setup Data Ingestion Service
- [ ] Integrate CoinGecko API
- [ ] Integrate FRED API
- [ ] Set up RabbitMQ
- [ ] Design TimescaleDB schema
- [ ] Setup Docker Compose

**Completed**

- [ ] _TBD_

**Retrospective notes**

- _What went well?_
- _What to improve?_

---

### Sprint 2 — AI Models (Weeks 3–4)

| | |
|---|---|
| **Board URL (capstone)** | [All Work — Sprint 2](https://github.com/orgs/TheQuintet/projects/6/views/6?query=sprint%3A%22Sprint%202%22) |
| **Dates** | Wed 29 Jul – Wed 5 Aug 2026 (1-week cadence) |
| **Status** | **Closed** 5 Aug 2026 — unfinished work carried into Sprint 3 |
| **Sprint goal** | Forecasting and correlation models |
| **Product Owner** | Sid Ahmed Mahieddine |
| **Scrum Master** | Loredana Lungu |

**Planned work**

- See [29 Jul planning notes](./meetings/2026-07-29-refinement-and-planning.md) — frontend setup, capacity-based frontend tasks, backend microservices refactor, use case diagram

**Completed**

- Backend: good progress, several features implemented
- Frontend: configuration/setup work progressing; little visible UI yet

**Retrospective notes**

- Full notes: [5 Aug 2026 retrospective](./meetings/2026-08-05-retrospective.md)
- Retro board (items captured live): [Sprint 2 retro view](https://github.com/orgs/TheQuintet/projects/6/views/10)
- Went well: backend collaboration, repo organization, peer reviews starting
- To improve: PR review turnaround (biggest velocity blocker), consistent daily updates, centralized docs, earlier UI sharing

---

### Sprint 3 — API & Alerts (Weeks 5–6)

| | |
|---|---|
| **Board URL (capstone)** | [All Work — Sprint 3](https://github.com/orgs/TheQuintet/projects/6/views/6?query=sprint%3A%22Sprint%203%22) |
| **Dates** | Started Wed 5 Aug 2026 (1-week cadence) |
| **Status** | **In progress** — 2 Sep session: S1 closed, T7/T8 in focus (see below) |
| **Sprint goal** | API Gateway and Alert Service |
| **Actual focus** | Finish the Sprint 2 carryover before adding new scope — [5 Aug planning notes](./meetings/2026-08-05-retrospective.md). **26 Aug:** alerts and frontend alert issues; ML / AI deferred to September — [26 Aug notes](./meetings/2026-08-26-review-and-planning.md). **2 Sep:** S1 closed; T7 (receive alerts from BTC) due Friday; T8 prediction and Prophet AI work in sprint; API Gateway at 34 endpoints — [2 Sep notes](./meetings/2026-09-02-review-and-planning.md). **9 Sep:** macro subscription UI closed; economic calendar merged; T8 UI PR + ML model debate (Prophet vs LightGBM/XGBoost); next FE focus A3/S3; AI backend blocked on model/naming and Gateway review — [9 Sep notes](./meetings/2026-09-09-review-and-planning.md). **23 Sep:** ~70% complete; feature engineering and 80-10-10 split done; investment-analyst UI stopped; Vercel plus Docker Compose; Gateway (~38 endpoints) is the integration bottleneck — [23 Sep notes](./meetings/2026-09-23-review-and-planning.md) |
| **Product Owner** | Sid Ahmed Mahieddine |
| **Scrum Master** | Loredana Lungu |

**Planned work**

- [ ] Sprint 2 carryover (no new issues until it is done)
- [ ] Faster, distributed PR reviews — frontend leads review frontend PRs, backend leads review backend PRs
- [ ] **26 Aug re-prioritization:** alerts and frontend alert issues; connect frontend alerts to the API gateway; complete the gateway for joint request/response validation
- [ ] Document five BTC + five macro / USD indicators in project stories
- [ ] Document selectable 24-hour and seven-day candlestick views on the relevant issue

**Completed**

- Frontend: **Loredana** implemented **macro-indicator charts and history** (color-coded cards, historical graph/table; demoed 26 Aug); candlesticks replace the line view
- **Richard** implemented **alerts** (recognized 26 Aug; Loredana mentored)
- Backend connections for macro-indicator data and BTC/USD price data (reported 26 Aug)

**Retrospective notes**

- No separate retro board session — the weekly sync focused on emergent integration and scope issues instead (see [Retrospective](#retrospective)). [26 Aug session notes](./meetings/2026-08-26-review-and-planning.md) capture planning and review topics only.
- Current-sprint constraint: keep essential work only; ML model, results, and performance metrics remain the principal technical gaps for Quantic

---

_Add Sprints 4–5 in the same format when ready (Dashboard, Deployment)._

---

## User story template

```
As a [type of user],
I want [goal],
so that [benefit].

Acceptance criteria:
- [ ] ...
- [ ] ...
```

---

## Key principles

| Principle | Why it matters |
|-----------|----------------|
| Start small | Don't overcomplicate the process |
| Update the board daily | Everyone knows what's happening |
| Review code quickly | Don't let PRs sit for days |
| Communicate blockers early | Label `blocked` and post in standup before you're stuck |
| Celebrate wins | Keep the team motivated |

---

## Version history

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-08 | Initial project management guide |
| 1.1 | 2026-07-14 | Merged into docs/agile.md |
| 1.2 | 2026-07-14 | Async standups, `blocked` label, board flow note |
| 1.3 | 2026-07-30 | Document four GitHub Project boards (Daily, MacroCrypto AI Team Planning, Team Retrospective, Roadmap) |
| 1.4 | 2026-08-05 | Sprint 2 closed / Sprint 3 started in the sprint log; link 5 Aug combined session notes from planning, refinement, and review ceremonies |
| 1.5 | 2026-08-26 | Link 26 Aug review / refinement / planning notes; record current-sprint focus (alerts + frontend) and September deferrals |
| 1.6 | 2026-08-30 | Richard Owusu: developer (frontend and ML), not Follow-up & QA — see [team-roles.md](./team-roles.md) |
| 1.7 | 2026-09-02 | Link 2 Sep review / refinement / planning notes; S1 closed; T7/T8 and AI (Prophet) sprint focus |
| 1.8 | 2026-09-09 | Link 9 Sep review / refinement / planning notes; A3/S3 FE focus; ML model justification and Gateway merge as blockers |
| 1.9 | 2026-09-25 | Link 23 Sep review / refinement / planning notes, revised from the Zoom transcript: BTC trader scope cut, Vercel, design-doc checklist, Gateway integration |

---

## Related pages

- [Planning template](./meetings/templates/planning.md)
- [Refinement template](./meetings/templates/refinement.md)
- [Standup template](./meetings/templates/standup.md)
- [Review template](./meetings/templates/review.md)
- [Retrospective template](./meetings/templates/retrospective.md)
- [29 Jul 2026 Refinement & Planning](./meetings/2026-07-29-refinement-and-planning.md)
- [5 Aug 2026 Retrospective, Review, Refinement & Planning](./meetings/2026-08-05-retrospective.md)
- [26 Aug 2026 Review, Refinement & Planning](./meetings/2026-08-26-review-and-planning.md)
- [2 Sep 2026 Review, Refinement & Planning](./meetings/2026-09-02-review-and-planning.md)
- [9 Sep 2026 Review, Refinement & Planning](./meetings/2026-09-09-review-and-planning.md)
- [23 Sep 2026 Review, Refinement & Planning](./meetings/2026-09-23-review-and-planning.md)
- [Team](./team-roles.md)
- [Deliverables](./quantic/deliverables.md)
- [GitHub Flow](../GITHUB_FLOW.md)
- [Docs home](./README.md)
