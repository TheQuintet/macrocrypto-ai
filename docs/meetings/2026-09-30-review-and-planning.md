# Review, Refinement & Planning — 30 Sep 2026

Weekly Capstone Scrum sync: AI service dual paths (live DB vs offline parquet), backend pipeline and CI/CD progress, **13-feature** dataset alignment for the frontend, Quantic deliverables and methodology docs, presentation format (live vs recorded segments), and a hybrid real/mock demo strategy.

| | |
|---|---|
| **Date** | Wed 30 Sep 2026 (Slot B) |
| **Type** | Review + Refinement + Planning |
| **Sprint** | Final submission push — about one week to the **14 Oct** sync; integration, documentation, deployment, and recording prep dominate |
| **Attendees** | Sid Ahmed Mahieddine, Loredana Lungu, Kingson Emma-Ochu, Mael Taye Deneke, Richard Owusu |
| **Facilitator** | Loredana Lungu (Scrum Master) |
| **Product Owner** | Sid Ahmed Mahieddine |

---

## Key outcomes

- **Sid** is implementing the **AI service on two paths**: a **live path** (scheduled jobs, features read from the database once Mael’s feature table exists) and an **offline / file path** (parquet files, CLI-style runs for fast demos and offline processing). A **config toggle** switches between them when the DB-backed features are ready.
- The live path includes **MLflow** tracking, a **comparison engine** over **six trained models**, **champion model selection** (performance rules per **24-hour** and **7-day** horizons), and a **correlation calculation** job. Sid estimated **2–3 days** to finish; he will **notify the team** when the **file path** is ready with **endpoints** the frontend can integrate.
- **Mael** reported the **data pipeline finalized** (since the last sync). Current work: **AI service hookup**, **API endpoint** completion and testing, **documentation**, and **CI/CD** for the **data service** and **alert service** targeting **>80% test coverage**. He is building a **dataset DB table** for ML features (backfill, cleaning, **quality-control metrics**) with a target of **by Friday** (3 Oct).
- The ML feature set is now **13 indicators/features** (down from earlier broader lists). **Mael** will **tell Loredana** what changed so the **frontend** can display the correct fields; **Loredana** will **update the UI** to match.
- **Frontend integration** is still blocked on the **prediction endpoint** Mael is finishing. **Kingson** will **review open frontend stories** and work on **closing remaining BTC-trader UI** tasks.
- **Quantic deliverables** the team called out explicitly: the **GitHub repository**, the **project board**, **testing approach and development methodology** documentation, **UML** and design artifacts, and **deployment** documentation. **Loredana** owns **methodology** documentation and will **collaborate with Mael** on other required project documents. **Tests** remain part of **PR acceptance** (Loredana confirmed).
- **Core BTC price prediction** is still not fully wired end-to-end in the demo sense; Mael asked everyone to name **concrete presentation content** and keep **actionable to-do lists** rather than open-ended discussion.
- **Presentation (≤20 minutes):** **Richard** will **draft an outline** on **Slack** (sections + who presents what). **Kingson** covers **frontend**; **Richard** covers **AI service** components. The group debated **one live take** vs **individual recorded segments**; **Sid** prefers **live** for flow, **Loredana** wants to **try recording** first. **Richard** will **coordinate individual recordings** rather than merging separate video files in post.
- **Demo data:** **Hybrid** — **real data** where integration works; **mock data** as fallback (e.g. **alerts** that cannot run on live data during the recording). **Loredana** owns **technical recording** and **deployment** segments; **Sid** will add a **script / storyline** alongside Richard’s outline.
- **Deployment:** Still **open** — team must **pick the strategy** (e.g. **Vercel**, carried over from [23 Sep](./2026-09-23-review-and-planning.md)) and **who creates the deployment account**.
- **Communication:** Mael asked the team to **read PR summaries**, **reply promptly** to **Slack DMs**, and not assume who is doing what without checking the channel.

---

## Decisions

| Topic | Decision |
|-------|----------|
| **AI service architecture** | **Two paths**: live (DB features + jobs) and offline (parquet / file). **Config toggle** when DB table is ready |
| **Frontend features** | Align UI with **13 ML indicators/features**; Mael notifies Loredana of data changes |
| **Prediction integration** | Frontend waits on **prediction endpoint**; file-path AI endpoints first, then live path |
| **CI/CD** | Mael targets **>80% coverage** and CI integration for **data service** and **alert service** |
| **Quantic docs** | Repository + board + **methodology** + **testing approach** + **UML** + deployment docs are in scope for grading |
| **Presentation length** | **Up to 20 minutes** |
| **Presentation format** | **Outline on Slack** (Richard); **script/storyline** (Sid); prefer testing **recorded segments** vs one live run — **not fully settled** |
| **Demo data** | **Hybrid real + mock** — real where possible; mock for alerts / unstable live paths |
| **Deployment** | **Decide account owner and host** (Vercel still the leading option from prior sync) |

