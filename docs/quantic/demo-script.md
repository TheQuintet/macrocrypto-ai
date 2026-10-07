# Capstone demo — speaking script (team)

**Single place for everyone’s lines.** Edit this file in a PR or commit on `main` (small text changes are fine).

| Role | Person |
|------|--------|
| Merge & narrative | **Sid Ahmed Mahieddine** (PO) |
| Timing & run-of-show | **Richard Owusu** |
| Facilitate recording | **Loredana Lungu** (SM) |

Run-of-show: [demo-prep.md](./demo-prep.md#agreed-run-of-show-18-min) · Decisions: [7 Oct notes](../meetings/2026-10-07-final-demo-planning.md) · Tracker: [#752](https://github.com/TheQuintet/macrocrypto-ai/issues/752)

**Deploy URL (fill when ready):** _TBD_

**Recording:** Sat **10 Oct 2026** ~**18:00** (Zoom — Loredana). **Scripts due Thu 8 Oct.**

---

## All members — intros & IDs (Quantic requirement)

Each person: name, capstone role, one sentence on what you built. Then **hold government ID** to camera (~10–15 s) so name and photo are legible. Order can follow the table below or a quick round-robin at the start.

### Sid Ahmed Mahieddine (Product Owner)

- **First line:**
- **ID:** (when in the recording order)
- **Notes:**

### Kingson Emma-Ochu (Frontend)

- **First line:**
- **ID:**
- **Notes:**

### Richard Owusu (ML / frontend)

- **First line:**
- **ID:**
- **Notes:**

### Loredana Lungu (Scrum Master / frontend)

- **First line:**
- **ID:**
- **Notes:**

### Mael Taye Deneke (Backend / code owner)

- **First line:**
- **ID:**
- **Notes:**

---

## Kingson — opening & welcome (~4:00)

- **First line:**
- **Talking points:** (welcome, team, one-sentence product hook; transition into Sid)
- **Handoff to Sid:**

---

## Sid — problem, product & AI service (~4:00)

- **First line:**
- **Screen:** (optional architecture slide; deployed home if useful)
- **Talking points:** origin, problem, solution, personas (BTC trader / investment analyst); **AI service** — six models, champion selection, scheduled correlation analysis
- **Handoff to Mael:**

---

## Mael — architecture & platform (~4:00)

- **First line:**
- **Screen:** (deploy URL, services diagram, CI badge, link to software design doc in repo)
- **Talking points:** tech stack, three services, RabbitMQ, Redis caching, CI/CD and test automation; point to design doc (MD + SVG), current vs future architecture
- **If API fails:** (one sentence + what to show)
- **Handoff to Richard:**
- **Backup:** pre-recorded segment if live connectivity fails

---

## Richard — data gathering & preprocessing (~4:00)

- **First line:**
- **Screen:** (research doc, preprocessing flow, or repo paths)
- **Talking points:**
- **Handoff to Loredana:**

---

## Loredana — agile process & alerts (~4:00)

- **First line:**
- **Screen:** (GitHub board — sprints + retro; alerts + notification bell on deploy)
- **Talking points:** PO/SM/code owner, meeting notes, PR/CI process; **alerts with dummy data** — state clearly on camera
- **If alerts fail:** (fallback line)
- **Handoff to Kingson:**

---

## Kingson — dashboard, forecast & closing demo (~4:00)

- **First line:**
- **Screen:** (deploy URL — dashboard, charts, forecast routes)
- **Click path:** (numbered steps; live data on deploy)
- **If API fails:**
- **Closing line:** (thank judges / Quantic)

---

## Global fallbacks (Sid maintains)

| Flow | If it breaks on camera, say | Show instead |
|------|-----------------------------|--------------|
| Forecast / prediction | | |
| Alerts | Dummy data disclaimer + | board or recording backup |
| Notifications | | |
| Macro / BTC load | Demo with **9 indicators** if 13 unavailable | |
| Deploy / health | | CI green pipelines |

---

## Status

- [ ] Each member filled their section above (**due Thu 8 Oct**)
- [ ] Sid merged transitions; total read-through fits **15–20 min** (Richard)
- [ ] Linked from [#752](https://github.com/TheQuintet/macrocrypto-ai/issues/752) or noted in Slack
