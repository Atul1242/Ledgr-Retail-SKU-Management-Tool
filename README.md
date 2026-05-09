<div align="center">

<img src="static/images/ledgr-brand.png" alt="Ledgr" width="380"/>

### Demand-forecasting AI for FMCG distributors

Reorder recommendations, stockout prevention, GST-compliant POs, batch-expiry tracking, multi-store scoping, and a RAG-grounded chatbot — backed by a 6-step LightGBM pipeline. Originally built for **Sunrise Consumer Goods** (Pune & Nashik, 320 outlets, 40 SKUs) for the **Demand Mirage** problem statement.

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](#)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask&logoColor=white)](#)
[![Postgres](https://img.shields.io/badge/PostgreSQL-15-336791?style=for-the-badge&logo=postgresql&logoColor=white)](#)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)](#)
[![LightGBM](https://img.shields.io/badge/LightGBM-Forecast-2EA44F?style=for-the-badge)](#)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-RAG-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white)](#)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](#)
[![Tabler](https://img.shields.io/badge/Tabler%20UI-1.2-066FD1?style=for-the-badge)](#)
[![Kotlin](https://img.shields.io/badge/Kotlin-2.0-7F52FF?style=for-the-badge&logo=kotlin&logoColor=white)](#)
[![Jetpack%20Compose](https://img.shields.io/badge/Jetpack%20Compose-Material%203-4285F4?style=for-the-badge&logo=jetpackcompose&logoColor=white)](#)
[![CameraX](https://img.shields.io/badge/CameraX-+%20ML%20Kit-EA4335?style=for-the-badge&logo=android&logoColor=white)](#)

</div>

---

## Quick start

```bash
git clone https://github.com/HoneyBadger-010/Ledgr-Retail-SKU-Management-Tool.git
cd Ledgr-Retail-SKU-Management-Tool
./run.sh                # auto-detects LAN IP, brings up Postgres + web + scheduler
# (or: docker compose up if you don't need the Android pairing QR)
```

First boot takes ~60 seconds — Postgres init, schema migration, seed of 40 SKUs / 320 outlets / supplier metadata / 103 batches, and an automatic pipeline run.

| | |
|---|---|
| **Dashboard** | [http://localhost:5000](http://localhost:5000) |
| **Demo accounts** | `owner@sunrise.com` · `sunrise2024` <br> `manager@sunrise.com` · `manager2024` <br> `salesman@sunrise.com` · `sales2024` |
| **Logs** | `docker compose logs -f web` |
| **Reset** | `docker compose down -v` |

> The Android scanner pairing QR encodes the host's LAN IP automatically when you launch with `./run.sh` — no manual config needed.

---

## What's inside

### 1. The web app
A Flask + Tabler UI dashboard for the entire FMCG inventory lifecycle.

| Page | What it shows |
|---|---|
| **Dashboard** | Revenue at risk · pending order value · live MAPE · pipeline status with run history |
| **Reorder** | 40-row pending-approval table with adjustable quantities, owner-only "Approve" — flows into Approved + In-Transit tabs |
| **Forecasts** | 6-week aggregate horizon, MAPE by category, top/bottom-confidence SKUs |
| **Diwali Retrospective** | Detection of the 14 known stockouts using 5 signals (capped surge, demand surge, Diwali 2022 pattern, inventory low, promo overlap) — 10/14 recall, no lookahead bias |
| **Outlets** | All 320 outlets with city/area/channel filters, per-outlet 156-week sales |
| **Data Quality** | Accept/reject/missing breakdown over actually-collected rows |
| **Supplier Performance** | Avg / P80 / festive lead times per supplier, variance scorecard |
| **Batch Expiry** | All batches with critical (<14d) / warning / OK buckets |
| **Purchase Orders** | GST-compliant PO generation grouped by supplier, intrastate (CGST + SGST) vs interstate (IGST) routing, persistent draft → approved flow, downloadable PDF invoices |
| **SKU Management** | Full SKU master incl. HSN/GST/supplier metadata, CSV upload, barcode-scan add, Add via Barcode QR for the Android scanner |
| **Audit Trail** | Inventory adjustments with user + reason |
| **Settings** | Profile, notification preferences, security (CSRF + session timeout) |

### 2. The 6-step pipeline (`backend/`)

```
1. Data Classification    → True-zero / missing-data / stockout-gap / uncertain (channel-aware)
2. Demand Forecasting     → LightGBM, one model per SKU, 6-week horizon
3. Diwali Retrospective   → No-lookahead 5-signal stockout detection
4. Reorder Engine         → Batch-aware available stock, MAPE-driven safety stock,
                            chronological week-by-week stockout simulation, EXPIRY_ALERT
5. SKU Classification     → Movement (fast/slow/seasonal/dead) + ABC analysis
6. Monday Report          → executive_summary + urgent_orders + overstock_alerts +
                            expiry_alerts + full_reorder_list
```

### 3. The Android app (`android/`)

Native Kotlin · Jetpack Compose · Material 3 industrial dark theme · CameraX + ML Kit barcode scanning · Retrofit with cookie persistence + CSRF · Room offline scan queue.

- **Pair**: scan the QR shown in SKU Management (or paste a server URL). The QR carries `{server_url, name}` JSON; the app stores it in DataStore.
- **Sign in**: salesman credentials → session cookie + CSRF token captured.
- **Scan**: live viewfinder with industrial corner brackets and an animated scan line. Square reticle for QR codes; wide reticle for retail barcodes. Each detection pops a quantity-confirm card.
- **Offline-first**: every scan goes into Room first, best-effort upload to `POST /api/sku/scan`. Failed/offline scans show as `QUEUED` with a Sync Now button.

Build: open `android/` in Android Studio (Hedgehog or newer, JDK 17), Sync, then Run. A signed-debug APK lives at `android/app/build/outputs/apk/debug/app-debug.apk` after `./gradlew assembleDebug`.

### 4. The chatbot (RAG)

The chat widget (sparkles button, lower right) answers questions about every domain on the dashboard:

- _"What's the best-performing outlet last week?"_ → OL-263 N Mart Aundh Pune, ₹61,212
- _"Show me supplier performance and lead times."_ → 12 suppliers · avg 9.0d · P80 12.0d · festive 15.6d, plus per-vendor breakdown
- _"Are any batches near expiry?"_ → 29 critical (<14d), with SKU IDs and days-to-expiry

Ingests **69 chunks** spanning SKUs, outlets, suppliers, batches, POs, pipeline runs, data quality, forecasts, retrospective accuracy, and classification — retrieved via TF-IDF + cosine before being sent to the LLM, so per-query cost stays bounded as the catalogue grows.

`OPENROUTER_KEY` in `.env` enables full LLM responses (Gemini 2.0 Flash via OpenRouter). Without it, a local keyword fallback still answers basic queries.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                       Browser (Tabler UI)                            │
│   Dashboard · Reorder · Forecasts · Retro · Outlets · POs · Audit   │
└──────────────┬───────────────────────────────┬───────────────────────┘
               │                               │
               │ JSON /api/*                   │ HTML (Jinja2)
               ▼                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    Flask · gunicorn (2 workers)                       │
│                                                                      │
│   auth.py        flask-login + bcrypt + CSRF + role-based gating     │
│   models.py      SQLAlchemy ORM (15 tables)                          │
│   pipeline.py    DB→CSV export, runs 6 backend scripts in order      │
│   rag.py         build_chunks + TF-IDF retrieval for chatbot context │
│   po_pdf.py      reportlab GST-compliant PDF generation              │
│   notifications.py   WhatsApp (Twilio) + Email + Telegram + non-     │
│                      submission alerts                                │
└──────────────┬───────────────────────────────────────────────────────┘
               │ SQL
               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                       PostgreSQL 15                                  │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│  APScheduler container                                               │
│  Mondays 7:45 IST → log_weekly_actuals → run_pipeline → notify       │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Configuration

`.env.example` has every variable; copy to `.env` to override Docker defaults.

| Variable | Purpose | Default |
|---|---|---|
| `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` | Postgres init | `ledgr` / `ledgr` / `ledgr_local_dev` |
| `WEB_PORT` | Host port for the dashboard | `5000` |
| `FLASK_SECRET_KEY` | Session/cookie signing | dev key — **must** be replaced in production |
| `FLASK_ENV` | `development` / `production` | `development` |
| `LEDGR_PUBLIC_HOST` | Host LAN IP for the Android pairing QR | auto-set by `run.sh` |
| `OPENROUTER_KEY` | Live LLM responses for the chatbot | unset (local fallback) |
| `HIDE_DEMO_CREDENTIALS` | Hide the demo accounts block on `/login` | unset |
| `TWILIO_*`, `MAIL_*`, `TELEGRAM_*` | Notification channels | unset (disabled) |

---

## Running without Docker

```bash
python -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/python app.py        # SQLite at ./sunrise.db
```

Useful one-shot scripts:

| Script | What it does |
|---|---|
| `scripts/install_product_images.py` | Maps and copies product photos into `static/images/products/` |
| `scripts/backfill_supplier_data.py` | Idempotently fills HSN / GST / supplier metadata for every SKU |
| `scripts/log_weekly_actuals.py` | Compares last week's forecast vs actuals → `forecast_accuracy_log` |
| `scripts/reconcile_outlet_channel.py` | One-time fix for `outlet_master.csv` channel column |

---

## Repository layout

```
.
├── app.py                Flask app — routes, RAG glue, chatbot endpoint
├── auth.py               Flask-Login + bcrypt + CSRF + role decorators
├── database.py           SQLAlchemy init, seed, migrations, query helpers
├── models.py             ORM models (15 tables)
├── pipeline.py           6-step pipeline orchestrator
├── ingestion.py          Sales-data validation firewall (Brief Part 2D)
├── rag.py                TF-IDF retrieval layer for the chatbot
├── notifications.py      WhatsApp / Email / Telegram + non-submission alerts
├── po_pdf.py             GST-compliant PDF invoice generator
├── scheduler.py          APScheduler Monday cron
├── backend/              The 6 pipeline steps
├── templates/            Jinja2 (Tabler-themed) — base.html + per-page
├── static/               JS, CSS, product images, brand assets
├── mobile/               PWA scanner shell + service-worker
├── android/              Native Android Studio project (Kotlin · Compose)
├── scripts/              One-shot maintenance + setup scripts
├── data/                 sku_master.csv, outlet_master.csv, sales_history.csv,
│                         inventory_snapshot.csv, festive_calendar.csv,
│                         promotions_calendar.csv
├── docker-compose.yml    Postgres + web + scheduler stack
├── Dockerfile            Single-image build for web/scheduler
├── run.sh                LAN-IP-aware boot wrapper
└── requirements.txt
```

---

## Production checklist

1. Replace `FLASK_SECRET_KEY` with a real random value.
2. Set `FLASK_ENV=production` (the app refuses to start with the default key under prod).
3. Set `HIDE_DEMO_CREDENTIALS=1` to remove the demo accounts block on the login page.
4. Migrate from the in-file `DEMO_USERS` dict to a real `users` table; add `POST /api/auth/change-password`.
5. Set `OPENROUTER_KEY` for live LLM responses.
6. Set `LEDGR_PUBLIC_HOST` to the externally-reachable hostname for Android pairing QR codes.
7. Front the gunicorn process with nginx + a real TLS cert; flip `usesCleartextTraffic` to `false` in the Android manifest.

---

## License

Same as the parent repo. Contributions and bug reports welcome.
