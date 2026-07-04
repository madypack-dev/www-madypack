import { Consent, ConsentStatus } from '../domain/Consent.js';
import { IConsentRepository } from '../domain/IConsentRepository.js';

export class LocalStorageConsentRepository extends IConsentRepository {
    constructor(key = 'cookie_consent_status') {
        super();
        this.key = key;
    }

    /**
     * @returns {Consent}
     */
    get() {
        try {
            const stored = localStorage.getItem(this.key);
            if (!stored) {
                return new Consent(ConsentStatus.PENDING);
            }
            return new Consent(stored);
        } catch (error) {
            console.error('Error reading from localStorage:', error);
            return new Consent(ConsentStatus.PENDING);
        }
    }

    /**
     * @param {Consent} consent
     * @returns {void}
     */
    save(consent) {
        try {
            localStorage.setItem(this.key, consent.getStatus());
        } catch (error) {
            console.error('Error writing to localStorage:', error);
        }
    }
}
