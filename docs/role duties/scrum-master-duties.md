# Scrum Master (SM) – Clear Duties & Daily Tasks (3-Month Project)

**MacroCrypto AI practice:** After a **Slack discussion** in `#capstone-project-group`, the team agreed **not** to run a daily standup (live or required offline/async posts). **Loredana Lungu** (SM) found the textbook “daily SM” routine difficult to sustain without that touchpoint. In practice the SM focused on the **weekly Capstone sync**, **GitHub board** hygiene, meeting notes, and blockers when they surfaced — see [Coordination without daily standup](../project-workflow.md#coordination-without-daily-standup-domain-slack). The daily task lists below are a **reference template**, not what we ran day to day.

## Core Responsibilities (High-Level)
- Ensure the Scrum framework is understood and enacted by the team.
- Remove impediments that block the development team's progress.
- Facilitate all Scrum events (standups, planning, review, retrospective).
- Shield the team from external distractions and interference.
- Coach the team in self-organization and cross-functionality.
- Improve team velocity and process efficiency.
- Maintain the Scrum boards and ensure they reflect reality.

---

## Daily / Every-Sprint Tasks (Routine)

### Every Day (30–45 min total)
1. **Morning Standup Facilitation (Daily Scrum – 15 min)**  
   - Start on time (same time every day).  
   - Ask the 3 questions:  
     *What did I do yesterday?*  
     *What will I do today?*  
     *Any impediments?*  
   - Keep it focused – no deep problem-solving during standup (parking lot).  
   - Note any blockers and assign follow-up actions.

2. **Impediment Triage (15 min after standup)**  
   - Review all blockers mentioned during standup.  
   - Take ownership of removing them (e.g., escalate, clarify requirements, unblock CI/CD, arrange access).  
   - Update the “Retrospective” board with recurring impediments.

3. **GitHub Projects Hygiene (10 min)**  
   - Ensure the “Iterative Development” board matches the actual sprint backlog.  
   - Move any stalled issues to “Blocked” column and add a comment with the reason.  
   - Verify that all sub-issues are correctly assigned and have proper labels.

4. **Team Check-in (5 min)**  
   - Briefly ask each developer (privately if needed) if they feel stuck or overwhelmed.  
   - Offer pair-programming suggestions or knowledge-sharing sessions.

5. **Sync with Product Owner (5 min)**  
   - Align on any priority changes, scope creep risks, or stakeholder feedback.  
   - Confirm the next 2–3 backlog items are ready for the next sprint.

---

### Every Sprint Planning Day (first day of each sprint – 2–3 hours)
- **Before planning:**  
  - Ensure the team’s velocity from the last 2–3 sprints is calculated.  
  - Confirm the product backlog is refined (PO should have top items ready).  
  - Prepare the capacity table (team availability – holidays, meetings).  
- **During planning:**  
  - Facilitate the session – keep time-box (max 2 hours per week of sprint).  
  - Help the team negotiate scope with the PO.  
  - Ensure the Sprint Goal is clear and achievable.  
  - Guide the team to break down stories into actionable tasks.  
  - Finalise the sprint backlog and update the board.  
- **After planning:**  
  - Update the sprint timeline on the Team Workflow board.  
  - Send a summary to all team members (since all are owners).

---

### Every Sprint Review Day (last day of each sprint – 1 hour)
- **Before review:**  
  - Confirm which stories are truly “Done” (meet DoD).  
  - Help the PO prepare the demo (setup environment, test data).  
- **During review:**  
  - Facilitate the session – keep it to 1 hour.  
  - Encourage the team to showcase their work, not just the PO.  
  - Capture feedback and add new backlog items from stakeholders.  
- **After review:**  
  - Update the “Roadmap” board with any scope/date changes.  
  - Ensure all accepted issues are closed properly on GitHub.

---

### Every Sprint Retrospective (immediately after review – 45 min)
- **Before retro:**  
  - Gather data: velocity chart, burndown, number of blockers, team happiness (anonymous quick poll).  
  - Prepare a fun/engaging format (e.g., Start/Stop/Continue, Sailboat, 4Ls).  
- **During retro:**  
  - Facilitate open, blameless discussion.  
  - Help the team identify 1–2 actionable improvements.  
  - Document action items with clear owners.  
- **After retro:**  
  - Add actions to the “Retrospective” board and track them daily.  
  - Follow up on previous retro actions – report progress.

---

## Weekly Tasks (every Friday, 1 hour)
1. **Velocity & Progress Analysis**  
   - Update the burndown/burnup charts (GitHub Projects can show this).  
   - Calculate average velocity – share with PO for backlog forecasting.

2. **Backlog Refinement Support (with PO)**  
   - Help the team understand upcoming stories (technical feasibility).  
   - Facilitate estimation sessions (planning poker if needed).  
   - Ensure each refined story has sub-tasks and acceptance criteria.

3. **Team Health Check**  
   - Send a 1-question pulse check (e.g., “How stressed are you?”).  
   - Address any team dynamics or interpersonal issues early.

4. **Tools & Automation Review**  
   - Check GitHub Actions / CI status – if broken, escalate or fix with team.  
   - Ensure issue templates, labels, and project boards are consistent.

5. **Stakeholder Update (internal)**  
   - Send a concise update to all members (since all are owners):  
     - Sprint progress (completed vs. planned).  
     - Upcoming changes or risks.  
     - Any process tweaks.

---

## One-Time / Monthly Tasks (over 3 months)

### Month 1 (Establish Foundation)
- **Define Working Agreement** with the team – hours, communication channels, DoD, DoR.  
- **Set up metrics** – velocity tracking, cycle time, and lead time.  
- **Train the team** on GitHub Projects usage (labels, boards, Sprint field).  
- **Establish a “Definition of Ready”** – stories must have AC, estimates, and dependencies mapped.

### Month 2 (Optimize & Stabilize)
- **Review velocity trends** – adjust sprint length or scope if needed.  
- **Introduce one improvement** from retros (e.g., automated testing, pair programming).  
- **Monitor team morale** – take action if burnout signs appear.

### Month 3 (Final Push & Handover)
- **Focus on bug-free completion** – enforce DoD strictly.  
- **Help the team with deployment/release coordination**.  
- **Conduct a final retrospective** – capture lessons learned for future projects.  
- **Prepare a handover document** for the SM role (processes, metrics, board states).

---

## Decision-Making Rules (for SM alone)
- **Escalate impediments** to management/stakeholders if not resolved in 24 hours.  
- **Protect the sprint goal** – say “NO” to any mid-sprint scope changes unless critical (then involve PO).  
- **Empower the team** – never assign tasks yourself; let the team self-organize.  
- **If the team is stuck**, suggest a 15-min spike or mob-programming session.

---

## Tools & Boards Usage (Github Projects)
| Board | SM’s Responsibility |
|-------|----------------------|
| **Team Planning** | Ensure sprints and epics are logically sequenced. |
| **Roadmap** | Flag any timeline risks to PO and team. |
| **Iterative Development** | Main board – keep it clean, updated, and accurate at all times. |
| **Retrospective** | Own this board – track improvement actions and their status. |

---

## Daily Checklist (printable)
- [ ] Facilitate standup (start on time, end on time).  
- [ ] Log all new impediments and assign owners.  
- [ ] Check the “Iterative Development” board – move stuck issues to “Blocked”.  
- [ ] Update the burndown chart if using one.  
- [ ] Follow up on at least 1 unresolved blocker.  
- [ ] Send a quick “all good?” message to each developer.  
- [ ] Ensure the next day’s standup has no surprise gaps.

---

## Success Criteria for SM (by end of 3 months)
- The team runs all Scrum events without SM facilitation (self-sufficient).  
- Average blocker resolution time < 4 hours.  
- Team velocity is stable and predictable.  
- Retrospective action items are 90% completed.  
- Team morale remains positive (survey score ≥ 4/5).  
- GitHub boards are 100% accurate at all times.

---

**Next:** Tell me which role you want to define next – **Code Owner** or the remaining **2 developers**.