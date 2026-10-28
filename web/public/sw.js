// Offline support (ADR 0024): app shell cached, data network-first with the last copy as fallback.
// Only same-origin GETs are handled; map tiles, satellite and ntfy requests go to the network.
const CACHE = "cropews-v1";
const SHELL = ["./", "manifest.webmanifest", "icon-192.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

async function networkFirst(req, fallback) {
  const cache = await caches.open(CACHE);
  try {
    const res = await fetch(req);
    if (res.ok) cache.put(fallback ?? req, res.clone());
    return res;
  } catch (err) {
    const hit = await cache.match(fallback ?? req);
    if (hit) return hit;
    throw err;
  }
}

async function cacheFirst(req) {
  const cache = await caches.open(CACHE);
  const hit = await cache.match(req);
  if (hit) return hit;
  const res = await fetch(req);
  if (res.ok) cache.put(req, res.clone());
  return res;
}

self.addEventListener("fetch", (e) => {
  const req = e.request;
  const url = new URL(req.url);
  if (req.method !== "GET" || url.origin !== self.location.origin) return;
  if (req.mode === "navigate") e.respondWith(networkFirst(req, new URL("./", self.registration.scope).href));
  else if (url.pathname.includes("/assets/")) e.respondWith(cacheFirst(req));
  else e.respondWith(networkFirst(req));
});
