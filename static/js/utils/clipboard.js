/**
 * Inicializa un botón de copiar que copia el texto de un elemento origen al portapapeles.
 *
 * @param {Object} config
 * @param {HTMLElement} config.button - Botón que dispara la acción.
 * @param {HTMLElement} config.source - Elemento que contiene el texto a copiar.
 * @param {HTMLElement} config.tooltip - Elemento donde se muestra el feedback.
 * @param {string} [config.successText="¡Copiado!"] - Texto a mostrar tras copiar.
 * @param {string} [config.defaultText="Copiar"] - Texto por defecto del tooltip.
 * @param {number} [config.feedbackMs=2000] - Tiempo que dura el feedback.
 */
export function initializeCopyButton({ button, source, tooltip, successText = "¡Copiado!", defaultText = "Copiar", feedbackMs = 2000 }) {
    if (!button || !source || !tooltip) {
        return;
    }

    button.addEventListener("click", async () => {
        const textToCopy = source.innerText || source.textContent || "";

        try {
            await navigator.clipboard.writeText(textToCopy);
            tooltip.innerText = successText;
            tooltip.classList.add("visible");

            setTimeout(() => {
                tooltip.innerText = defaultText;
                tooltip.classList.remove("visible");
            }, feedbackMs);
        } catch (error) {
            // eslint-disable-next-line no-console
            console.error("Error al copiar el texto: ", error);
        }
    });
}
