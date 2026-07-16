# AGENTS.md — Guía para agentes de código

> Este archivo documenta la arquitectura, convenciones y comandos del proyecto
> **Madypack**. Está escrito en español porque el código, los comentarios y la
> documentación del proyecto usan principalmente ese idioma.

---

## 1. Visión general del proyecto

Madypack es un ecommerce ligero y de alto rendimiento para la comercialización de
bolsas de papel sustentables. El contenido del sitio, el catálogo y las tarifas se
configuran en YAML sin modificar código fuente.

El proyecto sigue una **arquitectura por capas inspirada en hexagonal/ports and
adapters**:

- `domain/`: entidades, value objects, puertos (interfaces abstractas) y reglas de
  negocio puras.
- `application/`: casos de uso que orquestan el dominio.
- `adapters/`: implementaciones concretas de los puertos (repositorios, servicios,
  presentadores).
- `infrastructure/`: frameworks, rutas HTTP, templates, carga de YAML, logging,
  generación de assets y utilidades de sistema.

### Stack tecnológico

| Capa | Tecnología |
|------|------------|
| Lenguaje | Python 3.12 |
| Framework web | FastAPI + Uvicorn (ASGI) |
| Plantillas | Jinja2 |
| Validación | Pydantic v2 |
| Configuración de contenidos | YAML (PyYAML) |
| Cliente HTTP | httpx |
| Logging | structlog |
| PDFs | ReportLab + svglib |
| Tests | pytest |
| Estilos | CSS Vanilla (bundle concatenado) |
| Frontend | JavaScript ES Modules, vanilla |

---

## 2. Estructura de directorios

```text
.
├── data/
│   ├── site.yml                  # Configuración central del sitio (validada con Pydantic)
│   └── presupuestos/             # Presupuestos generados en JSON (ignorados por git)
├── docs/
│   └── DUDAS.md                  # Registro de dudas arquitectónicas resueltas/pendientes
├── logs/
│   └── failed_leads.log          # Leads fallidos (JSON Lines, ignorado por git)
├── src/
│   ├── adapters/
│   │   ├── controllers/          # (reservado)
│   │   ├── gateways/             # Implementaciones de repositorios y servicios
│   │   └── presenters/           # Formateadores y presentadores de salida
│   ├── application/
│   │   ├── commerce/             # Casos de uso del carrito
│   │   ├── lead/                 # DTOs de lead
│   │   └── quote/                # Casos de uso de presupuesto y helpers
│   ├── domain/
│   │   ├── commerce/             # Carrito, catálogo y repositorios (puertos)
│   │   ├── lead/                 # Entidad Lead, repositorio, cliente HTTP (puertos)
│   │   ├── pricing/              # Motor de cálculo de precios y tarifas
│   │   └── quote/                # Presupuesto, PDF, fallback, identidad visual
│   └── infrastructure/
│       ├── config/               # Settings Pydantic basados en variables de entorno
│       ├── fastapi/              # App, rutas, middleware, errores
│       ├── httpx/                # Adaptador de cliente HTTP
│       ├── pyyaml/               # Modelos y loaders de YAML
│       ├── reportlab/            # Generador de PDF
│       ├── structlog/            # Configuración de logging
│       ├── tailwindcss/          # Builder del bundle CSS
│       └── estaticos.py          # Utilidades para resolver archivos estáticos
├── static/
│   ├── css/                      # Módulos CSS y bundle.css generado
│   ├── fonts/
│   ├── images/
│   ├── js/                       # Frontend modular (domain/application/adapters/ui)
│   └── tenants/                  # Assets específicos por tenant
├── templates/
│   ├── components/               # Bloques reutilizables (header, footer, etc.)
│   ├── errors/                   # Templates 404/500 con CSS embebido
│   ├── layouts/                  # Layout base
│   ├── macros/                   # Macros Jinja2
│   └── pages/                    # Páginas completas
├── tests/                        # Tests organizados por capa/contexto
├── requirements.txt
├── run.sh                        # Script de desarrollo
├── pytest.ini
└── pyrightconfig.json
```

> **Nota:** el `README.md` muestra una estructura ligeramente desactualizada. El
> código real usa `src/adapters`, `src/application`, `src/domain` y
> `src/infrastructure` (no `src/comercio`, `src/precios`, etc.).

---

## 3. Configuración

La aplicación lee su configuración desde dos fuentes:

