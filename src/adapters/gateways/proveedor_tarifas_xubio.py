"""Adaptador de proveedor de tarifas desde Xubio ERP v1.1 con sanitización Zero-Trust."""

import asyncio
from typing import Any

from src.domain.erp.ports import IErpGateway
from src.domain.erp.sanitizer import sanitizar_item_tarifa
from src.domain.pricing.concepto_tarifa import ConceptoTarifa
from src.domain.pricing.proveedor_tarifas import IProveedorTarifas


class ProveedorTarifasXubio(IProveedorTarifas):
    """Proveedor de tarifas que obtiene y sanitiza costos reales desde la API de Xubio ERP.

    Sigue el principio de Inversión de Dependencias (DIP) implementando IProveedorTarifas
    y consumiendo el puerto de dominio IErpGateway.
    Si Xubio ERP no provee datos o la consulta falla, no inventa precios de resguardo.
    """

    def __init__(
        self,
        erp_gateway: IErpGateway,
        lista_precio_id: int = 1,
        logger: Any = None,
    ):
        self._gateway = erp_gateway
        self._lista_id = lista_precio_id
        self._logger = logger
        self._cache_tarifas: dict[str, ConceptoTarifa] | None = None

    def _sanitizar_items(self, items_raw: list[Any]) -> dict[str, ConceptoTarifa]:
        """Convierte una lista de ítems crudos en un diccionario de conceptos sanitizados."""
        tarifas: dict[str, ConceptoTarifa] = {}
        for item in items_raw:
            concepto = sanitizar_item_tarifa(item)
            if concepto is not None:
                tarifas[concepto.nombre] = concepto
        return tarifas

    async def _cargar_tarifas_desde_stock(self) -> dict[str, ConceptoTarifa]:
        """Consulta /productoStock como alternativa secundaria si la lista de precios no retornó ítems."""
        stock_res = await self._gateway.proxy_request("GET", "/productoStock")
        stock_items = stock_res.get("list", []) if isinstance(stock_res, dict) else []
        return self._sanitizar_items(stock_items)

    async def cargar_tarifas_async(self) -> dict[str, ConceptoTarifa]:
        """Carga y sanitiza asincrónicamente el conjunto de tarifas reales desde Xubio."""
        if self._cache_tarifas is not None:
            return self._cache_tarifas

        try:
            res = await self._gateway.proxy_request("GET", f"/listaPrecioBean/{self._lista_id}")
            items_raw = (
                res.get("listaPrecioItem", [])
                if isinstance(res, dict)
                else (res if isinstance(res, list) else [])
            )
            tarifas = self._sanitizar_items(items_raw)

            if not tarifas:
                tarifas = await self._cargar_tarifas_desde_stock()

            if tarifas:
                self._cache_tarifas = tarifas
                return self._cache_tarifas
        except Exception as exc:
            if self._logger:
                self._logger.warning(
                    "xubio.tarifas.error",
                    error=str(exc),
                    mensaje="Error consultando tarifas en Xubio ERP.",
                )

        self._cache_tarifas = {}
        return self._cache_tarifas

    def obtener_tarifas(self) -> dict[str, ConceptoTarifa]:
        """Interfaz sincrónica de IProveedorTarifas.

        Devuelve las tarifas cacheadas obtenidas desde Xubio o un diccionario vacío si aún no cargó.
        """
        if self._cache_tarifas is not None:
            return self._cache_tarifas

        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                loop.create_task(self.cargar_tarifas_async())
        except RuntimeError:
            pass

        return {}

