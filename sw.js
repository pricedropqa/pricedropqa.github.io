// Service worker: lets the app open offline and load fast.
// Change the version number whenever you update index.html so phones get the new version.
const CACHE = "pricedrop-v9";
const SHELL = ["./", "index.html", "manifest.json", "data.csv", "icons/icon-192.png", "icons/icon-512.png"];

self.addEventListener("install", e => {
  // Add files one by one so a single missing file can't break installation
  e.waitUntil(caches.open(CACHE).then(c => Promise.all(SHELL.map(u => c.add(u).catch(() => {})))));
  self.skipWaiting();
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))));
  self.clients.claim();
});
// Network first (fresh prices), fall back to cache when offline
self.addEventListener("fetch", e => {
  if (e.request.method !== "GET") return;
  e.respondWith(
    fetch(e.request).then(res => {
      if (res.ok && new URL(e.request.url).origin === location.origin) {
        const copy = res.clone();
        caches.open(CACHE).then(c => c.put(e.request.url.split("?")[0], copy));
      }
      return res;
    }).catch(() => caches.match(e.request.url.split("?")[0]).then(r => r || caches.match(e.request)))
  );
});
