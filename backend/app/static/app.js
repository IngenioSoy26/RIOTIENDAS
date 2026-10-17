import {
  api,
  avisar,
  cargarPerfil,
  cerrarToken,
  estadoApp,
  guardarToken,
  obtenerToken,
  sincronizarColaOffline,
  tienePermiso,
} from './api_cliente.js';
import { abrirModal, cerrarModal } from './componentes.js';
import {
  establecerNavegacion,
  paginaAlertas,
  paginaClientes,
  paginaCompras,
  paginaConfiguracion,
  paginaDomicilios,
  paginaHistorial,
  paginaInicio,
  paginaInventario,
  paginaMisPedidosCliente,
  paginaNoAutorizada,
  paginaPedidos,
  paginaProveedores,
  paginaReportes,
  paginaTiendaCliente,
  paginaUsuarios,
  paginaVentas,
} from './paginas.js';

const app = document.querySelector('#app');
let rutaActual = 'inicio';

const menuPorRol = {
  administrador: [
    ['inicio', '⌂', 'Inicio'],
    ['ventas', '🛒', 'Ventas / Caja'],
    ['inventario', '📦', 'Inventario'],
    ['compras', '📥', 'Compras'],
    ['proveedores', '🏪', 'Proveedores'],
    ['clientes', '👥', 'Clientes'],
    ['pedidos', '🚚', 'Pedidos'],
    ['alertas', '⚠', 'Alertas'],
    ['reportes', '📊', 'Reportes'],
    ['usuarios', '🔐', 'Usuarios'],
    ['historial', '🕘', 'Historial'],
    ['configuracion', '⚙', 'Configuración'],
  ],
  cajero: [
    ['inicio', '⌂', 'Inicio'],
    ['ventas', '🛒', 'Ventas / Caja'],
    ['inventario', '📦', 'Inventario'],
    ['clientes', '👥', 'Clientes'],
    ['pedidos', '🚚', 'Pedidos'],
    ['reportes', '📊', 'Reportes'],
  ],
  empleado: [
    ['inicio', '⌂', 'Inicio'],
    ['inventario', '📦', 'Inventario'],
    ['compras', '📥', 'Compras'],
    ['proveedores', '🏪', 'Proveedores'],
    ['pedidos', '🚚', 'Pedidos'],
    ['alertas', '⚠', 'Alertas'],
  ],
  domiciliario: [
    ['domicilios', '🛵', 'Mis domicilios'],
  ],
  cliente: [
    ['tienda', '🛍', 'Tienda'],
    ['mis-pedidos', '🚚', 'Mis pedidos'],
  ],
};

const permisoRuta = {
  inicio: 'dashboard.ver',
  ventas: 'ventas.ver',
  inventario: 'productos.ver',
  compras: 'compras.ver',
  proveedores: 'proveedores.ver',
  clientes: 'clientes.ver',
  pedidos: 'pedidos.ver',
  alertas: 'alertas.ver',
  reportes: 'reportes.ver',
  usuarios: 'usuarios.ver',
  historial: 'historial.ver',
  configuracion: null,
  domicilios: 'pedidos.propios',
  tienda: 'catalogo.ver',
  'mis-pedidos': 'pedidos.propios_cliente',
};

const renderizadores = {
  inicio: paginaInicio,
  ventas: paginaVentas,
  inventario: paginaInventario,
  compras: paginaCompras,
  proveedores: paginaProveedores,
  clientes: paginaClientes,
  pedidos: paginaPedidos,
  alertas: paginaAlertas,
  reportes: paginaReportes,
  usuarios: paginaUsuarios,
  historial: paginaHistorial,
  configuracion: paginaConfiguracion,
  domicilios: paginaDomicilios,
  tienda: paginaTiendaCliente,
  'mis-pedidos': paginaMisPedidosCliente,
};

function rutaInicial() {
  if (estadoApp.usuario?.rol === 'cliente') return 'tienda';
  if (estadoApp.usuario?.rol === 'domiciliario') return 'domicilios';
  return 'inicio';
}

