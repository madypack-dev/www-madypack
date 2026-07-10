# Madypack – Ecommerce de Bolsas de Papel Sustentables

Ecommerce ligero y de alto rendimiento para la comercialización de bolsas de papel sustentables. El contenido, catálogo y tarifas se configuran en YAML sin modificar código.

El proyecto está construido con **FastAPI**, **Jinja2** y configuración de contenidos en **YAML**.

---

## 🛠️ Tecnologías y Herramientas

* **Backend:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3)
* **Servidor ASGI:** [Uvicorn](https://www.uvicorn.org/)
* **Plantillas:** [Jinja2](https://jinja2.palletsprojects.com/) (HTML5 y macros reutilizables)
* **Estilos:** CSS Vanilla (organizado en módulos en `static/css`)
* **Configuración de Contenidos:** YAML (PyYAML para cargar datos estructurados)

---

## 📁 Estructura del Proyecto

```text
├── data/                           # Datos de contenido
│   ├── site.yml
│   ├── productos_tienda.yml
│   └── tarifas.yml
├── src/
│   ├── comercio/                   # Dominio y aplicación del carrito
│   ├── precios/                    # Dominio y lógica de cotización
│   ├── presupuesto/                # Dominio y aplicación de presupuestos
│   ├── lead/                       # Dominio y adaptadores de leads
│   └── infraestructura/            # Frameworks, rutas, templates y datos
│       ├── app.py
│       ├── build/                  # Builders de assets
│       ├── datos/
│       ├── rutas/
│       └── config/
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

El sitio estará disponible en [http://localhost:8000](http://localhost:8000).

O directamente con Uvicorn (previo build del CSS):

```bash
./venv/bin/python -m src.infraestructura.build.css_bundle
./venv/bin/uvicorn src.infraestructura.app:app --reload
```

---

## 💡 Características Clave

* **Configuración por YAML:** catálogo, tarifas y contenido se editan en `data/` sin modificar código.
* **Arquitectura por capas:** separación entre dominio, aplicación, adaptadores e infraestructura.
* **Bypass de Analíticas en Local:** los códigos de seguimiento no se cargan en `localhost` ni `127.0.0.1`.
* **Rutas modulares:** enrutamiento limpio en FastAPI con plantillas Jinja2.

---

## 🧪 Tests

```bash
./venv/bin/pytest
```
