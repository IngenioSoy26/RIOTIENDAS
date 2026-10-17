import {
  api,
  avisar,
  dinero,
  escapar,
  esRol,
  estadoApp,
  fechaCorta,
  tienePermiso,
} from './api_cliente.js';
import {
  abrirModal,
  cerrarModal,
  dibujarBarras,
  estadoInventario,
  tablaHTML,
  tarjetaKpi,
  tarjetaProducto,
} from './componentes.js';

let navegar = () => {};
export function establecerNavegacion(funcion) {
  navegar = funcion;
}

function encabezado(titulo, descripcion, acciones = '') {
  return `
    <div class="encabezado-pagina">
      <div>
        <h1>${escapar(titulo)}</h1>
        <p>${escapar(descripcion)}</p>
      </div>
      <div class="acciones">${acciones}</div>
    </div>
  `;
}

function boton(texto, clase = 'boton-primario', id = '') {
  return `<button ${id ? `id="${id}"` : ''} class="boton ${clase}">${texto}</button>`;
}

function obtenerContenedor() {
  return document.querySelector('#vista');
}

function valorInput(id) {
  return document.querySelector(`#${id}`)?.value?.trim() || '';
}

function numeroInput(id) {
  return Number(document.querySelector(`#${id}`)?.value || 0);
}

function descripcionEstado(estado) {
  const mapa = {
    recibido: 'Pedido recibido',
    preparando: 'Preparando',
    listo: 'Listo para salir',
    en_camino: 'En camino',
    entregado: 'Entregado',
    cancelado: 'Cancelado',
  };
  return mapa[estado] || estado;
}

function etiquetaEstado(estado) {
  return `<span class="estado ${escapar(estado)}">${escapar(descripcionEstado(estado))}</span>`;
}

// -----------------------------------------------------------------------------
// Dashboard administrativo / operativo
// -----------------------------------------------------------------------------
export async function paginaInicio() {
  const contenedor = obtenerContenedor();
  contenedor.innerHTML = `${encabezado('Panel principal', 'La información esencial del negocio en una sola pantalla.')}<div class="panel">Cargando...</div>`;

  try {
    const datos = await api('/dashboard');
    contenedor.innerHTML = `
      ${encabezado('Panel principal', 'La información esencial del negocio en una sola pantalla.')}
      <section class="panel hero-dashboard">
        <div>
          <span class="estado disponible">Todo bajo control</span>
          <h2>Administra tu tienda con datos, no con suposiciones.</h2>
          <p>Ventas, inventario, pedidos y alertas se actualizan con cada operación registrada en RioTiendas.</p>
          <strong>${escapar(estadoApp.usuario?.tienda?.nombre || 'RioTiendas')}</strong>
        </div>
        <img src="/static/assets/promo-controla.png" alt="RioTiendas en funcionamiento" />
      </section>

      <section class="rejilla-kpis" style="margin-top:1rem">
        ${tarjetaKpi('Ventas hoy', dinero(datos.ventas_hoy), '💳')}
        ${tarjetaKpi('Ventas semana', dinero(datos.ventas_semana), '📈')}
        ${tarjetaKpi('Ganancia estimada hoy', dinero(datos.ganancia_hoy), '💰')}
        ${tarjetaKpi('Pedidos pendientes', datos.pedidos_pendientes, '🚚')}
        ${tarjetaKpi('Productos disponibles', datos.productos_disponibles, '📦')}
        ${tarjetaKpi('Stock bajo', datos.productos_stock_bajo, '⚠️')}
        ${tarjetaKpi('Agotados', datos.productos_agotados, '🔴')}
        ${tarjetaKpi('Ventas mes', dinero(datos.ventas_mes), '🧾')}
      </section>

      <section class="rejilla-paneles">
        <article class="panel">
          <h3>Ventas de los últimos 7 días</h3>
          <canvas id="grafico-ventas" class="grafico"></canvas>
        </article>
        <article class="panel">
          <h3>Productos más vendidos</h3>
          <div id="ranking-productos"></div>
        </article>
      </section>
    `;

    dibujarBarras(document.querySelector('#grafico-ventas'), datos.ventas_ultimos_7_dias, 'fecha', 'total', '#F36A08');
    const ranking = document.querySelector('#ranking-productos');
    ranking.innerHTML = datos.productos_mas_vendidos.length
      ? datos.productos_mas_vendidos.map((item, i) => `
          <div class="ranking-item">
            <strong>${i + 1}. ${escapar(item.nombre)}</strong>
            <span>${escapar(item.cantidad)} unidad(es)</span>
          </div>
        `).join('')
      : '<div class="vacio">Aún no hay ventas suficientes para construir el ranking.</div>';
  } catch (error) {
    contenedor.innerHTML = `${encabezado('Panel principal', '')}<div class="panel">${escapar(error.message)}</div>`;
  }
}

// -----------------------------------------------------------------------------
// POS / Caja
// -----------------------------------------------------------------------------
let carritoVenta = [];

function totalCarrito() {
  return carritoVenta.reduce((total, item) => total + Number(item.precio_venta) * item.cantidad, 0);
}

function agregarAlCarrito(producto) {
  const existente = carritoVenta.find(item => item.id === producto.id);
  if (existente) {
    if (existente.cantidad + 1 > Number(producto.cantidad_disponible)) {
      avisar('No hay más unidades disponibles.', 'error');
      return;
    }
    existente.cantidad += 1;
  } else {
    if (Number(producto.cantidad_disponible) <= 0) {
      avisar('Ese producto está agotado.', 'error');
      return;
    }
    carritoVenta.push({ ...producto, cantidad: 1 });
  }
  renderCarritoVenta();
}

function cambiarCantidadVenta(productoId, diferencia) {
  const item = carritoVenta.find(producto => producto.id === productoId);
  if (!item) return;
  const nueva = item.cantidad + diferencia;
  if (nueva <= 0) {
    carritoVenta = carritoVenta.filter(producto => producto.id !== productoId);
  } else if (nueva <= Number(item.cantidad_disponible)) {
    item.cantidad = nueva;
  }
  renderCarritoVenta();
}

function renderCarritoVenta() {
  const contenedor = document.querySelector('#contenido-carrito');
  if (!contenedor) return;
  if (!carritoVenta.length) {
    contenedor.innerHTML = '<div class="vacio">Escanea o selecciona productos para comenzar.</div>';
    document.querySelector('#total-venta').textContent = dinero(0);
    return;
  }
  contenedor.innerHTML = carritoVenta.map(item => `
    <div class="linea-carrito">
      <div>
        <strong>${escapar(item.nombre)}</strong><br>
        <small>${dinero(item.precio_venta)} × ${item.cantidad}</small>
      </div>
      <div class="controles">
        <button data-restar="${item.id}">−</button>
        <strong>${item.cantidad}</strong>
        <button data-sumar="${item.id}">+</button>
      </div>
    </div>
  `).join('');
  document.querySelector('#total-venta').textContent = dinero(totalCarrito());
  contenedor.querySelectorAll('[data-restar]').forEach(b => b.addEventListener('click', () => cambiarCantidadVenta(Number(b.dataset.restar), -1)));
  contenedor.querySelectorAll('[data-sumar]').forEach(b => b.addEventListener('click', () => cambiarCantidadVenta(Number(b.dataset.sumar), 1)));
}

