// Brief Part 6B — PWA app-shell caching for offline scanner.
//
// Strategy:
//   - Pre-cache the app shell on install (HTML + manifest + Google Fonts).
//   - Network-first for shell URLs (so updates land), cache fallback when offline.
//   - Bypass /api/* entirely (those go through the IndexedDB queue in index.html).

const CACHE_VERSION = 'sunrise-scanner-v1';
const APP_SHELL = [
  '/mobile/',
  '/mobile/index.html',
  '/mobile/manifest.json',
  'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap'
];

self.addEventListener('install', (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_VERSION).then((cache) => cache.addAll(APP_SHELL).catch(() => {}))
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_VERSION).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Never cache API or auth flows. The page-side IndexedDB queue handles offline writes.
  if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/login') || url.pathname.startsWith('/logout')) {
    return;
  }

  // Only handle GETs.
  if (event.request.method !== 'GET') {
    return;
  }

  // Network-first for the shell so updates win when online; cache fallback offline.
  event.respondWith((async () => {
    try {
      const fresh = await fetch(event.request);
      if (fresh && fresh.status === 200 && (url.origin === self.location.origin || url.origin === 'https://fonts.googleapis.com' || url.origin === 'https://fonts.gstatic.com')) {
        const cache = await caches.open(CACHE_VERSION);
        cache.put(event.request, fresh.clone()).catch(() => {});
      }
      return fresh;
    } catch (err) {
      const cached = await caches.match(event.request);
      if (cached) return cached;
      // Last resort: return the cached shell index for navigation requests
      if (event.request.mode === 'navigate') {
        const fallback = await caches.match('/mobile/index.html');
        if (fallback) return fallback;
      }
      throw err;
    }
  })());
});
