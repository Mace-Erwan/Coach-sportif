/* Allure : réseau d'abord, cache en secours pour ouvrir l'appli hors connexion. */
const CACHE = 'allure-v1';
const CORE = ['./', 'index.html', 'vendor/d3.min.js', 'fonts/bc-600.woff2', 'fonts/bc-700.woff2',
  'icons/icon-180.png', 'icons/favicon-64.png', 'manifest.webmanifest'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(CORE)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys()
    .then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  const url = new URL(req.url);
  if (req.method !== 'GET' || url.origin !== location.origin) return;
  const key = url.origin + url.pathname;
  e.respondWith(
    fetch(req)
      .then((res) => {
        if (res.ok) { const copy = res.clone(); caches.open(CACHE).then((c) => c.put(key, copy)); }
        return res;
      })
      .catch(() => caches.match(key).then((hit) => hit || (req.mode === 'navigate' ? caches.match('./') : Response.error())))
  );
});
