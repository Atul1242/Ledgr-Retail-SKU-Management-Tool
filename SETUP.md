# Ledgr — Setup Guide

Get the full stack (web dashboard + Postgres + scheduler + Android scanner pairing) running in about **5 minutes**. The instructions below are exactly what we run on the dev machine — nothing extra, nothing skipped.

---

## 1. Prerequisites (one-time)

| | Why | Install |
|---|---|---|
| **Docker** ≥ 20.10 with the Compose plugin | runs the web + Postgres + scheduler stack | https://docs.docker.com/get-docker/ |
| **Git** | clone the repo | https://git-scm.com/downloads |
| *(optional)* **Android Studio** Hedgehog or newer | only if you want to rebuild the Android scanner APK from source | https://developer.android.com/studio |

A modern laptop with 4 GB free RAM is enough. The full image is ~600 MB.

---

## 2. Clone

```bash
git clone https://github.com/HoneyBadger-010/Ledgr-Retail-SKU-Management-Tool.git
cd Ledgr-Retail-SKU-Management-Tool
```

---

## 3. (Optional) Add your AI chatbot key

The chatbot has a **local keyword fallback** that works without any API key — every other feature works without configuration too. If you want the chat to give grounded LLM answers (Gemini 2.0 Flash via OpenRouter):

```bash
cp .env.example .env
```

Then open `.env` in your editor and paste your OpenRouter key on the `OPENROUTER_KEY=` line:

```ini
OPENROUTER_KEY=sk-or-v1-...
```

Get a key at https://openrouter.ai/keys — there's a free tier.

You can skip this entirely on the first run; the rest of the system doesn't need it.

---

## 4. Launch

**On Linux / macOS** — use the wrapper script (it auto-detects your LAN IP so the Android scanner can connect):

```bash
./run.sh
```

