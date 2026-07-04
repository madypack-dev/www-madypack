import { ITracker } from '../domain/ITracker.js';

export class GoogleTagManagerTracker extends ITracker {
    constructor(gtmId, isLocalhost = false) {
        super();
        this.gtmId = gtmId;
        this.isLocalhost = isLocalhost;
    }

    /**
     * @returns {void}
     */
    initialize() {
        if (!this.gtmId || this.isLocalhost) {
            return;
        }
        
        // Evitar inicializar dos veces
        if (window.dataLayer && window.dataLayer.some(e => e['gtm.start'])) {
            return;
        }

        window.dataLayer = window.dataLayer || [];
        window.dataLayer.push({ 'gtm.start': new Date().getTime(), event: 'gtm.js' });

        const script = document.createElement('script');
        script.async = true;
        script.src = 'https://www.googletagmanager.com/gtm.js?id=' + encodeURIComponent(this.gtmId);

        const firstScript = document.getElementsByTagName('script')[0];
        if (firstScript && firstScript.parentNode) {
            firstScript.parentNode.insertBefore(script, firstScript);
        } else {
            document.head.appendChild(script);
        }
    }
}

export class GoogleAnalyticsTracker extends ITracker {
    constructor(gaId, isLocalhost = false) {
        super();
        this.gaId = gaId;
        this.isLocalhost = isLocalhost;
    }

    /**
     * @returns {void}
     */
    initialize() {
        if (!this.gaId || this.isLocalhost) {
            return;
        }

        // Evitar inicializar dos veces
        if (window.gtag) {
            return;
        }

        const script = document.createElement('script');
        script.async = true;
        script.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(this.gaId);
        document.head.appendChild(script);

        window.dataLayer = window.dataLayer || [];
        function gtag() { window.dataLayer.push(arguments); }
        window.gtag = gtag;

        gtag('js', new Date());
        gtag('config', this.gaId);
    }
}
