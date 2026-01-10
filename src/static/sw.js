const CACHE_NAME = 'clientpublicip';
const OFFLINE_URL = '/offline';

const PRECACHE_ASSETS = [
    OFFLINE_URL,
    '/static/favicon.svg',
    '/static/icon-192.png',
    '/static/apple-touch-icon.png'
];

// Install: Cache offline page and essential assets
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => cache.addAll(PRECACHE_ASSETS))
            .then(() => self.skipWaiting())
    );
});

// Activate: Clean up old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames
                        .filter((name) => name !== CACHE_NAME)
                        .map((name) => caches.delete(name))
                );
            })
            .then(() => self.clients.claim())
    );
});

// Fetch: Network-first strategy with offline fallback
self.addEventListener('fetch', (event) => {
    // Only handle navigation requests (HTML pages)
    if (event.request.mode === 'navigate') {
        event.respondWith(
            fetch(event.request)
                .catch(() => {
                    return caches.match(OFFLINE_URL);
                })
        );
        return;
    }

    // For other requests (assets), try cache first, then network
    if (event.request.destination === 'image' ||
        event.request.url.includes('/static/')) {
        event.respondWith(
            caches.match(event.request)
                .then((cachedResponse) => {
                    if (cachedResponse) {
                        return cachedResponse;
                    }
                    return fetch(event.request)
                        .then((response) => {
                            // Cache successful responses
                            if (response.ok) {
                                const responseClone = response.clone();
                                caches.open(CACHE_NAME)
                                    .then((cache) => cache.put(event.request, responseClone));
                            }
                            return response;
                        });
                })
        );
        return;
    }

    // For API requests, just use network (no caching)
    event.respondWith(fetch(event.request));
});
