# Scrum Master – GitHub Projects Usage & Responsibilities

## Overview
The Scrum Master (SM) uses GitHub Projects as the primary tool to facilitate Scrum events, ensure process transparency, remove impediments, track team health, and drive continuous improvement. The SM is the **guardian of the process** – keeping boards accurate, ensuring the team follows Scrum, and making data-driven decisions visible.

Below is a detailed breakdown of exactly what the SM does on **each of the 4 GitHub Project boards**.

**MacroCrypto AI practice:** Sprints live on [Team Workflow #6](https://github.com/orgs/TheQuintet/projects/6) via the **Sprint** field. We do **not** use GitHub Issues milestones on the repo.

---

## 1. TEAM PLANNING Board

### Purpose
High-level strategic planning – epics, themes, major roadmap checkpoints, and release-level coordination.

### SM Responsibilities

#### Daily / Ongoing
- **Monitor the board** – ensure epics have clear owners and timelines.
- **Check for dependencies** – identify if any epics are blocking others and escalate.
- **Ensure consistency** – verify that epics on this board match the Roadmap roadmap checkpoints.

#### Weekly (every Friday)
- **Review epic progress** – check if epics are on track based on team velocity.
- **Flag risks** – if an epic is falling behind, add a "Risk" label and discuss with the PO.
- **Update epic status** – move epics between columns based on team progress.

#### Every Sprint Planning
- **Verify epic readiness** – ensure the top epics for the upcoming sprint have refined stories.
- **Check capacity** – ensure the team has enough capacity to work on the planned epics.
- **Identify dependencies** – flag any cross-epic dependencies that could block the team.

#### Every Month
- **Present a health report** – show epic completion trends to the team.
- **Recommend adjustments** – suggest reprioritizing epics if velocity is consistently off-track.

### Columns & What SM Does With Them

| Column | SM Action |
|--------|-----------|
| **Backlog (Epics)** | Ensure all epics have descriptions, owners, and target roadmap checkpoints. Add labels (e.g., "High Risk," "Needs Refinement"). |
| **Next Up (Epics)** | Verify that epics moved here have refined stories in the Iterative Development backlog. |
| **In Progress (Epics)** | Track overall progress – if an epic is stuck, investigate and escalate to the PO. |
| **Blocked** | Add detailed blocker descriptions. Coordinate with the PO and Code Owner to unblock. |
| **Done / Released** | Celebrate epic completions – move them here and archive if needed. |

### Example SM Tasks on Team Planning
- Add a "Risk" label to "Payment Integration" epic – the team lacks experience with Stripe.
- Move "User Authentication" from "Next Up" to "In Progress" after Sprint 1 starts.
- Flag that "Reporting Dashboard" is blocked by "Data Pipeline" – create a dependency note.

---

## 2. ROADMAP Board

### Purpose
Timeline view – shows the project schedule, key roadmap checkpoints, and release dates over the 3-month horizon.

### SM Responsibilities

#### Daily / Ongoing
- **Check the board** – ensure roadmap checkpoints are aligned with the Iterative Development board.
- **Update roadmap checkpoint progress** – add daily completion percentages (e.g., "Sprint 1: 60% done").
- **Flag slips** – if a roadmap checkpoint is at risk, add a comment explaining why and what's being done.

#### Weekly (every Friday)
- **Review the 3-month timeline** – compare planned vs. actual progress.
- **Calculate velocity** – use completed story points to forecast roadmap checkpoint completion.
- **Update the board** – adjust roadmap checkpoint dates if the team is consistently ahead or behind.
- **Share updates** – send a summary of the roadmap status to the team.

#### Every Sprint Review
- **Update roadmap checkpoint status** – mark completed roadmap checkpoints as "Achieved."
- **Add new roadmap checkpoints** – if new work emerges, add it to the roadmap.
- **Revise future roadmap checkpoints** – based on the team's velocity and remaining backlog.

#### Every Month
- **Facilitate a roadmap review session** – with the PO and team.
- **Ensure stakeholder alignment** – confirm that the roadmap matches stakeholder expectations.

### Columns & What SM Does With Them

| Column | SM Action |
|--------|-----------|
| **Backlog (roadmap)** | Ensure all future roadmap checkpoints have realistic dates and descriptions. Add notes about assumptions. |
| **Current Sprint** | Update daily – track % complete, add blockers, and adjust if needed. |
| **Next Sprint** | Prepare the next roadmap checkpoint – ensure stories are refined and estimated. |
| **Month 1 / 2 / 3** | Organize roadmap checkpoints – if the team is off-track, suggest moving items between months. |
| **Completed** | Move roadmap checkpoints here when all associated stories are done. Add a summary of what was delivered. |

### Example SM Tasks on Roadmap
- Update "Sprint 2 – Core Features" from 40% to 60% complete.
- Add a comment: "Roadmap checkpoint at risk – team is 1 day behind due to environment issues."
- Create a new roadmap checkpoint: "Hotfix Release – Week 8" for critical bugs found during testing.

---

## 3. ITERATIVE DEVELOPMENT Board

### Purpose
Sprint-level execution – this is the SM's **primary operational board**. It tracks daily progress, blockers, and sprint health.

### SM Responsibilities

#### Daily / Ongoing (CRITICAL)
- **Facilitate the Daily Standup** – use the board as the single source of truth.
- **Move issues** – ensure stories/tasks are moved to the correct columns.
- **Check for stale issues** – if an issue hasn't been updated in 2 days, ask the owner for an update.
- **Monitor the "Blocked" column** – this is the SM's top priority. Investigate and resolve blockers daily.
- **Ensure WIP limits** – if the team has too many "In Progress" items, remind them to focus.
- **Update the burndown** – if using a burndown chart, ensure it reflects reality.

#### Every Sprint Planning
- **Prepare the board** – ensure the backlog is refined and ready.
- **Move selected stories** – from "Ready" to "To Do" during planning.
- **Facilitate the session** – guide the team to break down stories into tasks.
- **Create a Sprint Goal** – add it as a pinned issue or note at the top of the board.
- **Set WIP limits** – agree on limits for "In Progress" and "Review/QA."

#### Every Sprint Review
- **Update the board** – ensure all "Done" stories are correctly moved.
- **Validate completeness** – check that all stories meet the Definition of Done.
- **Close the sprint** – archive or move completed items to a "Closed" column.

#### Every Sprint Retrospective
- **Analyze board data** – review cycle time, throughput, and blocker frequency.
- **Share metrics** – present data to the team (e.g., "We had 5 blockers this sprint").
- **Identify patterns** – if blockers recur, add them to the Retro board for improvement.

### Columns & What SM Does With Them

| Column | SM Action |
|--------|-----------|
| **Backlog** | Ensure the backlog is groomed – check that stories have estimates and labels. |
| **Ready** | This is the SM's most important column – ensure it NEVER runs empty (at least 2 sprints' worth of work). |
| **To Do** | During sprint planning, move selected stories here. Ensure they are assigned to developers. |
| **In Progress** | Monitor daily – if an issue stays here too long, ask the developer for an update. Enforce WIP limits. |
| **Review / QA** | Ensure code reviews happen quickly – remind the Code Owner and developers. |
| **Blocked** | **SM's #1 priority** – investigate daily. Add comments, escalate, and resolve. |
| **Done** | Move stories here only if they meet the Definition of Done. Celebrate! |

