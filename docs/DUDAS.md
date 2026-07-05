# Dudas de Alto Nivel — Optimización Frontend

Documento de decisiones estratégicas y arquitectónicas detectadas durante la optimización frontend de bajo nivel. Estos temas **no se implementaron** porque requieren consenso de negocio, cambios de infraestructura o reescrituras que exceden el alcance de mejoras incrementales seguras.

---

## 1. Reorganización de `templates/` y `static/css/` por feature/bounded context

- **Contexto:** El backend está organizado por dominio (`src/comercio/`, `src/precios/`, `src/presupuesto/`, `src/lead/`), pero `templates/` y `static/css/` están organizados por capa técnica (`layouts/`, `components/`, `pages/`, `base/`, `components/`, `layout.css`). Eso genera "disonancia arquitectónica": el frontend no "grita" el mismo dominio que el backend.
- **Opciones consideradas:**
  - **A.** Migrar a estructura por dominio, por ejemplo:
    - `templates/comercio/pages/tienda.html`, `templates/comercio/pages/producto.html`, `templates/comercio/pages/carrito.html`
    - `static/css/comercio/tienda.css`, `static/css/comercio/carrito.css`
    - `static/js/comercio/carrito.js`
  - **B.** Mantener estructura técnica actual y documentar la convención.
  - **C.** Híbrido: dejar `templates/pages/` y `static/css/components/` pero agrupar los archivos específicos de cada bounded context en subcarpetas dentro de esas capas.
- **Recomendación del agente:** Opción **C** como transición: mover `tienda.css`, `cart.css`, `confirmation.css` a `static/css/comercio/` y los templates correspondientes a `templates/comercio/pages/`, dejando layouts y componentes globales donde están.
- **Bloqueo:** Requiere actualizar todas las rutas en `src/infraestructura/rutas/` y los tests que validan rutas de templates. Cambia la convención de nombres de archivos y puede romper el flujo de trabajo de quienes editan YAML sin conocer frontend.
- **Impacto estimado:** Alto en mantenibilidad a largo plazo; medio en riesgo de regresión a corto plazo.
- **Tenant afectado:** Todos.

---

## 2. Code splitting de CSS por ruta

- **Contexto:** `compilar_bundle_css()` genera un único `bundle.css` que incluye todos los estilos (home, tienda, carrito, confirmación, etc.) para cada ruta. Esto significa que `/tienda/` carga CSS de la home y viceversa.
- **Opciones consideradas:**
  - **A.** Generar bundles separados por página (`home.css`, `tienda.css`, `carrito.css`, etc.) y que cada template cargue el suyo.
  - **B.** Mantener bundle único pero marcar explícitamente dependencias por template.
  - **C.** Dejar como está; el bundle es pequeño (~2 KB de CSS comprimido con gzip) y la penalidad es baja.
- **Recomendación del agente:** Opción **A** cuando el CSS crezca sensiblemente o se agreguen más páginas. Hoy el bundle completo es liviano y el costo de una petición extra por página puede superar el beneficio.
- **Bloqueo:** Cambia el contrato de `templates/components/head.html` y requiere lógica en `base.html` para decidir qué CSS cargar según la ruta. Aumenta complejidad del lifespan.
- **Impacto estimado:** Medio en performance; medio-alto en complejidad de build.
- **Tenant afectado:** Todos.

---

## 3. Migración de imágenes JPEG a WebP/AVIF con pipeline

- **Contexto:** Las fotos de tenant (`quienes-somos-eitec.jpg`, `quienes-somos-upp.jpg`, `quienes-somos-elgringo.jpg`) pesan ~1 MB cada una. No hay versiones WebP/AVIF ni `srcset`.
- **Opciones consideradas:**
  - **A.** Generar versiones `.webp` con `cwebp`/`imagemagick` en el servidor y servir `<picture>` con fallback JPEG.
  - **B.** Servir imágenes optimizadas por un CDN con transformación on-the-fly (Cloudflare Polish, CloudFront, etc.).
  - **C.** Reemplazar las JPEG originales por versiones comprimidas en el mismo formato sin cambiar pipeline.
