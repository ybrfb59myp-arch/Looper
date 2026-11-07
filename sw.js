// Looper: offline cache. Bump VERSION on every release so phones pick up the new files.
const VERSION = '20261107-231516';
const CACHE = 'looper-' + VERSION;
const ASSETS = ['./', './index.html', './rec-worklet.js', './mp3-worker.js', './lame.min.js', './manifest.webmanifest', './icon-192.png', './icon-512.png', './icon-maskable-512.png', './apple-touch-icon.png'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ASSETS.map((u) => new Request(u, { cache: 'reload' })))).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => (k.startsWith('petla-ab-') || k.startsWith('looper-')) && k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
  e.respondWith(
    caches.open(CACHE).then((c) =>
      c.match(req, { ignoreSearch: true }).then((hit) => {
        if (hit) return hit;
        return fetch(req).then((res) => {
          if (res && res.ok && res.type === 'basic') c.put(req, res.clone());
          return res;
        }).catch(() => (req.mode === 'navigate' ? c.match('./') : Response.error()));
      })
    )
  );
});
