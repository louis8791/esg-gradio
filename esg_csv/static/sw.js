/* 台南開放資料瀏覽器 - Service Worker
 * 策略:
 *  1. 預先快取離線頁與圖示
 *  2. 頁面導覽:網路優先,斷線時顯示 offline.html
 *  3. 靜態資源(Gradio 前端檔案、圖示):快取優先 + 背景更新
 *  4. API / 即時資料(/gradio_api、/queue 等)一律不快取
 * 更新時請把 VERSION 加 1,舊快取會自動清除。
 */
const VERSION = "v2";
const CACHE = "tainan-pwa-" + VERSION;
const PRECACHE = [
  "/offline.html",
  "/manifest.webmanifest",
  "/pwa-static/icons/icon-192.png",
  "/pwa-static/icons/icon-512.png",
  "/pwa-static/icons/apple-touch-icon.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(PRECACHE)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k.startsWith("tainan-pwa-") && k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

function isStaticAsset(url) {
  return (
    url.pathname.startsWith("/pwa-static/") ||
    url.pathname.startsWith("/assets/") ||
    url.pathname.startsWith("/_app/") ||
    url.pathname.startsWith("/static/") ||
    url.pathname === "/manifest.webmanifest"
  );
}

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;

  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  // 即時 API 不介入
  if (url.pathname.startsWith("/gradio_api") || url.pathname.startsWith("/queue") || url.pathname.startsWith("/run")) return;

  // 頁面導覽:網路優先,失敗顯示離線頁
  if (req.mode === "navigate") {
    event.respondWith(fetch(req).catch(() => caches.match("/offline.html")));
    return;
  }

  // 靜態資源:快取優先,同時背景更新
  if (isStaticAsset(url)) {
    event.respondWith(
      caches.open(CACHE).then((cache) =>
        cache.match(req).then((cached) => {
          const network = fetch(req)
            .then((res) => {
              if (res && res.ok) cache.put(req, res.clone());
              return res;
            })
            .catch(() => cached);
          return cached || network;
        })
      )
    );
  }
});
