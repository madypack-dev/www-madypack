"""Script de auditoría de limpieza y calidad de datos para la API de Xubio ERP v1.1."""

import asyncio
import base64
import logging
from typing import Any

import httpx

from src.adapters.gateways.null_erp_gateway import NullErpGateway
from src.adapters.gateways.xubio_client import XubioErpGateway
from src.domain.erp.sanitizer import (
    sanitizar_fecha,
    sanitizar_item_tarifa,
    sanitizar_monto,
    sanitizar_texto,
)
from src.infrastructure.config.settings import (
    XUBIO_API_URL,
    XUBIO_CLIENT_ID,
    XUBIO_PROVIDER,
    XUBIO_SECRET_ID,
)
from src.infrastructure.httpx.http_client import HttpxClientAdapter
from src.infrastructure.structlog.logger import get_logger

logger = get_logger()


async def diagnosticar_autenticacion_xubio(http_client: httpx.AsyncClient):
    """Diagnostica la respuesta exacta de /TokenEndpoint y prueba variantes de autenticación HTTP."""
    credentials = f"{XUBIO_CLIENT_ID}:{XUBIO_SECRET_ID}"
    encoded = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
    token_url = f"{XUBIO_API_URL.rstrip('/')}/TokenEndpoint"

    headers = {
        "Authorization": f"Basic {encoded}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = "scope=&grant_type=client_credentials"

    logger.info(f"Enviando POST {token_url}...")
    res = await http_client.post(token_url, headers=headers, content=data)
    logger.info(f"Respuesta TokenEndpoint status: {res.status_code}, body: {res.text}")

    if res.status_code != 200:
        return None

    body = res.json()
    token = body.get("access_token")
    token_type = body.get("token_type", "Bearer")
    logger.info(f"Token obtenido: tipo='{token_type}', longitud={len(str(token))}")

    # Probar variantes de encabezado de autenticación con GET /miempresa
    variantes = [
        {"name": "Authorization: Bearer <token>", "headers": {"Authorization": f"Bearer {token}"}},
        {"name": "Authorization: <token>", "headers": {"Authorization": str(token)}},
        {"name": "token: <token>", "headers": {"token": str(token)}},
        {
            "name": "Header 'token' + 'Authorization'",
            "headers": {"token": str(token), "Authorization": f"Bearer {token}"},
        },
    ]

    base_api = XUBIO_API_URL.rstrip("/")
    for v in variantes:
        test_headers = {**v["headers"], "Accept": "application/json"}
        miempresa_res = await http_client.get(f"{base_api}/miempresa", headers=test_headers)
        logger.info(
            f"Prueba Variant [{v['name']}] -> Status: {miempresa_res.status_code}, Body: {miempresa_res.text[:200]}"
        )
        if miempresa_res.status_code == 200:
            logger.info(f"¡ÉXITO ENCONTRADO CON FORMATO DE AUTENTICACIÓN: {v['name']}!")
            return v["headers"]

    return {"Authorization": f"Bearer {token}"}


async def auditar_datos():
    """Ejecuta una auditoría sobre las respuestas crudas de los endpoints de Xubio."""
    logger.info(f"Iniciando auditoría de datos Xubio ERP (Proveedor: {XUBIO_PROVIDER})...")

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

        try:
            logger.info("--- Auditando /miempresa ---")
            empresa_res = await gateway.proxy_request("GET", "/miempresa")
            logger.info(f"Respuesta cruda de /miempresa: {empresa_res}")
        except Exception as exc:
            logger.error(f"Error consultando /miempresa: {exc}")

        try:
            logger.info("--- Auditando /listaPrecioBean (General) ---")
            lista_res = await gateway.proxy_request("GET", "/listaPrecioBean")
            logger.info(f"Respuesta cruda de /listaPrecioBean: {lista_res}")

            if isinstance(lista_res, list):
                for list_item in lista_res:
                    list_id = list_item.get("listaPrecioID") or list_item.get("id")
                    if list_id:
                        logger.info(
                            f"--- Auditando Detalle de Lista de Precio /listaPrecioBean/{list_id} ---"
                        )
                        detail_res = await gateway.proxy_request(
                            "GET", f"/listaPrecioBean/{list_id}"
                        )
                        logger.info(
                            f"Detalle de Lista de Precio {list_id} ({list_item.get('nombre')}): {detail_res}"
                        )
        except Exception as exc:
            logger.error(f"Error consultando /listaPrecioBean: {exc}")

        try:
            logger.info("--- Auditando /ProductoVentaBean ---")
            productos_venta = await gateway.proxy_request("GET", "/ProductoVentaBean")
            logger.info(f"Respuesta cruda de /ProductoVentaBean: {productos_venta}")
        except Exception as exc:
            logger.error(f"Error consultando /ProductoVentaBean: {exc}")

        try:
            logger.info("--- Auditando /productoStock ---")
            stock_res = await gateway.proxy_request("GET", "/productoStock")
            logger.info(f"Respuesta cruda de /productoStock: {stock_res}")
        except Exception as exc:
            logger.error(f"Error consultando /productoStock: {exc}")

    # 3. Prueba de sanitización defensiva sobre datos anómalos (casos de borde)
    logger.info("--- Pruebas de Sanitización Zero-Trust ---")
    casos_anomalos = [
        {"codigo": "<script>alert(1)</script>bobina_kg", "precio": "1250.50", "fecha": "2026-08-07"},
        {"codigo": "confeccion", "precio": "invalid_number", "fecha": None},
        {"codigo": None, "precio": -50.0, "fecha": "fecha_corrupta"},
        {"codigo": "  manija_plana  ", "precio": float("nan"), "fecha": "2026-01-01T10:00:00Z"},
    ]

    for idx, caso in enumerate(casos_anomalos, 1):
        codigo_limpio = sanitizar_texto(caso.get("codigo"), default="desconocido")
        monto_limpio = sanitizar_monto(caso.get("precio"), default=0.0)
        fecha_limpia = sanitizar_fecha(caso.get("fecha"))
        tarifa_item = sanitizar_item_tarifa(caso)

        logger.info(
            f"Caso {idx} -> Entrada: {caso} | Sanitizado: codigo='{codigo_limpio}', monto={monto_limpio}, fecha={fecha_limpia} | Objeto Tarifa: {tarifa_item}"
        )

    logger.info("Auditoría completada exitosamente.")


if __name__ == "__main__":
    asyncio.run(auditar_datos())
