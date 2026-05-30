const CACHE_NAME = 'bloodlink-v5';

// Safe static assets only
const STATIC_ASSETS = [
    '/manifest.json',

    '/static/images/icon-192.png',
    '/static/images/icon-512.png',

    // Bootstrap CDN
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js',
];

// INSTALL
self.addEventListener('install', event => {

    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(STATIC_ASSETS))
    );

    self.skipWaiting();
});

// ACTIVATE
self.addEventListener('activate', event => {

    event.waitUntil(
        caches.keys().then(keys => {
            return Promise.all(
                keys.map(key => {
                    if (key !== CACHE_NAME) {
                        return caches.delete(key);
                    }
                })
            );
        })
    );

    self.clients.claim();
});

// FETCH
self.addEventListener('fetch', event => {

    // Only handle GET requests
    if (event.request.method !== 'GET') {
        return;
    }

    const url = new URL(event.request.url);

    // NEVER cache authentication/admin pages
    if (
        url.pathname.startsWith('/login') ||
        url.pathname.startsWith('/logout') ||
        url.pathname.startsWith('/admin') ||
        url.pathname.startsWith('/accounts')
    ) {
        return;
    }

    // NEVER cache API/JSON requests
    const acceptHeader = event.request.headers.get('accept');

    if (
        acceptHeader &&
        acceptHeader.includes('application/json')
    ) {
        return;
    }

    // STATIC FILES → CACHE FIRST
    if (
        url.pathname.startsWith('/static/') ||
        url.pathname.startsWith('/media/') ||
        url.hostname.includes('cdn.jsdelivr.net')
    ) {

        event.respondWith(

            caches.match(event.request).then(cached => {

                // Return cached version if available
                if (cached) {
                    return cached;
                }

                // Otherwise fetch from network
                return fetch(event.request)
                    .then(response => {

                        // Don't cache invalid responses
                        if (
                            !response ||
                            response.status !== 200 ||
                            response.redirected
                        ) {
                            return response;
                        }

                        const responseClone = response.clone();

                        caches.open(CACHE_NAME)
                            .then(cache => {
                                cache.put(event.request, responseClone);
                            });

                        return response;
                    });

            })

        );

        return;
    }

    // DONOR CARD → NETWORK FIRST, CACHE FOR OFFLINE
    if (url.pathname.startsWith('/recipients/donor/')) {

        event.respondWith(

            caches.open(CACHE_NAME).then(cache => {

                return fetch(event.request)
                    .then(response => {

                        // Save a fresh copy whenever online
                        if (response && response.status === 200 && !response.redirected) {
                            cache.put(event.request, response.clone());
                        }

                        return response;
                    })

                    .catch(() => {
                        // Offline → serve cached card
                        return caches.match(event.request);
                    });

            })

        );

        return;
    }

    // DYNAMIC PAGES → NETWORK FIRST
    event.respondWith(

        fetch(event.request)
            .then(response => {

                // Never cache redirects/errors
                if (
                    !response ||
                    response.status !== 200 ||
                    response.redirected
                ) {
                    return response;
                }

                return response;
            })

            // Offline fallback
            .catch(() => {

                // Try cached version if offline
                return caches.match(event.request);

            })

    );

});

// PUSH NOTIFICATIONS
self.addEventListener('push', event => {

    const data = event.data
        ? event.data.json()
        : {};

    const title = data.title || 'BloodLink';

    const options = {
        body: data.body || 'You have a new notification.',
        icon: '/static/images/icon-192.png',
        badge: '/static/images/icon-192.png',
        data: {
            url: data.url || '/',
        },
    };

    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

// NOTIFICATION CLICK
self.addEventListener('notificationclick', event => {

    event.notification.close();

    event.waitUntil(
        clients.openWindow(
            event.notification.data.url || '/'
        )
    );
});