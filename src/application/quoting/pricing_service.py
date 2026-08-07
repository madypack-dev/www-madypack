"""Servicio de aplicación que calcula precios estimados en valor presente."""

from datetime import date
from typing import Callable

from src.domain.pricing.actualizador_ipc import ActualizadorIPC
from src.domain.pricing.calculator import CalculadorPrecio
from src.domain.pricing.conversor_moneda import ConversorMoneda
from src.domain.pricing.proveedor_ipc import IProveedorIPC
from src.domain.pricing.proveedor_tarifas import IProveedorTarifas
from src.domain.pricing.proveedor_tasa_cambio import IProveedorTasaCambio

from src.domain.commerce.cart import ArticuloCarrito
from src.domain.commerce.catalog_repository import ICatalogRepository
from src.domain.commerce.product import ProductoBien


class CotizadorServicio:
    """Orquesta el cálculo de precios usando tarifas, tasa de cambio e IPC."""

    def __init__(
        self,
        catalogo: ICatalogRepository | None = None,
        registrar_error: Callable[[str], None] = lambda _: None,
        proveedor_tarifas: IProveedorTarifas | None = None,
        proveedor_tasa: IProveedorTasaCambio | None = None,
        proveedor_ipc: IProveedorIPC | None = None,
        fecha_presente: date | None = None,
        bolsa_solap_cm: float = 3.5,
    ):
        self.catalogo = catalogo
        self.registrar_error = registrar_error
        self._calculador = CalculadorPrecio()
        self._proveedor_tarifas = proveedor_tarifas
        self._proveedor_tasa = proveedor_tasa
        self._proveedor_ipc = proveedor_ipc
        self._actualizador = ActualizadorIPC(proveedor_ipc) if proveedor_ipc else None
        self._fecha_presente = fecha_presente or date.today()
        self._bolsa_solap_cm = bolsa_solap_cm

    def calcular_precio_estimado(self, articulo: ArticuloCarrito) -> float:
        conceptos_ars = self._conceptos_en_ars()
        try:
            if articulo.calculo is not None:
                return self._calculador.calcular(
                    articulo.calculo, conceptos_ars, articulo.cantidad
                )

            if self.catalogo is None:
                raise ValueError(
                    "El artículo no tiene configuración de cálculo y no se proporcionó catálogo."
                )

            producto = self.catalogo.obtener_por_id(articulo.id)
            if isinstance(producto, ProductoBien) and producto.es_compuesto:
                return self._calcular_compuesto(producto, articulo.cantidad, conceptos_ars)

            if isinstance(producto, ProductoBien) and producto.variaciones:
                return self._calculador.calcular(
                    producto.variaciones[0].calculo, conceptos_ars, articulo.cantidad
                )

            raise ValueError(f"No se puede cotizar el artículo {articulo.id}.")
        except Exception as err:
            self.registrar_error(f"Error calculando precio para artículo {articulo.id}: {err}")
            raise

    def _conceptos_en_ars(self) -> dict[str, float]:
        if self._proveedor_tarifas is None:
            raise ValueError("No se configuró un proveedor de tarifas.")
        if self._proveedor_tasa is None:
            raise ValueError("No se configuró un proveedor de tasa de cambio.")
        if self._actualizador is None:
            raise ValueError("No se configuró un proveedor de IPC.")

        tarifas = self._proveedor_tarifas.obtener_tarifas()
        tasa = self._proveedor_tasa.obtener_tasa()
        conceptos_dinero = ConversorMoneda(tasa).convertir_conceptos(tarifas)
        conceptos_actualizados = {
            nombre: self._actualizador.actualizar(dinero, self._fecha_presente)
            for nombre, dinero in conceptos_dinero.items()
        }
        return {nombre: float(dinero.monto) for nombre, dinero in conceptos_actualizados.items()}

    def _calcular_compuesto(
        self, compuesto: ProductoBien, cantidad: int, conceptos_ars: dict[str, float]
    ) -> float:
        total = 0.0
        for componente in compuesto.componentes:
            subtotal = self._calcular_componente(componente, cantidad, conceptos_ars)
            total += subtotal
        return total

    def _calcular_componente(
        self, componente, cantidad: int, conceptos_ars: dict[str, float]
    ) -> float:
        if componente.medidas is not None:
            kg_necesarios = (
                componente.medidas.kg_por_unidad(
                    componente.gramaje, solap_cm=self._bolsa_solap_cm
                )
                * cantidad
                * componente.cantidad
            )
            return kg_necesarios * conceptos_ars.get("bobina_kg", 0.0)

        if self.catalogo is None:
            raise ValueError("Se requiere un catálogo para resolver componentes.")

        item = self.catalogo.resolver_componente(componente)
        if item is None:
            raise ValueError(
                f"Componente {componente.referencia_id} no encontrado en el componente."
            )

        return self._calculador.calcular(
            item.calculo, conceptos_ars, cantidad * componente.cantidad
        )
