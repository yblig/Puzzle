/* Service worker: cache semua file agar game bisa dimainkan offline */
const CACHE = "dunia-puzzle-v1";
const FILES = [
  "./", "index.html", "manifest.webmanifest", "css/style.css",
  "js/app.js", "js/data/words.js", "js/data/quiz.js",
  "js/games/word.js", "js/games/logic.js", "js/games/number.js", "js/games/memory.js", "js/games/strategy.js",
  "assets/icon.svg", "assets/icon-192.png", "assets/icon-512.png",
];
self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(FILES)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET") return;
  e.respondWith(
    fetch(e.request)
      .then((res) => {
        if (res.ok && new URL(e.request.url).origin === location.origin) {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(e.request, copy));
        }
        return res;
      })
      .catch(() => caches.match(e.request).then((r) => r || caches.match("index.html")))
  );
});
