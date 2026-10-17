const API_BASE = '/api';
const CLAVE_TOKEN = 'riotiendas_token';
const CLAVE_COLA = 'riotiendas_cola_offline';

export const estadoApp = {
  usuario: null,
  instalacionPwa: null,
};

export function obtenerToken() {
  return localStorage.getItem(CLAVE_TOKEN);
}

export function guardarToken(token) {
  localStorage.setItem(CLAVE_TOKEN, token);
}

export function cerrarToken() {
  localStorage.removeItem(CLAVE_TOKEN);
  estadoApp.usuario = null;
}

export function dinero(valor) {
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    maximumFractionDigits: 0,
  }).format(Number(valor || 0));
}

export function fechaCorta(valor) {
  if (!valor) return '';
  const fecha = new Date(valor);
  if (Number.isNaN(fecha.getTime())) return valor;
  return fecha.toLocaleString('es-CO', { dateStyle: 'short', timeStyle: 'short' });
}

export function escapar(valor = '') {
  return String(valor)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

export function avisar(mensaje, tipo = 'exito') {
  const elemento = document.querySelector('#notificacion');
  if (!elemento) return;
  elemento.textContent = mensaje;
  elemento.className = `notificacion ${tipo}`;
  setTimeout(() => {
    elemento.classList.add('oculto');
  }, 3500);
}

function leerCola() {
  try {
    return JSON.parse(localStorage.getItem(CLAVE_COLA) || '[]');
  } catch {
    return [];
  }
}

function guardarCola(cola) {
  localStorage.setItem(CLAVE_COLA, JSON.stringify(cola));
}

function puedeIrACola(ruta, metodo) {
  if (metodo !== 'POST') return false;
  // Solo los pedidos se encolan. Las ventas POS no se confirman sin servidor,
  // porque hacerlo podría generar sobreventa si hay varias cajas trabajando a la vez.
  return ruta === '/pedidos';
}

function encolarPeticion(ruta, opciones) {
  const cola = leerCola();
  cola.push({
    id_local: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    ruta,
    metodo: opciones.method || 'POST',
    cuerpo: opciones.body ? JSON.parse(opciones.body) : null,
    creada_en: new Date().toISOString(),
  });
  guardarCola(cola);
}

export async function api(ruta, opciones = {}) {
  const token = obtenerToken();
  const configuracion = {
    method: opciones.method || 'GET',
    headers: {
      ...(opciones.body ? { 'Content-Type': 'application/json' } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(opciones.headers || {}),
    },
    ...opciones,
  };

  let respuesta;
  try {
    respuesta = await fetch(`${API_BASE}${ruta}`, configuracion);
  } catch (error) {
    // Si la PWA está sin conexión, guardamos algunas operaciones para sincronizarlas luego.
    if (puedeIrACola(ruta, configuracion.method)) {
      encolarPeticion(ruta, configuracion);
      avisar('Sin conexión: la operación quedó pendiente de sincronización.', 'aviso');
      return { pendiente_offline: true };
    }
    throw new Error('No hay conexión con el servidor.');
  }

  if (respuesta.status === 401) {
    cerrarToken();
  }

  if (!respuesta.ok) {
    let detalle = `Error ${respuesta.status}`;
    try {
      const cuerpo = await respuesta.json();
      detalle = cuerpo.detail || cuerpo.mensaje || detalle;
    } catch {
      // Si la respuesta no trae JSON, conservamos el mensaje genérico.
    }
    throw new Error(detalle);
  }

  const tipoContenido = respuesta.headers.get('content-type') || '';
  if (tipoContenido.includes('application/json')) return respuesta.json();
  return respuesta;
}

export async function cargarPerfil() {
  if (!obtenerToken()) return null;
  try {
    estadoApp.usuario = await api('/autenticacion/yo');
    return estadoApp.usuario;
  } catch {
    cerrarToken();
    return null;
  }
}

export function tienePermiso(permiso) {
  const permisos = estadoApp.usuario?.permisos || [];
  return permisos.includes('*') || permisos.includes(permiso);
}

export function esRol(rol) {
  return estadoApp.usuario?.rol === rol;
}

export async function sincronizarColaOffline() {
  const cola = leerCola();
  if (!cola.length || !obtenerToken()) return;

  const pendientes = [];
  let sincronizadas = 0;

  for (const elemento of cola) {
    try {
      await api(elemento.ruta, {
        method: elemento.metodo,
        body: JSON.stringify(elemento.cuerpo),
      });
      sincronizadas += 1;
    } catch {
      pendientes.push(elemento);
    }
  }

  guardarCola(pendientes);
  if (sincronizadas) {
    avisar(`${sincronizadas} operación(es) sin conexión fueron sincronizadas.`);
  }
}

window.addEventListener('online', sincronizarColaOffline);