async function abrirEscanerCodigo() {
  abrirModal('Escanear código de barras', `
    <div class="campo">
      <label>Código manual / lector USB o Bluetooth</label>
      <input id="codigo-escaner" class="entrada" autocomplete="off" placeholder="Escanea o escribe el código" />
    </div>
    <div class="acciones">
      <button id="buscar-codigo" class="boton boton-primario">Buscar producto</button>
      <button id="activar-camara" class="boton boton-azul">Usar cámara</button>
    </div>
    <video id="video-escaner" class="video-escaner oculto" autoplay playsinline></video>
    <p class="texto-ayuda">La cámara usa BarcodeDetector cuando el navegador lo soporta. Un lector USB funciona como teclado: solo escanea y presiona Enter.</p>
  `);

  const entrada = document.querySelector('#codigo-escaner');
  entrada.focus();
  entrada.addEventListener('keydown', (evento) => {
    if (evento.key === 'Enter') document.querySelector('#buscar-codigo').click();
  });

  document.querySelector('#buscar-codigo').addEventListener('click', async () => {
    const codigo = entrada.value.trim();
    if (!codigo) return;
    try {
      const producto = await api(`/productos/codigo/${encodeURIComponent(codigo)}`);
      agregarAlCarrito(producto);
      cerrarModal();
      avisar(`${producto.nombre} agregado a la venta.`);
    } catch (error) {
      avisar(`${error.message}. Puedes registrarlo desde Inventario.`, 'error');
    }
  });

  document.querySelector('#activar-camara').addEventListener('click', async () => {
    if (!('BarcodeDetector' in window)) {
      avisar('Este navegador no soporta lectura nativa por cámara. Usa el lector USB o escribe el código.', 'aviso');
      return;
    }
    try {
      const video = document.querySelector('#video-escaner');
      video.classList.remove('oculto');
      const flujo = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
      video.srcObject = flujo;
      const detector = new BarcodeDetector({ formats: ['ean_13', 'ean_8', 'code_128', 'upc_a', 'upc_e'] });
      let activo = true;
      const revisar = async () => {
        if (!activo || !document.body.contains(video)) {
          flujo.getTracks().forEach(track => track.stop());
          return;
        }
        try {
          const codigos = await detector.detect(video);
          if (codigos.length) {
            activo = false;
            entrada.value = codigos[0].rawValue;
            flujo.getTracks().forEach(track => track.stop());
            document.querySelector('#buscar-codigo').click();
            return;
          }
        } catch {
          // Algunas cámaras necesitan unos cuadros antes de detectar correctamente.
        }
        requestAnimationFrame(revisar);
      };
      revisar();
    } catch (error) {
      avisar('No fue posible acceder a la cámara.', 'error');
    }
  });
}

export async function paginaVentas() {
  const contenedor = obtenerContenedor();
  carritoVenta = [];
  const [productos, clientes, ventas] = await Promise.all([
    api('/productos'),
    tienePermiso('clientes.ver') ? api('/clientes') : Promise.resolve([]),
    tienePermiso('ventas.ver') ? api('/ventas') : Promise.resolve([]),
  ]);

  contenedor.innerHTML = `
    ${encabezado('Punto de venta', 'Escanea, agrega, cobra y el inventario se descuenta automáticamente.', `
      ${boton('📷 Escanear código', 'boton-azul', 'btn-escanear')}
    `)}
    <div class="pos-layout">
      <section class="panel">
        <div class="campo">
          <label>Buscar producto</label>
          <input id="buscar-pos" class="entrada" placeholder="Nombre, código de barras o código interno" />
        </div>
        <div id="catalogo-pos" class="catalogo-pos"></div>
      </section>
      <aside class="panel carrito">
        <h3>Venta actual</h3>
        <div id="contenido-carrito"></div>
        <div class="campo" style="margin-top:1rem">
          <label>Cliente</label>
          <select id="cliente-venta" class="entrada">
            <option value="">Venta de mostrador</option>
            ${clientes.map(c => `<option value="${c.id}">${escapar(c.nombre)}</option>`).join('')}
          </select>
        </div>
        <div class="campo">
          <label>Descuento</label>
          <input id="descuento-venta" class="entrada" type="number" min="0" value="0" />
        </div>
        <div class="campo">
          <label>Método de pago</label>
          <select id="metodo-venta" class="entrada">
            <option value="efectivo">Efectivo</option>
            <option value="tarjeta">Tarjeta</option>
            <option value="transferencia">Transferencia</option>
            <option value="otros">Otros</option>
          </select>
        </div>
        <div class="total-grande" id="total-venta">${dinero(0)}</div>
        <button id="cobrar-venta" class="boton boton-primario boton-ancho" style="margin-top:1rem">Cobrar y finalizar</button>
      </aside>
    </div>
    ${tienePermiso('ventas.ver') ? `
      <section class="panel" style="margin-top:1rem">
        <h3>Ventas recientes</h3>
        ${tablaHTML([
          { titulo: 'Número', campo: 'numero' },
          { titulo: 'Fecha', render: v => fechaCorta(v.fecha) },
          { titulo: 'Total', render: v => dinero(v.total) },
          { titulo: 'Ganancia', render: v => dinero(v.ganancia_estimada) },
          { titulo: 'Pago', campo: 'metodo_pago' },
        ], ventas.slice(0, 12))}
      </section>` : ''}
  `;

  const catalogo = document.querySelector('#catalogo-pos');
  const pintarCatalogo = (lista) => {
    catalogo.innerHTML = lista.map(producto => tarjetaProducto(
      producto,
      `<button class="boton boton-claro boton-ancho" data-agregar="${producto.id}">Agregar</button>`,
    )).join('') || '<div class="vacio">No hay productos.</div>';
    catalogo.querySelectorAll('[data-agregar]').forEach(elemento => {
      elemento.addEventListener('click', () => {
        const producto = productos.find(p => p.id === Number(elemento.dataset.agregar));
        agregarAlCarrito(producto);
      });
    });
  };
  pintarCatalogo(productos);
  renderCarritoVenta();

  document.querySelector('#buscar-pos').addEventListener('input', evento => {
    const q = evento.target.value.toLowerCase();
    pintarCatalogo(productos.filter(p =>
      p.nombre.toLowerCase().includes(q) ||
      (p.codigo_barras || '').toLowerCase().includes(q) ||
      (p.codigo_interno || '').toLowerCase().includes(q)
    ));
  });
  document.querySelector('#btn-escanear').addEventListener('click', abrirEscanerCodigo);

  document.querySelector('#cobrar-venta').addEventListener('click', async () => {
    if (!carritoVenta.length) return avisar('Agrega al menos un producto.', 'error');
    try {
      const resultado = await api('/ventas', {
        method: 'POST',
        body: JSON.stringify({
          cliente_id: valorInput('cliente-venta') ? Number(valorInput('cliente-venta')) : null,
          lineas: carritoVenta.map(item => ({ producto_id: item.id, cantidad: item.cantidad })),
          descuento: numeroInput('descuento-venta'),
          metodo_pago: valorInput('metodo-venta'),
        }),
      });
      if (resultado.pendiente_offline) {
        carritoVenta = [];
        renderCarritoVenta();
        return;
      }
      abrirModal('Venta registrada', `
        <div class="comprobante">
          <img src="/static/assets/logo-riotiendas.png" alt="RioTiendas" style="max-width:220px;margin:auto" />
          <h3>${escapar(resultado.numero)}</h3>
          <p>Total cobrado</p>
          <div class="total-grande">${dinero(resultado.total)}</div>
          <p>Ganancia estimada: <strong>${dinero(resultado.ganancia_estimada)}</strong></p>
          <p>Método: ${escapar(resultado.metodo_pago)}</p>
          <button id="cerrar-comprobante" class="boton boton-primario boton-ancho">Aceptar</button>
        </div>
      `, '440px');
      document.querySelector('#cerrar-comprobante').addEventListener('click', () => {
        cerrarModal();
        paginaVentas();
      });
    } catch (error) {
      avisar(error.message, 'error');
    }
  });
}

