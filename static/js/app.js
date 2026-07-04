import { LocalStorageConsentRepository } from './src/adapters/LocalStorageConsentRepository.js';
import { GoogleTagManagerTracker, GoogleAnalyticsTracker } from './src/adapters/GoogleTrackers.js';
import { ConsentService } from './src/application/ConsentService.js';
import { CookieBanner } from './src/ui/CookieBanner.js';
import { MobileMenu } from './src/ui/MobileMenu.js';

document.addEventListener('DOMContentLoaded', () => {
    // 1. Obtener configuración de infraestructura desde el DOM
    const html = document.documentElement;
    const gtmId = html.dataset.gtmId;
    const gaId = html.dataset.gaId;
    const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';

    // 2. Instanciar dependencias de trackers (Adapter Layer)
    const trackers = [];
    if (gtmId) {
        trackers.push(new GoogleTagManagerTracker(gtmId, isLocalhost));
    }
    if (gaId) {
        trackers.push(new GoogleAnalyticsTracker(gaId, isLocalhost));
    }

    // 3. Inicializar Caso de Uso / Servicio de Consentimiento (Application Layer)
    const consentRepository = new LocalStorageConsentRepository();
    const consentService = new ConsentService(consentRepository, trackers);

    // 4. Inicializar Componentes (UI Layer)
    const cookieBanner = new CookieBanner(consentService);
    cookieBanner.initialize();

    const mobileMenu = new MobileMenu();
    mobileMenu.initialize();
});
