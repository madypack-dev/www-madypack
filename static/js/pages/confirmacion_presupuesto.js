import { initializeCopyButton } from "../utils/clipboard.js";

document.addEventListener("DOMContentLoaded", () => {
    const btnCopy = document.getElementById("btn-copy-ref");
    const refCode = document.getElementById("ref-code");
    const tooltip = document.getElementById("copy-tooltip");

    initializeCopyButton({ button: btnCopy, source: refCode, tooltip });
});
