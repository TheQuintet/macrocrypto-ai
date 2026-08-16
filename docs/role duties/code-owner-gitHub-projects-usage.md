# Code Owner – GitHub Projects Usage & Responsibilities

## Overview
The Code Owner uses GitHub Projects as the primary tool to enforce code quality, manage technical debt, oversee the CI/CD pipeline, review pull requests, and ensure the codebase remains maintainable and secure. The Code Owner is the **guardian of technical excellence** – ensuring that every merge meets quality standards and that the team follows best practices.

Below is a detailed breakdown of exactly what the Code Owner does on **each of the 4 GitHub Project boards**.

---

## 1. TEAM PLANNING Board

### Purpose
High-level strategic planning – epics, themes, major milestones, and release-level coordination.

### Code Owner Responsibilities

#### Daily / Ongoing
- **Review epics** – ensure each epic has technical considerations documented (e.g., architecture, infrastructure needs).
- **Add technical epics** – create epics for infrastructure, refactoring, security, or tooling upgrades.
- **Flag technical risks** – if an epic requires significant architectural changes, add a "Technical Risk" label.

#### Weekly (every Friday)
- **Review technical epics** – ensure they are progressing and not being deprioritized.
- **Coordinate with the PO** – ensure technical epics are scheduled alongside feature epics.
- **Identify technical dependencies** – flag if feature epics depend on technical work.

#### Every Sprint Planning
- **Verify technical readiness** – ensure epics planned for the next sprint have technical tasks identified.
- **Assess technical complexity** – estimate architectural work required and communicate to the team.

#### Every Month
- **Review technical debt epics** – ensure at least 20% of sprint capacity is allocated to technical debt reduction.
- **Present technical health report** – share metrics (coverage, debt, build health) with the team.

### Columns & What Code Owner Does With Them

| Column | Code Owner Action |
|--------|-------------------|
| **Backlog (Epics)** | Add technical epics (e.g., "Upgrade to Node 18," "Database Migration," "Security Audit"). |
| **Next Up (Epics)** | Ensure technical epics are represented – prevent feature-only focus. |
| **In Progress (Epics)** | Track technical epic progress – if it's blocked, escalate to the SM. |
| **Blocked** | Add technical blocker details (e.g., "Waiting for infrastructure access"). |
| **Done / Released** | Close technical epics – ensure all associated tasks are completed. |

### Example Code Owner Tasks on Team Planning
- Create an epic: "Technical Debt – Refactor Auth Module" with 5 subtasks.
- Add a label: "Security Priority" to the "API Rate Limiting" epic.
- Flag that "Reports Dashboard" epic is blocked by the "Data Pipeline" technical epic – add a dependency note.

---

## 2. ROADMAP Board

### Purpose
Timeline view – shows the project schedule, key milestones, and release dates over the 3-month horizon.

### Code Owner Responsibilities

#### Daily / Ongoing
- **Check technical milestones** – ensure they are on track (e.g., "CI/CD Complete," "Security Audit Passed").
- **Flag technical risks** – if a milestone is at risk, add a comment explaining technical blockers.
- **Update technical milestones** – add progress updates (e.g., "Build pipeline 80% configured").

#### Weekly (every Friday)
- **Review technical milestone progress** – compare planned vs. actual.
- **Adjust technical milestones** – if the team is ahead/behind, update dates.
- **Add new technical milestones** – if new technical work emerges, add it to the roadmap.

#### Every Sprint Review
- **Update technical milestones** – mark as "Achieved" when completed.
- **Add technical accomplishments** – e.g., "Test coverage increased to 82%."

#### Every Month
- **Present technical timeline** – show progress on infrastructure, security, and debt reduction.
- **Recommend adjustments** – if technical work is falling behind, suggest reallocating capacity.

### Columns & What Code Owner Does With Them

| Column | Code Owner Action |
|--------|-------------------|
| **Backlog (Milestones)** | Add technical milestones with realistic dates (e.g., "API v2 Complete – Month 2"). |
| **Current Sprint** | Track technical tasks – ensure they're progressing alongside features. |
| **Next Sprint** | Prepare technical milestones – ensure associated tasks are refined. |
| **Month 1 / 2 / 3** | Organize technical milestones – ensure they don't slip. |
| **Completed** | Move technical milestones here – add a summary of technical achievements. |

### Example Code Owner Tasks on Roadmap
- Create a milestone: "CI/CD Pipeline Fully Automated – End of Month 1."
- Add a milestone: "Security Audit Passed – Month 2 Week 2."
- If the team is behind, extend "Database Migration" milestone by 1 week and comment on the reason.

---

## 3. ITERATIVE DEVELOPMENT Board

### Purpose
Sprint-level execution – this is the Code Owner's **primary operational board**. It tracks technical tasks, code quality, and ensures every story meets the Definition of Done from a technical perspective.

### Code Owner Responsibilities