- **Recomendación del agente:** Opción **A** para ganar inmediato en LCP sin depender de terceros, pero automatizándolo en el proceso de deploy. Opción **B** es más escalable si ya se usa CDN.
- **Bloqueo:** En el entorno no está disponible `cwebp`; `convert` de ImageMagick existe pero no produce WebP tan eficiente. Además, agregar `<picture>` requiere tocar todos los templates que muestran imágenes de producto y "quienes somos", y generar assets adicionales que deben versionarse. Cambiar los archivos binarios de imagen afecta el contenido visual de cada tenant.
- **Impacto estimado:** Alto en performance (LCP); medio en complejidad de assets.
- **Tenant afectado:** Todos, especialmente eitec, upp y plasticoselgringo cuyas fotos son las más pesadas.

---

## 4. Implementación de PWA, service workers y manifest

- **Contexto:** El sitio no tiene `manifest.json`, service worker ni estrategia offline/cache de assets.
- **Opciones consideradas:**
  - **A.** Agregar un service worker básico que cachee el shell y assets estáticos.
  - **B.** Solo agregar `manifest.json` sin service worker.
  - **C.** No hacer nada; el uso es B2B y la recurrencia de visitas no justifica PWA.
- **Recomendación del agente:** Opción **B** de bajo riesgo (manifest + iconos) y evaluar **A** si se detecta tráfico recurrente de compradores.
- **Bloqueo:** Requiere generar iconos en múltiples tamaños por tenant y decidir si el service worker debe invalidar el cache del bundle CSS generado dinámicamente.
- **Impacto estimado:** Bajo-medio en engagement; bajo en riesgo si solo se agrega manifest.
- **Tenant afectado:** Todos.

---

## 5. Adopción de un bundler/build tool para CSS/JS

- **Contexto:** El frontend usa ES modules nativos y un bundle CSS generado en Python en el lifespan. No hay npm, webpack, vite, esbuild, etc.
- **Opciones consideradas:**
  - **A.** Introducir Vite o esbuild para JS/CSS con salida a `static/dist/`.
  - **B.** Mantener el enfoque actual (sin build step) y mejorar el runtime bundle.
  - **C.** Usar herramientas Python como `libsass` o `rcssmin` para minificar el bundle CSS existente.
- **Recomendación del agente:** Opción **B** mientras el proyecto sea pequeño. Si se suman más páginas, interactividad compleja o un design system, evaluar **A**.
- **Bloqueo:** Agregar un bundler cambia el proceso de deploy, requiere Node.js en el entorno y modifica el flujo de trabajo del equipo. Va en contra de la restricción actual de "no agregar dependencias de build".
- **Impacto estimado:** Alto en tooling y developer experience; bajo-medio en performance actual.
- **Tenant afectado:** Todos.

---

## 6. Renombrar clases CSS al vocabulario del dominio

- **Contexto:** El backend habla de `ArticuloCatalogo`, `Carrito`, `Cotizacion`, `Presupuesto`; el frontend usa clases genéricas como `.product-card`, `.cart-item`, `.quote-card`, `.confirmation-card`.
- **Opciones consideradas:**
  - **A.** Renombrar clases a `.articulo-catalogo`, `.linea-carrito`, `.formulario-cotizacion`, `.confirmacion-presupuesto` para alinear vocabulario.
  - **B.** Mantener nombres actuales porque son comprensibles y están probados.
  - **C.** Híbrido: usar clases dobles (una semántica de dominio + una utilitaria) en elementos clave.
- **Recomendación del agente:** Opción **C** gradual: empezar a agregar clases de dominio sin eliminar las actuales, para no romper estilos ni tests.
- **Bloqueo:** Un renombre masivo toca ~15 archivos CSS y templates y puede romper overrides de tenant que dependen de las clases actuales.
- **Impacto estimado:** Medio en mantenibilidad; alto en riesgo de regresión si se hace de golpe.
- **Tenant afectado:** Todos.

---

## 7. Creación de un design system / component library compartido

- **Contexto:** Hay tokens de diseño iniciales en `static/css/base/variables.css`, pero no hay documentación ni componentes documentados. Cada tenant puede hacer override, pero no hay guía.
- **Opciones consideradas:**
  - **A.** Crear `docs/DESIGN_SYSTEM.md` con tokens, componentes y patrones de override.
  - **B.** Dejar la documentación implícita en el código.
  - **C.** Extraer componentes HTML reutilizables a Jinja macros más robustos (tarjeta de producto, botón, input).
- **Recomendación del agente:** Opción **A** como primer paso; luego **C** para componentes más complejos.
- **Bloqueo:** Requiere tiempo de documentación y consenso sobre qué componentes son core vs específicos de tenant.
- **Impacto estimado:** Medio en escalabilidad; bajo en riesgo.
- **Tenant afectado:** Todos.

