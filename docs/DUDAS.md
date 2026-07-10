# Dudas de alto nivel — Auditoría backend

> Registro de dudas arquitectónicas pendientes de resolver. Cada ítem es una afirmación, no una certeza.

## Resueltas

1. La mutación de `SiteConfig` en `src/infraestructura/rutas/carrito.py:184-185` fue eliminada. El precio estimado formateado ahora viaja como dato de contexto (`estimated_cost_formatted`) y el template `templates/pages/carrito.html:60` lo consume directamente, sin modificar el value object de configuración.

## Acoplamiento y fugas de capas

2. El context processor `inject_cart_count` en `src/infraestructura/rutas/base.py` depende directamente del adaptador `RepositorioCarritoCookie`, por lo que la capa de presentación conoce una implementación concreta de infraestructura.
3. El health check en `src/infraestructura/rutas/infraestructura.py` importa `httpx` dentro de la función y realiza una llamada de red síncrona a un servicio externo, lo que lo convierte en más pesado y acoplado de lo que un health check liviano debería ser.

## Rendimiento y diseño

4. `CotizadorServicio` recarga y parsea el YAML de tarifas en cada artículo cotizado, lo que genera trabajo redundante si se reutiliza el mismo servicio dentro de un request.
5. `get_http_client` en `src/infraestructura/dependencias.py` crea un cliente HTTP si no existe en `app.state`, mientras que `lifespan` ya inicializa uno; esta duplicidad de responsabilidad puede generar fugas de recursos o clientes no compartidos.

## Verificadas

6. `cantidad_por_defecto` **sí se usa** en los templates `templates/pages/tienda.html:43` y `templates/pages/producto.html:37,55` para precargar el input de cantidad y mostrar el pedido mínimo sugerido. No es código muerto.

## Modelado del dominio

7. `Carrito.actualizar_cantidad` muta el artículo in-place sin revalidar que la nueva cantidad cumpla las reglas de dominio (múltiplo de 100).

## Presentación y rutas

8. La lógica de cotización del carrito está duplicada entre `ver_carrito` y `read_cotizacion`, por lo que un cambio en el cálculo o formato debe aplicarse en dos lugares.
9. La ruta `descargar_presupuesto` ensambla `IdentidadVisual` directamente desde `SiteConfig`; este mapping de infraestructura a dominio es aceptable, pero podría extraerse a un builder o mapper para mantener la ruta limpia.
