# Ledgr Scanner — Android app

Native Android (Kotlin · Jetpack Compose · Material 3) industrial barcode scanner that talks to a Ledgr server.

## What it does

1. **First launch — Pair**: scan the QR code shown in **Ledgr → SKU Management → Add via Barcode** (or paste the server URL manually). The app stores the URL and never asks again.
2. **Sign in**: enter your Ledgr salesman credentials. The session cookie is kept in memory; CSRF token is captured from the home page and sent on every POST.
3. **Scan**: a live CameraX viewfinder + ML Kit barcode reader. Each detected barcode pops a confirmation card with a quantity field. Tap **Confirm & save** to upload.
4. **Offline-first**: every scan goes into a Room queue first, then a best-effort upload to `POST /api/sku/scan`. If the server is unreachable, the scan stays queued and shows up as `QUEUED` in the recent list. Tap **Sync now** to drain.

Supported barcode formats: EAN-13, EAN-8, UPC-A, UPC-E, Code-128, Code-39, ITF, Data Matrix, QR (used during pairing).

## Build it

You need **Android Studio Hedgehog (2023.1) or newer** with **JDK 17**.

```bash
# From the repo root
cd android
# In Android Studio: File → Open → select this folder
# Then click Run ▶ (or assemble: ./gradlew assembleDebug)
```

If you don't have a Gradle wrapper jar present yet (Android Studio downloads it on first sync), trigger a sync after opening the project — the `gradle/wrapper/gradle-wrapper.properties` file points at Gradle 8.7.

## App architecture

```
com.ledgr.scanner
├── LedgrApp.kt                      Application — owns AppContainer (manual DI)
├── MainActivity.kt                   Compose root + nav graph (pair → login → scanner)
├── data/
│   ├── AppContainer.kt               Wires prefs + db + apiHolder
│   ├── prefs/AppPrefs.kt             DataStore: server URL, name, CSRF, auth email
│   ├── db/ScanQueueDao.kt            Room entity + DAO + DB
│   ├── api/LedgrApi.kt               Retrofit interface (login, home, /api/sku/scan)
│   ├── api/RetrofitClient.kt         OkHttp + cookies + CSRF interceptor
│   ├── api/Models.kt                 Request/response DTOs
│   └── ScanRepository.kt             Local-first capture + queue drain
├── ui/
│   ├── theme/Theme.kt                Industrial dark Material 3 (gold-on-navy)
│   ├── components/Components.kt      Header, panel, primary/secondary CTA, status pill
│   ├── pairing/PairingScreen.kt      QR scan + manual URL fallback
│   ├── login/LoginScreen.kt          Email + password → /login
│   └── scanner/
│       ├── CameraScanner.kt          CameraX preview + ML Kit analyzer Composable
│       └── ScannerScreen.kt          Top bar + viewfinder + confirm panel + history
└── util/QrPayload.kt                 Parses QR content (URL or JSON pairing payload)
```

## Pairing payload formats

Two QR formats are accepted:

1. **Plain URL** (the existing PWA QR shows this):
   ```
   http://192.168.1.10:5000/mobile/
   ```
   The `/mobile/` suffix is stripped automatically — the API base becomes `http://192.168.1.10:5000`.

2. **JSON** (what `/api/qr-pairing` returns):
   ```json
   {"server_url":"http://192.168.1.10:5000","name":"Sunrise Pune"}
   ```

## Cleartext HTTP

The manifest sets `android:usesCleartextTraffic="true"` so the demo runs against a local Flask dev server on `http://`. For production, point the app at an HTTPS server and remove that flag (or use a `network_security_config.xml` to scope clear-text to your dev subnet only).

## License

Same as the parent repo.
