import { ITracker } from '../domain/ITracker.js';

export class MicrosoftClarityTracker extends ITracker {
    constructor(clarityId, isLocalhost = false) {
        super();
        this.clarityId = clarityId;
        this.isLocalhost = isLocalhost;
    }

    /**
     * @returns {void}
     */
    initialize() {
        if (!this.clarityId || this.clarityId === 'CLARITY_ID_AQUI' || this.isLocalhost) {
            return;
        }

        if (window.clarity) {
            return;
        }

        (function(c,l,a,r,i,t,y){
            c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};
            t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
            y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
        })(window, document, "clarity", "script", this.clarityId);
    }
}
