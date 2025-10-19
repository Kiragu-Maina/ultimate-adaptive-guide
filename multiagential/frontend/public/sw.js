/**
 * Service Worker for Push Notifications
 * Handles background notifications and click events
 */

const CACHE_NAME = 'alkenacode-v1';

// Install event
self.addEventListener('install', () => {
  console.log('Service Worker: Installed');
  self.skipWaiting();
});

// Activate event
self.addEventListener('activate', (event) => {
  console.log('Service Worker: Activated');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cache) => {
          if (cache !== CACHE_NAME) {
            console.log('Service Worker: Clearing Old Cache');
            return caches.delete(cache);
          }
        })
      );
    })
  );
  return self.clients.claim();
});

// Handle notification click
self.addEventListener('notificationclick', (event) => {
  console.log('Notification clicked:', event.notification.tag);

  event.notification.close();

  const data = event.notification.data || {};
  const urlToOpen = data.url || self.location.origin;

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      // Check if there's already a window/tab open
      for (let i = 0; i < clientList.length; i++) {
        const client = clientList[i];
        if (client.url === urlToOpen && 'focus' in client) {
          return client.focus();
        }
      }

      // If not, open a new window/tab
      if (clients.openWindow) {
        return clients.openWindow(urlToOpen);
      }
    })
  );
});

// Handle push event (for future web push integration)
self.addEventListener('push', (event) => {
  console.log('Push received:', event);

  if (event.data) {
    const data = event.data.json();

    const options = {
      body: data.body || 'New notification from AlkenaCode',
      icon: data.icon || '/icon-192.png',
      badge: data.badge || '/badge-72.png',
      vibrate: [200, 100, 200],
      data: data.data || {},
      requireInteraction: true,
    };

    event.waitUntil(
      self.registration.showNotification(data.title || 'AlkenaCode', options)
    );
  }
});

// Handle messages from the main thread
self.addEventListener('message', (event) => {
  console.log('Service Worker received message:', event.data);

  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
