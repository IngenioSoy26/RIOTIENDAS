# Despliegue de RIOTIENDAS

## Opción A — Demo rápida con Render/Railway

### Backend + frontend

RioTiendas sirve la PWA directamente desde FastAPI, por lo que basta desplegar **un solo servicio web**.

Directorio de trabajo:

```text
backend
```

Instalación:

```bash
pip install -r requirements.txt
```

Comando de inicio:

```bash
uvicorn app.main:aplicacion --host 0.0.0.0 --port $PORT
```

Variables mínimas:

```env
APP_AMBIENTE=produccion
APP_LLAVE_SECRETA=USA_UNA_LLAVE_ALEATORIA_LARGA_Y_PRIVADA
APP_URL_BD=postgresql://USUARIO:CLAVE@HOST:PUERTO/BASE
CORS_ORIGENES=https://tu-dominio.com,capacitor://localhost
```

## PostgreSQL

En producción se recomienda PostgreSQL. SQLAlchemy ya separa la lógica de persistencia, por lo que el cambio principal es `APP_URL_BD`.

Si el proveedor exige un driver específico, agrega `psycopg[binary]` a `requirements.txt`.

## HTTPS

Para instalar la PWA y usar cámara en dispositivos móviles se debe desplegar bajo HTTPS. `localhost` es la excepción habitual durante desarrollo.

## Cámara / códigos de barras

- Lector USB/Bluetooth: funciona como teclado y es la alternativa más universal.
- Cámara: usa `BarcodeDetector` donde el navegador lo soporte.
- Para producción móvil de alta compatibilidad conviene agregar un plugin de escáner nativo mediante Capacitor.

## Android e iOS

Consulta `/mobile/README.md`.

### Android
Puede generarse un proyecto Android con Capacitor y producir un AAB para Google Play.

### iOS
Requiere macOS, Xcode y cuenta de Apple Developer para compilar y publicar.

## Antes de producción real

Este MVP es funcional, pero un negocio real requiere además:

- migraciones de base de datos (Alembic);
- política formal de backups externos;
- almacenamiento de imágenes;
- correo transaccional para recuperación de contraseña;
- HTTPS y secretos robustos;
- monitoreo de errores;
- pruebas de carga;
- política de privacidad y tratamiento de datos;
- revisión tributaria antes de llamar “contabilidad” o “facturación electrónica” a módulos no certificados.
