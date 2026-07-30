# Agile & Sprints

How we manage MacroCrypto AI using GitHub Issues, Projects, and milestones.

We follow **Agile** with at least **three sprints** during the capstone. All tasks and user stories must be tracked on the **GitHub Project boards**.

**Workflow cycle:**

```
PLAN → ASSIGN → WORK → REVIEW → TRACK → CLOSE → RETROSPECT
```

---

## Ceremonies

Sprint **review** and **retrospective** are different ceremonies. We do not run a formal live review — there is not enough overlapping time — so review is **offline**. Retrospective stays on the weekly sync when scheduled.

| Ceremony | Purpose | Meeting notes |
|----------|---------|---------------|
| **Sprint planning** | Select stories, estimate, assign owners | [Planning template](./meetings/templates/planning.md) · [29 Jul 2026 notes](./meetings/2026-07-29-refinement-and-planning.md) |
| **Backlog refinement** | Clarify stories, acceptance criteria, estimates | [Refinement template](./meetings/templates/refinement.md) · [29 Jul 2026 notes](./meetings/2026-07-29-refinement-and-planning.md) |
| **Daily standup** (async) | Yesterday / today / blockers | [Standup template](./meetings/templates/standup.md) · written updates in Slack (role-specific channels) |
| **Sprint review** (offline) | Each teammate has repo access and explores/plays with the app to see what shipped | [Review template](./meetings/templates/review.md) · no live demo meeting |
| **Retrospective** | What went well, what to improve | [Retrospective template](./meetings/templates/retrospective.md) · [5 Aug 2026 notes](./meetings/2026-08-05-retrospective.md) · [Team Retrospective board](https://github.com/orgs/TheQuintet/projects/4) |

### Daily standup template

Standups are **async** — we cannot sync daily across time zones. Each person posts their own update in `#capstone-project-group` on working days.

```markdown
### You
- Yesterday: Set up RabbitMQ
- Today: Start Docker Compose
- Blockers: None
```

Replace the heading with your name. If you have a blocker, add the `blocked` label to the relevant issue and mention it here.

### Sprint review (offline)

There is no scheduled live demo. After each sprint (or when useful), every team member:

- [ ] Pull latest `main` and run the app locally (or use the shared environment if one is available)
- [ ] Explore the new/changed behaviour yourself
- [ ] Check completed work on the [Daily board](https://github.com/orgs/TheQuintet/projects/3)
- [ ] Flag issues or feedback in Slack or on the relevant GitHub issue

### Retrospective checklist

- [ ] Capture what went well / what to improve on the [Team Retrospective board](https://github.com/orgs/TheQuintet/projects/4)
- [ ] Agree action items and owners
- [ ] Update [meeting notes](./meetings/2026-08-05-retrospective.md)

### Retrospective questions

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
| [Daily board](https://github.com/orgs/TheQuintet/projects/3) | Day-to-day sprint work — primary board for standup and status | Daily |
| [MacroCrypto AI Team Planning](https://github.com/orgs/TheQuintet/projects/1/views/1) | Sprint/backlog planning and ceremony prep | Weekly |
| [MacroCrypto AI Team Retrospective](https://github.com/orgs/TheQuintet/projects/4) | Retro items (what went well / improvements / action items) | After each sprint |
| [MacroCrypto AI Roadmap](https://github.com/orgs/TheQuintet/projects/5) | Epics, features, and longer-term roadmap visibility | Weekly |
| [GitHub Milestones](https://github.com/TheQuintet/macrocrypto-ai/milestones) | Track sprint progress | Weekly |
| [GitHub Labels](https://github.com/TheQuintet/macrocrypto-ai/labels) | Prioritize and categorize | As needed |
| [Pull Requests](https://github.com/TheQuintet/macrocrypto-ai/pulls?q=sort%3Aupdated-desc+is%3Apr+state%3Aopen+) | Code review | Daily |
| Branch protection | Enforce quality | Always |

**Rule:** If it is not on a board, it is not officially tracked. Use **Daily** for day-to-day status; **MacroCrypto AI Team Planning** for refinement/planning; **MacroCrypto AI Team Retrospective** for retro follow-ups; **MacroCrypto AI Roadmap** for epics/features and longer-term visibility.

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

When blocked, add the `blocked` label to the issue ([labels](https://github.com/TheQuintet/macrocrypto-ai/labels)), note the blocker in a comment, and flag it in your daily standup. The [Scrum Master](./team-roles.md) helps clear blockers.

---

## Daily developer workflow

1. **Start day** — check assigned issues on the [Daily board](https://github.com/orgs/TheQuintet/projects/3); `git pull origin main`
2. **Work on issue** — move to In Progress; branch `feature/issue-name`; commit and push regularly
3. **Daily standup** — post yesterday / today / blockers in Slack; label blocked issues
4. **Open PR** — move issue to Review; request review from a teammate
5. **Review PRs** — review at least one PR per day; approve or request changes; merge when approved
6. **End day** — update Daily board status; close issues when done

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
| 1.3 | 2026-07-30 | Document four GitHub Project boards (Daily, MacroCrypto AI Team Planning, Team Retrospective, Roadmap) |

---

## Related pages

- [Planning template](./meetings/templates/planning.md)
- [Refinement template](./meetings/templates/refinement.md)
- [Standup template](./meetings/templates/standup.md)
- [Review template](./meetings/templates/review.md)
- [Retrospective template](./meetings/templates/retrospective.md)
- [29 Jul 2026 Refinement & Planning](./meetings/2026-07-29-refinement-and-planning.md)
- [5 Aug 2026 Retrospective](./meetings/2026-08-05-retrospective.md)
- [Team](./team-roles.md)
- [Deliverables](./quantic/deliverables.md)
- [GitHub Flow](../GITHUB_FLOW.md)
- [Docs home](./README.md)