function htmlAcceso() {
  return `
    <main class="pantalla-login">
      <section class="login-marca">
        <img src="/static/assets/logo-riotiendas.png" class="logo-login" alt="RioTiendas" />
        <h1>Tu tienda en orden, tu negocio en crecimiento.</h1>
        <p>
          Un sistema pensado como app: caja, inventario, compras, clientes, domicilios,
          reportes y control por roles desde computador, tableta o celular.
        </p>
        <div class="login-beneficios">
          <span>✓ Inventario en tiempo real</span>
          <span>✓ Caja rápida con código de barras</span>
          <span>✓ Pedidos y seguimiento a domicilio</span>
          <span>✓ PWA instalable</span>
        </div>
      </section>

      <section class="login-panel">
        <div class="tarjeta-login">
          <div class="pestanas-login">
            <button class="pestana activa" data-modo="ingresar">Ingresar</button>
            <button class="pestana" data-modo="registrar">Crear tienda</button>
          </div>

          <div id="formulario-ingreso">
            <h2>Ingresar</h2>
            <p class="subtitulo">Selecciona una cuenta demo o usa tus credenciales.</p>
            <form id="form-login">
              <div class="campo"><label>Correo</label><input id="login-correo" type="email" value="admin@riotiendas.app" required /></div>
              <div class="campo"><label>Contraseña</label><input id="login-clave" type="password" value="Rio2026*" required /></div>
              <button class="boton boton-primario boton-ancho" type="submit">Ingresar</button>
            </form>
            <button id="recuperar-clave" class="enlace-boton">¿Olvidaste tu contraseña?</button>

            <div class="cuentas-demo">
              <strong>Simular roles</strong><br>
              <button data-demo="admin@riotiendas.app">Administrador</button>
              <button data-demo="cajero@riotiendas.app">Cajero</button>
              <button data-demo="empleado@riotiendas.app">Empleado</button>
              <button data-demo="domiciliario@riotiendas.app">Domiciliario</button>
              <button data-demo="cliente@riotiendas.app">Cliente</button>
              <p><small>Clave común: <strong>Rio2026*</strong></small></p>
            </div>
          </div>

          <div id="formulario-registro" class="oculto">
            <h2>Crear una tienda</h2>
            <p class="subtitulo">El registro crea el negocio y su primer administrador.</p>
            <form id="form-registro-tienda">
              <div class="campo"><label>Nombre de la tienda</label><input id="reg-tienda" required /></div>
              <div class="campo"><label>Nombre del administrador</label><input id="reg-admin" required /></div>
              <div class="campo"><label>Correo</label><input id="reg-correo" type="email" required /></div>
              <div class="campo"><label>Teléfono</label><input id="reg-telefono" /></div>
              <div class="campo"><label>Dirección</label><input id="reg-direccion" /></div>
              <div class="campo"><label>Contraseña</label><input id="reg-clave" type="password" minlength="8" required /></div>
              <button class="boton boton-primario boton-ancho" type="submit">Crear tienda e ingresar</button>
            </form>
          </div>
        </div>
      </section>
    </main>
  `;
}