1. **Variables de entorno** (ver `src/infrastructure/config/settings.py`):

   | Variable | Default | Descripción |
   |----------|---------|-------------|
   | `APP_TITLE` | `"Madypack"` | Título de la app FastAPI |
   | `LOG_LEVEL` | `"INFO"` | Nivel de log |
   | `LOG_FORMAT` | — | Si vale `"json"` fuerza JSON |
   | `ENV` | — | Si vale `"production"` fuerza JSON |
   | `CHATWOOT_URL` | `http://localhost:3000` | URL base de Chatwoot |
   | `CHATWOOT_ACCOUNT_ID` | `1` | ID de cuenta Chatwoot |
   | `CHATWOOT_INBOX_ID` | `1` | ID de inbox Chatwoot |
   | `CHATWOOT_API_TOKEN` | `""` | Token de API Chatwoot |

2. **`data/site.yml`**: contenido del sitio, menús, textos, redes sociales,
   configuración del formulario de cotización, condiciones comerciales, etc. Se
   valida al iniciar la aplicación mediante los modelos Pydantic de
   `src/infrastructure/pyyaml/models.py`. Si `site.yml` es inválido, la app no
   arranca.

---

## 4. Comandos de build y ejecución

### Entorno

El proyecto usa un virtualenv ubicado en `venv/`. Python real es 3.12.3.

```bash
source venv/bin/activate
```

### Instalación

```bash
pip install -r requirements.txt
```

### Ejecutar en desarrollo

```bash
chmod +x run.sh
./run.sh [puerto]
```

Por defecto escucha en el puerto `8000`. El script:

1. Libera el puerto si está ocupado.
2. Compila el bundle CSS.
3. Levanta Uvicorn con recarga automática.

Equivalente manual:

```bash
./venv/bin/python -m src.infrastructure.tailwindcss.css_bundle
./venv/bin/uvicorn src.infrastructure.fastapi.app:app --reload --port 8000
```

### Compilar CSS

```bash
./venv/bin/python -m src.infrastructure.tailwindcss.css_bundle
```

Esto genera `static/css/bundle.css` concatenando los módulos definidos en
`src/infrastructure/tailwindcss/css_bundle.py`. Aunque el paquete se llama
`tailwindcss`, **no se usa TailwindCSS**; el bundle es una concatenación de CSS
vanilla para reducir requests.

> El archivo `static/css/bundle.css` está ignorado en `.gitignore` (`*bundle.css`).
> Se regenera automáticamente antes de correr tests mediante `tests/conftest.py`.

---

## 5. Tests

### Ejecutar tests

```bash
./venv/bin/pytest
```

Actualmente hay **99 tests** y todos pasan.

### Configuración

`pytest.ini`:

```ini
[pytest]
pythonpath = .
```

`tests/conftest.py` compila el bundle CSS automáticamente al inicio de la sesión
de tests.

### Estrategia de testing

- **Tests de dominio**: validan entidades, value objects y reglas de negocio
  (`tests/quote/`, `tests/commerce/`, `tests/lead/`).
- **Tests de aplicación**: validan casos de uso.
- **Tests de adaptadores**: usan `unittest.mock` para probar repositorios y
  servicios sin dependencias externas (`tests/adapters/gateways/`).
- **Tests de infraestructura**: prueban rutas FastAPI con `TestClient`, loaders
  YAML, generación de PDF, etc. (`tests/infrastructure/`).

Convenciones observadas:

- Clases de test nombradas como `Test<Entidad>`.
- Métodos descriptivos en español.
- Uso de `pytest.raises(ValidationError)` para validaciones Pydantic.
- Mocks de `AsyncMock`/`MagicMock` para cliente HTTP.

---

## 6. Guía de estilo y convenciones

### Idioma

- **Comentarios, docstrings, nombres de commits y documentación en español**.
- Variables, funciones, clases y módulos en español (ej. `Carrito`,
  `CasoUsoAgregarAlCarrito`, `Presupuesto`).
- Excepciones: abreviaturas técnicas en inglés son aceptables (`DTO`, `URL`,
  `JSON`, `PDF`, `HTML`).

### Imports

- Imports absolutos con prefijo `src.` (ej. `from src.domain.commerce.cart import
  Carrito`).
- `pytest.ini` configura `pythonpath = .` para que funcione tanto en desarrollo
  como en tests.

### Modelos Pydantic