#### Daily / Ongoing (CRITICAL)
- **Review all PRs** – check the "Review/QA" column for new PRs – aim for < 4-hour turnaround.
- **Check CI/CD status** – ensure all builds and tests are passing.
- **Monitor "Blocked" column** – for technical blockers (e.g., test failures, environment issues).
- **Ensure test coverage** – if a story is "In Progress," check that the developer is writing tests.
- **Enforce coding standards** – if you see deviations, add a comment and guide the developer.

#### Every Sprint Planning
- **Review upcoming stories** – identify technical complexity and risks.
- **Create technical subtasks** – break down stories into actionable technical tasks.
- **Estimate technical work** – help the team estimate using story points.
- **Commit to technical deliverables** – e.g., "We will refactor the DB layer this sprint."

#### Every Sprint Review
- **Validate technical completeness** – ensure all "Done" stories meet the technical DoD.
- **Check test coverage** – ensure no story is accepted with declining coverage.
- **Ensure CI/CD is green** – verify all merged code passes all checks.
- **Review code quality** – confirm no new technical debt was introduced.

#### Every Sprint Retrospective
- **Share technical metrics** – PR review time, test coverage %, build failure rate.
- **Discuss technical challenges** – e.g., flaky tests, slow builds, complex code.
- **Propose technical improvements** – add them as action items.

### Columns & What Code Owner Does With Them

| Column | Code Owner Action |
|--------|-------------------|
| **Backlog** | Add technical debt tasks (e.g., "Add missing unit tests," "Refactor service X"). |
| **Ready** | Ensure stories have technical subtasks and clear acceptance criteria from a technical perspective. |
| **To Do** | Verify technical subtasks are assigned to developers. |
| **In Progress** | Monitor – ensure developers are writing tests and following architecture. |
| **Review / QA** | **Code Owner's #1 priority** – review all PRs here. Approve, request changes, or reject. |
| **Blocked** | Investigate technical blockers – e.g., CI failure, missing dependency, environment issue. |
| **Done** | Only move stories here if they meet the technical DoD (tests pass, coverage meets threshold, no technical debt). |

### Example Code Owner Tasks on Iterative Development
- Review a PR in "Review/QA" – request changes because it lacks unit tests.
- Move "Upgrade DB Driver" to "Blocked" – the new driver conflicts with existing code.
- Add a subtask to a story: "Write integration tests for payment API."
- Enforce coverage: reject a PR that drops coverage from 80% to 78%.

---

## 4. RETROSPECTIVE Board

### Purpose
Continuous improvement – track what went well, what didn't, and action items for process improvement.

### Code Owner Responsibilities

#### Every Sprint Retrospective
- **Add technical items** – what went well/badly from a code quality perspective.
- **Share technical metrics** – present data (PR review time, test coverage, build failures).
- **Propose technical action items** – e.g., "Automate linting," "Improve CI speed."
- **Commit to improvements** – e.g., "I will reduce PR review time to < 4 hours."

#### Weekly (every Friday)
- **Review technical action items** – track progress.
- **Add new technical insights** – if you notice recurring issues, add them.
- **Follow up on action items** – remind owners if items are overdue.

#### Throughout the Sprint
- **Track technical action items** – ensure they are being addressed.
- **If an action item is stuck** – discuss with the team and adjust.
- **Celebrate technical wins** – e.g., "Build time reduced by 40%."

### Columns & What Code Owner Does With Them

| Column | Code Owner Action |
|--------|-------------------|
| **Went Well** | Add positive technical items – e.g., "Great code reviews this sprint." |
| **Needs Improvement** | Add technical issues – e.g., "CI is too slow (15 min build time)." |
| **Action Items** | Add technical actions – e.g., "Automate dependency updates." Assign to yourself or team. |
| **In Progress** | Update technical action items – e.g., "Setting up SonarQube." |
| **Done** | Move completed technical actions – e.g., "Added pre-commit hooks." |

### Example Code Owner Tasks on Retrospective
- Add: "Went Well – No critical security vulnerabilities found."
- Add: "Needs Improvement – PR reviews are taking > 24 hours."
- Create action: "Agree on SLAs for code reviews (max 4 hours) – assign to SM."
- Move action: "Set up automated linting" to "Done."

---

## Summary Table – Code Owner Activities by Board

| Board | Primary Code Owner Focus | Frequency | Key Actions |
|-------|--------------------------|-----------|-------------|
| **Team Planning** | Technical strategy & debt epics | Weekly / Monthly | Add technical epics, flag risks, ensure tech debt is scheduled. |
| **Roadmap** | Technical milestones & infrastructure | Weekly / Sprint Review | Update technical milestones, flag risks, add new technical milestones. |
| **Iterative Development** | Code quality & PR reviews | Daily (CRITICAL) | Review PRs, enforce standards, monitor CI, unblock technical issues. |
| **Retrospective** | Technical process improvement | Every Sprint / Weekly | Share metrics, propose improvements, track technical action items. |

---

## Code Owner's Daily GitHub Routine (Consolidated)

