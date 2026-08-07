# Documentación Técnica: SEO, SEM, Analytics (GA4 / GTM) y Microsoft Clarity

Este documento describe la arquitectura, configuración y contratos técnicos de las integraciones de **SEO técnico, seguimiento analítico (GA4 / GTM), eventos de conversiones para pauta publicitaria (Google Ads) y análisis de comportamiento de usuario (Microsoft Clarity)** en Madypack.

---

## 1. Arquitectura de Analítica y Tracking

El sistema utiliza una arquitectura modular por capas en el frontend (`static/js/src/`) para desacoplar los servicios de seguimiento del ciclo de vida de la aplicación:

```text
static/js/
├── app.js                           # Punto de entrada (wiring de trackers)
└── src/
    ├── domain/
    │   └── ITracker.js              # Interfaz base para todos los trackers
    ├── application/
    │   └── ConsentService.js        # Servicio que orquesta el consentimiento
    └── adapters/
        ├── GoogleTrackers.js        # Implementación GTM y GA4
        └── MicrosoftClarityTracker.js # Implementación Microsoft Clarity
```

### Comportamiento en Desarrollo vs Producción
- Todos los trackers comprueban la propiedad `isLocalhost`.
- En entornos `localhost` o `127.0.0.1`, los scripts de terceros (**GTM, GA4, Clarity**) **no se cargan ni ejecutan** para evitar contaminación de métricas de analítica durante el desarrollo local.

---

## 2. Configuración en `data/site.yml`

Las credenciales e identificadores de las herramientas de medición se configuran de manera centralizada en `data/site.yml`:

```yaml
analytics:
  gtm_id: "GTM-WGDHKRW8"
  ga_id: "G-MMGJ94QTB5"
  clarity_id: "CLARITY_ID_AQUI"
```

El modelo de validación Pydantic `AnalyticsConfig` en `src/infrastructure/pyyaml/models.py` asegura la integridad de estos campos durante el arranque de la aplicación FastAPI.

---

## 3. Contrato de Eventos `dataLayer` para Conversiones (Google Ads & GA4)

Para habilitar la medición de conversiones mejoradas y valor de conversión dinámico en Google Ads, la aplicación emite eventos estandarizados a `window.dataLayer`:

### Evento: `generate_lead` (Solicitud de Presupuesto)
Emitido en la vista de confirmación (`templates/pages/confirmacion_presupuesto.html`) al procesar un formulario de cotización:

```javascript
window.dataLayer = window.dataLayer || [];
window.dataLayer.push({
    event: 'generate_lead',
    transaction_id: 'COT-XXXXXX',  // Código de referencia único
    value: 125000.0,               // Importe estimado total en ARS
    currency: 'ARS',               // Moneda de curso legal
    total_items: 2000              // Cantidad total de bolsas cotizadas
});
```

---

## 4. SEO Técnico Dinámico (`/sitemap.xml` y `/robots.txt`)

La aplicación cuenta con un router dedicado (`src/infrastructure/fastapi/routes/seo.py`) que genera en tiempo real la estructura para motores de búsqueda:

### A. Sitemap XML (`GET /sitemap.xml`)
- Mapea las URLs estáticas principales (`/`, `/productos/`, `/quienes-somos/`, `/cotizacion/`, `/contacto/`).
- Consulta el repositorio de catálogo (`ICatalogRepository.obtener_todos()`) e inyecta dinámicamente cada producto activo: `/productos/{slug}/`.

### B. Robots TXT (`GET /robots.txt`)
- Retorna las directivas estándar de indexación y referencia automáticamente la ubicación del sitemap:
  ```text
  User-agent: *
  Allow: /

  Sitemap: https://madypack.com.ar/sitemap.xml
  ```

---

## 5. Mantenimiento y Pruebas

Los endpoints de SEO y la validación de configuraciones se encuentran cubiertos por pruebas unitarias en `pytest`:

```bash
./venv/bin/pytest tests/infrastructure/fastapi/routes/test_seo.py
```