**On Windows** (or anywhere `hostname -I` doesn't work) — plain Docker Compose:

```bash
docker compose up
```

You'll see Postgres init, the schema migrate, the seed populate (40 SKUs · 320 outlets · 103 batches · supplier/HSN/GST defaults), and the 6-step pipeline auto-run for ~50 seconds. When you see lines like:

```
web_1 | PIPELINE COMPLETE: 6/6 steps succeeded in 48.4s
web_1 | [INFO] Listening at: http://0.0.0.0:5000 (1)
```

…you're ready.

> **First boot only**: ~60 seconds total (compose builds the image + Postgres init + pipeline). Subsequent `docker compose up` boots in ~5 seconds.

---

## 5. Verify

Open **http://localhost:5000** in any modern browser (Chrome / Edge / Firefox / Safari).

Three pre-seeded demo accounts (visible on the login page until you set `HIDE_DEMO_CREDENTIALS=1`):

| Role | Email | Password | What you see |
|---|---|---|---|
| Owner | `owner@sunrise.com` | `sunrise2024` | Everything — incl. PO approval, SKU delete, order generation |
| Manager | `manager@sunrise.com` | `manager2024` | Everything except approve/delete (those buttons are hidden) |
| Salesman | `salesman@sunrise.com` | `sales2024` | Redirects to the mobile barcode-scan PWA at `/mobile/` |

Sign in as **Owner** to see the full dashboard. Click around — every page should have real data.

If you also added your OpenRouter key, the **sparkles button (bottom-right)** opens a chatbot. Try: *"What's the best-performing outlet last week?"* — it should answer with a specific outlet ID and revenue.

---

## 6. (Optional) Android scanner

A pre-built debug APK lives at:

```
android/app/build/outputs/apk/debug/app-debug.apk
```

If it isn't there, build it:

```bash
cd android
./gradlew assembleDebug
# APK lands in app/build/outputs/apk/debug/
```

(Requires JDK 17 + Android SDK 34 — Android Studio installs both.)

**Install on the phone:**

```bash
adb install -r android/app/build/outputs/apk/debug/app-debug.apk
```

…or copy the APK to the phone and tap to install (allow "Install from unknown sources" first).

**Pair the app to the server:**

1. Phone and laptop on the **same Wi-Fi**.
2. In your laptop browser, go to **SKU Management → Add via Barcode** tab. A QR code is shown.
3. Open **Ledgr Scanner** on the phone → grant camera → frame the QR. The app reads the server URL automatically.
4. Sign in with the **salesman** credentials.
5. Scan retail barcodes (EAN/UPC/Code-128). Each scan opens a confirm card with a quantity field. Tap **Confirm & save**.

If the phone says "could not reach server", make sure you launched the stack with `./run.sh` (which sets `LEDGR_PUBLIC_HOST` automatically). On Windows, set it manually:

```powershell
$env:LEDGR_PUBLIC_HOST = "192.168.1.10"   # your laptop's LAN IP
docker compose up
```

---

## 7. Common operations

| Goal | Command |
|---|---|
| Start (foreground, see logs) | `./run.sh` |
| Start in the background | `./run.sh -d` |
| Stop | `docker compose down` |
| **Reset everything** (drop Postgres + pipeline outputs) | `docker compose down -v` |
| Stream logs | `docker compose logs -f web` (or `scheduler`) |
| Re-run the 6-step pipeline | sign in as owner → SKU Management → top-right "Run Pipeline" — or just `docker compose restart web` (auto-runs on boot if outputs are missing) |
| Open a Postgres shell | `docker compose exec db psql -U ledgr -d ledgr` |
| Update to a newer commit | `git pull && docker compose up -d --build` |

---

## 8. Going to production

The defaults are tuned for local demo. Before deploying for real users:

1. **Replace `FLASK_SECRET_KEY`** in `.env` with a real random value (`python -c "import secrets; print(secrets.token_urlsafe(48))"`). The app refuses to start under `FLASK_ENV=production` with the dev key.
2. **Set `FLASK_ENV=production`**.
3. **Set `HIDE_DEMO_CREDENTIALS=1`** to hide the demo accounts block on the login page.
4. **Migrate the demo accounts** out of `auth.py` (`DEMO_USERS` dict) and into the real `users` Postgres table; add `POST /api/auth/change-password`.
5. **Set `OPENROUTER_KEY`** for live LLM chat.
6. **Set `LEDGR_PUBLIC_HOST`** to the externally-routable hostname (the address Android phones will use to talk to the server).
7. **Front gunicorn with nginx** + a real TLS cert. Flip `usesCleartextTraffic` to `false` in `android/app/src/main/AndroidManifest.xml` and rebuild the APK so the app refuses plain HTTP.
8. Configure WhatsApp (Twilio) / Email (Flask-Mail) / Telegram in `.env` if you want the Monday-morning notifications.

---

## 9. Troubleshooting

| Symptom | Fix |
|---|---|
| `port 5000 already in use` | another app is using port 5000. Either kill it (`lsof -ti:5000 \| xargs kill`) or set `WEB_PORT=5001` in `.env` and re-run. |
| `error while fetching server API version: Permission denied` (Linux) | your user isn't in the `docker` group. Run `sudo usermod -aG docker $USER` and log out/in, or prefix every command with `sudo`. |
| Web container shows `unhealthy` for the first 60 seconds | normal — it's running the initial pipeline. Wait. |
| Scheduler container shows `unhealthy` always | scheduler doesn't expose an HTTP endpoint, so the curl healthcheck fails. It's actually running fine — ignore. |
| Phone QR pairing says "could not reach server" | you launched with `docker compose up` instead of `./run.sh`. Stop the stack and re-run with `./run.sh`. Or set `LEDGR_PUBLIC_HOST` manually as shown above. |
| GitHub secret-scanning email about `OPENROUTER_KEY` | your `.env` got committed by accident. Rotate the key on https://openrouter.ai/keys, fix the commit (`git rm --cached .env && git commit && git push`), and confirm `.env` is in `.gitignore`. |
| Chatbot says "AI mode: local fallback" | `OPENROUTER_KEY` is empty. Add it to `.env` and `docker compose restart web`. |

---

## 10. What you get out of the box

After step 5, the dashboard already has:

- **40 SKUs** with full master data (HSN, GST, supplier, lead time, MOQ, shelf life)
- **320 outlets** across Pune & Nashik with channel + city + area
- **3 years of weekly sales history** (`sales_history.csv`, ~93 K rows)
- **103 inventory batches** (29 critical / <14d to expiry)
- **6-week LightGBM forecast** + MAPE accuracy logs
- **Diwali 2023 retrospective** with 10/14 known stockouts identified
- **Monday morning report** ready to read or trigger via WhatsApp

You can start clicking immediately. No additional data import needed.

---

Questions? Issues? File one at https://github.com/HoneyBadger-010/Ledgr-Retail-SKU-Management-Tool/issues — happy to help.
