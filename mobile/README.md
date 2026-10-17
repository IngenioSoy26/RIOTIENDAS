# Empaquetado móvil de RioTiendas

RioTiendas ya funciona como **PWA instalable**. Esta carpeta deja preparada una segunda vía con **Capacitor** para generar proyectos nativos Android/iOS a partir de la aplicación web desplegada.

## Android

1. Despliega primero RioTiendas en un dominio HTTPS.
2. Sustituye `https://TU-DOMINIO-RIOTIENDAS.com` en `capacitor.config.ts`.
3. Instala dependencias:

```bash
npm install
npx cap add android
npx cap sync android
npx cap open android
```

4. Android Studio abrirá el proyecto para generar APK/AAB.

## iOS

Necesitas macOS + Xcode:

```bash
npm install
npx cap add ios
npx cap sync ios
npx cap open ios
```

## Importante

Una app de tienda real publicada en tiendas de aplicaciones debe revisar permisos de cámara, privacidad, tratamiento de datos, política de respaldo y, si más adelante se maneja pago electrónico integrado, los requisitos legales y del proveedor de pagos.
