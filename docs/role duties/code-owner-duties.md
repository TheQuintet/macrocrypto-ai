# Code Owner – Clear Duties & Daily Tasks (3-Month Project)

## Core Responsibilities (High-Level)
- Own the overall code quality, architecture, and technical standards.
- Enforce coding conventions, best practices, and design patterns.
- Review all pull requests (PRs) – ensure they meet quality and security standards.
- Maintain the CI/CD pipeline and ensure automated tests pass.
- Manage the repository structure, branching strategy, and release process.
- Reduce technical debt and prevent accumulation of "hacks."
- Ensure the codebase remains maintainable, scalable, and testable.
- Be the final approver for merging code into the main branch.

---

## Daily / Every-Sprint Tasks (Routine)

### Every Day (60–90 min total)
1. **Pull Request Review (30–45 min)**  
   - Review all open PRs – aim for < 4 hours turnaround time.  
   - Check for:  
     - Code style and formatting (use linters/automation where possible).  
     - Test coverage – ensure new code has unit/integration tests.  
     - Security vulnerabilities – no hardcoded secrets, SQL injections, etc.  
     - Performance implications – O(n) complexity, memory leaks.  
     - Adherence to architecture – no circular dependencies, proper layering.  
   - Provide constructive, actionable feedback – never just "fix this."  
   - Approve or request changes – if changes, specify exactly what and why.

2. **CI/CD Pipeline Check (10 min)**  
   - Monitor GitHub Actions – ensure all workflows pass.  
   - If a build fails, investigate and either fix or assign to the right person.  
   - Keep the main branch always green (passing all checks).

3. **Codebase Health Scan (10 min)**  
   - Run (or check) static analysis tools (SonarQube, ESLint, etc.).  
   - Address any critical issues (security hotspots, blockers).  
   - Log any new technical debt as GitHub issues.

4. **Daily Sync with Scrum Master (5 min)**  
   - Report any technical blockers that need escalation.  
   - Align on upcoming features that may require architectural changes.

5. **Support Development Team (15 min)**  
   - Be available for technical questions – unblock developers quickly.  
   - Offer pair-programming sessions if someone is stuck.  
   - Mentor junior developers on design patterns and best practices.

---

### Every Sprint Planning Day (first day of each sprint – 2 hours)
- **Before planning:**  
  - Review the proposed backlog items – estimate complexity and technical risk.  
  - Identify any stories that need a technical spike (research).  
  - Pre-approve any architecture/design decisions for upcoming features.  
- **During planning:**  
  - Help the team break down stories into technical tasks.  
  - Highlight dependencies between tasks (e.g., "this DB migration must go first").  
  - Commit to technical deliverables (e.g., refactoring, test automation).  
  - Ensure each story has a clear "Definition of Done" from a code perspective.  
- **After planning:**  
  - Update any technical checkpoints on the "Roadmap" board.  
  - Create technical subtasks (e.g., setup new service, add monitoring).

---

### Every Sprint Review Day (last day of each sprint – 30 min)
- **Before review:**  
  - Ensure all completed stories meet the technical DoD.  
  - Verify that all merged code has passed CI/CD and is deployable.  
  - Prepare a brief technical summary (if needed) for stakeholders.  
- **During review:**  
  - Demo any significant technical improvements (e.g., faster builds, new architecture).  
  - Highlight any technical debt that was paid off or introduced.  
- **After review:**  
  - Merge any remaining approved PRs.  
  - Update the main branch with the latest release candidate.

---

### Every Sprint Retrospective (immediately after review – 30 min)
- **During retro:**  
  - Share metrics: PR review time, test coverage %, build failure rate.  
  - Discuss technical challenges – flaky tests, slow builds, complexity.  
  - Propose actionable improvements (e.g., "automate more checks").  
- **After retro:**  
  - Create issues for each technical improvement action.  
  - Prioritize them in the backlog.

---

## Weekly Tasks (every Friday, 1.5 hours)
1. **Technical Debt Review**  
   - List all debt-related issues (e.g., "refactor X," "upgrade library Y").  
   - Prioritize critical ones (security, performance) and add to backlog.  
   - Estimate the effort to pay off each debt item.

