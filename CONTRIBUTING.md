```markdown
# Contributing to MacroCrypto AI

Thank you for your interest in contributing to MacroCrypto AI! This document outlines the process for contributing to this project.

---

## 📋 Important Notice

All contributions to this project are the property of MacroCrypto AI. By submitting a pull request, you agree to transfer all rights, title, and interest in your contribution to MacroCrypto AI.

This project is proprietary and confidential. Unauthorized use, reproduction, or distribution is strictly prohibited.

---

## 🔄 How to Contribute

### 1. Create a Branch

Always branch from `main`:

```bash
git checkout main
git pull origin main
git checkout -b feature/your-feature-name
```

**Branch naming conventions:**

| Type | Format | Example |
|------|--------|---------|
| New feature | `feature/description` | `feature/data-ingestion` |
| Bug fix | `bugfix/description` | `bugfix/rabbitmq-connection` |
| Documentation | `docs/description` | `docs/api-readme` |
| Hotfix | `hotfix/description` | `hotfix/security-patch` |

---

### 2. Make Changes

Write code, commit, and push regularly:

```bash
git add .
git commit -m "feat: add data ingestion endpoint"
git push origin feature/your-feature-name
```

**Commit message format:**

| Type | Description | Example |
|------|-------------|---------|
| `feat:` | New feature | `feat: add price forecasting endpoint` |
| `fix:` | Bug fix | `fix: handle RabbitMQ reconnection` |
| `docs:` | Documentation | `docs: update API documentation` |
| `refactor:` | Code refactor | `refactor: optimize database queries` |
| `test:` | Testing | `test: add unit tests for AI service` |
| `chore:` | Maintenance | `chore: update dependencies` |

---

### 3. Open a Pull Request

1. Go to the repository on GitHub
2. Click **"Pull Requests"** → **"New Pull Request"**
3. Select: `main` ← `feature/your-feature-name`
4. Fill in the PR template:
   - **Title:** Brief description of the change
   - **Description:** What changed, why, and how to test
5. Click **"Create Pull Request"**

**PR Title Format:**
```
[Service] Brief description of the change
```

**Examples:**
- `[Data Ingestion] Add CoinGecko API integration`
- `[AI Service] Implement price forecasting model`
- `[API Gateway] Add JWT authentication`

---

### 4. Review and Address Feedback

- **Reviewer:** At least one team member must approve
- **Address comments:** Push new commits to the same branch
- **Request re-review:** When ready, request review again

**As a Reviewer:**
- Check code quality
- Verify tests pass
- Test the changes locally (if needed)
- Approve or request changes

**As an Author:**
- Address all comments
- Push fixes to your branch
- Do not merge without approval

---

### 5. Merge the PR

Once approved and all checks pass, merge via GitHub UI:

**Merge strategy:** Use **"Squash and merge"** to keep history clean.

**Before merging, ensure:**
- ✅ At least 1 approval
- ✅ All comments resolved
- ✅ All status checks pass
- ✅ Branch is up to date with main

---

### 6. Delete the Branch

After merging, delete the feature branch on GitHub.

---

## ✅ Key Rules

| ✅ Do | ❌ Don't |
|-------|----------|
| Create a branch for every change | Push directly to `main` |
| Open a PR for every change | Merge without approval |
| Request at least 1 review | Ignore PR comments |
| Keep branches short-lived (1-7 days) | Merge without passing tests |
| Write clear commit messages | Delete a branch before merging |
| Delete branches after merging | Rebase a shared branch |

---

## 🆘 Need Help?

If you're stuck or have questions:
1. Check the existing documentation
2. Ask in the team chat
3. Reach out to the project lead

