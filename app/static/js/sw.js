const CACHE_NAME = 'intranet-facial-v1';

const STATIC_ASSETS = [
  '/login',
  '/static/css/login.css',
  '/static/images/logo.png',
  'https://cdn.jsdelivr.net/npm/@tensorflow/tfjs@4.22.0/dist/tf.min.js',
  'https://cdn.jsdelivr.net/npm/@vladmandic/face-api@1.7.15/dist/face-api.js',
  'https://cdn.jsdelivr.net/npm/@vladmandic/face-api@1.7.15/model/tiny_face_detector_model-weights_manifest.json',
  'https://cdn.jsdelivr.net/npm/@vladmandic/face-api@1.7.15/model/tiny_face_detector_model-shard1',
  'https://cdn.jsdelivr.net/npm/@vladmandic/face-api@1.7.15/model/face_landmark_68_tiny_model-weights_manifest.json',
  'https://cdn.jsdelivr.net/npm/@vladmandic/face-api@1.7.15/model/face_landmark_68_tiny_model-shard1',
  'https://cdn.jsdelivr.net/npm/@vladmandic/face-api@1.7.15/model/face_recognition_model-weights_manifest.json',
  'https://cdn.jsdelivr.net/npm/@vladmandic/face-api@1.7.15/model/face_recognition_model-shard1',
  'https://cdn.jsdelivr.net/npm/@vladmandic/face-api@1.7.15/model/face_recognition_model-shard2'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(async (cache) => {
      for (const url of STATIC_ASSETS) {
        try {
          await cache.add(url);
        } catch (e) {
          // Omitimos errores de precache puntuales para no bloquear instalación.
        }
      }
    }).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(
      keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
    )).then(() => self.clients.claim())
  );
});

function isFacialApi(pathname) {
  return pathname === '/api/listado_fotos' || pathname === '/api/face_cache';
}

self.addEventListener('fetch', (event) => {
  const request = event.request;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);

  if (isFacialApi(url.pathname)) {
    // Network first para mantener frescura, con fallback a cache.
    event.respondWith(
      fetch(request)
        .then((response) => {
          const cloned = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, cloned));
          return response;
        })
        .catch(() => caches.match(request))
    );
    return;
  }

  // Cache first para modelos/scripts estáticos.
  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) return cached;
      return fetch(request).then((response) => {
        const cloned = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(request, cloned));
        return response;
      });
    })
  );
});
