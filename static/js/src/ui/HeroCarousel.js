export class HeroCarousel {
    /**
     * @param {string} slideSelector
     * @param {string} prevSelector
     * @param {string} nextSelector
     * @param {number} intervalMs
     */
    constructor(
        slideSelector = '.hero-slide',
        prevSelector = '.hero-arrow-prev',
        nextSelector = '.hero-arrow-next',
        intervalMs = 6000
    ) {
        this.slides = document.querySelectorAll(slideSelector);
        this.prevBtn = document.querySelector(prevSelector);
        this.nextBtn = document.querySelector(nextSelector);
        this.intervalMs = intervalMs;
        this.currentSlide = 0;
        this.timer = null;
    }

    /**
     * @returns {void}
     */
    initialize() {
        if (this.slides.length <= 1) {
            return;
        }

        // Registrar eventos de clic para las flechas
        if (this.prevBtn) {
            this.prevBtn.addEventListener('click', () => {
                this.prev();
                this.resetTimer();
            });
        }
        if (this.nextBtn) {
            this.nextBtn.addEventListener('click', () => {
                this.next();
                this.resetTimer();
            });
        }

        this.start();
    }

    /**
     * @returns {void}
     */
    start() {
        this.timer = setInterval(() => {
            this.next();
        }, this.intervalMs);
    }

    /**
     * @returns {void}
     */
    stop() {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
    }

    /**
     * @returns {void}
     */
    resetTimer() {
        this.stop();
        this.start();
    }

    /**
     * @returns {void}
     */
    next() {
        this.goToSlide((this.currentSlide + 1) % this.slides.length);
    }

    /**
     * @returns {void}
     */
    prev() {
        this.goToSlide((this.currentSlide - 1 + this.slides.length) % this.slides.length);
    }

    /**
     * @param {number} index
     * @returns {void}
     */
    goToSlide(index) {
        this.slides[this.currentSlide].classList.remove('active');
        this.currentSlide = index;
        this.slides[this.currentSlide].classList.add('active');
    }
}