### Example SM Tasks on Iterative Development
- At standup, ask: "I see 'User Profile' has been 'In Progress' for 3 days – is it blocked?"
- Move "Fix Login Bug" to "Blocked" because the team is waiting for an API key.
- Enforce WIP limit: if 5 items are "In Progress," ask the team to focus and finish 2 before starting new ones.
- Add a comment: "This story is at risk – please update by EOD."

---

## 4. RETROSPECTIVE Board

### Purpose
Continuous improvement – track what went well, what didn't, and action items for process improvement.

### SM Responsibilities

#### Every Sprint Retrospective (FACILITATOR)
- **Prepare the board** – add initial topics or prompts (e.g., "What slowed us down?").
- **Facilitate the session** – guide the team to add items to "Went Well," "Needs Improvement," and "Action Items."
- **Keep it blameless** – focus on systems, not individuals.
- **Create clear action items** – with owners and due dates.
- **Summarize the retro** – capture key takeaways and share them with the team.

#### Weekly (every Friday)
- **Review the board** – check progress on action items.
- **Follow up** – if an action item is overdue, gently remind the owner.
- **Celebrate progress** – move completed action items to "Done."
- **Add new insights** – if you notice recurring process issues, add them to the board.

#### Throughout the Sprint
- **Track action items** – ensure they are being addressed.
- **If an action item is stuck** – discuss with the team and adjust.
- **Collect data** – gather metrics (velocity, blockers, cycle time) for the next retro.

#### Every Month
- **Review the board** – identify long-term trends.
- **Celebrate wins** – move "Went Well" items to a "Celebrated" column.
- **Revisit old action items** – if they're not done, discuss why.

### Columns & What SM Does With Them

| Column | SM Action |
|--------|-----------|
| **Went Well** | SM encourages the team to add positive items. Add emojis or reactions to celebrate. |
| **Needs Improvement** | SM focuses on actionable items – if vague, ask the team to clarify. |
| **Action Items** | SM ensures each action has an owner and due date. Add labels (e.g., "Process," "Tools," "Team"). |
| **In Progress** | SM updates action items they own – e.g., "Creating a PR template." |
| **Done** | SM moves completed action items here – celebrate with the team. |

### Example SM Tasks on Retrospective
- Add: "Went Well – Daily standups were short and focused."
- Add: "Needs Improvement – PR reviews are taking too long (avg 2 days)."
- Create action: "Agree on a PR review SLA (e.g., 4 hours) – assign to Code Owner."
- Move action: "Set up automated CI checks" to "Done."

---

