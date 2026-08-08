# Integración de Presupuestos y Costos — Xubio ERP v1.1

> Guía técnica de la arquitectura de integración con la API de Xubio v1.1 (`https://xubio.com/API/1.1`) como fuente de verdad para presupuestos y costos en Madypack, bajo la premisa de **Zero-Trust ("No asumas nada como verdadero")**.

---

## 1. Visión General

La integración con Xubio ERP cumple dos funciones principales dentro del sistema:

1. **Fuente de Verdad para Costos y Tarifas**: Obtener los precios y costos actualizados de insumos (ej. bobinas, manijas, fotopolímeros, procesos) para alimentar el `CotizadorServicio`.
2. **Sincronización de Presupuestos**: Emitir y registrar las cotizaciones del e-commerce directamente en el módulo de presupuestos de Xubio (`/presupuestoBean`).

---

## 2. Principio Zero-Trust ("No asumas nada como verdadero")

Dado que la información proviene de una API de red externa administrada por terceros, **ningún campo recibido se asume correcto, seguro o válido de forma implícita**.

### 2.1 Reglas de Sanitización de Entradas (Xubio -> Madypack)

| Tipo de Dato | Riesgo | Regla de Sanitización | Fallback Seguro |
|--------------|--------|-----------------------|-----------------|
| **Cadenas de Texto** (`nombre`, `descripcion`, `codigo`) | Inyección XSS, HTML, espacios desbordados | Limpieza con expresión regular `re.sub(r"<[^>]+>", "")`, `.strip()`, truncamiento | `""` o SKU por defecto |
| **Valores Numéricos** (`precio`, `monto`, `cantidad`) | `NaN`, `Infinity`, valores negativos, `None` | Coerción estricta a `float`, verificación de no-negatividad | `0.0` o tarifa de resguardo |
| **Fechas** (`fecha`, `fechaVto`) | Formatos inválidos, strings corruptas, `None` | Parsing ISO (`date.fromisoformat`), validación de rangos | `date.today()` |
| **Identificadores** (`id`, `clienteId`, `productoId`) | Nulos, tipos mezclados (str vs int) | Conversión a `int` o `str` estricto | Ignorar ítem corrupto |

### 2.2 Estrategia de Resguardo y Alta Disponibilidad (Fallback)

En caso de:
- Falla de red, timeout o errores HTTP 4xx/5xx de la API de Xubio.
- Payloads JSON malformados o que no superen la sanitización de dominio.

El sistema activa automáticamente un **mecanismo de degradación suave**:
1. Se emite una advertencia estructurada mediante `structlog` (`xubio.tarifas.fallback`).
2. El sistema conmuta temporalmente al `ProveedorTarifasDefault` en memoria, garantizando que el e-commerce pueda seguir cotizando sin interrumpir al usuario final.

---

## 3. Mapeo de Endpoints de Xubio v1.1

### 3.1 Presupuestos (`/presupuestoBean`)

- **GET `/presupuestoBean`**: Obtiene el listado de presupuestos emitidos.
- **POST `/presupuestoBean`**: Crea una nueva transacción de presupuesto con la entidad `PresupuestoBean` y sus ítems `TransaccionProductoItems`.
- **PUT `/presupuestoBean/{id}/estado`**: Actualiza el estado del presupuesto (-3: Pendiente, -2: Aprobado, -7: Rechazado, -5: Facturado, -4: Remitido).

### 3.2 Tarifas y Listas de Precios (`/listaPrecioBean`)

- **GET `/listaPrecioBean`**: Listado de listas de precios (Venta / Compra).
- **GET `/listaPrecioBean/{id}`**: Detalle de ítems de la lista de precios (`ListaPrecioItemBean`), mapeando `codigo` a la tarifa unitaria en ARS/USD.

### 3.3 Catálogo de Productos y Stock (`/ProductoVentaBean` & `/productoStock`)

- **GET `/ProductoVentaBean`**: Catálogo de productos de venta de Xubio.
- **GET `/productoStock`**: Consulta de stock actual por depósito.

---

## 4. Arquitectura Hexagonal y Límite de Capas

```text
src/
├── domain/
│   └── erp/
│       ├── entities.py       # EmpresaERP, EstadoConexionERP
│       ├── ports.py          # Interface IErpGateway
│       └── sanitizer.py      # SanitizadorXubio (Funciones puras de limpieza Zero-Trust)
├── adapters/
│   └── gateways/
│       ├── xubio_client.py   # XubioErpGateway (Adaptador HTTP con OAuth2)
│       └── proveedor_tarifas_xubio.py # Proveedor de tarifas que sanitiza las respuestas de Xubio
└── infrastructure/
    └── fastapi/
        ├── dependencies.py   # Inyección de dependencias según XUBIO_PROVIDER
        └── routes/
            └── xubio_replica.py # Router Réplica ERP Privado
```

### Reglas de Dependencia
- `src/domain/erp/sanitizer.py` es **puro**; no depende de frameworks web, HTTP ni librerías de infraestructura.
- Las credenciales (`XUBIO_CLIENT_ID`, `XUBIO_SECRET_ID`) jamás se exponen en logs ni respuestas de error.

---

## 5. Modelo de Costos, Reventa y Producto Compuesto

El modelo de fijación de precio para los productos de Madypack sigue un esquema de **reventa con margen comercial común** aplicado sobre insumos y servicios:

1. **Bobina de Papel (Reventa de Bien / Insumo)**:
   - Se toma el costo base de compra por kg de bobina (`bobina_kg` de Xubio/tarifa).
   - Se le aplica el Value Object `MargenComercial` global:
     $$\text{Precio Bobina per kg} = \text{Costo Bobina kg} \times (1 + \text{Margen})$$
2. **Servicio de Confección (Reventa de Servicio)**:
   - Se toma el costo base del servicio de confección (`confeccion` de Xubio/tarifa).
   - Se le aplica el `MargenComercial` global:
     $$\text{Precio Confección} = \text{Costo Confección} \times (1 + \text{Margen})$$
3. **Bolsa de Papel (Producto Compuesto)**:
   - El precio final de la bolsa confeccionada es la **suma directa de sus componentes**:
     $$\text{Precio Bolsa} = \text{Subtotal Bobina (según gramaje y medidas)} + \text{Subtotal Confección}$$

