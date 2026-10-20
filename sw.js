/* ============================================================================
 * 汉堡包计划 · Service Worker
 * ----------------------------------------------------------------------------
 * 目标：一部手机、一个链接、离线可用、能加到桌面。
 * 策略：
 *   - 导航请求：网络优先，失败回落缓存的 index.html（保证更新能立刻拿到）
 *   - 字体 / 图标：缓存优先（体积大又不常变，装一次就够）
 *   - 其它同源资源：缓存优先 + 后台更新
 * ========================================================================= */
const VERSION = 'hb-v1.23.0';
const CORE = [
  './',
  './index.html',
  './manifest.webmanifest',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/icon-maskable-512.png',
  './icons/apple-touch-icon-180.png',
  './fonts/ResourceHanRoundedCN-subset.woff2',
  './fonts/ZCOOLKuaiLe-subset.woff2',
  './fonts/Baloo2-Medium-subset.woff2',
  './fonts/Baloo2-SemiBold-subset.woff2',
  './fonts/Baloo2-Bold-subset.woff2'
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(VERSION)
      .then(c => Promise.allSettled(CORE.map(u => c.add(new Request(u, { cache: 'reload' })))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== VERSION).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if(req.method !== 'GET') return;

  const url = new URL(req.url);
  if(url.origin !== self.location.origin) return;

  /* 页面导航：网络优先 */
  if(req.mode === 'navigate'){
    e.respondWith(
      fetch(req)
        .then(res => {
          const copy = res.clone();
          caches.open(VERSION).then(c => c.put('./index.html', copy)).catch(() => {});
          return res;
        })
        .catch(() => caches.match('./index.html').then(r => r || caches.match('./')))
    );
    return;
  }

  /* 静态资源：缓存优先 */
  e.respondWith(
    caches.match(req).then(hit => {
      if(hit) return hit;
      return fetch(req).then(res => {
        if(res && res.status === 200 && res.type === 'basic'){
          const copy = res.clone();
          caches.open(VERSION).then(c => c.put(req, copy)).catch(() => {});
        }
        return res;
      }).catch(() => hit);
    })
  );
});
