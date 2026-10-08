# Developers (Team Members) – GitHub Projects Usage & Responsibilities

## Overview
Developers use GitHub Projects as their primary tool for day-to-day work – tracking tasks, collaborating on code, updating progress, and ensuring transparency. Developers are the **execution engine** – they own their tasks, keep boards updated, participate in all Scrum events, and ensure the product increment is potentially releasable at the end of each sprint.

Below is a detailed breakdown of exactly what Developers do on **each of the 4 GitHub Project boards**.

**MacroCrypto AI practice:** Sprints live on [Team Workflow #6](https://github.com/orgs/TheQuintet/projects/6) via the **Sprint** field. We do **not** use GitHub Issues milestones on the repo.

---

## 1. TEAM PLANNING Board

### Purpose
High-level strategic planning – epics, themes, major roadmap checkpoints, and release-level coordination.

### Developers' Responsibilities

#### Daily / Ongoing
- **Review the board** – understand the big picture and how your work fits into epics.
- **Check upcoming epics** – anticipate what's coming in the next 1–2 sprints.
- **Flag technical concerns** – if an epic seems technically challenging, comment early.

#### Weekly (every Friday)
- **Review epic progress** – understand how your completed stories contribute to epic goals.
- **Provide technical input** – if an epic lacks technical details, add comments or suggest subtasks.
- **Prepare for upcoming epics** – read the descriptions and ask questions early.

#### Every Sprint Planning
- **Understand epic context** – know why this epic matters and how it impacts the product.
- **Ask clarifying questions** – if an epic is vague, request more details from the PO.

#### Every Month
- **Review epic completion** – celebrate epics you contributed to.
- **Provide feedback** – if epics are too large or unclear, suggest improvements.

### Columns & What Developers Do With Them

| Column | Developers' Action |
|--------|-------------------|
| **Backlog (Epics)** | Read epic descriptions – understand the business value and scope. |
| **Next Up (Epics)** | Prepare mentally – research technologies or patterns you'll need. |
| **In Progress (Epics)** | Track how your current sprint stories align with epic goals. |
| **Blocked** | If an epic you're working on is blocked, add a comment explaining the blocker. |
| **Done / Released** | Celebrate – you helped deliver this epic! |

### Example Developers' Tasks on Team Planning
- Read the "Payment Integration" epic – research Stripe API before the sprint starts.
- Comment on "Reporting Dashboard" epic: "We'll need a new database index for performance."
- Flag that the "User Profiles" epic is blocked because the design team hasn't delivered mockups.

---

## 2. ROADMAP Board

### Purpose
Timeline view – shows the project schedule, key roadmap checkpoints, and release dates over the 3-month horizon.

### Developers' Responsibilities

#### Daily / Ongoing
- **Check the board** – know the deadlines and plan your work accordingly.
- **Update your tasks** – ensure your progress is reflected so the board stays accurate.
- **Flag timeline risks** – if you think a roadmap checkpoint is at risk, speak up early.

#### Weekly (every Friday)
- **Review roadmap checkpoint progress** – check if you're on track to meet deadlines.
- **Adjust your pace** – if you're ahead, pick up extra tasks; if behind, ask for help.
- **Add comments** – if a roadmap checkpoint seems unrealistic, provide constructive feedback.

#### Every Sprint Review
- **Review roadmap checkpoint updates** – see what was achieved and what moved to the next sprint.
- **Celebrate roadmap checkpoint completions** – recognize the team's progress.

#### Every Month
- **Review the overall timeline** – understand the 3-month plan and your role in it.
- **Provide feedback** – if dates seem unrealistic, discuss with the team.

### Columns & What Developers Do With Them

| Column | Developers' Action |
|--------|-------------------|
| **Backlog (roadmap)** | Know what's coming – prepare mentally and technically. |
| **Current Sprint** | Track your daily progress – update your tasks to keep the roadmap checkpoint accurate. |
| **Next Sprint** | Prepare – start refining stories so they're ready. |
| **Month 1 / 2 / 3** | Understand the big picture – plan your work accordingly. |
| **Completed** | Celebrate – you helped deliver this roadmap checkpoint! |

### Example Developers' Tasks on Roadmap
- Update a task: "User Login API" – change from 50% to 80% complete.
- Comment on "Sprint 2 – Core Features" roadmap checkpoint: "We might be 1 day behind – I'll work extra to catch up."
- Check that "Month 3 – Polish & Release" is approaching – start thinking about final testing.

---

## 3. ITERATIVE DEVELOPMENT Board

### Purpose
Sprint-level execution – this is the Developers' **primary operational board**. It tracks daily work, progress, and collaboration.

### Developers' Responsibilities

#### Daily / Ongoing (CRITICAL)
- **Update your tasks** – move issues between columns as you work:
  - **To Do** → **In Progress** – when you start working.
  - **In Progress** → **Review/QA** – when you finish coding and create a PR.
  - **Review/QA** → **Done** – only if the Code Owner approves and you've merged.
- **Check comments** – respond to questions from the PO, SM, or Code Owner.
- **Check "Blocked" column** – if you're blocked, move your issue there and add a comment.
- **Review PRs** – check the "Review/QA" column for PRs from teammates – review them promptly.
- **Update progress daily** – leave comments like: "WIP – 60% done, tests passing."

#### Every Sprint Planning
- **Select your tasks** – move them from "Ready" to "To Do."
- **Break down stories** – create technical subtasks.
- **Estimate** – participate in story point estimation.
- **Commit to tasks** – be realistic about what you can achieve.

#### Every Sprint Review
- **Demo your work** – show what you accomplished.
- **Move accepted stories** – only if the PO approves them.
- **Move incomplete stories** – to the next sprint's backlog.

#### Every Sprint Retrospective
- **Share feedback** – what went well/badly for you.
- **Propose improvements** – e.g., "We need better test data."
- **Commit to action items** – personal improvements.

### Columns & What Developers Do With Them

| Column | Developers' Action |
|--------|-------------------|
| **Backlog** | Read stories – understand them and ask questions early. |
| **Ready** | Pick stories that are refined and ready to work on. |
| **To Do** | Move stories here during sprint planning – these are your commitments. |
| **In Progress** | **Your primary column** – move your story here when you start working. Update daily with comments. |
| **Review / QA** | Move your story here when you create a PR. Ask the Code Owner for a review. Review teammates' PRs. |
| **Blocked** | If you're stuck for > 1 hour, move your story here. Add a comment explaining the blocker. |
| **Done** | Only move stories here if: tests pass, PR is approved, merged, and the PO accepts. |

### Example Developers' Tasks on Iterative Development
- Move "User Login API" from "To Do" to "In Progress" – start coding.
- Comment on "Payment Processing": "WIP – 80% done, need to fix edge case."
- Move "Fix 2FA Bug" to "Blocked" – waiting for SM to get API access.
- Review a PR from another developer – add comments and approve.

---

## 4. RETROSPECTIVE Board

### Purpose
Continuous improvement – track what went well, what didn't, and action items for process improvement.

### Developers' Responsibilities

#### Every Sprint Retrospective
- **Add items** – what went well, what didn't, what you want to improve.
- **Be honest and blameless** – focus on systems, not people.
- **Vote on action items** – prioritize the most impactful improvements.
- **Commit to personal action items** – e.g., "I will write more tests."

#### Weekly (every Friday)
- **Review action items** – check progress on the ones you own.
- **Update status** – move your action items between columns.
- **Add new insights** – if you notice recurring issues, add them to the board.

#### Throughout the Sprint
- **Track your action items** – ensure you're making progress.
- **Ask for help** – if an action item is stuck, discuss with the team.
- **Celebrate wins** – when an action item is completed, celebrate!

### Columns & What Developers Do With Them

| Column | Developers' Action |
|--------|-------------------|
| **Went Well** | Add positive items – e.g., "Great team collaboration on the dashboard." |
| **Needs Improvement** | Add constructive items – e.g., "PR reviews are taking too long." |
| **Action Items** | Add personal actions – e.g., "I will review at least 2 PRs daily." Assign to yourself. |
| **In Progress** | Update actions you own – e.g., "Started reviewing PRs every morning." |
| **Done** | Move completed actions – e.g., "Reached 80% test coverage." |

### Example Developers' Tasks on Retrospective
- Add: "Went Well – Got good support from teammates when stuck."
- Add: "Needs Improvement – I didn't update the board enough this sprint."
- Create action: "I will update my task status every morning and afternoon."
- Move action: "Set up local test environment" to "Done."

---

## Summary Table – Developers' Activities by Board

| Board | Primary Developers' Focus | Frequency | Key Actions |
|-------|---------------------------|-----------|-------------|
| **Team Planning** | Big-picture awareness | Weekly / Monthly | Read epics, flag technical concerns, prepare for upcoming work. |
| **Roadmap** | Timeline awareness | Weekly / Sprint Review | Track deadlines, flag risks, adjust pace. |
| **Iterative Development** | Daily execution | Daily (CRITICAL) | Update tasks, code, review PRs, move issues, unblock. |
| **Retrospective** | Continuous improvement | Every Sprint / Weekly | Add feedback, commit to actions, track progress. |

---

## Developers' Daily GitHub Routine (Consolidated)

### Morning (Pre-Standup – 10 min)
1. **Check Iterative Development** – review your tasks.
2. **Update your tasks** – if you worked late, move them to the correct column.
3. **Check comments** – respond to any questions.
4. **Prepare for standup** – know what you'll say.

### During Standup (15 min)
- Use the board to report:
  - What I did yesterday.
  - What I'll do today.
  - Any blockers.

### After Standup (Ongoing)
1. **Start your first task** – move it to "In Progress."
2. **Code and test** – write code, run tests, commit frequently.
3. **Check comments/PRs** – respond to teammates within 1 hour.
4. **Review at least 2 PRs** – check the "Review/QA" column.
5. **Update the board** – move issues, add comments, change statuses.

### End of Day (10 min)
1. **Update all tasks** – ensure board reflects your progress.
2. **Push code** – commit and push before leaving.
3. **Leave comments** – if you're stuck, add a comment and tag the SM/Code Owner.
4. **Plan tomorrow** – know what you'll work on next.

---

## Developers' Weekly GitHub Routine (Every Friday)

1. **Team Planning** – review upcoming epics – prepare mentally.
2. **Roadmap** – check if you're on track – adjust pace if needed.
3. **Iterative Development** – ensure all your tasks are updated for the week.
4. **Retrospective** – add any feedback, update action items.
5. **Clean up** – close stale issues, update documentation.

---

## Developers' Sprint Routine on GitHub

| Event | Actions on GitHub |
|-------|-------------------|
| **Sprint Planning** | Move selected stories to "To Do." Break down into subtasks. Estimate. Commit to deliverables. |
| **During Sprint** | Daily – update tasks, code, review PRs, move issues, unblock. |
| **Sprint Review** | Demo your work. Move accepted stories to "Done." Move incomplete stories to backlog. |
| **Sprint Retro** | Add feedback. Create action items. Commit to improvements. |

---

## Developers' 3-Month Roadmap Checkpoints (by Board)

### Month 1 (Ramp-up)
- **Team Planning** – understand all epics – know the big picture.
- **Roadmap** – understand the timeline – know the deadlines.
- **Iterative Development** – establish good habits – update board daily, write tests, review PRs.
- **Retrospective** – start adding feedback – help improve processes early.

### Month 2 (Ownership)
- **Team Planning** – take ownership of at least 1 epic – contribute to technical decisions.
- **Roadmap** – track your roadmap checkpoints – ensure you're on schedule.
- **Iterative Development** – be a strong reviewer – help teammates improve code quality.
- **Retrospective** – follow through on action items – show personal growth.

### Month 3 (Delivery)
- **Team Planning** – help close all epics – ensure no loose ends.
- **Roadmap** – meet all deadlines – help with final release tasks.
- **Iterative Development** – final push – fix bugs, polish, test thoroughly.
- **Retrospective** – final retro – capture lessons learned for future projects.

---

## Developers' Collaboration Principles (via GitHub)

| Principle | How to Apply on GitHub |
|-----------|------------------------|
| **Be transparent** | Update boards daily – don't hide delays. |
| **Help others** | Review PRs quickly – unblock teammates. |
| **Ask for help** | If stuck > 1 hour, move to "Blocked" and tag the SM. |
| **Celebrate wins** | Mark "Done" stories – acknowledge progress. |
| **Improve continuously** | Use the Retro board – commit to actions. |
| **Own your work** | Move tasks, add comments, be responsible. |

---

## Developers' Checklist (Printable)

### Daily
- [ ] Update all tasks on Iterative Development (morning and afternoon).
- [ ] Move issues: To Do → In Progress → Review/QA → Done.
- [ ] Review at least 2 PRs from teammates.
- [ ] Respond to comments on your PRs.
- [ ] Check "Blocked" – move your blocked issues there.
- [ ] Write tests for all new code.
- [ ] Commit and push at least twice a day.
- [ ] Update comments on your tasks (progress, blockers, questions).

### Weekly
- [ ] Review upcoming epics on Team Planning.
- [ ] Check roadmap checkpoint deadlines on Roadmap.
- [ ] Ensure all your tasks are updated for the week.
- [ ] Add feedback to Retrospective.
- [ ] Update your action items.

### Sprint Events
- [ ] Participate in Sprint Planning – move stories to "To Do."
- [ ] Demo your work in Sprint Review.
- [ ] Move accepted stories to "Done."
- [ ] Add feedback to Retrospective.
- [ ] Commit to action items.

---

## Developers' Definition of Done (DoD) Checklist

Before moving a story to "Done," ensure:

- [ ] Code is written and pushed.
- [ ] All tests pass locally.
- [ ] Unit/integration tests are written for new code.
- [ ] Test coverage is not reduced.
- [ ] PR is created and linked to the issue.
- [ ] PR is reviewed and approved (by Code Owner or another developer).
- [ ] CI/CD pipeline passes all checks.
- [ ] Issue is updated with comments and moved to "Review/QA."
- [ ] PO reviews and accepts the story.
- [ ] Code is merged into the main branch.
- [ ] Issue is moved to "Done."

---

## Summary – All Roles at a Glance (GitHub Projects)

| Role | Primary Board | Daily Focus | Weekly Focus |
|------|---------------|-------------|--------------|
| **Product Owner** | Iterative Development | Prioritize backlog, accept/reject stories, refine requirements | Update epics, roadmap, prepare backlog |
| **Scrum Master** | Iterative Development | Facilitate standup, unblock, enforce WIP, update board | Review metrics, refine backlog, track action items |
| **Code Owner** | Iterative Development | Review PRs, enforce quality, check CI, unblock technical issues | Technical epics, roadmap checkpoints, debt management |
| **Developers** | Iterative Development | Update tasks, code, test, review PRs, move issues | Review epics, check deadlines, add retro feedback |

---

**All roles are now fully defined for GitHub Projects.**  
You have a complete breakdown for:
- 1 Product Owner
- 1 Scrum Master
- 1 Code Owner
- 2 Developers

If you need a consolidated cheat sheet (1-page summary for all roles), or if you want to adjust anything (e.g., specific tech stack, CI/CD setup, branching strategy), just let me know!