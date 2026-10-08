# Developer (Team Member) – Clear Duties & Daily Tasks (3-Month Project)

## Core Responsibilities (High-Level)
- Deliver high-quality, tested, and maintainable code.
- Self-organize and take ownership of user stories and tasks.
- Collaborate with the team – pair programming, knowledge sharing, and code reviews.
- Adhere to coding standards, architecture, and Definition of Done.
- Proactively communicate progress, blockers, and risks.
- Contribute to backlog refinement, planning, and retrospectives.
- Ensure the product increment is potentially releasable at the end of each sprint.

---

## Daily / Every-Sprint Tasks (Routine)

### Every Day (Full day – ~6 hours of focused work)
1. **Daily Standup (15 min)**  
   - Be on time – share what you did yesterday, what you'll do today, and any blockers.  
   - Listen to others – offer help if you can.  
   - Keep it brief – no deep technical discussions (take those offline).

2. **Sprint Backlog Work (4–5 hours)**  
   - Pick the next highest-priority task from the "In Progress" or "To Do" column.  
   - Break down tasks into small, testable chunks (≤ 4 hours of work).  
   - Write clean, well-commented, and testable code.  
   - Run tests locally before pushing – ensure nothing breaks.  
   - Commit frequently with meaningful commit messages (conventional commits).  
   - Push code at least twice a day – avoid long-lived branches.

3. **Code Review (30–60 min)**  
   - Review at least 2–3 PRs from other developers daily.  
   - Be respectful and constructive – suggest improvements, not just criticism.  
   - Look for: logic errors, test coverage, security, performance, and readability.  
   - Approve or request changes – respond to comments on your own PRs promptly.

4. **Testing & Quality Assurance (30–60 min)**  
   - Write unit/integration tests for all new code (aim for ≥ 80% coverage).  
   - Perform manual exploratory testing for your own changes (edge cases).  
   - Ensure no regression – run the full test suite before marking a story "Done."

5. **Documentation (15–30 min)**  
   - Update README, API docs, or inline comments when changing behavior.  
   - Document any new environment variables, setup steps, or gotchas.  
   - Update the team on any configuration changes.

6. **Collaboration & Support (30 min)**  
   - Pair program with a teammate if they're stuck – even 15 min helps.  
   - Answer questions in team chat – share knowledge proactively.  
   - Escalate blockers to the Scrum Master if not resolved within 2 hours.

7. **End-of-Day Check (10 min)**  
   - Update your task status on the GitHub Project board.  
   - Push any work-in-progress (with [WIP] label or draft PR).  
   - Note what you'll work on tomorrow – leave a comment on the issue.

---

### Every Sprint Planning Day (first day of each sprint – 2–3 hours)
- **Before planning:**  
  - Review the proposed backlog items – understand business value.  
  - Assess technical feasibility and complexity.  
  - Prepare questions for the PO about unclear requirements.  
- **During planning:**  
  - Estimate stories using story points (or t-shirt sizing) – be honest about capacity.  
  - Commit to tasks you are confident you can complete.  
  - Break stories into subtasks and assign yourself to at least 1–2.  
  - Ask clarifying questions – ensure you understand the acceptance criteria.  
- **After planning:**  
  - Move your assigned tasks to "To Do" or "In Progress."  
  - Set up any local environment needed for new features.

---

### Every Sprint Review Day (last day of each sprint – 1 hour)
- **Before review:**  
  - Ensure all your tasks are "Done" (meet Definition of Done).  
  - Prepare a short demo of your work (if applicable).  
  - Check that your code is merged and deployed to a review environment.  
- **During review:**  
  - Demo your features – show how they work and meet acceptance criteria.  
  - Be open to feedback – capture new requirements or changes.  
  - Celebrate team accomplishments.  
- **After review:**  
  - Close any completed issues – mark them as "Done."  
  - Move leftover tasks to the next sprint backlog.

---

### Every Sprint Retrospective (immediately after review – 45 min)
- **During retro:**  
  - Share what went well and what could be improved (process, tools, collaboration).  
  - Be honest and blameless – focus on systems, not individuals.  
  - Propose actionable improvements – e.g., "let's automate this manual step."  
  - Commit to 1–2 personal action items.  
- **After retro:**  
  - Implement your action items during the next sprint.  
  - Follow up on previous retro improvements.

---

## Weekly Tasks (every Friday, 1 hour)
1. **Backlog Refinement (with team)**  
   - Help the PO and SM refine upcoming stories – add technical details.  
   - Identify dependencies, risks, and assumptions.  
   - Provide effort estimates for future stories.

2. **Codebase Familiarity**  
   - Explore parts of the code you don't usually work on – improve bus factor.  
   - Review at least one architectural document or design decision.

