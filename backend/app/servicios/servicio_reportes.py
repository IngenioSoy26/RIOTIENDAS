from datetime import datetime, time, timedelta, timezone
from io import BytesIO, StringIO
import csv

from openpyxl import Workbook
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modelos.modelos import Compra, DetalleVenta, Gasto, Pedido, Producto, Usuario, Venta


class ServicioReportes:
    def __init__(self, db: Session, usuario: Usuario):
        self.db = db
        self.usuario = usuario

    def _inicio_dia(self):
        hoy = datetime.now(timezone.utc).date()
        return datetime.combine(hoy, time.min, tzinfo=timezone.utc)

    def resumen_dashboard(self):
        inicio_hoy = self._inicio_dia()
        inicio_semana = inicio_hoy - timedelta(days=inicio_hoy.weekday())
        inicio_mes = inicio_hoy.replace(day=1)

        def total_ventas(desde):
            return float(self.db.query(func.coalesce(func.sum(Venta.total), 0)).filter(
                Venta.tienda_id == self.usuario.tienda_id,
                Venta.anulada.is_(False),
                Venta.fecha >= desde,
            ).scalar() or 0)

        ventas_hoy = total_ventas(inicio_hoy)
        ventas_semana = total_ventas(inicio_semana)
        ventas_mes = total_ventas(inicio_mes)
        ganancia_hoy = float(self.db.query(func.coalesce(func.sum(Venta.ganancia_estimada), 0)).filter(
            Venta.tienda_id == self.usuario.tienda_id,
            Venta.anulada.is_(False),
            Venta.fecha >= inicio_hoy,
        ).scalar() or 0)

        productos = self.db.query(Producto).filter(
            Producto.tienda_id == self.usuario.tienda_id,
            Producto.activo.is_(True),
        ).all()
        pedidos_pendientes = self.db.query(func.count(Pedido.id)).filter(
            Pedido.tienda_id == self.usuario.tienda_id,
            Pedido.estado.notin_(["entregado", "cancelado"]),
        ).scalar() or 0

        ventas_recientes = self.db.query(Venta).filter(
            Venta.tienda_id == self.usuario.tienda_id,
            Venta.anulada.is_(False),
            Venta.fecha >= inicio_hoy - timedelta(days=6),
        ).all()
        por_dia = {}
        for i in range(7):
            fecha = (inicio_hoy - timedelta(days=6 - i)).date().isoformat()
            por_dia[fecha] = 0.0
        for venta in ventas_recientes:
            clave = venta.fecha.date().isoformat()
            if clave in por_dia:
                por_dia[clave] += venta.total

        detalles = self.db.query(DetalleVenta).join(Venta, DetalleVenta.venta_id == Venta.id).filter(
            Venta.tienda_id == self.usuario.tienda_id,
            Venta.anulada.is_(False),
        ).all()
        acumulado = {}
        for detalle in detalles:
            acumulado[detalle.producto_id] = acumulado.get(detalle.producto_id, 0) + detalle.cantidad
        ranking = sorted(acumulado.items(), key=lambda item: item[1], reverse=True)[:5]
        mas_vendidos = []
        for producto_id, cantidad in ranking:
            producto = self.db.get(Producto, producto_id)
            if producto:
                mas_vendidos.append({"nombre": producto.nombre, "cantidad": cantidad})

        return {
            "ventas_hoy": round(ventas_hoy, 2),
            "ventas_semana": round(ventas_semana, 2),
            "ventas_mes": round(ventas_mes, 2),
            "ganancia_hoy": round(ganancia_hoy, 2),
            "productos_disponibles": sum(1 for p in productos if p.cantidad_disponible > 0),
            "productos_agotados": sum(1 for p in productos if p.cantidad_disponible <= 0),
            "productos_stock_bajo": sum(1 for p in productos if 0 < p.cantidad_disponible <= p.stock_minimo),
            "pedidos_pendientes": pedidos_pendientes,
            "ventas_ultimos_7_dias": [{"fecha": k, "total": round(v, 2)} for k, v in por_dia.items()],
            "productos_mas_vendidos": mas_vendidos,
        }

    def filas_reporte_ventas(self):
        ventas = self.db.query(Venta).filter(Venta.tienda_id == self.usuario.tienda_id).order_by(Venta.fecha.desc()).all()
        return [
            [v.numero, v.fecha.strftime("%Y-%m-%d %H:%M"), v.total, v.ganancia_estimada, v.metodo_pago, "Sí" if v.anulada else "No"]
            for v in ventas
        ]

    def exportar_csv(self) -> bytes:
        salida = StringIO()
        escritor = csv.writer(salida)
        escritor.writerow(["Número", "Fecha", "Total", "Ganancia estimada", "Método de pago", "Anulada"])
        escritor.writerows(self.filas_reporte_ventas())
        return salida.getvalue().encode("utf-8-sig")

    def exportar_excel(self) -> bytes:
        libro = Workbook()
        hoja = libro.active
        hoja.title = "Ventas"
        hoja.append(["Número", "Fecha", "Total", "Ganancia estimada", "Método de pago", "Anulada"])
        for fila in self.filas_reporte_ventas():
            hoja.append(fila)
        salida = BytesIO()
        libro.save(salida)
        return salida.getvalue()

    def exportar_pdf(self) -> bytes:
        salida = BytesIO()
        documento = canvas.Canvas(salida, pagesize=letter)
        _, alto = letter
        documento.setFont("Helvetica-Bold", 16)
        documento.drawString(40, alto - 50, "RIOTIENDAS - Reporte de ventas")
        y = alto - 85
        documento.setFont("Helvetica", 9)
        for fila in self.filas_reporte_ventas()[:80]:
            texto = f"{fila[0]} | {fila[1]} | Total: ${fila[2]:,.0f} | Ganancia: ${fila[3]:,.0f} | {fila[4]}"
            documento.drawString(40, y, texto[:110])
            y -= 15
            if y < 50:
                documento.showPage()
                y = alto - 50
        documento.save()
        return salida.getvalue()