// -----------------------------------------------------------------------------
// Inventario
// -----------------------------------------------------------------------------
function modalProducto(categorias, proveedores) {
  abrirModal('Registrar producto', `
    <div class="form-grid">
      <div class="campo"><label>Nombre</label><input id="prod-nombre" /></div>
      <div class="campo"><label>Código de barras</label><input id="prod-barra" /></div>
      <div class="campo"><label>Código interno</label><input id="prod-interno" /></div>
      <div class="campo"><label>Marca</label><input id="prod-marca" /></div>
      <div class="campo"><label>Categoría</label><select id="prod-categoria"><option value="">Sin categoría</option>${categorias.map(c => `<option value="${c.id}">${escapar(c.nombre)}</option>`).join('')}</select></div>
      <div class="campo"><label>Proveedor</label><select id="prod-proveedor"><option value="">Sin proveedor</option>${proveedores.map(p => `<option value="${p.id}">${escapar(p.nombre)}</option>`).join('')}</select></div>
      <div class="campo"><label>Precio compra</label><input id="prod-compra" type="number" min="0" value="0" /></div>
      <div class="campo"><label>Precio venta</label><input id="prod-venta" type="number" min="0" value="0" /></div>
      <div class="campo"><label>Existencias iniciales</label><input id="prod-stock" type="number" min="0" value="0" /></div>
      <div class="campo"><label>Stock mínimo</label><input id="prod-minimo" type="number" min="0" value="5" /></div>
      <div class="campo"><label>Unidad de medida</label><input id="prod-unidad" value="unidad" /></div>
      <div class="campo"><label>Fecha de vencimiento</label><input id="prod-vencimiento" type="date" /></div>
      <div class="campo ancho"><label>URL de imagen (opcional)</label><input id="prod-imagen" /></div>
    </div>
    <button id="guardar-producto" class="boton boton-primario boton-ancho">Guardar producto</button>
  `);
  document.querySelector('#guardar-producto').addEventListener('click', async () => {
    try {
      await api('/productos', {
        method: 'POST',
        body: JSON.stringify({
          nombre: valorInput('prod-nombre'),
          codigo_barras: valorInput('prod-barra'),
          codigo_interno: valorInput('prod-interno'),
          categoria_id: valorInput('prod-categoria') ? Number(valorInput('prod-categoria')) : null,
          proveedor_id: valorInput('prod-proveedor') ? Number(valorInput('prod-proveedor')) : null,
          marca: valorInput('prod-marca'),
          precio_compra: numeroInput('prod-compra'),
          precio_venta: numeroInput('prod-venta'),
          cantidad_disponible: numeroInput('prod-stock'),
          stock_minimo: numeroInput('prod-minimo'),
          unidad_medida: valorInput('prod-unidad') || 'unidad',
          fecha_vencimiento: valorInput('prod-vencimiento') || null,
          imagen_url: valorInput('prod-imagen'),
        }),
      });
      cerrarModal();
      avisar('Producto registrado correctamente.');
      paginaInventario();
    } catch (error) {
      avisar(error.message, 'error');
    }
  });
}

export async function paginaInventario() {
  const contenedor = obtenerContenedor();
  const [productos, categorias, proveedores] = await Promise.all([
    api('/productos'),
    api('/categorias'),
    tienePermiso('proveedores.ver') || tienePermiso('*') ? api('/proveedores').catch(() => []) : Promise.resolve([]),
  ]);
  const acciones = [
    tienePermiso('productos.crear') ? boton('+ Producto', 'boton-primario', 'nuevo-producto') : '',
    tienePermiso('productos.crear') ? boton('+ Categoría', 'boton-claro', 'nueva-categoria') : '',
  ].join('');
  contenedor.innerHTML = `
    ${encabezado('Inventario', 'Existencias, costos, precios, rentabilidad y alertas de stock.', acciones)}
    <section class="rejilla-kpis">
      ${tarjetaKpi('Productos', productos.length, '📦')}
      ${tarjetaKpi('Disponibles', productos.filter(p => p.estado === 'disponible').length, '✅')}
      ${tarjetaKpi('Stock bajo', productos.filter(p => p.estado === 'poco_inventario').length, '⚠️')}
      ${tarjetaKpi('Agotados', productos.filter(p => p.estado === 'agotado').length, '🔴')}
    </section>
    <section class="panel" style="margin-top:1rem">
      <div class="campo"><label>Buscar</label><input id="buscar-inventario" class="entrada" placeholder="Nombre, código o marca" /></div>
      <div id="tabla-inventario"></div>
    </section>
  `;

  const nombreCategoria = id => categorias.find(c => c.id === id)?.nombre || '—';
  const pintar = lista => {
    document.querySelector('#tabla-inventario').innerHTML = tablaHTML([
      { titulo: 'Producto', render: p => `<strong>${escapar(p.nombre)}</strong><br><small>${escapar(p.marca || '')}</small>` },
      { titulo: 'Código', render: p => escapar(p.codigo_barras || p.codigo_interno || '—') },
      { titulo: 'Categoría', render: p => escapar(nombreCategoria(p.categoria_id)) },
      { titulo: 'Existencias', render: p => `${p.cantidad_disponible} ${escapar(p.unidad_medida)}` },
      { titulo: 'Compra', render: p => dinero(p.precio_compra) },
      { titulo: 'Venta', render: p => dinero(p.precio_venta) },
      { titulo: 'Ganancia/u.', render: p => dinero(p.ganancia_unitaria) },
      { titulo: 'Estado', render: p => estadoInventario(p) },
    ], lista, tienePermiso('inventario.ajustar') ? p => `<button class="boton boton-claro" data-ajuste="${p.id}">Ajustar</button>` : null);
    document.querySelectorAll('[data-ajuste]').forEach(elemento => {
      elemento.addEventListener('click', () => {
        const producto = productos.find(p => p.id === Number(elemento.dataset.ajuste));
        abrirModal(`Ajustar: ${producto.nombre}`, `
          <p>Existencia actual: <strong>${producto.cantidad_disponible}</strong></p>
          <div class="campo"><label>Cantidad a sumar o restar</label><input id="ajuste-cantidad" type="number" step="0.001" placeholder="Ej: 5 o -2" /></div>
          <div class="campo"><label>Motivo</label><input id="ajuste-nota" placeholder="Conteo físico, pérdida, corrección..." /></div>
          <button id="guardar-ajuste" class="boton boton-primario boton-ancho">Aplicar ajuste</button>
        `, '500px');
        document.querySelector('#guardar-ajuste').addEventListener('click', async () => {
          try {
            await api(`/inventario/${producto.id}/ajustar`, {
              method: 'POST',
              body: JSON.stringify({ cantidad: numeroInput('ajuste-cantidad'), nota: valorInput('ajuste-nota') }),
            });
            cerrarModal();
            avisar('Inventario actualizado.');
            paginaInventario();
          } catch (error) { avisar(error.message, 'error'); }
        });
      });
    });
  };
  pintar(productos);
  document.querySelector('#buscar-inventario').addEventListener('input', evento => {
    const q = evento.target.value.toLowerCase();
    pintar(productos.filter(p => `${p.nombre} ${p.codigo_barras} ${p.codigo_interno} ${p.marca}`.toLowerCase().includes(q)));
  });

  document.querySelector('#nuevo-producto')?.addEventListener('click', () => modalProducto(categorias, proveedores));
  document.querySelector('#nueva-categoria')?.addEventListener('click', () => {
    abrirModal('Nueva categoría', `
      <div class="campo"><label>Nombre</label><input id="cat-nombre" /></div>
      <div class="campo"><label>Descripción</label><textarea id="cat-descripcion"></textarea></div>
      <button id="guardar-categoria" class="boton boton-primario boton-ancho">Guardar</button>
    `, '500px');
    document.querySelector('#guardar-categoria').addEventListener('click', async () => {
      try {
        await api('/categorias', { method: 'POST', body: JSON.stringify({ nombre: valorInput('cat-nombre'), descripcion: valorInput('cat-descripcion') }) });
        cerrarModal();
        avisar('Categoría creada.');
        paginaInventario();
      } catch (error) { avisar(error.message, 'error'); }
    });
  });
}

