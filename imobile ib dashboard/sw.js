const CACHE_NAME = 'prsh-cache-v12';
const PRECACHE_URLS = [
  '/prshresearch/',
  '/prshresearch/index.html',
  '/prshresearch/time_range_60m.html',
  '/prshresearch/manifest.json',
  '/prshresearch/icon-192.png',
  '/prshresearch/icon-512.png',
  '/prshresearch/favicon.ico',
  '/prshresearch/styles.css',
  '/prshresearch/main.js',
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
    caches.match(event.request).then((cachedResponse) => {
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
