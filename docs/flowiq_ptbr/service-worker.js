/* FlowIQ Service Worker — Cache Offline v4 */
const CACHE_NAME = 'flowiq-v4';
const OFFLINE_URL = './';

const CACHE_URLS = [
  './',
  './index.html',
  './manifest.json',
  './icon-192.png',
  './icon-512.png',
];

/* Install: pré-cache recursos críticos */
self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_NAME).then(function(cache) {
      return cache.addAll(CACHE_URLS).catch(function(err) {
        console.warn('SW cache partial fail:', err);
        return cache.add('./');
      });
    }).then(function() {
      return self.skipWaiting();
    })
  );
});

/* Activate: limpar caches antigos */
self.addEventListener('activate', function(event) {
  event.waitUntil(
    caches.keys().then(function(keyList) {
      return Promise.all(keyList.map(function(key) {
        if (key !== CACHE_NAME) {
          return caches.delete(key);
        }
      }));
    }).then(function() {
      return self.clients.claim();
    })
  );
});

/* Fetch: Network First, fallback to cache */
self.addEventListener('fetch', function(event) {
  if (event.request.method !== 'GET') return;
  
  var url = event.request.url;
  
  // Não interceptar chamadas externas (APIs, CDN externo)
  if (url.includes('supabase.co') || url.includes('googleapis') || 
      url.includes('gstatic') || url.includes('api.anthropic')) {
    return;
  }

  event.respondWith(
    fetch(event.request.clone()).then(function(response) {
      // Cachear respostas bem-sucedidas
      if (response && response.status === 200 && response.type === 'basic') {
        var responseClone = response.clone();
        caches.open(CACHE_NAME).then(function(cache) {
          cache.put(event.request, responseClone);
        });
      }
      return response;
    }).catch(function() {
      // Offline: servir do cache
      return caches.match(event.request).then(function(cached) {
        if (cached) return cached;
        // Fallback para a página principal
        if (event.request.mode === 'navigate') {
          return caches.match('./');
        }
        return new Response('', {status: 503, statusText: 'Offline'});
      });
    })
  );
});

/* Background sync para quando voltar online */
self.addEventListener('sync', function(event) {
  if (event.tag === 'sync-scores') {
    // Sincronizar pontuações pendentes
    event.waitUntil(Promise.resolve());
  }
});

/* Push notifications (futuro) */
self.addEventListener('push', function(event) {
  var data = event.data ? event.data.json() : {};
  var options = {
    body: data.body || 'Hora de treinar seu cérebro! 🧠',
    icon: './icon-192.png',
    badge: './icon-72.png',
    vibrate: [100, 50, 100],
    data: {url: data.url || './'},
    actions: [
      {action: 'play', title: 'Treinar agora'},
      {action: 'dismiss', title: 'Mais tarde'}
    ]
  };
  event.waitUntil(
    self.registration.showNotification(data.title || 'FlowIQ', options)
  );
});

self.addEventListener('notificationclick', function(event) {
  event.notification.close();
  if (event.action === 'play') {
    event.waitUntil(clients.openWindow('./'));
  }
});
