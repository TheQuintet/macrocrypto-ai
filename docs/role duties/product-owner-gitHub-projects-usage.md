# Product Owner – GitHub Projects Usage & Responsibilities

## Overview
The Product Owner (PO) uses GitHub Projects as the primary tool to manage the product backlog, communicate priorities, track progress toward release goals, and ensure transparency with stakeholders. Below is a detailed breakdown of exactly what the PO does on **each of the 4 GitHub Project boards**.

**MacroCrypto AI practice:** Sprints live on [Team Workflow #6](https://github.com/orgs/TheQuintet/projects/6) via the **Sprint** field. We do **not** use GitHub Issues milestones on the repo.

---

## 1. TEAM PLANNING Board

### Purpose
High-level strategic planning – epics, themes, major roadmap checkpoints, and release-level coordination.

### PO Responsibilities

#### Daily / Ongoing
- **Review the board** – ensure it reflects the current strategic direction.
- **Add new epics/themes** as they emerge from stakeholder feedback or market changes.
- **Reorganize epics** – drag and drop to reflect shifting business priorities.
- **Link epics to issues** – ensure every epic has at least one associated user story.

#### Weekly (every Friday)
- **Update epic descriptions** – clarify business value, target users, and success metrics.
- **Review roadmap checkpoint dates** – adjust if scope or velocity changes.
- **Add/remove epics** based on the 3-month roadmap – if an epic won't fit, move it to a "Future" column.

#### Every Sprint Planning
- **Verify epic readiness** – ensure the top epics for the next sprint have refined stories.
- **Check dependencies** – ensure epics are sequenced logically (e.g., "Authentication" before "User Dashboard").

#### Every Month
- **Conduct a roadmap review** – present the board to stakeholders (internal or external).
- **Reprioritize epics** based on new feedback or market shifts.
- **Archive completed epics** – move them to a "Done/Released" column.

### Columns & What PO Does With Them

| Column | PO Action |
|--------|-----------|
| **Backlog (Epics)** | Add new epics with clear titles, descriptions, and business value. Prioritize by dragging up/down. |
| **Next Up (Epics)** | Move epics that are ready for the upcoming 1–2 sprints. Ensure they have refined stories. |
| **In Progress (Epics)** | Move epics when their first story is started – track overall epic progress. |
| **Blocked** | Move epics that are stalled – add a comment explaining the blocker and action plan. |
| **Done / Released** | Move epics only when ALL associated stories are completed and released. |

### Example PO Tasks on Team Planning
- Create an epic: "MVP Core Features" with 5 associated user stories.
- Create a roadmap checkpoint: "Sprint 1-3 MVP" and link all stories to it.
- Add a new epic: "Payment Integration" – reprioritize it above "Advanced Reporting" based on stakeholder demand.

---

## 2. ROADMAP Board

### Purpose
Timeline view – shows the project schedule, key roadmap checkpoints, and release dates over the 3-month horizon.

### PO Responsibilities

#### Daily / Ongoing
- **Check the board** – ensure all roadmap checkpoints are up-to-date.
- **Adjust dates** if the team is ahead or behind schedule.
- **Flag risks** – add notes to roadmap checkpoints that are at risk of slipping.

#### Weekly (every Friday)
- **Update roadmap checkpoint progress** – add % complete or number of stories done/total.
- **Communicate changes** – if a release date shifts, update the board and notify the team.
- **Review the 3-month timeline** – ensure it remains realistic based on velocity.

#### Every Sprint Review
- **Update the board** – mark completed roadmap checkpoints as "Achieved."
- **Add new roadmap checkpoints** for any newly discovered work (e.g., "Hotfix Release").
- **Adjust future roadmap checkpoints** based on the team's velocity and remaining scope.

#### Every Month
- **Present the roadmap** to stakeholders (visual timeline).
- **Re-baseline** – if scope changes significantly, recreate the timeline.

### Columns & What PO Does With Them

| Column | PO Action |
|--------|-----------|
| **Backlog (roadmap)** | Add future roadmap checkpoints with target dates (e.g., "Alpha Release – Month 2"). |
| **Current Sprint** | Link the current sprint roadmap checkpoint – track daily progress. |
| **Next Sprint** | Prepare the next sprint roadmap checkpoint – ensure stories are refined. |
| **Month 1 / 2 / 3** | Organize roadmap checkpoints by month – drag to adjust timing. |
| **Completed** | Move roadmap checkpoints when all associated stories are delivered. |

### Example PO Tasks on Roadmap
- Create a roadmap checkpoint: "Month 1 – Foundation (Auth + User Profiles)" with target date end of Month 1.
- Add a roadmap checkpoint: "Month 2 – Core Features (Dashboard + Reports)".
- If the team is behind, drag "Month 3 – Polish & Release" later by 1 week.

---

## 3. ITERATIVE DEVELOPMENT Board

### Purpose
Sprint-level execution – this is the PO's main operational board. It tracks user stories, tasks, and day-to-day progress.

### PO Responsibilities

#### Daily / Ongoing
- **Prioritize the backlog** – drag stories up/down within the "Backlog" column to reflect real-time priorities.
- **Review "In Progress" stories** – check if they are stuck or need clarification.
- **Respond to comments** – answer questions on issues within 2–4 hours.
- **Accept or reject stories** in the "Review/QA" column – close them with feedback.
- **Ensure the "Ready" column** has at least 3–5 refined stories for the next sprint.

#### Every Sprint Planning
- **Select stories** for the sprint – move them from "Backlog" to "Ready" (if not already).
- **Confirm the Sprint Goal** – add it as a pinned note at the top of the board.
- **Ensure each story has** – acceptance criteria, estimates, and subtasks.

#### Every Sprint Review
- **Review all "Done" stories** – ensure they meet acceptance criteria.
- **Close accepted stories** – move to "Done" or "Closed."
- **Reject stories** – move them back to "Backlog" with a comment on what's missing.
- **Move incomplete stories** – to the next sprint's backlog.

#### Throughout the Sprint
- **Monitor the burndown** (if available) – adjust priorities if the team is falling behind.
- **Add new urgent stories** – if a critical bug or stakeholder request appears, add it and prioritize.
- **Swap stories** – if a story is blocked, replace it with a lower-priority one (with team agreement).

### Columns & What PO Does With Them

| Column | PO Action |
|--------|-----------|
| **Backlog** | The main backlog – PO constantly reprioritizes by dragging. |
| **Ready** | Stories that are refined (AC, estimates, subtasks). PO ensures this is never empty. |
| **To Do** | Stories selected for the current sprint. PO verifies they align with the Sprint Goal. |
| **In Progress** | PO monitors – checks comments, answers questions, unblocks. |
| **Review / QA** | PO's primary daily focus – accepts or rejects stories. |
| **Blocked** | PO adds blocker description and works with SM to resolve. |
| **Done** | PO moves accepted stories here – they are potentially releasable. |

### Example PO Tasks on Iterative Development
- Move "User Login" from "Backlog" to "Ready" and add acceptance criteria.
- Review "Payment Processing" in "Review/QA" – reject it because tax calculation is wrong.
- Add a new urgent story: "Fix 2FA timeout bug" – drag it to the top of "Backlog."
- During sprint planning, move 8 stories from "Ready" to "To Do."

---

## 4. RETROSPECTIVE Board

### Purpose
Continuous improvement – track what went well, what didn't, and action items for process improvement.

### PO Responsibilities

#### Every Sprint Retrospective
- **Add items** to the board during the retro session – what went well, what didn't, and improvement ideas.
- **Focus on product-related issues** – e.g., unclear requirements, changing priorities, stakeholder feedback.
- **Commit to 1–2 action items** – e.g., "I will add more detailed acceptance criteria," or "I will hold a weekly stakeholder sync."

#### Weekly (every Friday)
- **Review the board** – check progress on action items.
- **Update the status** of action items – mark as "In Progress" or "Done."
- **Add new insights** – if you notice recurring issues, add them to the board.

#### Throughout the Sprint
- **Track action items** – ensure they are being addressed.
- **If an action item is stuck** – discuss with the team or SM.
- **Celebrate successes** – move "Went Well" items to a "Celebrated" column.

### Columns & What PO Does With Them

| Column | PO Action |
|--------|-----------|
| **Went Well** | PO adds positive feedback – e.g., "Good clarity on requirements this sprint." |
| **Needs Improvement** | PO adds product-related issues – e.g., "Stories lack edge-case acceptance criteria." |
| **Action Items** | PO adds specific actions – e.g., "Create a template for user stories." Assign to themselves if applicable. |
| **In Progress** | PO updates action items they own – e.g., "Drafting the user story template." |
| **Done** | PO moves completed action items here – e.g., "Template created and shared." |

### Example PO Tasks on Retrospective
- Add: "Went Well – Stakeholder demo was well received."
- Add: "Needs Improvement – Acceptance criteria were too vague for Story #42."
- Add action: "I will review all backlog stories and add missing AC by Friday."
- Mark "Action: Weekly PO sync with team" as Done.

---

## Summary Table – PO Activities by Board

| Board | Primary PO Focus | Frequency | Key Actions |
|-------|------------------|-----------|-------------|
| **Team Planning** | Strategy & epics | Weekly / Monthly | Add epics, link stories, reprioritize based on roadmap. |
| **Roadmap** | Timeline & roadmap checkpoints | Weekly / Sprint Review | Update dates, add/remove roadmap checkpoints, track release progress. |
| **Iterative Development** | Day-to-day backlog & sprint execution | Daily / Sprint Planning | Prioritize backlog, refine stories, accept/reject, unblock. |
| **Retrospective** | Continuous improvement | Every Sprint / Weekly | Add retro items, track action items, improve product processes. |

---

## PO's Daily GitHub Routine (Consolidated)

1. **Check Iterative Development** – respond to comments, review "Review/QA" stories, reprioritize backlog.
2. **Check Team Planning** – ensure epics are up-to-date and aligned with the roadmap.
3. **Check Roadmap** – verify roadmap checkpoint dates and progress.
4. **Check Retrospective** – review progress on your action items.
5. **Update any boards** – if you changed priorities or accepted/rejected stories.

---

## PO's Weekly GitHub Routine (Every Friday)

1. **Team Planning** – review epics, add/remove, re-prioritize.
2. **Roadmap** – update roadmap checkpoint progress, adjust dates if needed.
3. **Iterative Development** – ensure the backlog has 3–5 "Ready" stories for next sprint.
4. **Retrospective** – add any new insights, update action item status.

---

## PO's Sprint Routine on GitHub

| Event | Actions on GitHub |
|-------|-------------------|
| **Sprint Planning** | Move stories from "Backlog" → "Ready" → "To Do." Ensure AC and estimates exist. |
| **During Sprint** | Daily – review "Review/QA," answer comments, reprioritize if needed. |
| **Sprint Review** | Accept/reject stories in "Review/QA." Close accepted ones. Move incomplete ones to backlog. |
| **Sprint Retro** | Add items to the Retro board. Create action items. Commit to improvements. |

---

## PO's 3-Month Roadmap Checkpoints (by Board)

### Month 1
- **Team Planning** – define all epics for MVP.
- **Roadmap** – create initial 3-month timeline with 3 major roadmap checkpoints.
- **Iterative Development** – ensure Sprint 1 and 2 backlogs are fully refined.
- **Retrospective** – establish baseline – what's working/not working.

### Month 2
- **Team Planning** – re-prioritize epics based on feedback.
- **Roadmap** – adjust remaining roadmap checkpoints based on velocity.
- **Iterative Development** – focus on high-value features; accept/reject aggressively.
- **Retrospective** – act on at least 2 improvement actions.

### Month 3
- **Team Planning** – finalize all epics; archive completed ones.
- **Roadmap** – ensure the final release roadmap checkpoint is on track.
- **Iterative Development** – final sprint: only critical bugs and polish.
- **Retrospective** – final retro – capture lessons learned.

---

**Next:** Tell me which role you want next for GitHub Projects – **Scrum Master**, **Code Owner**, or **Developers**.