function prepararAcceso() {
  document.querySelectorAll('[data-modo]').forEach(boton => {
    boton.addEventListener('click', () => {
      document.querySelectorAll('[data-modo]').forEach(b => b.classList.remove('activa'));
      boton.classList.add('activa');
      const modo = boton.dataset.modo;
      document.querySelector('#formulario-ingreso').classList.toggle('oculto', modo !== 'ingresar');
      document.querySelector('#formulario-registro').classList.toggle('oculto', modo !== 'registrar');
    });
  });

  document.querySelectorAll('[data-demo]').forEach(boton => {
    boton.addEventListener('click', () => {
      document.querySelector('#login-correo').value = boton.dataset.demo;
      document.querySelector('#login-clave').value = 'Rio2026*';
    });
  });

  document.querySelector('#form-login').addEventListener('submit', async evento => {
    evento.preventDefault();
    const correo = document.querySelector('#login-correo').value.trim();
    const contrasena = document.querySelector('#login-clave').value;
    try {
      const resultado = await api('/autenticacion/ingresar', {
        method: 'POST',
        body: JSON.stringify({ correo, contrasena }),
      });
      guardarToken(resultado.access_token);
      await cargarPerfil();
      avisar(`Bienvenido, ${estadoApp.usuario.nombre}.`);
      mostrarAplicacion();
    } catch (error) {
      avisar(error.message, 'error');
    }
  });

  document.querySelector('#form-registro-tienda').addEventListener('submit', async evento => {
    evento.preventDefault();
    try {
      const resultado = await api('/autenticacion/registrar-tienda', {
        method: 'POST',
        body: JSON.stringify({
          nombre_tienda: document.querySelector('#reg-tienda').value.trim(),
          nombre_administrador: document.querySelector('#reg-admin').value.trim(),
          correo: document.querySelector('#reg-correo').value.trim(),
          telefono: document.querySelector('#reg-telefono').value.trim(),
          direccion: document.querySelector('#reg-direccion').value.trim(),
          contrasena: document.querySelector('#reg-clave').value,
        }),
      });
      guardarToken(resultado.access_token);
      await cargarPerfil();
      avisar('Tienda creada correctamente.');
      mostrarAplicacion();
    } catch (error) {
      avisar(error.message, 'error');
    }
  });

  document.querySelector('#recuperar-clave').addEventListener('click', () => {
    abrirModal('Recuperar contraseña', `
      <p>En esta versión demo el token de recuperación se muestra en pantalla. En producción se enviaría por correo.</p>
      <div class="campo"><label>Correo</label><input id="rec-correo" type="email" /></div>
      <button id="solicitar-recuperacion" class="boton boton-primario boton-ancho">Generar recuperación</button>
      <div id="paso-restablecer"></div>
    `, '520px');
    document.querySelector('#solicitar-recuperacion').addEventListener('click', async () => {
      try {
        const datos = await api('/autenticacion/solicitar-recuperacion', {
          method: 'POST',
          body: JSON.stringify({ correo: document.querySelector('#rec-correo').value.trim() }),
        });
        if (!datos.token_demo) {
          avisar(datos.mensaje);
          return;
        }
        document.querySelector('#paso-restablecer').innerHTML = `
          <div class="campo" style="margin-top:1rem"><label>Nueva contraseña</label><input id="rec-nueva" type="password" minlength="8" /></div>
          <button id="confirmar-restablecimiento" class="boton boton-azul boton-ancho">Cambiar contraseña</button>
        `;
        document.querySelector('#confirmar-restablecimiento').addEventListener('click', async () => {
          try {
            await api('/autenticacion/restablecer-contrasena', {
              method: 'POST',
              body: JSON.stringify({ token: datos.token_demo, nueva_contrasena: document.querySelector('#rec-nueva').value }),
            });
            cerrarModal();
            avisar('Contraseña actualizada. Ya puedes iniciar sesión.');
          } catch (error) { avisar(error.message, 'error'); }
        });
      } catch (error) { avisar(error.message, 'error'); }
    });
  });
}

function construirMenu() {
  const rol = estadoApp.usuario.rol;
  const base = menuPorRol[rol] || [];
  return base.filter(([ruta]) => {
    const permiso = permisoRuta[ruta];
    if (!permiso) return true;
    return tienePermiso(permiso);
  }).map(([ruta, icono, texto]) => `
    <button data-ruta="${ruta}" class="${ruta === rutaActual ? 'activo' : ''}">
      <span>${icono}</span><span>${texto}</span>
    </button>
  `).join('');
}

function htmlShell() {
  const usuario = estadoApp.usuario;
  return `
    <div class="app-shell">
      <aside class="sidebar" id="sidebar">
        <img src="/static/assets/logo-riotiendas.png" class="logo-sidebar" alt="RioTiendas" />
        <div class="datos-tienda">
          <strong>${usuario.tienda?.nombre || 'RioTiendas'}</strong>
          <span>${usuario.tienda?.direccion || 'Gestión comercial'}</span>
        </div>
        <nav class="menu" id="menu-principal">${construirMenu()}</nav>
        <div class="usuario-sidebar">
          <strong>${usuario.nombre}</strong><br>
          <span>${usuario.correo}</span><br>
          <span class="rol">${usuario.rol}</span>
          <button id="cerrar-sesion" class="boton boton-claro boton-ancho" style="margin-top:.8rem">Cerrar sesión</button>
        </div>
      </aside>

      <section class="area-principal">
        <header class="topbar">
          <button id="abrir-menu" class="boton boton-claro mobile-top">☰</button>
          ${tienePermiso('busqueda.usar') ? '<div class="busqueda-global"><input id="busqueda-global" placeholder="Buscar productos, clientes, proveedores o pedidos..." /></div>' : '<div></div>'}
          <div class="topbar-acciones">
            <span id="estado-red" class="estado-red ${navigator.onLine ? 'en-linea' : 'sin-linea'}">${navigator.onLine ? '● En línea' : '● Sin conexión'}</span>
            <button id="instalar-app" class="boton boton-claro oculto">Instalar app</button>
          </div>
        </header>
        <main class="contenido" id="vista"></main>
      </section>
    </div>
  `;
}

