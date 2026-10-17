from datetime import datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


def ahora_utc():
    return datetime.now(timezone.utc)


class Tienda(Base):
    __tablename__ = "tiendas"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    nit: Mapped[str] = mapped_column(String(40), default="")
    telefono: Mapped[str] = mapped_column(String(30), default="")
    direccion: Mapped[str] = mapped_column(String(180), default="")
    correo: Mapped[str] = mapped_column(String(120), default="")
    moneda: Mapped[str] = mapped_column(String(10), default="COP")
    impuesto_porcentaje: Mapped[float] = mapped_column(Float, default=0)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora_utc)


class Cliente(Base):
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(primary_key=True)
    tienda_id: Mapped[int] = mapped_column(ForeignKey("tiendas.id"), index=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    telefono: Mapped[str] = mapped_column(String(30), default="")
    direccion: Mapped[str] = mapped_column(String(180), default="")
    correo: Mapped[str] = mapped_column(String(120), default="")
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora_utc)


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    tienda_id: Mapped[int] = mapped_column(ForeignKey("tiendas.id"), index=True)
    cliente_id: Mapped[int | None] = mapped_column(ForeignKey("clientes.id"), nullable=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    correo: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    telefono: Mapped[str] = mapped_column(String(30), default="")
    contrasena_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[str] = mapped_column(String(30), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    permisos_personalizados: Mapped[str | None] = mapped_column(Text, nullable=True)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora_utc)


class Categoria(Base):
    __tablename__ = "categorias"

    id: Mapped[int] = mapped_column(primary_key=True)
    tienda_id: Mapped[int] = mapped_column(ForeignKey("tiendas.id"), index=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    descripcion: Mapped[str] = mapped_column(String(220), default="")


class Proveedor(Base):
    __tablename__ = "proveedores"

    id: Mapped[int] = mapped_column(primary_key=True)
    tienda_id: Mapped[int] = mapped_column(ForeignKey("tiendas.id"), index=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    telefono: Mapped[str] = mapped_column(String(30), default="")
    direccion: Mapped[str] = mapped_column(String(180), default="")
    correo: Mapped[str] = mapped_column(String(120), default="")
    notas: Mapped[str] = mapped_column(Text, default="")
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


class Producto(Base):
    __tablename__ = "productos"

    id: Mapped[int] = mapped_column(primary_key=True)
    tienda_id: Mapped[int] = mapped_column(ForeignKey("tiendas.id"), index=True)
    categoria_id: Mapped[int | None] = mapped_column(ForeignKey("categorias.id"), nullable=True)
    proveedor_id: Mapped[int | None] = mapped_column(ForeignKey("proveedores.id"), nullable=True)
    nombre: Mapped[str] = mapped_column(String(140), nullable=False, index=True)
    codigo_barras: Mapped[str] = mapped_column(String(80), default="", index=True)
    codigo_interno: Mapped[str] = mapped_column(String(60), default="", index=True)
    marca: Mapped[str] = mapped_column(String(100), default="")
    precio_compra: Mapped[float] = mapped_column(Float, default=0)
    precio_venta: Mapped[float] = mapped_column(Float, default=0)
    cantidad_disponible: Mapped[float] = mapped_column(Float, default=0)
    stock_minimo: Mapped[float] = mapped_column(Float, default=0)
    unidad_medida: Mapped[str] = mapped_column(String(30), default="unidad")
    fecha_vencimiento: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    imagen_url: Mapped[str] = mapped_column(String(255), default="")
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


class Venta(Base):
    __tablename__ = "ventas"

    id: Mapped[int] = mapped_column(primary_key=True)
    tienda_id: Mapped[int] = mapped_column(ForeignKey("tiendas.id"), index=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    cliente_id: Mapped[int | None] = mapped_column(ForeignKey("clientes.id"), nullable=True)
    pedido_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    numero: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    subtotal: Mapped[float] = mapped_column(Float, default=0)
    descuento: Mapped[float] = mapped_column(Float, default=0)
    impuesto: Mapped[float] = mapped_column(Float, default=0)
    total: Mapped[float] = mapped_column(Float, default=0)
    costo_total: Mapped[float] = mapped_column(Float, default=0)
    ganancia_estimada: Mapped[float] = mapped_column(Float, default=0)
    metodo_pago: Mapped[str] = mapped_column(String(40), default="efectivo")
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora_utc)
    anulada: Mapped[bool] = mapped_column(Boolean, default=False)


class DetalleVenta(Base):
    __tablename__ = "detalles_venta"

    id: Mapped[int] = mapped_column(primary_key=True)
    venta_id: Mapped[int] = mapped_column(ForeignKey("ventas.id"), index=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id"))
    cantidad: Mapped[float] = mapped_column(Float, nullable=False)
    precio_unitario: Mapped[float] = mapped_column(Float, nullable=False)
    costo_unitario: Mapped[float] = mapped_column(Float, nullable=False)
    subtotal: Mapped[float] = mapped_column(Float, nullable=False)


class Compra(Base):
    __tablename__ = "compras"

    id: Mapped[int] = mapped_column(primary_key=True)
    tienda_id: Mapped[int] = mapped_column(ForeignKey("tiendas.id"), index=True)
    proveedor_id: Mapped[int | None] = mapped_column(ForeignKey("proveedores.id"), nullable=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    numero: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    total: Mapped[float] = mapped_column(Float, default=0)
    observacion: Mapped[str] = mapped_column(Text, default="")
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora_utc)


class DetalleCompra(Base):
    __tablename__ = "detalles_compra"

    id: Mapped[int] = mapped_column(primary_key=True)
    compra_id: Mapped[int] = mapped_column(ForeignKey("compras.id"), index=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id"))
    cantidad: Mapped[float] = mapped_column(Float, nullable=False)
    costo_unitario: Mapped[float] = mapped_column(Float, nullable=False)
    subtotal: Mapped[float] = mapped_column(Float, nullable=False)


class Pedido(Base):
    __tablename__ = "pedidos"

    id: Mapped[int] = mapped_column(primary_key=True)
    tienda_id: Mapped[int] = mapped_column(ForeignKey("tiendas.id"), index=True)
    cliente_id: Mapped[int | None] = mapped_column(ForeignKey("clientes.id"), nullable=True)
    usuario_creador_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    domiciliario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    numero: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    nombre_cliente: Mapped[str] = mapped_column(String(120), nullable=False)
    telefono: Mapped[str] = mapped_column(String(30), nullable=False)
    direccion: Mapped[str] = mapped_column(String(180), nullable=False)
    notas: Mapped[str] = mapped_column(Text, default="")
    subtotal: Mapped[float] = mapped_column(Float, default=0)
    costo_domicilio: Mapped[float] = mapped_column(Float, default=0)
    total: Mapped[float] = mapped_column(Float, default=0)
    metodo_pago: Mapped[str] = mapped_column(String(40), default="efectivo")
    estado: Mapped[str] = mapped_column(String(40), default="recibido", index=True)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora_utc)
    fecha_actualizacion: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora_utc)


class DetallePedido(Base):
    __tablename__ = "detalles_pedido"

    id: Mapped[int] = mapped_column(primary_key=True)
    pedido_id: Mapped[int] = mapped_column(ForeignKey("pedidos.id"), index=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id"))
    cantidad: Mapped[float] = mapped_column(Float, nullable=False)
    precio_unitario: Mapped[float] = mapped_column(Float, nullable=False)
    subtotal: Mapped[float] = mapped_column(Float, nullable=False)


class Gasto(Base):
    __tablename__ = "gastos"

    id: Mapped[int] = mapped_column(primary_key=True)
    tienda_id: Mapped[int] = mapped_column(ForeignKey("tiendas.id"), index=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    concepto: Mapped[str] = mapped_column(String(160), nullable=False)
    categoria: Mapped[str] = mapped_column(String(80), default="general")
    valor: Mapped[float] = mapped_column(Float, nullable=False)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora_utc)


class MovimientoInventario(Base):
    __tablename__ = "movimientos_inventario"

    id: Mapped[int] = mapped_column(primary_key=True)
    tienda_id: Mapped[int] = mapped_column(ForeignKey("tiendas.id"), index=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id"))
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    tipo: Mapped[str] = mapped_column(String(50), nullable=False)
    cantidad: Mapped[float] = mapped_column(Float, nullable=False)
    existencia_anterior: Mapped[float] = mapped_column(Float, nullable=False)
    existencia_nueva: Mapped[float] = mapped_column(Float, nullable=False)
    referencia: Mapped[str] = mapped_column(String(100), default="")
    nota: Mapped[str] = mapped_column(Text, default="")
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora_utc)


class Actividad(Base):
    __tablename__ = "actividades"

    id: Mapped[int] = mapped_column(primary_key=True)
    tienda_id: Mapped[int] = mapped_column(ForeignKey("tiendas.id"), index=True)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    accion: Mapped[str] = mapped_column(String(100), nullable=False)
    entidad: Mapped[str] = mapped_column(String(80), default="")
    entidad_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    detalle: Mapped[str] = mapped_column(Text, default="")
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora_utc)
