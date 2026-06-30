/**
 * Madypack - Bolsas Sustentables
 * Lógica del lado del cliente
 */

document.addEventListener('DOMContentLoaded', () => {
    console.log('☘️ Madypack Frontend: Entorno inicializado correctamente con FastAPI y Jinja2.');

    // Aquí puedes inicializar tus sliders, carruseles o lógica de carrito de compras
    initApp();
});

function initApp() {
    // Ejemplo de inicialización funcional segura
    const mainTitle = document.querySelector('header h1');
    if (mainTitle) {
        // Tu código interactivo aquí
        console.log('Estructura principal detectada de forma exitosa.');
    }
}