import { dinero, escapar } from './api_cliente.js';

export function tarjetaKpi(titulo, valor, icono = '●', clase = '') {
  return `
    <article class="kpi ${clase}">
      <div class="producto-icono">${icono}</div>
      <div>
        <span class="etiqueta">${escapar(titulo)}</span>
        <div class="valor">${escapar(valor)}</div>
      </div>
    </article>
  `;
}

export function estadoInventario(producto) {
  if (Number(producto.cantidad_disponible) <= 0) return '<span class="estado agotado">Agotado</span>';
  if (Number(producto.cantidad_disponible) <= Number(producto.stock_minimo)) return '<span class="estado poco_inventario">Poco inventario</span>';
  return '<span class="estado disponible">Disponible</span>';
}

export function abrirModal(titulo, contenido, ancho = '760px') {
  cerrarModal();
  const contenedor = document.createElement('div');
  contenedor.id = 'modal-global';
  contenedor.className = 'modal-fondo';
  contenedor.innerHTML = `
    <div class="modal" style="max-width:${ancho}">
      <div class="modal-cabecera">
        <h2>${escapar(titulo)}</h2>
        <button class="cerrar" id="cerrar-modal" aria-label="Cerrar">×</button>
      </div>
      <div class="modal-contenido">${contenido}</div>
    </div>
  `;
  document.body.appendChild(contenedor);
  document.querySelector('#cerrar-modal')?.addEventListener('click', cerrarModal);
  contenedor.addEventListener('click', (evento) => {
    if (evento.target === contenedor) cerrarModal();
  });
}

export function cerrarModal() {
  document.querySelector('#modal-global')?.remove();
}

export function campoFormulario(etiqueta, id, tipo = 'text', valor = '', extra = '') {
  return `
    <label class="campo">
      <span>${escapar(etiqueta)}</span>
      <input id="${id}" type="${tipo}" value="${escapar(valor)}" ${extra} />
    </label>
  `;
}

export function selectorFormulario(etiqueta, id, opciones, valor = '') {
  const htmlOpciones = opciones.map((opcion) => {
    const objeto = typeof opcion === 'string' ? { valor: opcion, texto: opcion } : opcion;
    return `<option value="${escapar(objeto.valor)}" ${String(objeto.valor) === String(valor) ? 'selected' : ''}>${escapar(objeto.texto)}</option>`;
  }).join('');
  return `
    <label class="campo">
      <span>${escapar(etiqueta)}</span>
      <select id="${id}">${htmlOpciones}</select>
    </label>
  `;
}

export function tablaHTML(columnas, filas, renderAcciones = null) {
  if (!filas.length) return '<div class="vacio">No hay registros para mostrar.</div>';
  const cabecera = columnas.map(c => `<th>${escapar(c.titulo)}</th>`).join('');
  const cuerpo = filas.map((fila) => {
    const celdas = columnas.map((columna) => {
      const valor = columna.render ? columna.render(fila) : escapar(fila[columna.campo] ?? '');
      return `<td>${valor}</td>`;
    }).join('');
    const acciones = renderAcciones ? `<td class="celda-acciones">${renderAcciones(fila)}</td>` : '';
    return `<tr>${celdas}${acciones}</tr>`;
  }).join('');
  return `
    <div class="tabla-wrap">
      <table >
        <thead><tr>${cabecera}${renderAcciones ? '<th>Acciones</th>' : ''}</tr></thead>
        <tbody>${cuerpo}</tbody>
      </table>
    </div>
  `;
}

export function dibujarBarras(canvas, datos, campoEtiqueta, campoValor, color = '#F36A08') {
  if (!canvas || !datos?.length) return;
  const escala = window.devicePixelRatio || 1;
  const anchoCss = Math.max(canvas.clientWidth, 300);
  const altoCss = 230;
  canvas.width = anchoCss * escala;
  canvas.height = altoCss * escala;
  const ctx = canvas.getContext('2d');
  ctx.scale(escala, escala);
  ctx.clearRect(0, 0, anchoCss, altoCss);

  const margen = { izquierda: 42, derecha: 16, arriba: 18, abajo: 44 };
  const ancho = anchoCss - margen.izquierda - margen.derecha;
  const alto = altoCss - margen.arriba - margen.abajo;
  const maximo = Math.max(...datos.map(item => Number(item[campoValor] || 0)), 1);

  ctx.strokeStyle = '#E7EDF5';
  ctx.fillStyle = '#6B7A90';
  ctx.font = '11px system-ui';
  for (let i = 0; i <= 4; i++) {
    const y = margen.arriba + (alto / 4) * i;
    ctx.beginPath();
    ctx.moveTo(margen.izquierda, y);
    ctx.lineTo(margen.izquierda + ancho, y);
    ctx.stroke();
    const valor = Math.round(maximo - (maximo / 4) * i);
    ctx.fillText(String(valor), 4, y + 4);
  }

  const espacio = ancho / datos.length;
  const anchoBarra = Math.min(38, espacio * 0.55);
  datos.forEach((item, indice) => {
    const valor = Number(item[campoValor] || 0);
    const altoBarra = (valor / maximo) * alto;
    const x = margen.izquierda + indice * espacio + (espacio - anchoBarra) / 2;
    const y = margen.arriba + alto - altoBarra;
    const gradiente = ctx.createLinearGradient(0, y, 0, y + altoBarra);
    gradiente.addColorStop(0, color);
    gradiente.addColorStop(1, '#FFB11B');
    ctx.fillStyle = gradiente;
    ctx.fillRect(x, y, anchoBarra, altoBarra);

    ctx.fillStyle = '#53657C';
    ctx.textAlign = 'center';
    ctx.fillText(String(item[campoEtiqueta] ?? '').slice(0, 10), x + anchoBarra / 2, altoCss - 18);
  });
  ctx.textAlign = 'left';
}

export function tarjetaProducto(producto, boton = '') {
  const inicial = escapar(producto.nombre?.charAt(0)?.toUpperCase() || 'P');
  return `
    <article class="producto-card">
      <div class="producto-icono">${producto.imagen_url ? `<img src="${escapar(producto.imagen_url)}" alt="">` : inicial}</div>
      <h4>${escapar(producto.nombre)}</h4>
      <div class="precio">${dinero(producto.precio_venta)}</div>
      <small>Disponibles: ${escapar(producto.cantidad_disponible)}</small>
      <div style="margin-top:.7rem">${boton}</div>
    </article>
  `;
}
