# Final demo planning — 7 Oct 2026

Stand-up, presentation order, deployment, and recording plan for the Capstone demo video (~one week to submission).

| | |
|---|---|
| **Date** | Wed 7 Oct 2026 (Slot B) |
| **Type** | Weekly sync + final demo planning |
| **Attendees** | Sid Ahmed Mahieddine, Loredana Lungu, Kingson Emma-Ochu, Mael Taye Deneke, Richard Owusu (Mael joined late — audio) |
| **Facilitator** | Loredana Lungu (Scrum Master) |
| **Product Owner** | Sid Ahmed Mahieddine |

**Context.** Integration is the critical path: **frontend on real backend data**, **Sid’s remaining data-service branches**, **Mael end-to-end AI wiring by Thu 8 Oct**, then **Vercel deploy** and **Sat 10 Oct recording**. Tracker: [#752](https://github.com/TheQuintet/macrocrypto-ai/issues/752) · [demo-prep](../quantic/demo-prep.md) (repo, [sprint board](https://github.com/orgs/TheQuintet/projects/3), domain Slack, design & testing links).

---

## Stand-up snapshot

| Who | Update |
|-----|--------|
| **Loredana** | Merged dynamic macro-indicator cards (API-driven + tests). Playwright E2E PR to merge today. Economic calendar works locally. Still wiring ML/prediction API on frontend — **9 of 13** indicators visible in her environment. |
| **Kingson** | Forecast work done: linked from dashboard and forecast page, accuracy chart, details view — PRs merged. |
| **Richard** | No new code updates. ML service ready; suggested demoing **9 indicators** rather than blocking on all 13. |
| **Sid** | Data service: fixed Parquet resolution (daily → hourly for ML). **Two branches** open; needs Mael’s review. Waiting on Dr. Robert (dummy data for demo). Limited availability this week (other program). |
| **Mael** | AI service connected via API Gateway. Reviewed Sid’s data-service PRs (summary posted). **All 13 indicators** display on his machine. |

---

## Demo presentation — agreed order

**Mael’s split accepted:** Sid presents the **AI/ML service**; Mael focuses on **architecture and platform** he built.

| # | Presenter | Segment |
|---|-----------|---------|
| 1 | Kingson | Opening and welcome |
| 2 | Sid | Origin of the idea, problem, solution, high-level overview, and **AI service** (one slide: six models, champion selection, scheduled correlation analysis) |
| 3 | Mael | Architecture and tech stack, three services implemented, RabbitMQ, Redis caching, CI/CD and test automation, link to software design docs |
| 4 | Richard | Data gathering and preprocessing research |
| 5 | Loredana | Scrum process (board, sprints, meeting notes, retro) and **frontend alerts** |
| 6 | Kingson | Dashboard, charts, forecast, and **closing live demo** |

**Guidelines**

- One **continuous storyline**, not separate handovers (Richard).
- Target **~4 minutes** per segment; total must fit **15–20 minutes** — keep each part tight.
- Frame demos around **BTC trader** and **investment analyst** personas where it helps the narrative.
- Use **dummy data** to trigger alerts; **state clearly on camera** that alert data is dummy. Use the **live deployed URL** for everything else.
- **All five on camera** for the full recording (Quantic ID rules still apply — see [demo-prep](../quantic/demo-prep.md)).

---

## Action items

| Owner | Action | Target | Status |
|-------|--------|--------|--------|
| **Loredana** | Share final presentation order and expectations with the team | After meeting | ✅ Done ([demo-prep](../quantic/demo-prep.md), [demo-script](../quantic/demo-script.md); merged 7 Oct) |
| **Loredana** | Merge Playwright E2E PR | 7 Oct | 🟡 In progress ([#718](https://github.com/TheQuintet/macrocrypto-ai/pull/718) open) |
| **Loredana** | Connect real backend data to the frontend (prediction + macro indicators) | **Thu 8 Oct** (code freeze) | 🟡 In progress |
| **Loredana** | Deploy to **Vercel** (her account); share URL; verify health endpoints and green CI | Before recording | 🟡 In progress |
| **Loredana** | Update Quantic/docs from frontend side; fix README (**MBA → MSSE** where wrong) | Before submission | ✅ Done (PRs [#789](https://github.com/TheQuintet/macrocrypto-ai/pull/789)–[#791](https://github.com/TheQuintet/macrocrypto-ai/pull/791); [deliverables](../quantic/deliverables.md), [AI disclosure](../ai-assisted-development-disclosure.md)) |
| **Loredana** | Prepare board for demo (sprints with visible progress + retro) | Before recording | ✅ Done ([deliverables §4](../quantic/deliverables.md#4-agile-task-board), Sprint 1–3 links) |
| **Loredana** | Send **Sat 10 Oct ~18:00** Zoom invite; record, upload to Google Drive, share link | 10 Oct | ✅ Done (invite sent — recording + Drive upload still **10 Oct**) |
| **Loredana** | Short sync with Mael on **9 vs 13 indicators** if still mismatched | **Thu 8 Oct** | ⏳ Open |
| **Sid** | Finish two data-service branches; apply Mael’s review | **Thu 8 Oct** | ⏳ Open |
| **Sid** | Hand off AI integration details to Mael; stay reachable through Thu | **Thu 8 Oct** | ⏳ Open |
| **Sid** | Add Quantic submitter / grader access per checklist | Before submission | ⏳ Open |
| **Mael** | Integrate Sid’s final PRs + AI service end-to-end | **Thu 8 Oct** | ⏳ Open |
| **Mael** | Finalize software design doc (single MD, SVG links, current + future architecture) | Before submission | ⏳ Open |
| **Mael** | Review open backend story on board — close or flag | This week | ⏳ Open |
| **Mael** | Support deployment; note AI service memory/CPU needs when known | **Thu 8 Oct** | ⏳ Open |
| **Mael** | Pre-record segment backup (connectivity fallback) | Before 10 Oct | ⏳ Open |
| **Richard** | Review AI-generated documentation | This week | ⏳ Open |
| **Richard** | Prepare data gathering and preprocessing segment | **Thu 8 Oct** | ⏳ Open |
| **Kingson** | Triage unassigned testing issues (prediction unit test, accuracy metrics, Redis cache test) — close or drop | Before 10 Oct | ⏳ Open |
| **Kingson** | Prepare opening + closing demo segments | **Thu 8 Oct** | ⏳ Open |
| **Everyone** | Share talking points / scripts ([demo-script](../quantic/demo-script.md)) | **Thu 8 Oct** | ⏳ Open |
| **Everyone** | Attend Sat recording, on camera | **10 Oct ~18:00** | ⏳ Open |

---

## Progress update (8 Oct 2026)

| Who | Update |
|-----|--------|
| **Loredana** | Capstone docs and demo prep aligned in repo ([#789](https://github.com/TheQuintet/macrocrypto-ai/pull/789)–[#791](https://github.com/TheQuintet/macrocrypto-ai/pull/791)): [deliverables](../quantic/deliverables.md) statuses, agile board links, demo prep run-of-show. **Sat ~18:00** recording invite sent. Still on critical path: merge Playwright system E2E ([#718](https://github.com/TheQuintet/macrocrypto-ai/pull/718)), finish frontend ↔ backend integration (prediction + macro indicators), **Vercel** deploy + smoke/CI, and sync with Mael on indicator count. |

---

## Decisions

| Topic | Decision |
|-------|----------|
| Recording | **Sat 10 Oct 2026**, ~**18:00** (exact TZ TBD). Submission **Sunday** after recording (exact time/TZ TBD). |
| Code freeze | All coding and integration **done by Thu 8 Oct 2026**. **No development on Sat** (recording day). |
| Deployment | **Vercel** on **Loredana’s** account. Fallback **Railway** or **Render**; paid tier if memory-limited. |
| Smoke test | After deploy: **health endpoints** + **green CI pipelines** on camera. Full post-deploy smoke suite **not required**. |
| Macro indicators | Demo with **9** if that is all that is stable; do not block the video on all **13**. |
| Software design docs | **One Markdown** file linking **SVG UML** in a separate folder; class diagrams show **key classes** only; include **current and future** architecture. |
| Post-submission changes | **None** unless Quantic (Katie) approves — Sid asked in global channel. |
| Recording storage | Loredana records on **Zoom**; final **`.mp4`** on **Google Drive** (anyone with link). |
| Presentation roles | See table above — supersedes the [30 Sep](./2026-09-30-review-and-planning.md) run-of-show for **who presents AI vs platform**. |
| Daily coordination | **No daily standup** (live or required offline). Domain Slack for normal discussion; document visibility trade-off in demo ([workflow](../project-workflow.md#coordination-without-daily-standup-domain-slack)). |

---

## Open questions

- Exact **submission deadline** and **time zone** for the Sat **18:00** slot.
- **Memory/CPU** for deployed AI service (Mael expects clarity by Thu 8 Oct).
- Fallback if **all hosting fails** (local demo was raised — avoid if possible).
- **All-six-models** predictions page (Sid’s idea): only if time allows; **BTC forecast** remains priority.

---

## Notes

- Previous session: [30 Sep 2026](./2026-09-30-review-and-planning.md) · [Quantic demo prep](../quantic/demo-prep.md) · [#752](https://github.com/TheQuintet/macrocrypto-ai/issues/752).

---

## Next meeting

**Sat 10 Oct 2026** — final **demo recording** (~18:00). Optional **Wed 14 Oct** sync only if needed post-submission ([schedule](../team-roles.md#recurring-meetings-through-14-oct-2026)).