## Summary Table – SM Activities by Board

| Board | Primary SM Focus | Frequency | Key Actions |
|-------|------------------|-----------|-------------|
| **Team Planning** | Strategic alignment & dependency management | Weekly / Monthly | Flag epic risks, track dependencies, ensure refinement. |
| **Roadmap** | Timeline tracking & forecasting | Daily / Weekly | Update roadmap checkpoint progress, adjust dates, flag slips. |
| **Iterative Development** | Daily execution & blocker removal | Daily (CRITICAL) | Facilitate standup, enforce WIP, unblock, refine backlog. |
| **Retrospective** | Process improvement & team health | Every Sprint / Weekly | Facilitate retro, track action items, share metrics. |

---

## SM's Daily GitHub Routine (Consolidated)

1. **Check Iterative Development (Morning)** – review "Blocked," check "In Progress" ages, ensure board accuracy.
2. **Facilitate Standup** – use the board as the agenda.
3. **Impediment Triage** – investigate all "Blocked" items – escalate/resolve.
4. **Check Roadmap** – update roadmap checkpoint progress if needed.
5. **Check Retrospective** – review action item status.
6. **End-of-day check** – ensure the board is updated for tomorrow's standup.

---

## SM's Weekly GitHub Routine (Every Friday)

1. **Team Planning** – review epic progress, flag risks, check dependencies.
2. **Roadmap** – update roadmap checkpoint progress, adjust dates, forecast completion.
3. **Iterative Development** – ensure the "Ready" column has at least 3–5 refined stories.
4. **Retrospective** – add new insights, follow up on action items, send a summary to the team.
5. **Metrics** – calculate velocity, cycle time, and blocker frequency – share with the team.

---

## SM's Sprint Routine on GitHub

| Event | Actions on GitHub |
|-------|-------------------|
| **Sprint Planning** | Prepare the board – ensure "Ready" is full. Move stories to "To Do." Create Sprint Goal. Facilitate task breakdown. |
| **During Sprint** | Daily – check "Blocked," enforce WIP limits, update board, facilitate standup. |
| **Sprint Review** | Ensure all "Done" stories meet DoD. Move completed roadmap checkpoints to "Achieved." Validate board accuracy. |
| **Sprint Retro** | Prepare the board with prompts. Facilitate the session. Create action items with owners. Share metrics. |

---

## SM's 3-Month Roadmap Checkpoints (by Board)

### Month 1 (Foundation)
- **Team Planning** – ensure all epics are defined and dependencies mapped.
- **Roadmap** – create the initial 3-month timeline with roadmap checkpoints.
- **Iterative Development** – set up the board with WIP limits, labels, and workflows.
- **Retrospective** – facilitate the first retro – establish baseline metrics.

### Month 2 (Optimization)
- **Team Planning** – review epic progress – recommend reprioritization if needed.
- **Roadmap** – adjust roadmap checkpoints based on actual velocity.
- **Iterative Development** – monitor and improve processes – e.g., faster PR reviews.
- **Retrospective** – track that at least 50% of action items are completed.

### Month 3 (Finalization)
- **Team Planning** – ensure all epics are completed or handed off.
- **Roadmap** – finalize the release roadmap checkpoint – track it daily.
- **Iterative Development** – final sprint: ensure all stories meet DoD.
- **Retrospective** – facilitate the final retro – capture lessons learned.

---

## SM Metrics to Track (via GitHub)

| Metric | How to Track | Purpose |
|--------|--------------|---------|
| **Velocity** | Sum of story points per sprint | Forecast future capacity. |
| **Cycle Time** | Time from "In Progress" to "Done" | Identify process bottlenecks. |
| **Blocked Time** | Time spent in "Blocked" column | Measure impediment removal efficiency. |
| **PR Review Time** | Time from PR creation to merge | Improve code review processes. |
| **Burndown** | Remaining work vs. time | Track sprint progress and risks. |
| **Sprint Goal Success** | % of sprints where the goal is met | Measure team effectiveness. |

---

## SM Checklist (Printable)

### Daily
- [ ] Check "Blocked" column – investigate and resolve at least 1 blocker.
- [ ] Facilitate standup – use the board.
- [ ] Ensure all issues are up-to-date (column, assignees, comments).
- [ ] Enforce WIP limits.
- [ ] Check for stale issues (> 2 days no update).
- [ ] Update the board with any new impediments.

### Weekly
- [ ] Review epic progress on Team Planning.
- [ ] Update roadmap checkpoint progress on Roadmap.
- [ ] Ensure "Ready" column has 3–5 stories.
- [ ] Follow up on Retrospective action items.
- [ ] Share velocity and blocker metrics with the team.

### Sprint Events
- [ ] Prepare the board for Sprint Planning.
- [ ] Ensure the Sprint Goal is visible.
- [ ] Validate all "Done" stories meet DoD.
- [ ] Facilitate Retrospective and create action items.

---

**Next:** Tell me which role you want next for GitHub Projects – **Code Owner** or **Developers**.