---

## Sprint review

| Area | Owner | Status |
|------|-------|--------|
| **Data pipeline** | Mael (Richard advising) | **Finalized** since last meeting |
| **Feature dataset in DB** | Mael | **In progress** — table, backfill, QC metrics; target **by Fri 3 Oct** |
| **AI service — offline path** | Sid | **In progress** (~2–3 days): MLflow, six-model comparison, champions, correlation job, parquet path |
| **AI service — live path** | Sid | **Blocked on** Mael’s feature table persistence |
| **API / prediction endpoint** | Mael | **In progress** — needed for frontend integration |
| **CI/CD (data + alert)** | Mael | **In progress** — >80% test coverage goal |
| **Documentation checklist / design docs** | Mael + Loredana | **Ongoing** — methodology and Quantic-required artifacts |
| **BTC trader frontend** | Loredana / Kingson | Sub-issues largely done; **13-feature alignment** and **real prediction data** still open |
| **Open frontend stories** | Kingson | **To review** next working day |
| **Presentation outline** | Richard | **Not started** — due on Slack |
| **Deployment** | Team | **Undecided** — account owner and final host |

---

## Refinement

| Item | Outcome | Ready for sprint? |
|------|---------|-------------------|
| **13-feature set** | Mael documents changes; Loredana updates macro/BTC UI fields | Yes |
| **File-path AI endpoints** | Sid notifies channel when ready for frontend wiring | Yes |
| **Prediction endpoint** | Mael completes; Loredana integrates forecast UI | Yes |
| **Methodology + Quantic docs** | Loredana + Mael split required write-ups | Yes |
| **Presentation sections** | Richard outline; Sid script; speakers pick parts | Yes |
| **Recording rehearsal** | Loredana tests real-data capture + mock fallback | Yes |
| **Deployment account** | Team decides who signs up and where (Vercel vs alternatives) | Yes |

---

## Sprint planning — next focus

| Focus | Owner | Notes |
|-------|-------|-------|
| **Feature DB table + QC** | Mael | By **Fri 3 Oct** |
| **AI service (file path first)** | Sid | Endpoints for frontend; **2–3 days** |
| **Prediction + remaining Gateway routes** | Mael | Unblocks Loredana’s integration |
| **CI/CD >80% (data + alert)** | Mael | Part of rubric / quality story |
| **Frontend — 13 features + integration** | Loredana | After Mael’s indicator summary |
| **Close open frontend stories** | Kingson | Trader scope only |
| **Methodology documentation** | Loredana | With Mael on other required docs |
| **Presentation outline** | Richard | Slack — frontend / AI / backend / board |
| **Presentation script** | Sid | Storyline for recording or live run |
| **Deployment decision** | Team | Account + host; document for graders |
| **Communication hygiene** | All | Read PR summaries; fast Slack replies |

**Out of this push**

- **Investment analyst** persona (unchanged from [23 Sep](./2026-09-23-review-and-planning.md))
- Merging multiple presenter videos in editing — **individual clips** coordinated by Richard

---

## Action items

| Owner | Action | Status |
|-------|--------|--------|
| Sid | Finish **AI service** (offline + live design, MLflow, champions, correlation, config toggle) — **~2–3 days** | ⏳ Open |
| Sid | **Announce file-path endpoints** when ready for frontend integration | ⏳ Open |
| Sid | Draft **presentation script / storyline** (with Richard’s outline) | ⏳ Open |
| Mael | Implement **ML feature dataset table** (backfill, cleaning, QC) — **by Fri 3 Oct** | ⏳ Open |
| Mael | **CI/CD** for data + alert services; **>80%** test coverage | ⏳ Open |
| Mael | **Summarize indicator/data changes** (13 features) for Loredana | ⏳ Open |
| Mael | Complete **prediction endpoint** and related API work | ⏳ Open |
| Loredana | **Methodology** documentation; collaborate with Mael on other **Quantic** docs | ⏳ Open |
| Loredana | Update **frontend** for **13 indicators/features**; integrate **prediction** when endpoints land | ⏳ Open |
| Loredana | **Record demo segments** (real data + mock fallback); cover **deployment** in recording | ⏳ Open |
| Kingson | **Review open frontend stories** and wrap trader UI work | ⏳ Open |
| Richard | Post **presentation outline** on Slack (sections + speaker assignments) | ⏳ Open |
| Richard | **Coordinate individual recording segments** (AI service portion) | ⏳ Open |
| Team | **Decide deployment** platform and **account owner** | ⏳ Open |
| Team | **Read PR summaries**; respond quickly on Slack | ⏳ Open |