// -----------------------------------------------------------------------------
// Compras y proveedores
// -----------------------------------------------------------------------------
let lineasCompra = [];

export async function paginaCompras() {
  const contenedor = obtenerContenedor();
  const [productos, proveedores, compras] = await Promise.all([
    api('/productos'),
    api('/proveedores'),
    api('/compras'),
  ]);
  lineasCompra = [];
  contenedor.innerHTML = `
    ${encabezado('Compras', 'Registra mercancía recibida y el inventario aumentará automáticamente.', boton('+ Registrar compra', 'boton-primario', 'nueva-compra'))}
    <section class="panel">
      ${tablaHTML([
        { titulo: 'Número', campo: 'numero' },
        { titulo: 'Fecha', render: c => fechaCorta(c.fecha) },
        { titulo: 'Proveedor', render: c => escapar(proveedores.find(p => p.id === c.proveedor_id)?.nombre || 'Sin proveedor') },
        { titulo: 'Total', render: c => dinero(c.total) },
        { titulo: 'Observación', campo: 'observacion' },
      ], compras)}
    </section>
  `;

  document.querySelector('#nueva-compra').addEventListener('click', () => {
    abrirModal('Registrar compra de mercancía', `
      <div class="campo"><label>Proveedor</label><select id="compra-proveedor"><option value="">Sin proveedor</option>${proveedores.map(p => `<option value="${p.id}">${escapar(p.nombre)}</option>`).join('')}</select></div>
      <div class="form-grid">
        <div class="campo"><label>Producto</label><select id="compra-producto">${productos.map(p => `<option value="${p.id}">${escapar(p.nombre)}</option>`).join('')}</select></div>
        <div class="campo"><label>Cantidad</label><input id="compra-cantidad" type="number" min="0.001" value="1" step="0.001" /></div>
        <div class="campo"><label>Costo unitario</label><input id="compra-costo" type="number" min="0" value="0" /></div>
        <div class="campo" style="align-self:end"><button id="agregar-linea-compra" class="boton boton-claro">Agregar línea</button></div>
      </div>
      <div id="lineas-compra" style="margin:1rem 0"></div>
      <div class="campo"><label>Observación</label><input id="compra-observacion" /></div>
      <button id="guardar-compra" class="boton boton-primario boton-ancho">Registrar compra</button>
    `);

    const render = () => {
      const elemento = document.querySelector('#lineas-compra');
      elemento.innerHTML = lineasCompra.length ? lineasCompra.map((linea, i) => `
        <div class="linea-carrito"><div><strong>${escapar(productos.find(p => p.id === linea.producto_id)?.nombre || '')}</strong><br><small>${linea.cantidad} × ${dinero(linea.costo_unitario)}</small></div><button class="boton boton-peligro" data-quitar-compra="${i}">Quitar</button></div>
      `).join('') : '<div class="vacio">Agrega los productos recibidos.</div>';
      elemento.querySelectorAll('[data-quitar-compra]').forEach(b => b.addEventListener('click', () => {
        lineasCompra.splice(Number(b.dataset.quitarCompra), 1); render();
      }));
    };
    render();
    document.querySelector('#agregar-linea-compra').addEventListener('click', () => {
      const productoId = Number(valorInput('compra-producto'));
      const producto = productos.find(p => p.id === productoId);
      lineasCompra.push({
        producto_id: productoId,
        cantidad: numeroInput('compra-cantidad'),
        costo_unitario: numeroInput('compra-costo') || Number(producto?.precio_compra || 0),
      });
      render();
    });
    document.querySelector('#guardar-compra').addEventListener('click', async () => {
      if (!lineasCompra.length) return avisar('Agrega al menos un producto.', 'error');
      try {
        const resultado = await api('/compras', {
          method: 'POST',
          body: JSON.stringify({
            proveedor_id: valorInput('compra-proveedor') ? Number(valorInput('compra-proveedor')) : null,
            lineas: lineasCompra,
            observacion: valorInput('compra-observacion'),
          }),
        });
        cerrarModal();
        avisar(`Compra ${resultado.numero} registrada por ${dinero(resultado.total)}.`);
        paginaCompras();
      } catch (error) { avisar(error.message, 'error'); }
    });
  });
}

export async function paginaProveedores() {
  const contenedor = obtenerContenedor();
  const proveedores = await api('/proveedores');
  contenedor.innerHTML = `
    ${encabezado('Proveedores', 'Datos de contacto y fuentes de abastecimiento.', tienePermiso('proveedores.crear') ? boton('+ Proveedor', 'boton-primario', 'nuevo-proveedor') : '')}
    <section class="panel">
      ${tablaHTML([
        { titulo: 'Nombre', campo: 'nombre' },
        { titulo: 'Teléfono', campo: 'telefono' },
        { titulo: 'Correo', campo: 'correo' },
        { titulo: 'Dirección', campo: 'direccion' },
        { titulo: 'Notas', campo: 'notas' },
      ], proveedores)}
    </section>
  `;
  document.querySelector('#nuevo-proveedor')?.addEventListener('click', () => {
    abrirModal('Nuevo proveedor', `
      <div class="form-grid">
        <div class="campo"><label>Nombre</label><input id="prov-nombre" /></div>
        <div class="campo"><label>Teléfono</label><input id="prov-telefono" /></div>
        <div class="campo"><label>Correo</label><input id="prov-correo" type="email" /></div>
        <div class="campo"><label>Dirección</label><input id="prov-direccion" /></div>
        <div class="campo ancho"><label>Notas</label><textarea id="prov-notas"></textarea></div>
      </div>
      <button id="guardar-proveedor" class="boton boton-primario boton-ancho">Guardar</button>
    `);
    document.querySelector('#guardar-proveedor').addEventListener('click', async () => {
      try {
        await api('/proveedores', { method: 'POST', body: JSON.stringify({
          nombre: valorInput('prov-nombre'), telefono: valorInput('prov-telefono'), correo: valorInput('prov-correo'),
          direccion: valorInput('prov-direccion'), notas: valorInput('prov-notas'),
        }) });
        cerrarModal(); avisar('Proveedor creado.'); paginaProveedores();
      } catch (error) { avisar(error.message, 'error'); }
    });
  });
}

