from typing import Callable, Protocol

from src.domain.commerce.cart import ArticuloCarrito
from src.domain.commerce.catalog_repository import ICatalogRepository
from src.domain.commerce.manija import FormatoManija
from src.domain.commerce.product import ProductoBien
from src.domain.pricing.calculator import CalculadorPrecio
from src.domain.pricing.concepto_tarifa import ConceptoTarifa
from src.domain.pricing.conversor_moneda import ConversorMoneda
from src.domain.pricing.moneda import Moneda
from src.domain.pricing.tasa_cambio import TasaCambio
from src.infrastructure.config.settings import BOLSA_SOLAP_CM


class IProveedorTasaCambio(Protocol):
    """Puerto para obtener la tasa de cambio vigente."""

    def obtener_tasa(self) -> TasaCambio:
        ...


class _ProveedorTasaCambioDefault:
    """Proveedor de respaldo que asume paridad 1:1 entre USD y ARS.

    Permite que el cotizador funcione sin configuración de tasa cuando todos
    los conceptos están expresados en ARS. Si algún concepto está en USD,
    el valor queda igual en ARS (tasa 1.0), lo que facilita tests y arranques
    sin datos de mercado.
    """

    def obtener_tasa(self) -> TasaCambio:
        from datetime import date

        return TasaCambio(fecha=date.today(), ars_por_usd=1.0, fuente="default")


def _tarifas_manija_cordon() -> dict[str, ConceptoTarifa]:
    """Tarifas unitarias derivadas del peso de papel de cada formato de manija."""
    return {
        f"manija_cordon_{fmt.largo_mm}": ConceptoTarifa(
            nombre=f"manija_cordon_{fmt.largo_mm}",
            monto=fmt.peso_kg_por_unidad,
            moneda=Moneda.ARS,
        )
        for fmt in [FormatoManija(114), FormatoManija(152), FormatoManija(190)]
    }


# Conceptos de costo estáticos (tarifas) por defecto, todos en ARS.
TARIFAS = {
    "base": ConceptoTarifa(nombre="base", monto=0.15, moneda=Moneda.ARS),
    "manija_plana": ConceptoTarifa(nombre="manija_plana", monto=0.35, moneda=Moneda.ARS),
    "personalizacion": ConceptoTarifa(nombre="personalizacion", monto=0.20, moneda=Moneda.ARS),
    "pegado": ConceptoTarifa(nombre="pegado", monto=0.10, moneda=Moneda.ARS),
    "confeccion": ConceptoTarifa(nombre="confeccion", monto=0.08, moneda=Moneda.ARS),
    "fotopolimero": ConceptoTarifa(nombre="fotopolimero", monto=0.05, moneda=Moneda.ARS),
    "bobina_kg": ConceptoTarifa(nombre="bobina_kg", monto=1.0, moneda=Moneda.ARS),
    "corte": ConceptoTarifa(nombre="corte", monto=0.02, moneda=Moneda.ARS),
    "confeccion_cuerdas": ConceptoTarifa(nombre="confeccion_cuerdas", monto=0.05, moneda=Moneda.ARS),
    "fijo_matriz": ConceptoTarifa(nombre="fijo_matriz", monto=1500.00, moneda=Moneda.ARS),
    **_tarifas_manija_cordon(),
}


class CotizadorServicio:
    """Servicio que calcula precios estimados usando tarifas en ARS o USD."""

    def __init__(
        self,
        catalogo: ICatalogRepository | None = None,
        registrar_error: Callable[[str], None] = lambda _: None,
        proveedor_tasa: IProveedorTasaCambio | None = None,
        conceptos: dict[str, ConceptoTarifa] | None = None,
    ):
        self.catalogo = catalogo
        self.registrar_error = registrar_error
        self._calculador = CalculadorPrecio()
        self._proveedor_tasa = proveedor_tasa or _ProveedorTasaCambioDefault()
        self._conceptos = conceptos if conceptos is not None else TARIFAS

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
                # Bien simple referenciado por su ID; usamos la primera variación
                return self._calculador.calcular(
                    producto.variaciones[0].calculo, conceptos_ars, articulo.cantidad
                )

            raise ValueError(f"No se puede cotizar el artículo {articulo.id}.")
        except Exception as err:
            self.registrar_error(f"Error calculando precio para artículo {articulo.id}: {err}")
            raise

    def _conceptos_en_ars(self) -> dict[str, float]:
        tasa = self._proveedor_tasa.obtener_tasa()
        return ConversorMoneda(tasa).convertir_conceptos(self._conceptos)

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
                    componente.gramaje, solap_cm=BOLSA_SOLAP_CM
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
