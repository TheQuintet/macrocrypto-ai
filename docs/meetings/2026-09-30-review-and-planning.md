# Review, Refinement & Planning — 30 Sep 2026

Final submission push (~one week to **14 Oct**): backend integration, Quantic documentation, deployment, and presentation prep.

| | |
|---|---|
| **Date** | Wed 30 Sep 2026 (Slot B) |
| **Type** | Review + Refinement + Planning |
| **Attendees** | Sid Ahmed Mahieddine, Loredana Lungu, Kingson Emma-Ochu, Mael Taye Deneke, Richard Owusu |
| **Facilitator** | Loredana Lungu (Scrum Master) |
| **Product Owner** | Sid Ahmed Mahieddine |

**Context.** Data preparation is **done**. The critical path is **feature table → AI service (file path first) → prediction endpoint → frontend on real data**. ML inputs are now **13 indicators/features**. **Investment analyst** scope stays out ([23 Sep](./2026-09-23-review-and-planning.md)). Presentation cap: **20 minutes**.

---

## Action items

| Owner | Action | Target | Status |
|-------|--------|--------|--------|
| **Sid** | AI service: **offline parquet path** + **live DB path** (scheduled jobs), **MLflow**, six-model comparison, **champion** selection (24h + 7d), **correlation** job, **config toggle** when DB features exist | ~**2–3 days** | ⏳ Open |
| **Sid** | Post in Slack when **file-path endpoints** are ready for frontend integration | After file path ships | ⏳ Open |
| **Sid** | Write presentation **script / storyline** (works with Richard’s outline) | Before recording | ⏳ Open |
| **Mael** | **ML feature dataset** PostgreSQL table — backfill, cleaning, **QC metrics** | **Fri 3 Oct** | ⏳ Open |
| **Mael** | **CI/CD** for **data service** + **alert service**; **>80%** test coverage | Submission push | ⏳ Open |
| **Mael** | **Notify Loredana** of indicator/data changes (**13 features**) so macro/BTC UI can align | ASAP | ⏳ Open |
| **Mael** | Finish **prediction endpoint** and remaining **API Gateway** exposure frontend needs | Unblocks integration | ⏳ Open |
| **Loredana** | **Methodology** documentation; pair with Mael on other **Quantic-required** docs (testing approach, UML, deployment write-ups) | Submission push | ⏳ Open |
| **Loredana** | Update **frontend** for **13 features**; wire **forecast** to prediction API when Mael/Sid endpoints land | After Mael’s summary | ⏳ Open |
| **Loredana** | **Record demo** segments — **real data** where integrated; **mock** fallback (e.g. alerts); cover **deployment** in the recording | Before submission | ⏳ Open |
| **Kingson** | Review **open frontend stories** and close remaining **BTC trader** UI work | Next working day | ⏳ Open |
| **Richard** | Share presentation **outline on Slack** (sections + who presents what) | ASAP | ⏳ Open |
| **Richard** | **Coordinate individual recording clips** (present **AI service** portion; avoid merging videos in post) | After outline | ⏳ Open |
| **Team** | Choose **deployment** host ( **Vercel** preferred from [23 Sep](./2026-09-23-review-and-planning.md)) and **account owner** | This week | ⏳ Open |
| **Team** | Read **PR summaries**; reply quickly to **Slack DMs**; post blockers in `#capstone-project-group` | Ongoing | ⏳ Open |

**Presentation roles (from outline, not separate tasks):** Kingson — frontend; Richard — AI/ML service; others — parts they built (backend, data, board, process).

**Dependencies:** Loredana’s real-data UI waits on **Mael’s prediction endpoint** and **Sid’s file-path AI endpoints**. Live AI path waits on **Mael’s feature table**.

---

## Decisions

| Topic | Decision |
|-------|----------|
| AI integration order | **File / parquet path first** for demo and frontend; **live path** when DB features + toggle are ready |
| Demo data | **Hybrid** — real where stable; **mock** for alerts or unfinished live paths |
| Presentation format | Richard **outline** + Sid **script**; **individual clips** coordinated by Richard; **live vs recorded** — rehearse recording (Loredana), Sid prefers live flow |
| Grading artifacts | Repo, **GitHub board**, **methodology**, **testing** docs, **UML**, **deployment** docs; tests stay **PR acceptance** criteria |
| Scope | **BTC trader + prediction** only; no investment-analyst push |

---

## Status snapshot

| Area | Owner | Note |
|------|-------|------|
| Data pipeline | Mael | **Complete** |
| Feature table + QC | Mael | In progress → **Fri 3 Oct** |
| AI service | Sid | In progress; live path blocked on feature table |
| Prediction / Gateway | Mael | In progress — **frontend blocker** |
| CI/CD (data + alert) | Mael | In progress (>80% goal) |
| Trader frontend | Loredana / Kingson | UI largely done; **13 features** + **real prediction** open |
| Docs (Quantic) | Loredana / Mael | Methodology + checklist-driven gaps |
| Presentation | Richard / Sid | Outline + script not yet on Slack |
| Deployment | Team | Host/account **not locked** |

---

## Notes

- Source: Zoom AI summary — `Weekly Capstone Scrum meeting. (1).md` (**30 Sep 2026**). Expand from a full transcript if one is added later.
- Previous session: [23 Sep 2026](./2026-09-23-review-and-planning.md) · [Dr. Robert checkpoint](./2026-09-04-dr-robert-steele-checkpoint.md) · [Quantic grading](../quantic/grading.md) · [Deliverables](../quantic/deliverables.md).

---

## Next meeting

Wed **7 Oct 2026** (Slot B) — [recurring sync](../team-roles.md#recurring-meetings-through-14-oct-2026).
