A. INSTRUCTIONS
1. Always save the changes to CHANGESLOG.MD files
2. Always refer to the Product Requirements Document (PRD)
3. Make sure the project is compatible with docker container

B. Product Requirements Document (PRD)
**Project:** Universal Web Scraper & Gemini Enrichment Platform

---

### 1 · Problem Statement

Teams need fresh, structured data from many public web sources, but each site uses different layouts and anti-bot defenses. Existing single-site scrapers break frequently, require per-site code, and provide raw HTML that still demands manual analysis. We need a **config-driven, resilient scraper** that runs on a schedule, stores results, and auto-enriches them through Google Gemini so downstream users can focus on insights, not extraction.

---

### 2 · Goals & Success Metrics

| Goal                                   | Metric                                               | Target (v1 launch + 30 days) |
| -------------------------------------- | ---------------------------------------------------- | ---------------------------- |
| Extract data reliably from many sites  | ≥ 95 % scrape success rate after retries             |                              |
| Reduce engineering effort per new site | < 15 min median to onboard a simple site via UI/API  |                              |
| Minimize anti-bot blocks               | < 5 % requests returning 403/429                     |                              |
| Deliver enriched insights fast         | P95 end-to-end (scrape → Gemini stored) ≤ 15 s       |                              |
| Enable historical analysis             | 100 % of raw & Gemini records retained and queryable |                              |
---
### 5 · Product Features

| Priority | Feature                      | Description                                                                             | Notes                     |
| -------- | ---------------------------- | --------------------------------------------------------------------------------------- | ------------------------- |
| **MVP**  | Configurable Target Registry | UI/API to add site name, start URL, CSS selector, region/proxy, schedule, Gemini prompt | No code deploys           |
| **MVP**  | Resilient Scraper Engine     | Playwright-based, stealth, rotating proxies, CAPTCHA fallback                           | Modular anti-bot plugins  |
| **MVP**  | Scheduler                    | Cron-like service storing last run, retry queue                                         | APScheduler / Celery-beat |
| **MVP**  | Result Storage               | Raw HTML + extracted JSON + metadata in Postgres/TimescaleDB                            | 30-day raw retention      |
| **MVP**  | Gemini Adapter               | Calls model with per-config prompt; handles rate-limit & cost logging                   | Model configurable        |
| **MVP**  | Admin Console                | CRUD configs, run-now, view logs & last results                                         | React + FastAPI           |
| **MVP**  | Observability                | Prometheus metrics, Grafana dashboards, structured JSON logs                            | Error alerts              |

### 8 · UX Requirements (Admin Console)

* **Create/Edit Site** form with live CSS selector preview.
* Dashboard cards: Upcoming runs, Last run status, Avg duration.
* Table view of runs with filter by status, date, site.
* Result detail page: raw HTML viewer (collapsed), extracted JSON, Gemini response JSON.
* Dark-mode default (internal dev preference).
* English + Korean UI strings (i18n ready).

### 9 · Analytics & Reporting

* **Core metrics**: jobs triggered, jobs succeeded, avg scrape time, CAPTCHAs solved, Gemini cost USD/day.
* **Audit log**: who changed configs, when.
* **Optional alerts**: PagerDuty on scrape success-rate < 90 % for 15 min.

---

### 10 · Technical Overview (for reference)

* **Scraper**: Python 3.12, Playwright-Stealth, rotating proxy pool (internal + 3rd-party).
* **Backend API / Scheduler**: FastAPI + APScheduler + Celery (Redis queue).
* **DB**: Postgres 16 + TimescaleDB for time-series metrics.
* **Infra**: Docker images, GitHub Actions CI/CD, secrets in HashiCorp Vault.
* **Security**: TLS everywhere, AES-256 at-rest, JWT auth, RBAC.
