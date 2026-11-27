// Offline support (ADR 0024): app shell cached, data network-first with the last copy as fallback.
// Only same-origin GETs are handled; map tiles, satellite and ntfy requests go to the network.
const CACHE = "cropews-v2";
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

// An explicit visit-pack save must verify that this app version can reopen offline.
self.addEventListener("message", (event) => {
  if (event.data?.type !== "PREPARE_VISITS" || !event.ports[0]) return;
  const reply = event.ports[0];
  event.waitUntil((async () => {
    try {
      const scope = new URL(self.registration.scope);
      const assets = event.data.assets;
      if (!Array.isArray(assets) || assets.length > 100) throw Error("Invalid assets");
      const urls = assets.map((value) => {
        const url = new URL(value);
        if (url.origin !== scope.origin || !url.pathname.startsWith(`${scope.pathname}assets/`) ||
            !/\.(js|css)$/.test(url.pathname) || url.search || url.hash) throw Error("Invalid asset URL");
        return url.href;
      });
      if (!urls.some((u) => u.endsWith(".js"))) throw Error("No app script");
      const cache = await caches.open(CACHE);
      await cache.addAll([...new Set([scope.href, ...urls])]);
      // Static hosts may return their HTML fallback with 200 for a missing asset.
      for (const url of urls) {
        const response = await cache.match(url);
        const type = response?.headers.get("content-type") ?? "";
        if (url.endsWith(".css") ? !type.includes("text/css") : !/javascript/.test(type)) {
          await cache.delete(url);
          throw Error("Invalid asset content");
        }
      }
      reply.postMessage({ ok: true });
    } catch {
      reply.postMessage({ ok: false });
    }
  })());
});