2. **Architecture Sync / Design Review (1 hour)**  
   - Review any upcoming major features – ensure they fit the architecture.  
   - Document design decisions (ADR – Architecture Decision Records).  
   - Update the high-level system diagram / documentation.

3. **Dependency Management**  
   - Check for outdated libraries / security vulnerabilities (e.g., Dependabot).  
   - Plan updates – schedule them with the team (usually 1 sprint per quarter).  
   - Ensure no deprecated or end-of-life dependencies are used.

4. **Test Coverage Report**  
   - Generate coverage report – aim for ≥ 80% (or agreed threshold).  
   - Flag any modules with declining coverage – create tasks to improve.

5. **Code Quality Metrics**  
   - Run linters, code smells analysis, duplication checks.  
   - Share a "health dashboard" with the team (visible in GitHub).  
   - Propose fixes for top 3 issues.

6. **Environment Check**  
   - Verify that dev/staging/prod environments are stable.  
   - Check logs for recurring errors – file bugs for them.

---

## One-Time / Monthly Tasks (over 3 months)

### Month 1 (Foundation)
- **Set up repository structure** – folders, modules, naming conventions.  
- **Define branching strategy** – e.g., GitFlow or trunk-based.  
- **Establish CI/CD pipeline** – build, test, deploy (with GitHub Actions).  
- **Define coding standards** – style guides, linter configs, pre-commit hooks.  
- **Set up code review guidelines** – checklist template for PRs.  
- **Create a "Technical Vision" document** – tech stack, frameworks, patterns.

### Month 2 (Iteration & Hardening)
- **Review architecture** – ensure it scales with new features.  
- **Introduce performance testing** (if not already).  
- **Security audit** – run SAST/DAST tools, fix critical issues.  
- **Refactor at least 2 high-debt modules** (from the debt list).  
- **Automate more checks** – e.g., coverage threshold enforcement.

### Month 3 (Finalisation & Delivery)
- **Final code freeze** – no new features, only bug fixes and documentation.  
- **Complete all security and performance fixes.**  
- **Run full regression suite** – ensure everything works.  
- **Prepare release artifacts** – binaries, containers, or packages.  
- **Write / finalize technical documentation** – API docs, setup guides.  
- **Conduct final code audit** – ensure no critical debt remains.

---

## Decision-Making Rules (for Code Owner alone)
- **Merge only if:** all tests pass, 2 approvals (at least 1 from code owner), no unresolved comments.  
- **Reject PR if:** test coverage drops by > 2%, security issues present, or design is flawed.  
- **Any architectural change** must be discussed and approved before implementation.  
- **Hotfixes** can bypass some rules but must be followed by a post-fix refactor within 2 days.  
- **Technical debt** is acceptable only if a follow-up issue is created and scheduled within 2 sprints.

---

## Tools & Boards Usage (Github Projects)
| Board | Code Owner’s Responsibility |
|-------|-----------------------------|
| **Team Planning** | Add technical epics (infrastructure, upgrades, refactoring). |
| **Roadmap** | Mark technical checkpoints (e.g., "CI/CD complete," "API v1 ready"). |
| **Iterative Development** | Own all technical subtasks – ensure they move to "Done" each sprint. |
| **Retrospective** | Add technical improvements that require team adoption. |

---

## Daily Checklist (printable)
- [ ] Review all open PRs – comment/approve/request changes.  
- [ ] Check CI/CD status – fix or escalate any failures.  
- [ ] Run static analysis – address critical issues.  
- [ ] Respond to technical questions from the team.  
- [ ] Update any technical documentation if changes were made.  
- [ ] Ensure main branch is green (passing all checks).  
- [ ] Log any new technical debt as an issue.

---

## Success Criteria for Code Owner (by end of 3 months)
- Average PR review time < 4 hours.  
- Test coverage ≥ 80% (or agreed target).  
- Zero critical security vulnerabilities.  
- CI/CD pipeline is fully automated and reliable (failure rate < 5%).  
- Technical debt is tracked and reduced by at least 30%.  
- Team follows coding standards without enforcement.  
- The final release is stable, deployable, and well-documented.

---

**Next:** Tell me which role you want to define next – the remaining **2 developers** (or if you want a combined "Developer" role definition).