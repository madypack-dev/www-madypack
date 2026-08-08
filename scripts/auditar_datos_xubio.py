"""Script de auditoría unificado de limpieza, calidad de datos y detección estadística de anomalías de Xubio ERP.

Delega la presentación visual interactiva a la capa de infraestructura (src/infrastructure/cli/audit_presenter.py).
"""

import asyncio
from typing import Any

from src.adapters.gateways.null_erp_gateway import NullErpGateway
from src.adapters.gateways.xubio_client import XubioErpGateway
from src.domain.erp.anomalies import analizar_anomalias_items
from src.domain.erp.sanitizer import (
    sanitizar_fecha,
    sanitizar_monto,
    sanitizar_texto,
)
from src.infrastructure.cli.audit_presenter import (
    presentar_analisis_anomalias,
    presentar_casos_zero_trust,
    presentar_listas_precio,
    presentar_perfil_empresa,
    presentar_productos_stock,
)
from src.infrastructure.config.settings import (
    XUBIO_API_URL,
    XUBIO_CLIENT_ID,
    XUBIO_PROVIDER,
    XUBIO_SECRET_ID,
)
from src.infrastructure.httpx.http_client import crear_cliente_http_async
from src.infrastructure.pyyaml.loaders import cargar_configuracion_negocio
from src.infrastructure.structlog.logger import get_logger

logger = get_logger()


async def _consultar_empresa(gateway: Any) -> dict[str, Any]:
    """Consulta los datos de perfil de la empresa desde Xubio o retorna fallback mock."""
    try:
        res = await gateway.proxy_request("GET", "/miempresa")
        if isinstance(res, dict):
            return res
    except Exception:
        pass
    return {"nombreEmpresa": "Empresa Madygraf (Modo Test)", "cuit": "33-71465177-9"}


def _normalizar_detalle_lista(detail: Any) -> list[dict[str, Any]]:
    """Normaliza la respuesta de detalle de lista de precio a una lista de ítems."""
    if isinstance(detail, dict) and "listaPrecioItem" in detail:
        return detail["listaPrecioItem"]
    if isinstance(detail, dict):
        return [detail]
    if isinstance(detail, list):
        return detail
    return []


async def _consultar_listas_precio(gateway: Any) -> list[dict[str, Any]]:
    """Consulta las listas de precio e ítems de detalle desde Xubio."""
    try:
        res = await gateway.proxy_request("GET", "/listaPrecioBean")
        if not isinstance(res, list):
            return []
        for item in res:
            lid = item.get("listaPrecioID") or item.get("id")
            if lid:
                detail = await gateway.proxy_request("GET", f"/listaPrecioBean/{lid}")
                item["listaPrecioItem"] = _normalizar_detalle_lista(detail)
        return res
    except Exception:
        return []


async def _consultar_productos(gateway: Any) -> list[dict[str, Any]]:
    """Consulta el listado de stock de productos desde Xubio."""
    try:
        res = await gateway.proxy_request("GET", "/productoStock")
        if isinstance(res, dict) and "registros" in res:
            return res["registros"]
    except Exception:
        pass
    return []


def _ejecutar_pruebas_zero_trust() -> None:
    """Ejecuta las pruebas defensivas de sanitización Zero-Trust."""
    casos_anomalos = [
        {"codigo": "<script>alert(1)</script>bobina_kg", "precio": "1250.50", "fecha": "2026-08-07"},
        {"codigo": "confeccion", "precio": "invalid_number", "fecha": None},
        {"codigo": None, "precio": -50.0, "fecha": "fecha_corrupta"},
        {"codigo": "  manija_plana  ", "precio": float("nan"), "fecha": "2026-01-01T10:00:00Z"},
    ]

    casos_sanitizados = [
        {
            "entrada": caso,
            "codigo": sanitizar_texto(caso.get("codigo"), default="desconocido"),
            "monto": sanitizar_monto(caso.get("precio"), default=0.0),
            "fecha": sanitizar_fecha(caso.get("fecha")),
        }
        for caso in casos_anomalos
    ]
    presentar_casos_zero_trust(casos_sanitizados)


async def auditar_datos():
    """Ejecuta la suite unificada de auditoría y análisis de anomalías en Xubio ERP."""
    config_negocio = cargar_configuracion_negocio()
    factor_k = config_negocio.anomalias_bobina.factor_k_mad

    async with crear_cliente_http_async(timeout=10.0) as adapter:
        if XUBIO_PROVIDER == "xubio":
            gateway = XubioErpGateway(
                client=adapter,
                client_id=XUBIO_CLIENT_ID,
                secret_id=XUBIO_SECRET_ID,
                base_url=XUBIO_API_URL,
                logger=logger,
            )
        else:
            gateway = NullErpGateway()

        empresa_res = await _consultar_empresa(gateway)
        presentar_perfil_empresa(empresa_res)

        listas_res = await _consultar_listas_precio(gateway)
        presentar_listas_precio(listas_res)

        productos_res = await _consultar_productos(gateway)
        presentar_productos_stock(productos_res)

        todos_los_items = list(productos_res)
        for lista in listas_res:
            todos_los_items.extend(lista.get("listaPrecioItem", []))

        reporte_anomalias = analizar_anomalias_items(todos_los_items, factor_k=factor_k)
        presentar_analisis_anomalias(reporte_anomalias)

    _ejecutar_pruebas_zero_trust()


if __name__ == "__main__":
    asyncio.run(auditar_datos())
