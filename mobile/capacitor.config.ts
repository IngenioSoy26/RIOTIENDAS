import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.riotiendas.app',
  appName: 'RioTiendas',
  webDir: 'www',
  // Para la demo móvil, reemplaza esta URL por el dominio HTTPS donde
  // publiques RioTiendas. Así Android/iOS muestran la misma aplicación web.
  server: {
    url: 'https://TU-DOMINIO-RIOTIENDAS.com',
    cleartext: false,
  },
};

export default config;
