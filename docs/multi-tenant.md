# Modelo Multi-Tenant

Este documento explica cómo la aplicación sirve a múltiples empresas desde el mismo código, resolviendo el tenant según el entorno.

---

## 1. Resumen

Cada empresa (tenant) tiene su propia configuración de contenido, catálogo y tarifas. La aplicación detecta automáticamente qué tenant atender según:

* el **puerto** en desarrollo local,
* el **subdominio** en staging,
* el **dominio propio** en producción.

---

## 2. Entornos y Criterios de Resolución

| Entorno | Criterio | Ejemplo | Tenant resultante |
|---------|----------|---------|-------------------|
| Desarrollo local | Puerto | `localhost:8001` | `madypack` |
| Staging | Subdominio | `empresa-1.datamaq.com.ar` | `empresa-1` |
| Producción | Dominio propio | `empresa-1.com.ar` | `empresa-1` |

El tenant `default` corresponde a Madypack y funciona como fallback cuando un archivo o dominio no está configurado.

---

## 3. Estructura de Datos por Tenant

Los datos de cada empresa se organizan en carpetas separadas bajo `data/`:

```text
data/
├── default/
│   ├── site.yml              # Contenido, menús, contacto, textos legales
│   ├── productos_tienda.yml   # Catálogo de productos
│   └── tarifas.yml           # Tarifas de cotización
└── empresa-1/
    ├── site.yml
    ├── productos_tienda.yml
    └── tarifas.yml
```

### Archivos por tenant

* `site.yml`: configuración global del sitio (brand, menús, textos, schema, etc.).
* `productos_tienda.yml`: catálogo de productos disponibles en la tienda.
* `tarifas.yml`: parámetros para el cálculo de precios estimados.

Si un archivo no existe para un tenant específico, la aplicación usa el archivo del tenant `default` como fallback y registra un warning en los logs.

---

## 4. Cómo Funciona la Resolución

La lógica vive en `src/infraestructura/tenant/resolutor.py`.

Orden de resolución:

1. **Puerto** – si el header `Host` incluye un puerto mapeado (desarrollo local).
2. **Mapeo explícito** – dominios configurados manualmente en `MAPEO_TENANTS`.
3. **Inferencia por patrón** – si el host coincide con `empresa-N.datamaq.com.ar` o `empresa-N.com.ar`.
4. **Fallback** – devuelve `default` si ninguna regla aplica.

### Mapeos actuales

La configuración centralizada vive en `src/infraestructura/config/settings.py`.

```python
MAPEO_PUERTOS = {
    "8000": "default",
    "8001": "madypack",
    "8002": "eitec",
    "8003": "upp",
    "8004": "plasticoselgringo",
}
```

Los dominios de staging y producción se inferen automáticamente por el patrón `empresa-N`, por lo que no es necesario agregarlos uno a uno salvo que sean casos especiales. También se pueden sobrescribir mediante la variable de entorno `MAPEO_TENANTS`.

---

## 5. Cómo Agregar una Nueva Empresa

### Paso 1: Crear la carpeta de datos

```bash
cp -r data/default data/madypack    # o data/empresa-N
```

### Paso 2: Personalizar los YAML

Editar `data/empresa-N/site.yml`, `data/empresa-N/productos_tienda.yml` y `data/empresa-N/tarifas.yml`.

### Paso 3: Configurar el puerto de desarrollo

Agregar en `src/infraestructura/config/settings.py`:

```python
MAPEO_PUERTOS = {
    ...
    "800N": "empresa-N",  # o "madypack"
}
```

O, sin modificar código, usando una variable de entorno:

```bash
export MAPEO_PUERTOS="8005=empresa-5,8006=empresa-6"
./run.sh empresa-5
```

### Paso 4: Configurar staging y producción

* Staging: apuntar el subdominio `empresa-N.datamaq.com.ar` a la aplicación.
* Producción: apuntar el dominio `empresa-N.com.ar` a la aplicación.

No es necesario modificar código para staging/producción si se respeta el patrón `empresa-N`.

---

## 6. Desarrollo Local con Múltiples Empresas

Levantar una instancia por puerto:

```bash
# Terminal 1 – default
./venv/bin/uvicorn src.infraestructura.app:app --port 8000

# Terminal 2 – empresa-1
./venv/bin/uvicorn src.infraestructura.app:app --port 8001

# Terminal 3 – empresa-2
./venv/bin/uvicorn src.infraestructura.app:app --port 8002
```

Cada instancia carga automáticamente el tenant correspondiente.

---

## 7. Decisiones de Diseño

* **YAML como fuente de datos:** se mantiene por simplicidad. A futuro puede migrarse a base de datos sin cambiar la arquitectura.
* **Fallback a `default`:** permite tener tenants parcialmente configurados mientras se personaliza el contenido.
* **Resolución en infraestructura:** el dominio y los casos de uso no conocen el concepto de tenant.
* **Inferencia por patrón:** reduce la necesidad de mantener listas de dominios en el código.
