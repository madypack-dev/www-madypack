/**
 * @interface IConsentRepository
 */
export class IConsentRepository {
    /**
     * @returns {Consent}
     */
    get() {
        throw new Error('Method "get" must be implemented');
    }
    
    /**
     * @param {Consent} consent
     * @returns {void}
     */
    save(consent) {
        throw new Error('Method "save" must be implemented');
    }
}