// -----------------------------------------------------------------------------
// Clientes
// -----------------------------------------------------------------------------
export async function paginaClientes() {
  const contenedor = obtenerContenedor();
  const clientes = await api('/clientes');
  contenedor.innerHTML = `
    ${encabezado('Clientes', 'Base de clientes para ventas y domicilios.', tienePermiso('clientes.crear') ? boton('+ Cliente', 'boton-primario', 'nuevo-cliente') : '')}
    <section class="panel">
      ${tablaHTML([
        { titulo: 'Nombre', campo: 'nombre' },
        { titulo: 'Teléfono', campo: 'telefono' },
        { titulo: 'Dirección', campo: 'direccion' },
        { titulo: 'Correo', campo: 'correo' },
      ], clientes)}
    </section>
  `;
  document.querySelector('#nuevo-cliente')?.addEventListener('click', () => {
    abrirModal('Registrar cliente', `
      <div class="form-grid">
        <div class="campo"><label>Nombre</label><input id="cli-nombre" /></div>
        <div class="campo"><label>Teléfono</label><input id="cli-telefono" /></div>
        <div class="campo"><label>Dirección</label><input id="cli-direccion" /></div>
        <div class="campo"><label>Correo</label><input id="cli-correo" type="email" /></div>
      </div>
      <button id="guardar-cliente" class="boton boton-primario boton-ancho">Guardar</button>
    `);
    document.querySelector('#guardar-cliente').addEventListener('click', async () => {
      try {
        await api('/clientes', { method: 'POST', body: JSON.stringify({
          nombre: valorInput('cli-nombre'), telefono: valorInput('cli-telefono'), direccion: valorInput('cli-direccion'), correo: valorInput('cli-correo'),
        }) });
        cerrarModal(); avisar('Cliente registrado.'); paginaClientes();
      } catch (error) { avisar(error.message, 'error'); }
    });
  });
}

// -----------------------------------------------------------------------------
// Pedidos administrativos
// -----------------------------------------------------------------------------
function botonesPedido(pedido, domiciliarios = []) {
  const botones = [];
  if ((tienePermiso('pedidos.preparar') || tienePermiso('*')) && pedido.estado === 'recibido') {
    botones.push(`<button class="boton boton-claro" data-estado-pedido="${pedido.id}" data-estado="preparando">Preparar</button>`);
  }
  if ((tienePermiso('pedidos.preparar') || tienePermiso('*')) && pedido.estado === 'preparando') {
    botones.push(`<button class="boton boton-verde" data-estado-pedido="${pedido.id}" data-estado="listo">Marcar listo</button>`);
  }
  if ((tienePermiso('pedidos.preparar') || tienePermiso('*')) && ['recibido', 'preparando', 'listo'].includes(pedido.estado)) {
    botones.push(`<button class="boton boton-peligro" data-estado-pedido="${pedido.id}" data-estado="cancelado">Cancelar</button>`);
  }
  if ((tienePermiso('pedidos.asignar') || tienePermiso('*')) && pedido.estado === 'listo') {
    botones.push(`<button class="boton boton-azul" data-asignar="${pedido.id}">Asignar domicilio</button>`);
  }
  return botones.join(' ');
}

export async function paginaPedidos() {
  const contenedor = obtenerContenedor();
  const [pedidos, domiciliarios] = await Promise.all([api('/pedidos'), api('/domiciliarios')]);
  contenedor.innerHTML = `
    ${encabezado('Pedidos a domicilio', 'Controla el pedido desde su recepción hasta la entrega.')}
    <section class="rejilla-kpis">
      ${tarjetaKpi('Recibidos', pedidos.filter(p => p.estado === 'recibido').length, '📥')}
      ${tarjetaKpi('Preparando', pedidos.filter(p => p.estado === 'preparando').length, '🧺')}
      ${tarjetaKpi('En camino', pedidos.filter(p => p.estado === 'en_camino').length, '🛵')}
      ${tarjetaKpi('Entregados', pedidos.filter(p => p.estado === 'entregado').length, '✅')}
    </section>
    <section class="panel" style="margin-top:1rem">
      ${tablaHTML([
        { titulo: 'Pedido', campo: 'numero' },
        { titulo: 'Cliente', render: p => `<strong>${escapar(p.nombre_cliente)}</strong><br><small>${escapar(p.telefono)}</small>` },
        { titulo: 'Dirección', campo: 'direccion' },
        { titulo: 'Total', render: p => dinero(p.total) },
        { titulo: 'Estado', render: p => etiquetaEstado(p.estado) },
        { titulo: 'Domiciliario', render: p => escapar(p.domiciliario_nombre || 'Sin asignar') },
        { titulo: 'Fecha', render: p => fechaCorta(p.fecha) },
      ], pedidos, p => botonesPedido(p, domiciliarios))}
    </section>
  `;

  document.querySelectorAll('[data-estado-pedido]').forEach(b => b.addEventListener('click', async () => {
    try {
      await api(`/pedidos/${b.dataset.estadoPedido}/estado`, { method: 'POST', body: JSON.stringify({ estado: b.dataset.estado }) });
      avisar('Estado actualizado.'); paginaPedidos();
    } catch (error) { avisar(error.message, 'error'); }
  }));

  document.querySelectorAll('[data-asignar]').forEach(b => b.addEventListener('click', () => {
    abrirModal('Asignar domiciliario', `
      <div class="campo"><label>Domiciliario</label><select id="domiciliario-seleccion">${domiciliarios.map(d => `<option value="${d.id}">${escapar(d.nombre)}</option>`).join('')}</select></div>
      <button id="confirmar-domiciliario" class="boton boton-primario boton-ancho">Asignar</button>
    `, '480px');
    document.querySelector('#confirmar-domiciliario').addEventListener('click', async () => {
      try {
        await api(`/pedidos/${b.dataset.asignar}/asignar`, { method: 'POST', body: JSON.stringify({ domiciliario_id: Number(valorInput('domiciliario-seleccion')) }) });
        cerrarModal(); avisar('Domiciliario asignado.'); paginaPedidos();
      } catch (error) { avisar(error.message, 'error'); }
    });
  }));
}

// -----------------------------------------------------------------------------
// Experiencia de cliente
// -----------------------------------------------------------------------------
let carritoCliente = [];

