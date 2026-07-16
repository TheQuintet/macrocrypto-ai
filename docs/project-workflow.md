# Agile & Sprints

How we manage MacroCrypto AI using GitHub Issues, Projects, and milestones.

We follow **Agile** with at least **three sprints** during the capstone. All tasks and user stories must be tracked on the **GitHub Project board**.

**Workflow cycle:**

```
PLAN → ASSIGN → WORK → REVIEW → TRACK → CLOSE → RETROSPECT
```

---

## Tools

| Tool | Purpose | How often |
|------|---------|-----------|
| [GitHub Issues](https://github.com/TheQuintet/macrocrypto-ai/issues) | Track tasks and bugs | Daily |
| GitHub Projects | Visualize workflow (Kanban) | Daily |
| GitHub Milestones | Track sprint progress | Weekly |
| GitHub Labels | Prioritize and categorize | As needed |
| Pull Requests | Code review | Daily |
| Branch protection | Enforce quality | Always |

---

## Task board

| | |
|---|---|
| **Board URL** | _TBD — add GitHub Projects link_ |
| **Repo** | [TheQuintet/macrocrypto-ai](https://github.com/TheQuintet/macrocrypto-ai) |

**Rule:** If it is not on the board, it is not officially tracked. Update the board during and after each ceremony.

### Columns

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

## Labels

| Label | Purpose |
|-------|---------|
| `high-priority` | Must be done first |
| `medium-priority` | Important but not urgent |
| `low-priority` | Can wait |
| `backend` | Backend-related tasks |
| `frontend` | Frontend-related tasks |
| `devops` | Infrastructure tasks |
| `database` | Database-related tasks |
| `bug` | Bugs |
| `enhancement` | New features |
| `documentation` | Docs-related tasks |
| `blocked` | Task cannot proceed — waiting on a dependency, decision, or person. Remove when unblocked. |

When blocked, add the `blocked` label to the issue, note the blocker in a comment, and flag it in your daily standup. The [Scrum Master](./team.md) helps clear blockers.

---

## Milestones

| Milestone | Description | Target |
|-----------|-------------|--------|
| **Sprint 1: Foundation** | Infrastructure, Docker, data ingestion | Weeks 1–2 |
| **Sprint 2: AI Models** | Forecasting and correlation models | Weeks 3–4 |
| **Sprint 3: API & Alerts** | API Gateway and Alert Service | Weeks 5–6 |
| **Sprint 4: Dashboard** | React dashboard | Weeks 7–8 |
| **Sprint 5: Deployment** | Cloud deployment and final testing | Weeks 9–10 |

---

## Ceremonies

| Ceremony | Purpose | Notes |
|----------|---------|-------|
| **Sprint planning** | Select stories, estimate, assign owners | See [Planning sessions](./meetings/planning.md) |
| **Backlog refinement** | Clarify stories, acceptance criteria, estimates | See [Refinement sessions](./meetings/refinement.md) |
| **Daily standup** (async) | Yesterday / today / blockers | Written update in Slack — see template below |
| **Sprint review** | Demo completed work, review what's left | End of each sprint |
| **Retrospective** | What went well, what to improve | After each sprint |

### Daily standup template

Standups are **async** — we cannot sync daily across time zones. Each person posts their own update in `#capstone-project-group` on working days.

```markdown
### You
- Yesterday: Set up RabbitMQ
- Today: Start Docker Compose
- Blockers: None
```

Replace the heading with your name. If you have a blocker, add the `blocked` label to the relevant issue and mention it here.

### Sprint review checklist

- [ ] Review completed work (Done column)
- [ ] Review what's left (In Progress, To Do)
- [ ] Demo new features to the team
- [ ] Identify blockers
- [ ] Plan next sprint (Backlog → To Do)

### Retrospective questions

| Question | Purpose |
|----------|---------|
| What went well? | Celebrate successes |
| What went wrong? | Identify problems |
| What can we improve? | Changes for next sprint |
| What should we stop doing? | Remove bad habits |
| What should we start doing? | Add good practices |

---

## Daily developer workflow

1. **Start day** — check assigned issues on the board; `git pull origin main`
2. **Work on issue** — move to In Progress; branch `feature/issue-name`; commit and push regularly
3. **Daily standup** — post yesterday / today / blockers in Slack; label blocked issues
4. **Open PR** — move issue to Review; request review from a teammate
5. **Review PRs** — review at least one PR per day; approve or request changes; merge when approved
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
| Slack `#capstone-project-group` | Daily standups, quick questions, async updates |
| Email / WhatsApp | See [team.md](./team.md#communication) |
| GitHub Issues | Task discussions |
| PR comments | Code discussions |

---

## Sprint requirements (capstone)

- Complete **at least 3 sprints** during the capstone.
- Each sprint needs a clear **goal**, **planned stories/tasks**, and a **review** of what was completed.
- [Product Owner](./team.md) prioritizes; [Scrum Master](./team.md) facilitates.

---

## Sprint checklist

### Before sprint starts

- [ ] Create issues for the sprint
- [ ] Assign tasks to team members
- [ ] Move issues to To Do
- [ ] Share board link with team
- [ ] Agree on async standup format (Slack, working days)

### During sprint

- [ ] Update board daily
- [ ] Review PRs promptly
- [ ] Label blocked issues and communicate blockers immediately
- [ ] Post daily standup update in Slack

### After sprint ends

- [ ] Review completed work
- [ ] Demo new features
- [ ] Conduct retrospective
- [ ] Plan next sprint

---

## Sprint log

### Sprint 1 — Foundation (Weeks 1–2)

| | |
|---|---|
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
| **Dates** | _TBD_ |
| **Sprint goal** | Forecasting and correlation models |
| **Product Owner** | _TBD_ |
| **Scrum Master** | _TBD_ |

**Planned work**

- [ ] _TBD_

**Completed**

- [ ] _TBD_

**Retrospective notes**

- _TBD_

---

### Sprint 3 — API & Alerts (Weeks 5–6)

| | |
|---|---|
| **Dates** | _TBD_ |
| **Sprint goal** | API Gateway and Alert Service |
| **Product Owner** | _TBD_ |
| **Scrum Master** | _TBD_ |

**Planned work**

- [ ] _TBD_

**Completed**

- [ ] _TBD_

**Retrospective notes**

- _TBD_

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

---

## Related pages

- [Planning sessions](./meetings/planning.md)
- [Refinement sessions](./meetings/refinement.md)
- [Team](./team.md)
- [Deliverables](./quantic/deliverables.md)
- [GitHub Flow](../GITHUB_FLOW.md)
- [Docs home](./README.md)