1. **Check Iterative Development (Morning)** – review all PRs in "Review/QA" – aim for < 4-hour response.
2. **Check CI/CD** – ensure all builds pass – if not, investigate and assign fixes.
3. **Check "Blocked" column** – resolve any technical blockers (test failures, environment issues).
4. **Monitor "In Progress"** – ensure developers are writing tests and following standards.
5. **Check Roadmap** – update technical milestone progress if needed.
6. **Check Retrospective** – review progress on technical action items.
7. **End-of-day check** – ensure no PRs are left unreviewed for > 4 hours.

---

## Code Owner's Weekly GitHub Routine (Every Friday)

1. **Team Planning** – review technical epics – add/remove, adjust priorities.
2. **Roadmap** – update technical milestone progress, adjust dates if needed.
3. **Iterative Development** – ensure technical debt tasks are in the backlog (at least 20% of total).
4. **Retrospective** – add technical insights, update action item status.
5. **Metrics** – generate test coverage, static analysis, and build health reports – share with the team.

---

## Code Owner's Sprint Routine on GitHub

| Event | Actions on GitHub |
|-------|-------------------|
| **Sprint Planning** | Review stories – add technical subtasks. Estimate complexity. Commit to technical deliverables. |
| **During Sprint** | Daily – review PRs, enforce quality, unblock technical issues, check CI. |
| **Sprint Review** | Validate technical completeness of all "Done" stories. Ensure no coverage drop. Check CI/CD green. |
| **Sprint Retro** | Share technical metrics. Add technical items. Create action items for improvement. |

---

## Code Owner's 3-Month Milestone Checkpoints (by Board)

### Month 1 (Foundation)
- **Team Planning** – create technical epics for infrastructure, CI/CD, and security.
- **Roadmap** – set up technical milestones (e.g., "CI/CD Complete," "Test Coverage 70%").
- **Iterative Development** – enforce coding standards – add linting, pre-commit hooks.
- **Retrospective** – establish baseline metrics (coverage, build time, debt).

### Month 2 (Optimization)
- **Team Planning** – ensure tech debt epics are being addressed – allocate 20% capacity.
- **Roadmap** – adjust technical milestones based on progress – add new ones if needed.
- **Iterative Development** – enforce stricter quality – reject PRs that drop coverage.
- **Retrospective** – track that technical action items are completed.

### Month 3 (Finalization)
- **Team Planning** – close all technical epics – ensure no critical debt remains.
- **Roadmap** – finalize technical milestones – ensure all are "Achieved."
- **Iterative Development** – final review – ensure every story meets technical DoD.
- **Retrospective** – final retro – capture lessons learned for future projects.

---

## Code Owner's Technical Metrics to Track (via GitHub)

| Metric | How to Track | Purpose |
|--------|--------------|---------|
| **Test Coverage** | GitHub Actions / SonarQube report | Ensure quality standards are maintained. |
| **PR Review Time** | Time from PR creation to merge | Improve collaboration efficiency. |
| **Build Failure Rate** | CI/CD status checks | Identify reliability issues. |
| **Technical Debt** | Static analysis tools (SonarQube) | Track and reduce debt over time. |
| **Code Duplication** | Static analysis | Improve maintainability. |
| **Security Vulnerabilities** | Dependency scanners (Dependabot) | Ensure security compliance. |

---

## Code Owner Checklist (Printable)

### Daily
- [ ] Review all PRs in "Review/QA" – approve or request changes.
- [ ] Check CI/CD – ensure all builds pass.
- [ ] Check "Blocked" – investigate technical blockers.
- [ ] Ensure test coverage is not declining.
- [ ] Enforce coding standards – add comments if needed.
- [ ] Update technical milestone progress on Roadmap.

### Weekly
- [ ] Review technical epics on Team Planning.
- [ ] Update technical milestones on Roadmap.
- [ ] Ensure technical debt tasks are in the backlog.
- [ ] Follow up on Retrospective technical action items.
- [ ] Share technical metrics with the team.

### Sprint Events
- [ ] Review upcoming stories – add technical subtasks.
- [ ] Validate all "Done" stories meet technical DoD.
- [ ] Ensure no coverage drop in the sprint.
- [ ] Present technical metrics in Retrospective.
- [ ] Propose technical improvements.

---

## Code Owner's Responsibility for Definition of Done (Technical)

A story is technically "Done" only when:

- [ ] Code passes all CI/CD checks (build, tests, linting).
- [ ] Test coverage is ≥ agreed threshold (e.g., 80%).
- [ ] No security vulnerabilities (Dependabot, SAST).
- [ ] Code review approved by at least 1 other developer.
- [ ] Code Owner has approved the PR.
- [ ] No new technical debt introduced (or a follow-up issue is created).
- [ ] Documentation is updated (README, API docs, inline comments).
- [ ] Branch is merged into the main branch.

---

**Next:** Tell me which role you want next for GitHub Projects – **Developers (2)** or if you want a combined summary for all roles.