function renderCarritoCliente() {
  const panel = document.querySelector('#carrito-cliente');
  if (!panel) return;
  const total = carritoCliente.reduce((sum, item) => sum + item.precio_venta * item.cantidad, 0);
  panel.innerHTML = `
    <h3>Tu pedido</h3>
    ${carritoCliente.length ? carritoCliente.map(item => `
      <div class="linea-carrito">
        <div><strong>${escapar(item.nombre)}</strong><br><small>${item.cantidad} × ${dinero(item.precio_venta)}</small></div>
        <div class="controles"><button data-cliente-restar="${item.id}">−</button><strong>${item.cantidad}</strong><button data-cliente-sumar="${item.id}">+</button></div>
      </div>
    `).join('') : '<div class="vacio">Tu carrito está vacío.</div>'}
    <p>Total productos</p>
    <div class="total-grande">${dinero(total)}</div>
    <div class="campo"><label>Costo domicilio</label><input id="cliente-domicilio" type="number" value="5000" min="0" /></div>
    <div class="campo"><label>Método de pago</label><select id="cliente-pago"><option value="efectivo">Efectivo</option><option value="transferencia">Transferencia</option><option value="tarjeta">Tarjeta</option></select></div>
    <div class="campo"><label>Notas</label><textarea id="cliente-notas" placeholder="Ej: llamar al llegar"></textarea></div>
    <button id="confirmar-pedido-cliente" class="boton boton-primario boton-ancho" ${carritoCliente.length ? '' : 'disabled'}>Confirmar pedido</button>
  `;
  panel.querySelectorAll('[data-cliente-restar]').forEach(b => b.addEventListener('click', () => {
    const item = carritoCliente.find(i => i.id === Number(b.dataset.clienteRestar));
    if (!item) return;
    item.cantidad -= 1;
    if (item.cantidad <= 0) carritoCliente = carritoCliente.filter(i => i.id !== item.id);
    renderCarritoCliente();
  }));
  panel.querySelectorAll('[data-cliente-sumar]').forEach(b => b.addEventListener('click', () => {
    const item = carritoCliente.find(i => i.id === Number(b.dataset.clienteSumar));
    if (item && item.cantidad < item.cantidad_disponible) item.cantidad += 1;
    renderCarritoCliente();
  }));
  document.querySelector('#confirmar-pedido-cliente')?.addEventListener('click', async () => {
    try {
      const resultado = await api('/pedidos', {
        method: 'POST',
        body: JSON.stringify({
          costo_domicilio: numeroInput('cliente-domicilio'),
          metodo_pago: valorInput('cliente-pago'),
          notas: valorInput('cliente-notas'),
          lineas: carritoCliente.map(item => ({ producto_id: item.id, cantidad: item.cantidad })),
        }),
      });
      carritoCliente = [];
      if (!resultado.pendiente_offline) avisar(`Pedido ${resultado.numero} creado correctamente.`);
      paginaTiendaCliente();
    } catch (error) { avisar(error.message, 'error'); }
  });
}

export async function paginaTiendaCliente() {
  const contenedor = obtenerContenedor();
  carritoCliente = [];
  const productos = await api('/productos');
  contenedor.innerHTML = `
    ${encabezado('Compra en tu tienda', 'Selecciona productos y solicita domicilio desde el celular.')}
    <div class="pos-layout">
      <section>
        <div class="catalogo-cliente" id="catalogo-cliente"></div>
      </section>
      <aside class="panel carrito" id="carrito-cliente"></aside>
    </div>
  `;
  const catalogo = document.querySelector('#catalogo-cliente');
  catalogo.innerHTML = productos.filter(p => p.cantidad_disponible > 0).map(producto => `
    <article class="tarjeta-producto-cliente">
      <div class="emoji">🛒</div>
      <h3>${escapar(producto.nombre)}</h3>
      <p>${dinero(producto.precio_venta)}</p>
      <small>Disponibles: ${producto.cantidad_disponible}</small>
      <button class="boton boton-primario boton-ancho" data-comprar="${producto.id}" style="margin-top:.8rem">Agregar</button>
    </article>
  `).join('') || '<div class="panel vacio">La tienda todavía no tiene productos disponibles.</div>';
  catalogo.querySelectorAll('[data-comprar]').forEach(b => b.addEventListener('click', () => {
    const producto = productos.find(p => p.id === Number(b.dataset.comprar));
    const existente = carritoCliente.find(p => p.id === producto.id);
    if (existente) existente.cantidad += 1;
    else carritoCliente.push({ ...producto, cantidad: 1 });
    renderCarritoCliente();
  }));
  renderCarritoCliente();
}

export async function paginaMisPedidosCliente() {
  const contenedor = obtenerContenedor();
  const pedidos = await api('/pedidos');
  const pasos = ['recibido', 'preparando', 'listo', 'en_camino', 'entregado'];
  contenedor.innerHTML = `
    ${encabezado('Mis pedidos', 'Consulta en tiempo real en qué etapa se encuentra cada domicilio.')}
    <div class="rejilla-tres">
      ${pedidos.map(pedido => `
        <article class="panel">
          <div class="encabezado-pagina">
            <div><h3>${escapar(pedido.numero)}</h3><small>${fechaCorta(pedido.fecha)}</small></div>
            ${etiquetaEstado(pedido.estado)}
          </div>
          <p>${escapar(pedido.direccion)}</p>
          <div class="ruta-pedido">
            ${pasos.map(paso => `<span class="paso-ruta ${pasos.indexOf(paso) <= pasos.indexOf(pedido.estado) && pedido.estado !== 'cancelado' ? 'completado' : ''}">${escapar(descripcionEstado(paso))}</span>`).join('')}
          </div>
          <ul>${pedido.lineas.map(linea => `<li>${escapar(linea.producto)} × ${linea.cantidad}</li>`).join('')}</ul>
          <div class="total-grande">${dinero(pedido.total)}</div>
          ${pedido.domiciliario_nombre ? `<p>Domiciliario: <strong>${escapar(pedido.domiciliario_nombre)}</strong></p>` : ''}
        </article>
      `).join('') || '<div class="panel vacio">Todavía no has realizado pedidos.</div>'}
    </div>
  `;
}

// -----------------------------------------------------------------------------
// Domiciliario
// -----------------------------------------------------------------------------
export async function paginaDomicilios() {
  const contenedor = obtenerContenedor();
  const pedidos = await api('/pedidos');
  contenedor.innerHTML = `
    ${encabezado('Mis domicilios', 'Pedidos asignados a tu ruta de entrega.')}
    <section class="rejilla-kpis">
      ${tarjetaKpi('Asignados', pedidos.length, '🛵')}
      ${tarjetaKpi('Listos', pedidos.filter(p => p.estado === 'listo').length, '📦')}
      ${tarjetaKpi('En camino', pedidos.filter(p => p.estado === 'en_camino').length, '📍')}
      ${tarjetaKpi('Entregados', pedidos.filter(p => p.estado === 'entregado').length, '✅')}
    </section>
    <div class="rejilla-tres" style="margin-top:1rem">
      ${pedidos.map(p => `
        <article class="panel">
          <div class="encabezado-pagina"><h3>${escapar(p.numero)}</h3>${etiquetaEstado(p.estado)}</div>
          <p><strong>${escapar(p.nombre_cliente)}</strong><br>${escapar(p.telefono)}<br>${escapar(p.direccion)}</p>
          <p>${p.lineas.map(l => `${escapar(l.producto)} × ${l.cantidad}`).join('<br>')}</p>
          <div class="total-grande">${dinero(p.total)}</div>
          ${p.estado === 'listo' ? `<button class="boton boton-azul boton-ancho" data-domicilio-estado="${p.id}" data-estado="en_camino">Iniciar entrega</button>` : ''}
          ${p.estado === 'en_camino' ? `<button class="boton boton-verde boton-ancho" data-domicilio-estado="${p.id}" data-estado="entregado">Confirmar entregado</button>` : ''}
        </article>
      `).join('') || '<div class="panel vacio">No tienes pedidos asignados en este momento.</div>'}
    </div>
  `;
  document.querySelectorAll('[data-domicilio-estado]').forEach(b => b.addEventListener('click', async () => {
    try {
      await api(`/pedidos/${b.dataset.domicilioEstado}/estado`, { method: 'POST', body: JSON.stringify({ estado: b.dataset.estado }) });
      avisar('Estado del domicilio actualizado.'); paginaDomicilios();
    } catch (error) { avisar(error.message, 'error'); }
  }));
}