- Se usa `model_config = {"frozen": True}` para value objects inmutables.
- Validaciones de dominio como `cantidad` múltiplo de 100.
- `model_config = {"validate_assignment": True}` cuando los modelos mutan en
  runtime (ej. artículos del carrito).

### Logging

- Usar `structlog` a través de `src.infrastructure.structlog.logger.get_logger()`.
- No usar `print`.
- En producción (`ENV=production`) o salida no TTY, los logs se emiten en JSON.

### Manejo de errores

- Las excepciones de dominio se propagan como `ValueError`.
- Las rutas capturan errores y redirigen con mensajes de query param (ej.
  `?error=datos_invalidos`).
- Existe un handler global de 500 y un handler específico de 404 con templates
  embebidos.

### Rutas

- Las URLs de páginas terminan en `/` (trailing slash).
- `TrailingSlashMiddleware` redirige 301 si falta la barra final.
- Formularios POST responden con redirecciones 303 (Post/Redirect/Get).

---

## 7. Arquitectura en detalle

### 7.1 Dominio (`src/domain`)

- **`commerce/`**: `Carrito`, `ArticuloCarrito`, `ProductoBien`,
  `ProductoServicio`, `ComponenteBien`, `VariacionProducto`, `CalculoArticulo`
  y puertos de repositorios.
- **`pricing/`**: `CalculadorPrecio` con estrategias registrables
  (`suma_por_unidad`, `suma_por_unidad_mas_fijo`), `Tarifas`.
- **`quote/`**: `Presupuesto`, `LineaPresupuesto`, `DatosSolicitante`, puertos para
  repositorio de presupuesto, generador de PDF y registro fallback.
- **`lead/`**: `Lead` con factories (`crear`, `crear_cotizacion_general`,
  `crear_contacto`, `crear_emergencia`), puertos `ILeadRepository` e `IHttpClient`.

### 7.2 Aplicación (`src/application`)

- **`commerce/cart_use_cases.py`**: `CasoUsoAgregarAlCarrito`,
  `CasoUsoEliminarDelCarrito`, `CasoUsoActualizarCarrito`,
  `CasoUsoObtenerResumenCarrito`.
- **`quote/process_quote_request.py`**: `ProcesarSolicitudPresupuesto` orquesta
  lead, presupuesto y fallback.
- **`quote/generate_quote_pdf.py`**: `CasoUsoGenerarPresupuestoPDF`.
- **`quote/quote_helpers.py`**: `construir_lineas_presupuesto`.

### 7.3 Adaptadores (`src/adapters`)

- **`gateways/commerce_cookie_repository.py`**: persistencia del carrito en cookie
  (`articulos_carrito`).
- **`gateways/catalog/in_memory_catalog_repository.py`**: adaptador delgado que
  implementa `ICatalogRepository` en memoria.
- **`gateways/catalog/catalog_seed.py`**: orquestador que ensambla el catálogo.
- **`gateways/catalog/data.py`**: datos semi-estáticos y constantes del catálogo.
- **`gateways/catalog/builders.py`**: helpers puros (SKU, MOQ, cálculo de precio,
  imagen).
- **`gateways/catalog/bolsas.py`**: builders de bolsas simples y sus variaciones.
- **`gateways/catalog/componentes.py`**: builders de manijas, fotopolímero y bobina.
- **`gateways/catalog/servicios.py`**: builders de servicios.
- **`gateways/catalog/compuestos.py`**: builders de bienes compuestos.
- **`gateways/pricing_service.py`**: cotizador con tarifas estáticas en código.
- **`gateways/json_quote_repository.py`**: guarda presupuestos en
  `data/presupuestos/{ref}.json`.
- **`gateways/lead_chatwoot_repository.py`**: envía leads a Chatwoot vía API REST.
- **`gateways/quote_fallback_repository.py`**: registra leads fallidos en
  `logs/failed_leads.log`.
- **`presenters/`**: formateo de moneda/unidades y presentador de confirmación.

### 7.4 Infraestructura (`src/infrastructure`)

- **`fastapi/app.py`**: aplica `lifespan`, monta estáticos, registra middlewares,
  excepciones y routers.
- **`fastapi/routes/`**: routers divididos por contexto (pages, cart, quote,
  infrastructure).
