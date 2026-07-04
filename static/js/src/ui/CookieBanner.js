export class CookieBanner {
    /**
     * @param {ConsentService} consentService
     * @param {string} bannerId
     * @param {string} acceptBtnId
     * @param {string} declineBtnId
     */
    constructor(consentService, bannerId = 'cookie-consent-banner', acceptBtnId = 'btn-accept-cookies', declineBtnId = 'btn-decline-cookies') {
        this.consentService = consentService;
        this.banner = document.getElementById(bannerId);
        this.acceptBtn = document.getElementById(acceptBtnId);
        this.declineBtn = document.getElementById(declineBtnId);
    }

    /**
     * @returns {void}
     */
    initialize() {
        if (!this.banner) {
            return;
        }

        const consent = this.consentService.initialize();

        if (consent.isPending()) {
            this._showBanner();
        }

        if (this.acceptBtn) {
            this.acceptBtn.addEventListener('click', () => this._handleAccept());
        }

        if (this.declineBtn) {
            this.declineBtn.addEventListener('click', () => this._handleDecline());
        }
    }

    /**
     * @private
     */
    _showBanner() {
        this.banner.removeAttribute('hidden');
    }

    /**
     * @private
     */
    _hideBanner() {
        this.banner.classList.add('fade-out');
        // Esperar a que termine la animación CSS para ocultarlo por completo
        this.banner.addEventListener('transitionend', () => {
            this.banner.setAttribute('hidden', '');
            this.banner.classList.remove('fade-out');
        }, { once: true });
    }

    /**
     * @private
     */
    _handleAccept() {
        this.consentService.acceptConsent();
        this._hideBanner();
    }

    /**
     * @private
     */
    _handleDecline() {
        this.consentService.declineConsent();
        this._hideBanner();
    }
}