---

## Discussion notes

### Sid — dual-path AI service

Sid’s near-term delivery is an AI service that can run **without** waiting on every live-data edge case: the **parquet / file path** produces comparable outputs for demos and grading, while the **live path** turns on once Mael persists engineered features in PostgreSQL. **MLflow** tracks runs; six models are compared; **champion** models are chosen separately for **24h** and **7d** horizons. A **correlation job** remains part of the service responsibilities discussed in prior sessions. The frontend should integrate against the **file-path endpoints first**, then swap or toggle to live data via configuration.

### Mael — pipeline done, integration and quality bar

With the **data preparation pipeline closed**, Mael’s bandwidth shifts to **database-backed features**, **AI integration**, **Gateway-facing endpoints** (including **prediction**), and **engineering hygiene**: documentation updates, tests, and **CI/CD** on data and alert services. He reiterated that **BTC price prediction** must appear in the submission narrative, not only peripheral UI. He wants **explicit** presentation commitments from each member and faster async responses so backend work is not blocked waiting for acknowledgments.

### Frontend and the 13-feature contract

Loredana’s integration work depends on Mael’s **prediction API** and a clear list of the **13** model inputs the UI should surface (replacing older indicator counts from earlier sprints). Kingson picks up **remaining trader frontend stories** after a fresh pass on the board. Alerts may stay **mocked in the recording** if live notification paths are risky during demo.

### Quantic grading artifacts

The team aligned on what graders will inspect beyond code: **how** the team developed and tested (methodology), **UML** and design docs already started under `docs/`, the **GitHub Projects board**, and **deployment** instructions. Loredana leads methodology; Mael continues checklist-driven doc work from the [23 Sep](./2026-09-23-review-and-planning.md) plan. PRs still require tests as acceptance criteria.

### Presentation planning

Time box remains **20 minutes**. Richard owns the **structural outline** and **speaker coordination**; Kingson presents **frontend**; Richard presents **AI service** topics. Sid favors a **single live presentation** for narrative flow; Loredana prefers **proving recording workflow** early (real integrated data, mock where needed). Richard’s plan to use **separate recordings per speaker** avoids heavy video merging. Sid adds a **script** so segments stay within time and hit rubric points (board, testing, ML rationale).

### Deployment

[23 Sep](./2026-09-23-review-and-planning.md) narrowed hosting toward **Vercel** and a **Docker Compose** bundle; this session did not finalize **who** creates the account or whether a **paid tier** is already approved. That decision remains before the **14 Oct** deadline.

### Communication

Mael repeated the [23 Sep](./2026-09-23-review-and-planning.md) ask: do not assume work is happening in silence — **read PR descriptions**, answer **DMs**, and post blockers in `#capstone-project-group`.

---

## Key takeaways

- **Data prep is done**; the critical path is **feature table → AI paths → prediction endpoint → frontend on real data**.
- Ship **file-path AI first**, then enable the **live toggle** when DB features are stable.
- **13 features** is the new contract between ML and UI — update docs and screens together.
- **Quantic** needs **methodology + testing + UML + deployment** write-ups, not only a working demo.
- **Presentation mechanics** (live vs clips, real vs mock) are decided in principle; **outline and rehearsal** happen this week.

---

## Notes

- Source: Zoom AI summary — `Weekly Capstone Scrum meeting. (1).md` (exported **30 Sep 2026**). No full speech-to-text transcript was available in the repo at write-up time; expand this page if a `.txt` transcript is added later.
- Zoom task lists name **Owusu** for Richard Owusu and once label Loredana as “Product Owner”; roles in this doc follow [team-roles.md](../team-roles.md) (PO: Sid; SM: Loredana).
- Previous documented session: [23 Sep 2026 Review, Refinement & Planning](./2026-09-23-review-and-planning.md).
- Related: [4 Sep 2026 Dr. Robert checkpoint](./2026-09-04-dr-robert-steele-checkpoint.md) · Capstone criteria: [Quantic grading](../quantic/grading.md) · [Deliverables](../quantic/deliverables.md).

---

## Next meeting

Wed **7 Oct 2026** (Slot B) — see [recurring sync schedule](../team-roles.md#recurring-meetings-through-14-oct-2026).