- **`fastapi/dependencies.py`**: wiring de dependencias con `Depends` de FastAPI.
- **`fastapi/middleware/`**: `TrailingSlashMiddleware` y `request_id_middleware`.
- **`fastapi/errors/handlers.py`**: handlers de 404 y 500 con templates embebidos.
- **`pyyaml/loaders.py` + `models.py`**: carga y validación de `site.yml`.
- **`reportlab/pdf_generator.py`**: generación de PDF de presupuesto.
- **`structlog/logger.py`**: logging estructurado.

### 7.5 Frontend (`static/js`)

Aunque es pequeño, sigue una arquitectura por capas:

- `domain/`: entidades y contratos puros.
- `application/`: casos de uso (`ConsentService`).
- `adapters/`: repositorios (`LocalStorageConsentRepository`) y trackers
  (`GoogleTrackers`).
- `ui/`: componentes de interfaz (`CookieBanner`, `MobileMenu`, `HeroCarousel`).

Los trackers de Google se desactivan automáticamente en `localhost` y
`127.0.0.1`.

---

## 8. Flujos principales

### Carrito

1. El usuario agrega una variación de producto desde `/productos/{slug}/`.
2. `CasoUsoAgregarAlCarrito` valida el MOQ dinámico (`cantidad_por_defecto`) y
   multiplicidad de 100.
3. El carrito se serializa en la cookie `articulos_carrito` (30 días).
4. `/cart/` muestra el resumen usando `CasoUsoObtenerResumenCarrito`.

### Presupuesto

1. El usuario completa el formulario en `/cotizacion/` y envía a `/presupuesto/`.
2. `ProcesarSolicitudPresupuesto` crea un `Lead` y lo envía a Chatwoot.
3. Si hay carrito, construye líneas de presupuesto con el cotizador y guarda el
   JSON en `data/presupuestos/`.
4. En caso de falla, registra el lead en `logs/failed_leads.log`.
5. La vista de confirmación ofrece WhatsApp y descarga de PDF.
6. `/presupuesto/descargar/?ref=...` genera el PDF al vuelo con ReportLab.

---

## 9. Consideraciones de seguridad

- **Variables de entorno sensibles**: `CHATWOOT_API_TOKEN` debe configurarse por
  entorno, nunca hardcodeada.
- **Archivos estáticos**: `resolver_archivo_estatico` previene path traversal
  rechazando `..` y validando que el path resuelto esté dentro de `static/`.
- **Cookies**: el carrito viaja en cookie firmada por el navegador (no por el
  servidor); no contiene datos de precios ni lógica de negocio crítica.
- **Bypass de analíticas**: GTM/GA no se cargan en `localhost`/`127.0.0.1`.
- **Health check**: `/health` realiza una petición `HEAD` a `CHATWOOT_URL`; en
  producción asegurarse de que no exponga información interna.

---

## 10. Notas para agentes

- Si agregás un campo nuevo al formulario de cotización, actualizá tanto
  `data/site.yml` como `QUOTE_FORM_FIELD_NAMES` en
  `src/infrastructure/pyyaml/models.py` y el endpoint POST en
  `src/infrastructure/fastapi/routes/quote.py`.
- Si modificás CSS, no edités `static/css/bundle.css` directamente; editá los
  módulos en `static/css/` y ejecutá el builder.
- Si agregás una estrategia de cálculo de precios, registrala en
  `CalculadorPrecio._estrategias` o mediante `registrar_estrategia`.
- Si cambiás la estructura de `site.yml`, asegurate de que los tests de
  `tests/infrastructure/pyyaml/` y las rutas FastAPI sigan pasando.
- El catálogo se construye en `catalog_seed.py` y se expone a través de
  `InMemoryCatalogRepository`; para cambiar productos simples, servicios,
  compuestos, variaciones o MOQs hay que modificar `catalog_seed.py` y sus
  tests.
- Antes de commitear, ejecutá `./venv/bin/pytest` para verificar que no se
  rompió nada.

---

## 11. Referencias rápidas

| Comando | Descripción |
|---------|-------------|
| `./run.sh` | Levanta desarrollo en puerto 8000 |
| `./run.sh 8080` | Levanta desarrollo en puerto 8080 |
| `./venv/bin/pytest` | Ejecuta la suite completa |
| `./venv/bin/python -m src.infrastructure.tailwindcss.css_bundle` | Compila CSS |
| `./venv/bin/uvicorn src.infrastructure.fastapi.app:app --reload` | Uvicorn manual |
