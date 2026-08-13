const CACHE_NAME = 'prsh-cache-v24';
const PRECACHE_URLS = [
  '/prshresearch/',
  '/prshresearch/index.html?bust=1',
  '/prshresearch/dashboard.html?bust=1',
  '/prshresearch/styles.css?bust=1',
  '/prshresearch/main.js?bust=1',
  '/prshresearch/data/time_range_10m.json',
  '/prshresearch/data/time_range_120m.json',
  '/prshresearch/data/time_range_15m.json',
  '/prshresearch/data/time_range_15m_step.json',
  '/prshresearch/data/time_range_30m.json',
  '/prshresearch/data/time_range_30m_15m_step.json',
  '/prshresearch/data/time_range_45m.json',
  '/prshresearch/data/time_range_60m.json',
  '/prshresearch/data/time_range_7m.json',
  '/prshresearch/data/time_range_7m_1m_step.json',
  '/prshresearch/manifest.json',
  '/prshresearch/icon-192.png',
  '/prshresearch/icon-512.png',
  '/prshresearch/favicon.ico',
  '/prshresearch/offline.html',
  '/prshresearch/pdr_analysis.html',
  '/prshresearch/pwr_analysis.html'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(PRECACHE_URLS);
    }).then(() => {
      return self.skipWaiting();
    })
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      return clients.claim();
    })
  );
});

self.addEventListener('fetch', (event) => {
  // Only cache GET requests
  if (event.request.method !== 'GET') return;

  event.respondWith(
    caches.match(event.request, { ignoreSearch: true }).then((cachedResponse) => {
      if (cachedResponse) {
        // Fetch in background to update cache (stale-while-revalidate)
        event.waitUntil(
          fetch(event.request).then((networkResponse) => {
            if (networkResponse && networkResponse.status === 200) {
              caches.open(CACHE_NAME).then((cache) => {
                cache.put(event.request, networkResponse.clone());
              });
            }
          }).catch(() => {})
        );
        return cachedResponse;
      }

      // If not in cache, fetch from network
      return fetch(event.request).then((networkResponse) => {
        if (networkResponse && networkResponse.status === 200) {
          const responseToCache = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseToCache);
          });
        }
        return networkResponse;
      }).catch(() => {
        // Return offline page for navigation requests (HTML pages)
        if (event.request.mode === 'navigate') {
          return caches.match('/prshresearch/offline.html');
        }
        // For API data or other assets, we just return undefined/fail silently
      });
    })
  );
});
