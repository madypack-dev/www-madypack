export class MobileMenu {
    /**
     * @param {string} toggleSelector
     * @param {string} menuId
     */
    constructor(toggleSelector = '.menu-toggle', menuId = 'mobile-menu') {
        this.toggle = document.querySelector(toggleSelector);
        this.menu = document.getElementById(menuId);
    }

    /**
     * @returns {void}
     */
    initialize() {
        if (!this.toggle || !this.menu) {
            return;
        }

        this.toggle.addEventListener('click', () => {
            const isExpanded = this.toggle.getAttribute('aria-expanded') === 'true';
            this.toggle.setAttribute('aria-expanded', String(!isExpanded));
            this.menu.hidden = isExpanded;
        });
    }
}
