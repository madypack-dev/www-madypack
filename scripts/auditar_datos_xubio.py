"""Script de auditoría unificado de limpieza, calidad de datos y detección estadística de anomalías de Xubio ERP.

Delega la presentación visual interactiva a la capa de infraestructura (src/infrastructure/cli/audit_presenter.py).
"""

import asyncio
import base64
from typing import Any

import httpx

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
from src.infrastructure.httpx.http_client import HttpxClientAdapter
from src.infrastructure.pyyaml.loaders import cargar_configuracion_negocio
from src.infrastructure.structlog.logger import get_logger

logger = get_logger()


async def diagnosticar_autenticacion_xubio(http_client: httpx.AsyncClient) -> dict[str, str]:
    """Diagnostica la respuesta exacta de /TokenEndpoint y aprueba los encabezados de red."""
    credentials = f"{XUBIO_CLIENT_ID}:{XUBIO_SECRET_ID}"
    encoded = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
    token_url = f"{XUBIO_API_URL.rstrip('/')}/TokenEndpoint"

    headers = {
        "Authorization": f"Basic {encoded}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = "scope=&grant_type=client_credentials"

    res = await http_client.post(token_url, headers=headers, content=data)
    if res.status_code != 200:
        return {"Authorization": f"Basic {encoded}"}

    body = res.json()
    token = str(body.get("access_token"))
    return {"Authorization": f"Bearer {token}", "token": token}


async def _consultar_empresa(gateway: Any) -> dict[str, Any]:
    """Consulta los datos de perfil de la empresa desde Xubio o retorna fallback mock."""
    try:
        res = await gateway.proxy_request("GET", "/miempresa")
        if isinstance(res, dict):
            return res
    except Exception:
        pass
    return {"nombreEmpresa": "Empresa Madygraf (Modo Test)", "cuit": "33-71465177-9"}


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
                if isinstance(detail, dict) and "listaPrecioItem" in detail:
                    item["listaPrecioItem"] = detail["listaPrecioItem"]
                elif isinstance(detail, dict):
                    item["listaPrecioItem"] = [detail]
                elif isinstance(detail, list):
                    item["listaPrecioItem"] = detail
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

    async with httpx.AsyncClient(timeout=10.0) as http_client:
        adapter = HttpxClientAdapter(http_client)
        if XUBIO_PROVIDER == "xubio":
            await diagnosticar_autenticacion_xubio(http_client)
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