---

## 8. Estrategia de cacheo de assets estáticos

- **Contexto:** FastAPI sirve `/static/*` directamente. No hay headers de cache (`Cache-Control`, `ETag`, `Last-Modified`) configurados en el repo. El bundle CSS se regenera en cada arranque, pero su URL no tiene hash.
- **Opciones consideradas:**
  - **A.** Configurar headers `Cache-Control` largos en `/static/` y versionar los nombres de archivos con hash.
  - **B.** Dejar que un reverse proxy (nginx/Cloudflare) maneje cacheo.
  - **C.** Agregar `ETag` o `Last-Modified` en el endpoint de estáticos.
- **Recomendación del agente:** Opción **B** si se despliega detrás de nginx/Cloudflare; opción **A** para máximo control.
- **Bloqueo:** Requiere decidir política de invalidación del bundle CSS (que cambia en cada deploy) y posiblemente modificar `url_for('static', ...)` para incluir versionado.
- **Impacto estimado:** Alto en performance recurrente; medio en complejidad de deploy.
- **Tenant afectado:** Todos.

---

## 9. Páginas legales/institucionales no existentes referenciadas en tenants

- **Contexto:** Los tenants `upp` y `plasticoselgringo` tienen en `site.yml` enlaces de footer a `/faqs`, `/terminos`, `/fichas-tecnicas`, `/condiciones`. No existen templates ni rutas para esos paths.
- **Opciones consideradas:**
  - **A.** Crear las páginas genéricas correspondientes o redirigir a `/terminos-y-condiciones/`.
  - **B.** Pedir a cada tenant que defina los textos legales y luego crear las páginas.
  - **C.** Eliminar los enlaces del YAML de esos tenants.
- **Recomendación del agente:** Opción **A** de forma transitoria: crear páginas genéricas con mensaje "próximamente" o redirigir a las legales existentes, hasta que cada tenant defina su contenido.
- **Bloqueo:** Son cambios en `data/<tenant>/site.yml` (contenido), que la restricción de trabajo prohíbe modificar. Requiere decisión del dueño de cada tenant.
- **Impacto estimado:** Medio en UX (evita 404); bajo en esfuerzo técnico.
- **Tenant afectado:** `upp`, `plasticoselgringo`.

---

## 10. Lazy loading de iframes y scripts de terceros

- **Contexto:** El mapa de Google en `templates/components/sections/contact.html` ya tiene `loading="lazy"`, pero los scripts de GTM/GA se inyectan dinámicamente en `<head>` desde `GoogleTrackers.js`.
- **Opciones consideradas:**
  - **A.** Cargar GTM/GA solo tras consentimiento explícito y de forma diferida (`defer`/`async`).
  - **B.** Mover la carga de trackers a un evento de interacción del usuario para reducir impacto en LCP.
  - **C.** Mantener carga actual, ya que `GoogleTagManagerTracker` respeta localhost y ya se carga de forma asíncrona (`script.async = true`).
- **Recomendación del agente:** Opción **A** + **B** para cumplir con privacidad y mejorar métricas. Hoy el código ya respeta consentimiento, pero se inicializa en DOMContentLoaded.
- **Bloqueo:** Cambiar la estrategia de carga puede afectar la calidad de datos de analytics y requiere validación de negocio.
- **Impacto estimado:** Medio en performance y compliance; bajo-medio en riesgo.
- **Tenant afectado:** Todos.

---

## 11. Content Security Policy (CSP)

- **Contexto:** Se eliminó el único script inline de `templates/pages/confirmacion_presupuesto.html` y se movió a un módulo ES6. Esto abre la puerta a habilitar una CSP restrictiva (`script-src 'self'`) sin necesidad de `unsafe-inline`.
- **Opciones consideradas:**
  - **A.** Agregar headers CSP estrictos en `app.py`.
  - **B.** Documentar recomendaciones CSP sin implementarlas.
  - **C.** Mantener CSP por defecto del navegador.
- **Recomendación del agente:** Opción **A** con directivas permisivas al principio y luego ajustar según errores reportados. GTM/GA requieren dominios de Google en `script-src` y `connect-src`.
- **Bloqueo:** CSP puede romper integraciones de terceros (GTM, GA, WhatsApp, mapas de Google) si no se configuran todos los orígenes permitidos. Requiere pruebas exhaustivas.
- **Impacto estimado:** Alto en seguridad; medio en riesgo de romper funcionalidad.
- **Tenant afectado:** Todos.
