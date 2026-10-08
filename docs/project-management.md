# Project Management Guide - MacroCrypto AI

This guide outlines how our team will manage the MacroCrypto AI project using GitHub's project management tools.

---

## 🎯 Overview

Our project management workflow follows a simple cycle:

```
PLAN → ASSIGN → WORK → REVIEW → TRACK → CLOSE → RETROSPECT
```

---

## 📋 Step-by-Step Process

### 1. Planning (Sprint Planning)

At the start of each sprint (1-2 weeks), we plan what to build.

| Action | Who | How |
|--------|-----|-----|
| Review backlog | Team lead | Look at all open issues |
| Select tasks | Team | Choose what fits in the sprint |
| Set priority | Team lead | Label as `high-priority`, `medium-priority` |
| Assign to sprint | Team lead | Set **Sprint** on [Team Workflow #6](https://github.com/orgs/TheQuintet/projects/6) (`Sprint 1`, `Sprint 2`, …) |
| Move to "To Do" | Anyone | Drag issues to the "To Do" column |

---

### 2. Daily Work (The Development Cycle)

Each team member follows this daily workflow:

```
┌─────────────────────────────────────────────────────────────────┐
│                    DAILY DEVELOPER WORKFLOW                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Start Day                                                   │
│     ├── Check your assigned issues on the board                 │
│     └── Update your branch: git pull origin main               │
│                                                                  │
│  2. Work on Issue                                               │
│     ├── Move issue to "In Progress" on the board               │
│     ├── Create branch: git checkout -b feature/issue-name     │
│     ├── Write code and commit                                   │
│     └── Push regularly                                          │
│                                                                  │
│  3. Daily Standup (15 min)                                      │
│     ├── What did you do yesterday?                              │
│     ├── What are you doing today?                               │
│     └── Any blockers?                                           │
│                                                                  │
│  4. Open Pull Request                                           │
│     ├── Move issue to "Review" on the board                    │
│     ├── Open PR on GitHub                                       │
│     └── Request review from a teammate                          │
│                                                                  │
│  5. Review Others' PRs                                          │
│     ├── Review at least 1 PR per day                            │
│     ├── Approve or request changes                              │
│     └── Merge when approved                                     │
│                                                                  │
│  6. End Day                                                     │
│     ├── Update board status                                     │
│     └── Close issues when done                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

### 3. The Kanban Board Workflow

Tasks move across the board in this order:

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   BACKLOG    │────▶│    TO DO     │────▶│  IN PROGRESS │────▶│   REVIEW     │────▶│     DONE     │
├──────────────┤     ├──────────────┤     ├──────────────┤     ├──────────────┤     ├──────────────┤
│ Ideas that   │     │ Ready to     │     │ Currently    │     │ Code review  │     │ Completed    │
│ need         │     │ start        │     │ being worked │     │ in progress  │     │ and merged   │
│ refinement   │     │              │     │ on           │     │              │     │              │
│              │     │              │     │              │     │              │     │              │
│ - Feature A  │     │ - Issue 1    │     │ - Issue 3    │     │ - Issue 4    │     │ - Issue 1    │
│ - Feature B  │     │ - Issue 2    │     │              │     │              │     │ - Issue 2    │
│              │     │              │     │              │     │              │     │ - Issue 3    │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

**How to move tasks:**

| Action | From → To | Who |
|--------|-----------|-----|
| Issue is ready for sprint | Backlog → To Do | Team lead |
| Developer starts working | To Do → In Progress | Developer |
| Developer opens PR | In Progress → Review | Developer |
| PR is approved and merged | Review → Done | Developer |
| Issue is closed | Done → (closed) | Developer |

---

### 4. Communication Practices

#### Daily Standup (15 minutes)

| What to Discuss | Example |
|-----------------|---------|
| **Yesterday:** What did you complete? | "I finished the CoinGecko integration and pushed it" |
| **Today:** What are you working on? | "I'm starting the FRED API integration" |
| **Blockers:** Any issues? | "I'm stuck on RabbitMQ configuration, need help" |

**Tools for communication:**

| Tool | Purpose |
|------|---------|
| GitHub Issues | Task discussions |
| PR Comments | Code discussions |
| Team Chat | Quick questions |
| Email | Formal communication |

---

### 5. Code Review Process

```
┌─────────────────────────────────────────────────────────────────┐
│                    CODE REVIEW PROCESS                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Author Creates PR                                            │
│     ├── Moves issue to "Review" column                         │
│     ├── Adds description and context                           │
│     └── Requests review from a teammate                         │
│                                                                  │
│  2. Reviewer Reviews                                            │
│     ├── Checks code quality                                     │
│     ├── Runs tests locally (if needed)                          │
│     ├── Leaves comments or suggestions                         │
│     └── Approves or requests changes                            │
│                                                                  │
│  3. Author Addresses Feedback                                   │
│     ├── Addresses all comments                                  │
│     ├── Pushes new commits                                      │
│     └── Requests re-review                                      │
│                                                                  │
│  4. Merge and Close                                             │
│     ├── Merge PR (Squash and merge)                            │
│     ├── Move issue to "Done" column                            │
│     └── Close issue                                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

### 6. Sprint Review (End of Sprint)

At the end of each sprint (every 1-2 weeks), we review progress.

| Action | How |
|--------|-----|
| Review completed work | Check the "Done" column |
| Review what's left | Check "In Progress" and "To Do" |
| Demo new features | Show what you built to the team |
| Identify blockers | What prevented progress? |
| Plan next sprint | Move items from backlog to "To Do" |

---

### 7. Retrospective (After Each Sprint)

Questions to ask:

| Question | Purpose |
|----------|---------|
| What went well? | Celebrate successes |
| What went wrong? | Identify problems |
| What can we improve? | Make changes for next sprint |
| What should we stop doing? | Remove bad habits |
| What should we start doing? | Add good practices |

---

## 🛠️ Tools We Use

| Tool | Purpose | How Often |
|------|---------|-----------|
| GitHub Issues | Track tasks and bugs | Daily |
| GitHub Projects | Visualize workflow | Daily |
| GitHub Labels | Prioritize and categorize | As needed |
| Pull Requests | Code review | Daily |
| Branch Protection | Enforce quality | Always |

---

## 📋 Sample Sprint 1 Plan (Weeks 1-2)

### Sprint Goal: Infrastructure Foundation

| Issue | Assignee | Status |
|-------|----------|--------|
| Setup Data Ingestion Service | You | ✅ Done |
| Integrate CoinGecko API | Teammate A | ✅ Done |
| Integrate FRED API | Teammate A | ✅ Done |
| Set up RabbitMQ | You | ✅ Done |
| Design TimescaleDB Schema | Teammate B | ⏳ In Progress |
| Setup Docker Compose | You | ⏳ In Progress |

### Daily Standup Template

```markdown
## Team Standup - [Date]

### You
- Yesterday: Set up RabbitMQ
- Today: Start Docker Compose
- Blockers: None

### Teammate A
- Yesterday: CoinGecko API integration complete
- Today: Start FRED API integration
- Blockers: FRED API key not working (need help)

### Teammate B
- Yesterday: Designed TimescaleDB schema
- Today: Start implementing the schema
- Blockers: None
```

---

## 📊 Board Setup Instructions

### Columns

| Column | Purpose |
|--------|---------|
| **Backlog** | Ideas that need to be refined |
| **To Do** | Tasks ready to be worked on |
| **In Progress** | Tasks currently being worked on |
| **Review** | Tasks in pull request / code review |
| **Done** | Completed tasks |

### Labels

| Label | Color | Purpose |
|-------|-------|---------|
| `high-priority` | Red | Must be done first |
| `medium-priority` | Orange | Important but not urgent |
| `low-priority` | Blue | Can wait |
| `backend` | Purple | Backend-related tasks |
| `frontend` | Green | Frontend-related tasks |
| `devops` | Cyan | Infrastructure tasks |
| `database` | Yellow | Database-related tasks |
| `bug` | Red | Bugs |
| `enhancement` | Green | New features |
| `documentation` | Blue | Docs-related tasks |

### Sprints (project board)

Track sprints with the **Sprint** field on [Team Workflow #6](https://github.com/orgs/TheQuintet/projects/6) — not GitHub Issues milestones on the repo.

| Sprint | Description | Target |
|--------|-------------|--------|
| **Sprint 1: Foundation** | Setup infrastructure, Docker, and data ingestion | Week 1-2 |
| **Sprint 2: AI Models** | Implement forecasting and correlation models | Week 3-4 |
| **Sprint 3: API & Alerts** | Build API Gateway and Alert Service | Week 5-6 |
| **Sprint 4: Dashboard** | Build React dashboard | Week 7-8 |
| **Sprint 5: Deployment** | Deploy to cloud and final testing | Week 9-10 |

---

## ✅ Sprint Checklist

### Before Sprint Starts
- [ ] Create issues for the sprint
- [ ] Assign tasks to team members
- [ ] Move issues to "To Do"
- [ ] Share board link with team
- [ ] Schedule daily standups

### During Sprint
- [ ] Update board daily
- [ ] Review PRs promptly
- [ ] Communicate blockers immediately
- [ ] Attend daily standups

### After Sprint Ends
- [ ] Review completed work
- [ ] Demo new features
- [ ] Conduct retrospective
- [ ] Plan next sprint

---

## 🔑 Key Takeaways

| Principle | Why It Matters |
|-----------|----------------|
| **Start small** | Don't overcomplicate the process |
| **Update the board daily** | Everyone knows what's happening |
| **Review code quickly** | Don't let PRs sit for days |
| **Communicate blockers** | Get help early |
| **Celebrate wins** | Keep team motivated |

---

## 📄 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-08 | Initial version |
```