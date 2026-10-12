# Deliverables

To receive credit for the Capstone, we must submit **all** of the following. Use this page as a living checklist.

**Grading:** Projects are scored **0–5**. A score of **3 or higher** is required to pass. See [Grading & Pass Criteria](./grading.md) for details.

---
##  Deadline :  October 11 (official) · team target: October 5

## Mandatory submissions

### 1. GitHub repository

|            |                                                                                                                  |
| ---------- | ---------------------------------------------------------------------------------------------------------------- |
| **Status** | ✅ Done                                                                                                          |
| **URL**    | [https://github.com/TheQuintet/macrocrypto-ai/tree/main](https://github.com/TheQuintet/macrocrypto-ai/tree/main) |

**Requirements**

- [ ] Code is appropriately documented
- [x] Repository is shared with the `quantic-grader` account — invite sent 10 Oct 2026; grader is added on request
- [x] README explains setup, architecture, and how to run the project
- [x] All team members have contributed (visible in commit history / PRs) — 5 members, all with commits and PRs on `main` (checked 11 Oct 2026)

---

### 2. Deployed application

|              |                                                                                                                  |
| ------------ | ---------------------------------------------------------------------------------------------------------------- |
| **Status**   | 🟡 In progress: deployed with simulated data; live API connection pending                                        |
| **URL**      | [https://macrocrypto-ai.lgloredanaelena.workers.dev/](https://macrocrypto-ai.lgloredanaelena.workers.dev/)       |
| **Platform** | Cloudflare Workers (static assets, `frontend/wrangler.jsonc`)                                                    |
| **Backend API** | [https://macrocrypto-api.lgloredanaelena.workers.dev](https://macrocrypto-api.lgloredanaelena.workers.dev/health) (health check; Hetzner VM, Docker Compose, Caddy TLS) · [Deployment guide](../guides/deployment-platform-analysis.md#deployment-of-the-backend) |

**Requirements**

- [x] Application is **publicly accessible**: the root URL and `/macro` both return HTTP 200 (checked 9 Oct 2026)
- [ ] Deployment is stable enough for demo and grading: pending the live API connection and green CI on the deployed build
- [x] Environment variables and secrets are not committed to the repo: `frontend/.env.example` only lists `VITE_API_GATEWAY_BASE_URL` with an empty value

---

### 3. Design and testing document

|                    |                                           |
| ------------------ | ----------------------------------------- |
| **Status**         | 🟡 In progress                            |
| **URL / location** | [Design hub](../design/README.md) · [Testing (local & CI/CD)](../test%20documents/local-and-ci-cd-tests.md) · [README index](https://github.com/TheQuintet/macrocrypto-ai#design-and-testing-documentation) |

**Requirements**

- [x] Architecture decisions explained — ADR-001 to ADR-005 in `docs/design/adr/`
- [x] Patterns and design choices documented — `docs/design/architectural-object-oriented-patterns.md`
- [x] Automated testing approach described — `docs/test documents/local-and-ci-cd-tests.md`
- [ ] Written **manually** — see [Policies & Standards](./policies.md) for AI rules

---

### 4. Agile task board

|            |                                                                                                                  |
| ---------- | ---------------------------------------------------------------------------------------------------------------- |
| **Status** | ✅ Done                                                                                                          |
| **URL**    | [https://github.com/orgs/TheQuintet/projects/6/views/6](https://github.com/orgs/TheQuintet/projects/6/views/6) |

**Sprints:** we ran **9 sprints** in total on the board (**Sprint 1–9** on Team Workflow #6). Capstone evidence uses **saved project views** for the first three sprints (not All Work URL filters):

[Sprint 1](https://github.com/orgs/TheQuintet/projects/6/views/18) · [Sprint 2](https://github.com/orgs/TheQuintet/projects/6/views/19) · [Sprint 3](https://github.com/orgs/TheQuintet/projects/6/views/20)

**Requirements**

- [ ] At least **three sprints**, user stories, and tasks visible on the board ([Sprint 1–3](#4-agile-task-board) · [Agile & sprints](../project-workflow.md#coordination-without-daily-standup-domain-slack))
- [ ] Completed work matches what we demoed / shipped
- [ ] `quantic-grader` can open the org project (in addition to repo access in §1)

---

### 5. Video presentation

|            |                                           |
| ---------- | ----------------------------------------- |
| **Status** | 🟡 In progress                            |
| **URL**    | [Google Drive folder](https://drive.google.com/drive/folders/1RhPLlVtBjOKQvEkGr-yBQ6DruhyWsiDG?usp=sharing) (link set, contents not yet verified) |
| **Length** | 15–20 minutes                             |

**Prep (recording only — not a second checklist):** [Demo prep](./demo-prep.md) · [#752](https://github.com/TheQuintet/macrocrypto-ai/issues/752). **Speaking order and script:** [demo script](./demo-script.md) · [run-of-show](./demo-prep.md#agreed-run-of-show-18-min).

**Requirements**

- [ ] Shows the **working system**
- [ ] **Every team member** speaks on camera
- [ ] **Every team member** is visible on camera
- [ ] **Every team member** presents a **government-issued ID** for verification
- [ ] Script / slide outline prepared and rehearsed

---

## Pre-submission checklist

Before final submission, confirm:

- [ ] `quantic-grader` has access to the repo
- [ ] All links in this wiki are updated and working
- [ ] Design doc cites any AI influence where applicable — see [AI-assisted development disclosure](../ai-assisted-development-disclosure.md)
- [ ] Video meets length and identity requirements for all six members
- [ ] Task board matches what we actually built (§4)

---

## Related pages

- [Demo prep](./demo-prep.md) — schedule, run-of-show, and recording steps for §5
- [Grading & Pass Criteria](./grading.md)
- [Scope](../project-scope.md)
- [Agile & Sprints](../project-workflow.md)
- [Policies & Standards](./policies.md)
- [Graduation home](./README.md)
