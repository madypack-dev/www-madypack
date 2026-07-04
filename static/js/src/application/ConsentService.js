import { Consent, ConsentStatus } from '../domain/Consent.js';

export class ConsentService {
    /**
     * @param {IConsentRepository} consentRepository
     * @param {ITracker[]} trackers
     */
    constructor(consentRepository, trackers = []) {
        this.repository = consentRepository;
        this.trackers = trackers;
    }

    /**
     * @returns {Consent}
     */
    getConsent() {
        return this.repository.get();
    }

    /**
     * @returns {Consent}
     */
    acceptConsent() {
        const consent = new Consent(ConsentStatus.ACCEPTED);
        this.repository.save(consent);
        this._initializeTrackers();
        return consent;
    }

    /**
     * @returns {Consent}
     */
    declineConsent() {
        const consent = new Consent(ConsentStatus.DECLINED);
        this.repository.save(consent);
        return consent;
    }

    /**
     * @returns {Consent}
     */
    initialize() {
        const consent = this.getConsent();
        if (consent.isAccepted()) {
            this._initializeTrackers();
        }
        return consent;
    }

    /**
     * @private
     */
    _initializeTrackers() {
        this.trackers.forEach(tracker => {
            try {
                tracker.initialize();
            } catch (error) {
                console.error('Error initializing tracker:', error);
            }
        });
    }
}