// -----------------------------------------------------------------------------
// Alertas
// -----------------------------------------------------------------------------
export async function paginaAlertas() {
  const contenedor = obtenerContenedor();
  const alertas = await api('/alertas');
  contenedor.innerHTML = `
    ${encabezado('Alertas de inventario', 'Prioriza agotados, stock bajo y próximos vencimientos.')}
    <section class="panel">
      ${alertas.length ? alertas.map(alerta => `
        <div class="alerta-item ${alerta.nivel}">
          <strong>${alerta.nivel === 'critico' ? '🔴' : '⚠️'} ${escapar(alerta.tipo.replace('_', ' '))}</strong>
          <p>${escapar(alerta.mensaje)}</p>
        </div>
      `).join('') : '<div class="vacio">No hay alertas activas.</div>'}
    </section>
  `;
}

// -----------------------------------------------------------------------------
// Reportes
// -----------------------------------------------------------------------------
async function descargarReporte(formato) {
  try {
    const respuesta = await api(`/reportes/exportar/${formato}`);
    const blob = await respuesta.blob();
    const url = URL.createObjectURL(blob);
    const enlace = document.createElement('a');
    enlace.href = url;
    enlace.download = `ventas_riotiendas.${formato}`;
    enlace.click();
    URL.revokeObjectURL(url);
  } catch (error) { avisar(error.message, 'error'); }
}

export async function paginaReportes() {
  const contenedor = obtenerContenedor();
  const datos = await api('/reportes/resumen');
  contenedor.innerHTML = `
    ${encabezado('Reportes', 'Resumen financiero y exportación de la información del negocio.', `
      ${boton('CSV', 'boton-claro', 'exportar-csv')}
      ${boton('Excel', 'boton-verde', 'exportar-xlsx')}
      ${boton('PDF', 'boton-peligro', 'exportar-pdf')}
      ${tienePermiso('gastos.crear') || tienePermiso('*') ? boton('+ Gasto', 'boton-primario', 'nuevo-gasto') : ''}
    `)}
    <section class="rejilla-kpis">
      ${tarjetaKpi('Ventas históricas', dinero(datos.total_historico_ventas), '💳')}
      ${tarjetaKpi('Ganancia estimada', dinero(datos.total_historico_ganancia), '📈')}
      ${tarjetaKpi('Compras', dinero(datos.total_compras), '📦')}
      ${tarjetaKpi('Gastos', dinero(datos.total_gastos), '🧾')}
    </section>
    <section class="rejilla-paneles">
      <article class="panel"><h3>Ventas últimos 7 días</h3><canvas id="grafico-reporte" class="grafico"></canvas></article>
      <article class="panel"><h3>Lectura rápida</h3><p>Ventas hoy: <strong>${dinero(datos.ventas_hoy)}</strong></p><p>Ventas semana: <strong>${dinero(datos.ventas_semana)}</strong></p><p>Ventas mes: <strong>${dinero(datos.ventas_mes)}</strong></p></article>
    </section>
  `;
  dibujarBarras(document.querySelector('#grafico-reporte'), datos.ventas_ultimos_7_dias, 'fecha', 'total', '#073565');
  document.querySelector('#exportar-csv').addEventListener('click', () => descargarReporte('csv'));
  document.querySelector('#exportar-xlsx').addEventListener('click', () => descargarReporte('xlsx'));
  document.querySelector('#exportar-pdf').addEventListener('click', () => descargarReporte('pdf'));
  document.querySelector('#nuevo-gasto')?.addEventListener('click', () => {
    abrirModal('Registrar gasto', `
      <div class="campo"><label>Concepto</label><input id="gasto-concepto" /></div>
      <div class="campo"><label>Categoría</label><input id="gasto-categoria" value="general" /></div>
      <div class="campo"><label>Valor</label><input id="gasto-valor" type="number" min="1" /></div>
      <button id="guardar-gasto" class="boton boton-primario boton-ancho">Guardar gasto</button>
    `, '500px');
    document.querySelector('#guardar-gasto').addEventListener('click', async () => {
      try {
        await api('/gastos', { method: 'POST', body: JSON.stringify({ concepto: valorInput('gasto-concepto'), categoria: valorInput('gasto-categoria'), valor: numeroInput('gasto-valor') }) });
        cerrarModal(); avisar('Gasto registrado.'); paginaReportes();
      } catch (error) { avisar(error.message, 'error'); }
    });
  });
}

// -----------------------------------------------------------------------------
// Usuarios y permisos
// -----------------------------------------------------------------------------
const PERMISOS_DISPONIBLES = [
  ['dashboard.ver', 'Ver dashboard'], ['ventas.ver', 'Ver ventas'], ['ventas.crear', 'Crear ventas'],
  ['productos.ver', 'Ver productos'], ['productos.crear', 'Crear productos'], ['productos.editar', 'Editar productos'],
  ['inventario.ver', 'Ver movimientos'], ['inventario.ajustar', 'Ajustar inventario'],
  ['clientes.ver', 'Ver clientes'], ['clientes.crear', 'Crear clientes'], ['pedidos.ver', 'Ver pedidos'],
  ['pedidos.crear', 'Crear pedidos'], ['pedidos.preparar', 'Preparar/cancelar pedidos'], ['pedidos.asignar', 'Asignar domiciliarios'],
  ['compras.ver', 'Ver compras'], ['compras.crear', 'Registrar compras'], ['proveedores.ver', 'Ver proveedores'],
  ['proveedores.crear', 'Crear proveedores'], ['alertas.ver', 'Ver alertas'], ['reportes.ver', 'Ver reportes'],
  ['gastos.crear', 'Registrar gastos'], ['busqueda.usar', 'Usar búsqueda global'], ['usuarios.ver', 'Ver usuarios'],
  ['usuarios.crear', 'Crear usuarios'], ['usuarios.permisos', 'Modificar permisos'], ['historial.ver', 'Ver auditoría'],
  ['respaldo.generar', 'Generar respaldo'],
];

