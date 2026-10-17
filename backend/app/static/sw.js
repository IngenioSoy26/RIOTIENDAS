const CACHE = 'riotiendas-v2';
const ARCHIVOS = [
  '/',
  '/static/estilos.css',
  '/static/app.js',
  '/static/api_cliente.js',
  '/static/componentes.js',
  '/static/paginas.js',
  '/static/assets/logo-riotiendas.png',
  '/static/assets/icon-192.png',
  '/static/assets/icon-512.png'
];

self.addEventListener('install', evento => {
  evento.waitUntil(caches.open(CACHE).then(cache => cache.addAll(ARCHIVOS)));
  self.skipWaiting();
});

self.addEventListener('activate', evento => {
  // Borra los cachés de versiones anteriores para no servir archivos antiguos.
  evento.waitUntil(
    caches.keys()
      .then(claves => Promise.all(
        claves.filter(clave => clave !== CACHE).map(clave => caches.delete(clave))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', evento => {
  if (evento.request.method !== 'GET') return;

  const esNavegacion = evento.request.mode === 'navigate';
  // Las llamadas a la API siempre van a la red: nunca deben recibir el HTML de
  // la aplicación ni datos de inventario que ya quedaron desactualizados.
  if (!esNavegacion && new URL(evento.request.url).pathname.startsWith('/api/')) return;

  evento.respondWith(
    fetch(evento.request)
      .then(respuesta => {
        const copia = respuesta.clone();
        caches.open(CACHE).then(cache => cache.put(evento.request, copia));
        return respuesta;
      })
      .catch(() => caches.match(evento.request).then(r => r || (esNavegacion ? caches.match('/') : Response.error())))
  );
});