3. **Personal Skill Development (30 min)**  
   - Learn something new – watch a talk, read a blog, practice a new pattern.  
   - Share findings with the team (quick 5-min brownbag session).

4. **Environment & Tooling Maintenance**  
   - Update your local development environment – install new dependencies.  
   - Check that your IDE/linters are configured correctly.

5. **Peer Feedback**  
   - Give constructive feedback to at least one teammate (privately or publicly).  
   - Thank someone for good work – positive reinforcement.

---

## One-Time / Monthly Tasks (over 3 months)

### Month 1 (Ramp-up & Foundation)
- **Set up local development environment** – follow the team's setup guide.  
- **Learn the codebase** – understand the high-level architecture and key modules.  
- **Establish good habits** – write tests, commit frequently, update boards.  
- **Contribute to at least 3 code reviews** – learn the standards.  
- **Create a personal "cheat sheet"** of common commands and workflows.

### Month 2 (Iteration & Ownership)
- **Take ownership of at least 1 complex feature** – from design to deployment.  
- **Improve test coverage** in a legacy module – reduce technical debt.  
- **Propose and implement 1 process improvement** (e.g., better CI steps).  
- **Mentor another developer** (if paired with a junior).  
- **Write at least 1 technical documentation page** (e.g., API guide).

### Month 3 (Finalisation & Delivery)
- **Focus on bug-fixing and polishing** – ensure all edge cases handled.  
- **Help with deployment** – verify production readiness.  
- **Perform end-to-end testing** – simulate real user workflows.  
- **Prepare for handover** – update all documentation and comments.  
- **Participate in the final release** – ensure a smooth delivery.

---

## Decision-Making Rules (for Developers)
- **If stuck for > 30 min** – ask for help (team chat, pair programming).  
- **If unsure about requirements** – ask the PO immediately (do not assume).  
- **If a task is too large** – break it down further and discuss with the team.  
- **If you break the build** – fix it within 1 hour or revert your changes.  
- **If you see technical debt** – create an issue and discuss with the Code Owner.  
- **If a PR has 2 approvals** – merge it (after ensuring CI passes).  
- **If you need to cut corners** – leave a TODO comment and create a follow-up issue.

---

## Tools & Boards Usage (Github Projects)
| Board | Developer’s Responsibility |
|-------|----------------------------|
| **Team Planning** | Understand epics and sprint goals – align your work accordingly. |
| **Roadmap** | Be aware of deadlines – plan your work to meet them. |
| **Iterative Development** | Your main board – update it daily: To Do → In Progress → Review → Done. |
| **Retrospective** | Actively participate – add items and follow up on actions. |

---

## Daily Checklist (printable)
- [ ] Attend standup – report clearly and listen to others.  
- [ ] Update your task status on the project board.  
- [ ] Write / update tests for your code.  
- [ ] Run the full test suite before pushing.  
- [ ] Review at least 2 PRs from teammates.  
- [ ] Respond to comments on your own PRs.  
- [ ] Commit and push code at least twice.  
- [ ] Log any blocker or risk to the Scrum Master.  
- [ ] Document any new code or configuration.  
- [ ] End-of-day: update board and plan tomorrow's task.

---

## Success Criteria for Developers (by end of 3 months)
- All committed stories are "Done" by the sprint end (≥ 90% completion rate).  
- Test coverage of your code ≥ 80% (or team agreed target).  
- PR review turnaround time ≤ 4 hours for your PRs.  
- You have reviewed at least 50 PRs total.  
- You have contributed to at least 2 team process improvements.  
- You can explain the overall architecture to a new team member.  
- You have delivered at least 1 end-to-end feature independently.  
- You have helped at least 2 teammates unblock themselves.

---

## Team Collaboration Principles
- **Pair when stuck** – two heads are better than one.  
- **Share knowledge** – don't be a bus factor of 1.  
- **Be transparent** – report delays early, not at the deadline.  
- **Celebrate wins** – small victories matter.  
- **Respect the process** – follow Scrum events and board updates.  
- **Be kind** – code review is about the code, not the person.

---

## Summary Table – Role Breakdown (for quick reference)

| Role | Main Focus | Key Daily Task |
|------|------------|----------------|
| **Product Owner** | What to build | Backlog priority & requirement clarity |
| **Scrum Master** | How to build it right | Facilitate, remove blockers, coach |
| **Code Owner** | Quality & architecture | Review PRs, CI/CD, technical debt |
| **Developers (2)** | Build it | Write code, tests, review, collaborate |

---

**All roles are now defined.**  
You have a complete set of responsibilities for your 5-person team:
- 1 Product Owner  
- 1 Scrum Master  
- 1 Code Owner  
- 2 Developers  

If you need any adjustments (e.g., shorter daily tasks, specific tech stack guidance, or a combined "developer + code owner" hybrid), just let me know!