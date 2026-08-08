"""Script de auditoría de limpieza y calidad de datos para la API de Xubio ERP v1.1."""

import asyncio
import json
import logging
from typing import Any

from src.adapters.gateways.null_erp_gateway import NullErpGateway
from src.domain.erp.sanitizer import (
    sanitizar_fecha,
    sanitizar_item_tarifa,
    sanitizar_monto,
    sanitizar_texto,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("auditoria_xubio")


async def auditar_datos():
    """Ejecuta una auditoría sobre las respuestas crudas de los endpoints de Xubio."""
    logger.info("Iniciando auditoría de datos Xubio ERP...")
    gateway = NullErpGateway()

    # 1. Auditoría de /listaPrecioBean
    logger.info("--- Auditando /listaPrecioBean ---")
    lista_res = await gateway.proxy_request("GET", "/listaPrecioBean")
    logger.info(f"Respuesta cruda de /listaPrecioBean: {lista_res}")

    # 2. Auditoría de /productoStock
    logger.info("--- Auditando /productoStock ---")
    stock_res = await gateway.proxy_request("GET", "/productoStock")
    logger.info(f"Respuesta cruda de /productoStock: {stock_res}")

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