async function ejecutarRuta(ruta) {
  rutaActual = ruta;
  const permiso = permisoRuta[ruta];
  if (permiso && !tienePermiso(permiso)) {
    paginaNoAutorizada();
    return;
  }
  const funcion = renderizadores[ruta];
  if (!funcion) return;
  document.querySelectorAll('[data-ruta]').forEach(b => b.classList.toggle('activo', b.dataset.ruta === ruta));
  document.querySelector('#sidebar')?.classList.remove('abierta');
  try {
    await funcion();
  } catch (error) {
    document.querySelector('#vista').innerHTML = `<section class="panel"><h2>No fue posible cargar el módulo</h2><p>${error.message}</p></section>`;
    avisar(error.message, 'error');
  }
}

function prepararShell() {
  document.querySelectorAll('[data-ruta]').forEach(boton => {
    boton.addEventListener('click', () => ejecutarRuta(boton.dataset.ruta));
  });
  document.querySelector('#cerrar-sesion').addEventListener('click', () => {
    cerrarToken();
    mostrarAcceso();
  });
  document.querySelector('#abrir-menu')?.addEventListener('click', () => {
    document.querySelector('#sidebar').classList.toggle('abierta');
  });

  const buscador = document.querySelector('#busqueda-global');
  let temporizadorBusqueda;
  buscador?.addEventListener('input', evento => {
    clearTimeout(temporizadorBusqueda);
    const q = evento.target.value.trim();
    if (q.length < 2) {
      document.querySelector('#resultados-busqueda')?.remove();
      return;
    }
    temporizadorBusqueda = setTimeout(async () => {
      try {
        const resultados = await api(`/buscar?q=${encodeURIComponent(q)}`);
        document.querySelector('#resultados-busqueda')?.remove();
        const caja = document.createElement('div');
        caja.id = 'resultados-busqueda';
        caja.className = 'resultados-busqueda';
        caja.innerHTML = resultados.length ? resultados.map(item => `
          <button><strong>${item.titulo}</strong><small>${item.tipo} · ${item.subtitulo}</small></button>
        `).join('') : '<div class="vacio">Sin resultados.</div>';
        buscador.parentElement.appendChild(caja);
      } catch {
        // La búsqueda no interrumpe la operación principal si falla.
      }
    }, 250);
  });

  const botonInstalar = document.querySelector('#instalar-app');
  if (estadoApp.instalacionPwa) botonInstalar.classList.remove('oculto');
  botonInstalar?.addEventListener('click', async () => {
    if (!estadoApp.instalacionPwa) return;
    estadoApp.instalacionPwa.prompt();
    await estadoApp.instalacionPwa.userChoice;
    estadoApp.instalacionPwa = null;
    botonInstalar.classList.add('oculto');
  });
}

async function mostrarAplicacion() {
  if (!estadoApp.usuario) await cargarPerfil();
  if (!estadoApp.usuario) return mostrarAcceso();
  rutaActual = rutaInicial();
  app.innerHTML = htmlShell();
  prepararShell();
  await sincronizarColaOffline();
  await ejecutarRuta(rutaActual);
}

function mostrarAcceso() {
  app.innerHTML = htmlAcceso();
  prepararAcceso();
}

establecerNavegacion(ejecutarRuta);

window.addEventListener('beforeinstallprompt', evento => {
  evento.preventDefault();
  estadoApp.instalacionPwa = evento;
  document.querySelector('#instalar-app')?.classList.remove('oculto');
});

function actualizarEstadoRed() {
  const elemento = document.querySelector('#estado-red');
  if (!elemento) return;
  elemento.className = `estado-red ${navigator.onLine ? 'en-linea' : 'sin-linea'}`;
  elemento.textContent = navigator.onLine ? '● En línea' : '● Sin conexión';
}
window.addEventListener('online', actualizarEstadoRed);
window.addEventListener('offline', actualizarEstadoRed);

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => navigator.serviceWorker.register('/sw.js').catch(console.error));
}

(async function iniciar() {
  if (obtenerToken()) {
    const perfil = await cargarPerfil();
    if (perfil) return mostrarAplicacion();
  }
  mostrarAcceso();
})();