export async function paginaUsuarios() {
  const contenedor = obtenerContenedor();
  const usuarios = await api('/usuarios');
  contenedor.innerHTML = `
    ${encabezado('Usuarios y roles', 'Control de acceso para dueño, cajeros, empleados y domiciliarios.', boton('+ Usuario', 'boton-primario', 'nuevo-usuario'))}
    <section class="panel">
      ${tablaHTML([
        { titulo: 'Nombre', campo: 'nombre' },
        { titulo: 'Correo', campo: 'correo' },
        { titulo: 'Rol', render: u => `<span class="estado activo">${escapar(u.rol)}</span>` },
        { titulo: 'Estado', render: u => u.activo ? 'Activo' : 'Inactivo' },
        { titulo: 'Permisos', render: u => u.permisos.includes('*') ? 'Todos' : `${u.permisos.length} permiso(s)` },
      ], usuarios, u => `<button class="boton boton-claro" data-permisos="${u.id}">Permisos</button>`)}
    </section>
  `;

  document.querySelector('#nuevo-usuario').addEventListener('click', () => {
    abrirModal('Crear usuario', `
      <div class="form-grid">
        <div class="campo"><label>Nombre</label><input id="usr-nombre" /></div>
        <div class="campo"><label>Correo</label><input id="usr-correo" type="email" /></div>
        <div class="campo"><label>Teléfono</label><input id="usr-telefono" /></div>
        <div class="campo"><label>Contraseña</label><input id="usr-clave" type="password" value="Rio2026*" /></div>
        <div class="campo ancho"><label>Rol</label><select id="usr-rol"><option value="cajero">Cajero</option><option value="empleado">Empleado</option><option value="domiciliario">Domiciliario</option><option value="cliente">Cliente</option><option value="administrador">Administrador</option></select></div>
        <div class="campo ancho oculto" id="usr-campo-direccion"><label>Dirección</label><input id="usr-direccion" /></div>
      </div>
      <button id="guardar-usuario" class="boton boton-primario boton-ancho">Crear usuario</button>
    `);
    const selectorRol = document.querySelector('#usr-rol');
    const campoDireccion = document.querySelector('#usr-campo-direccion');
    selectorRol.addEventListener('change', () => {
      campoDireccion.classList.toggle('oculto', selectorRol.value !== 'cliente');
    });
    document.querySelector('#guardar-usuario').addEventListener('click', async () => {
      try {
        await api('/usuarios', { method: 'POST', body: JSON.stringify({
          nombre: valorInput('usr-nombre'), correo: valorInput('usr-correo'), telefono: valorInput('usr-telefono'), direccion: valorInput('usr-direccion'), contrasena: valorInput('usr-clave'), rol: valorInput('usr-rol'),
        }) });
        cerrarModal(); avisar('Usuario creado.'); paginaUsuarios();
      } catch (error) { avisar(error.message, 'error'); }
    });
  });

  document.querySelectorAll('[data-permisos]').forEach(b => b.addEventListener('click', () => {
    const usuario = usuarios.find(u => u.id === Number(b.dataset.permisos));
    abrirModal(`Permisos de ${usuario.nombre}`, `
      <p>Los permisos seleccionados reemplazarán los predeterminados del rol. Para volver al rol base usa “Restaurar”.</p>
      <div class="lista-permisos">
        ${PERMISOS_DISPONIBLES.map(([valor, texto]) => `
          <label class="permiso-item"><input type="checkbox" data-permiso value="${valor}" ${usuario.permisos.includes('*') || usuario.permisos.includes(valor) ? 'checked' : ''}> <span>${escapar(texto)}</span></label>
        `).join('')}
      </div>
      <div class="acciones" style="margin-top:1rem">
        <button id="guardar-permisos" class="boton boton-primario">Guardar selección</button>
        <button id="restaurar-permisos" class="boton boton-claro">Restaurar rol</button>
      </div>
    `);
    document.querySelector('#guardar-permisos').addEventListener('click', async () => {
      const permisos = [...document.querySelectorAll('[data-permiso]:checked')].map(c => c.value);
      try {
        await api(`/usuarios/${usuario.id}/permisos`, { method: 'PUT', body: JSON.stringify({ permisos }) });
        cerrarModal(); avisar('Permisos personalizados guardados.'); paginaUsuarios();
      } catch (error) { avisar(error.message, 'error'); }
    });
    document.querySelector('#restaurar-permisos').addEventListener('click', async () => {
      try {
        await api(`/usuarios/${usuario.id}/permisos`, { method: 'PUT', body: JSON.stringify({ permisos: null }) });
        cerrarModal(); avisar('Se restauraron los permisos del rol.'); paginaUsuarios();
      } catch (error) { avisar(error.message, 'error'); }
    });
  }));
}

// -----------------------------------------------------------------------------
// Historial y configuración
// -----------------------------------------------------------------------------
export async function paginaHistorial() {
  const contenedor = obtenerContenedor();
  const historial = await api('/historial');
  contenedor.innerHTML = `
    ${encabezado('Historial de actividad', 'Auditoría: quién hizo qué, cuándo y sobre qué registro.')}
    <section class="panel">
      ${tablaHTML([
        { titulo: 'Fecha', render: a => fechaCorta(a.fecha) },
        { titulo: 'Usuario', campo: 'usuario' },
        { titulo: 'Acción', campo: 'accion' },
        { titulo: 'Entidad', campo: 'entidad' },
        { titulo: 'Detalle', campo: 'detalle' },
      ], historial)}
    </section>
  `;
}

export async function paginaConfiguracion() {
  const contenedor = obtenerContenedor();
  const tienda = await api('/configuracion/tienda');
  contenedor.innerHTML = `
    ${encabezado('Configuración', 'Información general y herramientas de protección de datos.')}
    <section class="rejilla-paneles">
      <article class="panel">
        <h3>${escapar(tienda.nombre)}</h3>
        <p><strong>NIT:</strong> ${escapar(tienda.nit || 'No registrado')}</p>
        <p><strong>Teléfono:</strong> ${escapar(tienda.telefono || '—')}</p>
        <p><strong>Dirección:</strong> ${escapar(tienda.direccion || '—')}</p>
        <p><strong>Correo:</strong> ${escapar(tienda.correo || '—')}</p>
        <p><strong>Moneda:</strong> ${escapar(tienda.moneda)}</p>
      </article>
      <article class="panel">
        <h3>Respaldo</h3>
        <p>Genera una copia JSON con productos, clientes, proveedores, ventas, compras y pedidos.</p>
        ${tienePermiso('respaldo.generar') || tienePermiso('*') ? '<button id="descargar-respaldo" class="boton boton-azul">Descargar respaldo</button>' : ''}
      </article>
    </section>
    <section class="panel" style="margin-top:1rem">
      <img src="/static/assets/promo-crecimiento.png" alt="RioTiendas" style="border-radius:18px;width:100%;max-height:430px;object-fit:cover" />
    </section>
  `;
  document.querySelector('#descargar-respaldo')?.addEventListener('click', async () => {
    try {
      const respuesta = await api('/respaldo');
      const blob = await respuesta.blob();
      const url = URL.createObjectURL(blob);
      const enlace = document.createElement('a');
      enlace.href = url; enlace.download = 'respaldo_riotiendas.json'; enlace.click();
      URL.revokeObjectURL(url);
    } catch (error) { avisar(error.message, 'error'); }
  });
}

export function paginaNoAutorizada() {
  obtenerContenedor().innerHTML = `
    <section class="panel">
      <h2>Acceso restringido</h2>
      <p>Tu rol no tiene permiso para usar este módulo.</p>
      <button class="boton boton-claro" id="volver-inicio">Volver</button>
    </section>
  `;
  document.querySelector('#volver-inicio')?.addEventListener('click', () => navegar('inicio'));
}
