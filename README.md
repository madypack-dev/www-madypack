# Madypack – Plantilla de Ecommerce Multi-Tenant

Plantilla de ecommerce ligera y de alto rendimiento para la comercialización de bolsas de papel sustentables. Está pensada para servir a **múltiples empresas** desde el mismo código, permitiendo personalizar catálogo, tarifas y contenido por tenant.

El proyecto está construido con **FastAPI**, **Jinja2** y configuración de contenidos en **YAML**.

---

## 🛠️ Tecnologías y Herramientas

* **Backend:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3)
* **Servidor ASGI:** [Uvicorn](https://www.uvicorn.org/)
* **Plantillas:** [Jinja2](https://jinja2.palletsprojects.com/) (HTML5 y macros reutilizables)
* **Estilos:** CSS Vanilla (organizado en módulos en `static/css`)
* **Configuración de Contenidos:** YAML (PyYAML para cargar datos estructurados por tenant)

---

## 📁 Estructura del Proyecto

```text
├── data/                           # Datos de contenido por tenant
│   ├── default/                    # Tenant por defecto (Madypack)
│   │   ├── site.yml
│   │   ├── carrito_defecto.yml
│   │   └── tarifas.yml
│   └── empresa-1/                  # Ejemplo de tenant adicional
│       ├── site.yml
│       ├── carrito_defecto.yml
│       └── tarifas.yml
├── docs/                           # Documentación del proyecto
│   ├── DDD.md                      # Arquitectura por capas
│   ├── multi-tenant.md             # Modelo de tenants y resolución
│   ├── refactoring_plan.md         # Plan de refactorización
│   ├── TODO.md
│   └── UIUX.md
├── src/
│   ├── comercio/                   # Dominio y aplicación del carrito
│   ├── precios/                    # Dominio y lógica de cotización
│   └── infraestructura/            # Frameworks, rutas, templates y datos
│       ├── app.py
│       ├── datos/
│       ├── rutas/
│       └── tenant/
├── static/                         # CSS, imágenes y JS
├── templates/                      # Componentes, layouts, macros y páginas
├── venv/                           # Entorno virtual
├── requirements.txt
├── run.sh                          # Inicio rápido en desarrollo
└── pyrightconfig.json
```

---

## 🚀 Instalación y Uso en Local

### 1. Requisitos Previos
* Python 3.10 o superior.
* Entorno virtual de Python configurado.

### 2. Configurar el Entorno

```bash
git clone <url-del-repositorio>
cd www-madypack
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Ejecutar el Servidor de Desarrollo

```bash
chmod +x run.sh
./run.sh
```

O directamente:

```bash
./venv/bin/uvicorn src.infraestructura.app:app --reload
```

El sitio estará disponible en [http://localhost:8000](http://localhost:8000).

Para levantar una empresa específica en desarrollo, usá el puerto correspondiente:

```bash
./venv/bin/uvicorn src.infraestructura.app:app --port 8001  # empresa-1
```

Ver [docs/multi-tenant.md](docs/multi-tenant.md) para más detalles.

---

## 🏢 Modelo Multi-Tenant

La aplicación resuelve el tenant según el entorno:

| Entorno | Criterio de resolución | Ejemplo |
|---------|------------------------|---------|
| Desarrollo | Puerto | `localhost:8000` → `default`, `localhost:8001` → `empresa-1` |
| Staging | Subdominio | `empresa-1.datamaq.com.ar` → `empresa-1` |
| Producción | Dominio propio | `empresa-1.com.ar` → `empresa-1` |

Cada tenant tiene su propia carpeta en `data/<tenant>/` con `site.yml`, `carrito_defecto.yml` y `tarifas.yml`.

Más información en [docs/multi-tenant.md](docs/multi-tenant.md).

---

## 💡 Características Clave

* **Configuración por tenant:** cada empresa puede tener su propio catálogo, tarifas y contenido sin modificar código.
* **Arquitectura por capas:** separación entre dominio, aplicación, adaptadores e infraestructura.
* **Bypass de Analíticas en Local:** los códigos de seguimiento no se cargan en `localhost` ni `127.0.0.1`.
* **Rutas modulares:** enrutamiento limpio en FastAPI con plantillas Jinja2.

---

## 📚 Documentación

* [docs/DDD.md](docs/DDD.md) – Arquitectura por capas y análisis DDD/SOLID.
* [docs/multi-tenant.md](docs/multi-tenant.md) – Modelo multi-tenant y guía de configuración.
* [docs/refactoring_plan.md](docs/refactoring_plan.md) – Plan de refactorización por capas.
