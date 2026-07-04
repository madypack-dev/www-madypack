export const ConsentStatus = {
    PENDING: 'PENDING',
    ACCEPTED: 'ACCEPTED',
    DECLINED: 'DECLINED'
};

export class Consent {
    constructor(status = ConsentStatus.PENDING) {
        if (!Object.values(ConsentStatus).includes(status)) {
            throw new Error(`Invalid consent status: ${status}`);
        }
        this._status = status;
    }

    getStatus() {
        return this._status;
    }

    isAccepted() {
        return this._status === ConsentStatus.ACCEPTED;
    }

    isDeclined() {
        return this._status === ConsentStatus.DECLINED;
    }

    isPending() {
        return this._status === ConsentStatus.PENDING;
    }
}
