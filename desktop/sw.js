/**
 * ResumeAI Desktop - Service Worker
 * Provides offline capability and caching
 */

const CACHE_NAME = 'resumeai-v1';
const STATIC_CACHE = 'resumeai-static-v1';
const DYNAMIC_CACHE = 'resumeai-dynamic-v1';

// Static assets to cache
const STATIC_ASSETS = [
    '/',
    '/index.html',
    '/manifest.json',
    '/src/css/styles.css',
    '/src/js/api.js',
    '/src/js/storage.js',
    '/src/js/utils.js',
    '/src/js/app.js',
    '/src/js/components/toast.js',
    '/src/js/components/modal.js',
    '/src/js/components/charts.js',
    '/src/js/views/dashboard.js',
    '/src/js/views/resume.js',
    '/src/js/views/generate.js',
    '/src/js/views/tracking.js',
    '/src/js/views/analytics.js',
    '/src/js/views/settings.js',
];

// API endpoints to cache
const API_CACHE_LIMIT = 50;

// Install event - cache static assets
self.addEventListener('install', (event) => {
    console.log('[ServiceWorker] Install');
    event.waitUntil(
        caches.open(STATIC_CACHE).then((cache) => {
            console.log('[ServiceWorker] Caching static assets');
            return cache.addAll(STATIC_ASSETS);
        })
    );
    self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('[ServiceWorker] Activate');
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames
                    .filter((name) => name !== STATIC_CACHE && name !== DYNAMIC_CACHE)
                    .map((name) => {
                        console.log('[ServiceWorker] Deleting old cache:', name);
                        return caches.delete(name);
                    })
            );
        })
    );
    self.clients.claim();
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }

    // Skip chrome-extension and other non-http(s) requests
    if (!url.protocol.startsWith('http')) {
        return;
    }

    // Handle API requests
    if (url.pathname.startsWith('/v1/') || url.pathname.startsWith('/api/')) {
        event.respondWith(handleAPIRequest(request));
        return;
    }

    // Handle static assets
    if (isStaticAsset(url.pathname)) {
        event.respondWith(handleStaticAsset(request));
        return;
    }

    // Handle navigation requests
    if (request.mode === 'navigate') {
        event.respondWith(handleNavigation(request));
        return;
    }

    // Default: network first, fallback to cache
    event.respondWith(
        fetch(request)
            .then((response) => {
                // Clone response for caching
                const responseClone = response.clone();
                caches.open(DYNAMIC_CACHE).then((cache) => {
                    cache.put(request, responseClone);
                });
                return response;
            })
            .catch(() => {
                return caches.match(request);
            })
    );
});

/**
 * Check if URL is a static asset
 */
function isStaticAsset(pathname) {
    return (
        pathname.endsWith('.css') ||
        pathname.endsWith('.js') ||
        pathname.endsWith('.png') ||
        pathname.endsWith('.jpg') ||
        pathname.endsWith('.svg') ||
        pathname.endsWith('.ico') ||
        pathname.endsWith('.woff') ||
        pathname.endsWith('.woff2')
    );
}

/**
 * Handle static asset requests
 */
async function handleStaticAsset(request) {
    const cached = await caches.match(request);
    if (cached) {
        return cached;
    }

    try {
        const response = await fetch(request);
        if (response.ok) {
            const cache = await caches.open(STATIC_CACHE);
            cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        return new Response('Asset not available offline', {
            status: 503,
            statusText: 'Service Unavailable',
        });
    }
}

/**
 * Handle API requests with caching
 */
async function handleAPIRequest(request) {
    try {
        // Try network first for fresh data
        const response = await fetch(request);
        if (response.ok) {
            // Cache successful responses
            const cache = await caches.open(DYNAMIC_CACHE);
            await cache.put(request, response.clone());
            
            // Limit cache size
            await limitCacheSize(DYNAMIC_CACHE, API_CACHE_LIMIT);
        }
        return response;
    } catch (error) {
        // Fallback to cache
        const cached = await caches.match(request);
        if (cached) {
            return cached;
        }

        // Return offline response
        return new Response(
            JSON.stringify({
                error: 'offline',
                message: 'You are offline. Some features may be limited.',
            }),
            {
                status: 503,
                headers: { 'Content-Type': 'application/json' },
            }
        );
    }
}

/**
 * Handle navigation requests
 */
async function handleNavigation(request) {
    try {
        const response = await fetch(request);
        if (response.ok) {
            return response;
        }
    } catch (error) {
        // Fallback to index.html for SPA routing
        const cached = await caches.match('/index.html');
        if (cached) {
            return cached;
        }
    }
    return new Response('Page not available offline', {
        status: 503,
        statusText: 'Service Unavailable',
    });
}

/**
 * Limit cache size by removing oldest entries
 */
async function limitCacheSize(cacheName, maxItems) {
    const cache = await caches.open(cacheName);
    const keys = await cache.keys();
    
    if (keys.length > maxItems) {
        await cache.delete(keys[0]);
    }
}

/**
 * Handle messages from main thread
 */
self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }

    if (event.data && event.data.type === 'CLEAR_CACHE') {
        caches.keys().then((cacheNames) => {
            cacheNames.forEach((name) => {
                if (name !== STATIC_CACHE) {
                    caches.delete(name);
                }
            });
        });
    }
});

/**
 * Background sync for offline actions
 */
self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-applications') {
        event.waitUntil(syncApplications());
    }
});

/**
 * Sync pending applications when back online
 */
async function syncApplications() {
    // This would sync any pending offline actions
    console.log('[ServiceWorker] Syncing applications...');
}

/**
 * Push notifications
 */
self.addEventListener('push', (event) => {
    const data = event.data ? event.data.json() : {};
    const title = data.title || 'ResumeAI';
    const options = {
        body: data.body || 'New update available',
        icon: '/icons/icon-192.png',
        badge: '/icons/icon-72.png',
        data: data.url || '/',
    };

    event.waitUntil(self.registration.showNotification(title, options));
});

/**
 * Handle notification clicks
 */
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    event.waitUntil(
        clients.matchAll({ type: 'window' }).then((clientList) => {
            // Focus existing window or open new one
            for (const client of clientList) {
                if (client.url === event.notification.data && 'focus' in client) {
                    return client.focus();
                }
            }
            if (clients.openWindow) {
                return clients.openWindow(event.notification.data);
            }
        })
    );
});
