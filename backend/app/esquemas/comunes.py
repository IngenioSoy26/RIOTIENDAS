from pydantic import BaseModel, EmailStr, Field


class Credenciales(BaseModel):
    correo: EmailStr
    contrasena: str


class UsuarioCrear(BaseModel):
    nombre: str = Field(min_length=3, max_length=120)
    correo: EmailStr
    telefono: str = ""
    direccion: str = ""
    contrasena: str = Field(min_length=8, max_length=80)
    rol: str


class UsuarioPermisosActualizar(BaseModel):
    permisos: list[str] | None = None


class ProductoEntrada(BaseModel):
    nombre: str
    codigo_barras: str = ""
    codigo_interno: str = ""
    categoria_id: int | None = None
    proveedor_id: int | None = None
    marca: str = ""
    precio_compra: float = Field(ge=0)
    precio_venta: float = Field(ge=0)
    cantidad_disponible: float = Field(default=0, ge=0)
    stock_minimo: float = Field(default=0, ge=0)
    unidad_medida: str = "unidad"
    fecha_vencimiento: str | None = None
    imagen_url: str = ""


class AjusteInventario(BaseModel):
    cantidad: float
    nota: str = ""


class LineaVenta(BaseModel):
    producto_id: int
    cantidad: float = Field(gt=0)


class VentaCrear(BaseModel):
    cliente_id: int | None = None
    lineas: list[LineaVenta]
    descuento: float = Field(default=0, ge=0)
    metodo_pago: str = "efectivo"


class ProveedorEntrada(BaseModel):
    nombre: str
    telefono: str = ""
    direccion: str = ""
    correo: str = ""
    notas: str = ""


class LineaCompra(BaseModel):
    producto_id: int
    cantidad: float = Field(gt=0)
    costo_unitario: float = Field(gt=0)


class CompraCrear(BaseModel):
    proveedor_id: int | None = None
    lineas: list[LineaCompra]
    observacion: str = ""


class ClienteEntrada(BaseModel):
    nombre: str
    telefono: str = ""
    direccion: str = ""
    correo: str = ""


class LineaPedido(BaseModel):
    producto_id: int
    cantidad: float = Field(gt=0)


class PedidoCrear(BaseModel):
    cliente_id: int | None = None
    nombre_cliente: str | None = None
    telefono: str | None = None
    direccion: str | None = None
    notas: str = ""
    metodo_pago: str = "efectivo"
    costo_domicilio: float = Field(default=0, ge=0)
    lineas: list[LineaPedido]


class PedidoAsignar(BaseModel):
    domiciliario_id: int


class PedidoEstado(BaseModel):
    estado: str


class GastoCrear(BaseModel):
    concepto: str
    categoria: str = "general"
    valor: float = Field(gt=0)

class TiendaRegistro(BaseModel):
    nombre_tienda: str = Field(min_length=3, max_length=160)
    nombre_administrador: str = Field(min_length=3, max_length=120)
    correo: EmailStr
    telefono: str = ""
    direccion: str = ""
    contrasena: str = Field(min_length=8, max_length=80)


class RecuperacionSolicitud(BaseModel):
    correo: EmailStr


class RestablecerContrasena(BaseModel):
    token: str
    nueva_contrasena: str = Field(min_length=8, max_length=80)

class CategoriaEntrada(BaseModel):
    nombre: str = Field(min_length=2, max_length=80)
    descripcion: str = ""
