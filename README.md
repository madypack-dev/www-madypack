# Madypack – Sitio Web Oficial

Sitio web oficial de **Madypack**, marca ecológica de fabricación y confección de bolsas de papel sustentables (lisas y personalizadas), producidas por la cooperativa gráfica **Madygraf** en Garín, Buenos Aires, Argentina.

El proyecto está construido como una aplicación web ligera y de alto rendimiento utilizando **FastAPI** y el motor de plantillas **Jinja2**.

---

## 🛠️ Tecnologías y Herramientas

*   **Backend:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3)
*   **Servidor ASGI:** [Uvicorn](https://www.uvicorn.org/)
*   **Plantillas:** [Jinja2](https://jinja.palletsprojects.com/) (HTML5 y macros reutilizables)
*   **Estilos:** CSS Vanilla (organizado en módulos en la carpeta `static/css`)
*   **Configuración de Contenidos:** YAML (usando PyYAML para cargar datos estructurados)

---

## 📁 Estructura del Proyecto

```text
├── data/
│   └── site.yml                # Configuración global, textos, menús y datos de contacto del sitio
├── docs/
│   └── SEO.md                  # Reporte y recomendaciones técnicas de la auditoría SEO
├── src/
│   └── infrastructure/
│       └── app.py              # Aplicación FastAPI, configuración de estáticos y enrutamiento
├── static/
│   ├── css/                    # Estilos CSS del sitio (variables, componentes y layouts)
│   ├── images/                 # Logotipos y recursos visuales (formatos SVG y JPG)
│   └── js/
│       └── app.js              # Script principal (menú responsive y control de analíticas)
├── templates/
│   ├── components/             # Fragmentos reutilizables (header, footer,noscript)
│   │   └── sections/           # Secciones visuales de la home (hero, about, contact, quote_form)
│   ├── layouts/
│   │   └── base.html           # Estructura HTML base del sitio
│   ├── macros/
│   │   ├── contact.html        # Macros auxiliares (ej. generación de URL de WhatsApp)
│   │   └── social.html         # Macros para renderizar iconos y URLs de redes sociales
│   └── pages/
│       ├── index.html          # Página de inicio (Landing Page)
│       ├── quienes-somos.html  # Página institucional de Quiénes Somos
│       ├── cotizacion.html     # Página con el formulario de solicitud de presupuesto
│       ├── contacto.html       # Página con información de contacto y ubicación física
│       ├── terminos-y-condiciones.html  # Página de términos legales
│       └── politica-de-privacidad.html # Página de política de privacidad de datos
├── requirements.txt            # Dependencias del proyecto Python
├── run.sh                      # Script ejecutable de inicio rápido en desarrollo
└── pyrightconfig.json          # Configuración del tipado estático (Pyright)
```

---

## 🚀 Instalación y Uso en Local

### 1. Requisitos Previos
*   Python 3.10 o superior instalado.
*   Entorno virtual de Python configurado.

### 2. Configurar el Entorno
Cloná el repositorio y accedé al directorio del proyecto:
```bash
git clone <url-del-repositorio>
cd www-madypack
```

Si no tenés creado el entorno virtual, podés inicializarlo y activarlo con:
```bash
python -m venv venv
source venv/bin/activate   # En Linux/macOS
# o bien:
# venv\Scripts\activate    # En Windows
```

Instalá las dependencias del proyecto:
```bash
pip install -r requirements.txt
```

### 3. Ejecutar el Servidor de Desarrollo
Podés iniciar el servidor local usando el script de conveniencia `run.sh`:
```bash
chmod +x run.sh  # Asegurar permisos de ejecución
./run.sh
```

O bien directamente a través de Uvicorn en tu consola:
```bash
uvicorn src.infrastructure.app:app --reload
```

El sitio estará disponible en [http://localhost:8000](http://localhost:8000).

---

## 💡 Características Clave de Desarrollo

*   **Configuración desde un solo lugar:** El contenido del sitio (números de contacto, enlaces de redes sociales, imágenes, campos de formularios y textos) se administra directamente desde [site.yml](file:///home/agustin/proyectos_software/www-madypack/data/site.yml) sin tocar el HTML.
*   **Bypass de Analíticas en Local:** Los códigos de seguimiento de Google Tag Manager (GTM) y Google Analytics (GA) están configurados en [app.js](file:///home/agustin/proyectos_software/www-madypack/static/js/app.js) para que **no se carguen** si estás navegando en entornos locales (`localhost` o `127.0.0.1`), protegiendo tus métricas reales de producción y eliminando advertencias y bloqueos en la consola de desarrollo.
*   **Enrutamiento Modular:** Rutas dinámicas para la landing y páginas complementarias mapeadas de forma limpia en FastAPI, renderizando plantillas modulares Jinja2.
