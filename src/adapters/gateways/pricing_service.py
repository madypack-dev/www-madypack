from typing import Callable

from src.domain.commerce.cart import ArticuloCarrito
from src.domain.commerce.catalog_repository import ICatalogRepository
from src.domain.commerce.manija import FormatoManija
from src.domain.commerce.product import ProductoBien
from src.domain.pricing.calculator import CalculadorPrecio
from src.infrastructure.config.settings import BOLSA_SOLAP_CM


def _tarifas_manija_cordon() -> dict[str, float]:
    """Tarifas unitarias derivadas del peso de papel de cada formato de manija."""
    return {
        f"manija_cordon_{fmt.largo_mm}": fmt.peso_kg_por_unidad
        for fmt in [FormatoManija(114), FormatoManija(152), FormatoManija(190)]
    }


# Conceptos de costo estáticos (tarifas) en pesos
TARIFAS = {
    "base": 0.15,
    "manija_plana": 0.35,
    "personalizacion": 0.20,
    "pegado": 0.10,
    "confeccion": 0.08,
    "fotopolimero": 0.05,
    "bobina_kg": 1.0,
    "corte": 0.02,
    "confeccion_cuerdas": 0.05,
    "fijo_matriz": 1500.00,
    **_tarifas_manija_cordon(),
}


class CotizadorServicio:
    """Servicio que calcula los precios estimados utilizando tarifas estáticas en código."""

    def __init__(
        self,
        catalogo: ICatalogRepository | None = None,
        registrar_error: Callable[[str], None] = lambda _: None,
    ):
        self.catalogo = catalogo
        self.registrar_error = registrar_error
        self._calculador = CalculadorPrecio()
        self._conceptos = TARIFAS

    def calcular_precio_estimado(self, articulo: ArticuloCarrito) -> float:
        try:
            if articulo.calculo is not None:
                return self._calculador.calcular(
                    articulo.calculo, self._conceptos, articulo.cantidad
                )

            if self.catalogo is None:
                raise ValueError(
                    "El artículo no tiene configuración de cálculo y no se proporcionó catálogo."
                )

            producto = self.catalogo.obtener_por_id(articulo.id)
            if isinstance(producto, ProductoBien) and producto.es_compuesto:
                return self._calcular_compuesto(producto, articulo.cantidad)

            if isinstance(producto, ProductoBien) and producto.variaciones:
                # Bien simple referenciado por su ID; usamos la primera variación
                return self._calculador.calcular(
                    producto.variaciones[0].calculo, self._conceptos, articulo.cantidad
                )

            raise ValueError(f"No se puede cotizar el artículo {articulo.id}.")
        except Exception as err:
            self.registrar_error(f"Error calculando precio para artículo {articulo.id}: {err}")
            raise

    def _calcular_compuesto(self, compuesto: ProductoBien, cantidad: int) -> float:
        total = 0.0
        for componente in compuesto.componentes:
            subtotal = self._calcular_componente(componente, cantidad)
            total += subtotal
        return total

    def _calcular_componente(self, componente, cantidad: int) -> float:
        if componente.medidas is not None:
            kg_necesarios = (
                componente.medidas.kg_por_unidad(
                    componente.gramaje, solap_cm=BOLSA_SOLAP_CM
                )
                * cantidad
                * componente.cantidad
            )
            return kg_necesarios * self._conceptos.get("bobina_kg", 0.0)

        if self.catalogo is None:
            raise ValueError("Se requiere un catálogo para resolver componentes.")

        item = self.catalogo.resolver_componente(componente)
        if item is None:
            raise ValueError(
                f"Componente {componente.referencia_id} no encontrado en el componente."
            )

        return self._calculador.calcular(
            item.calculo, self._conceptos, cantidad * componente.cantidad
        )
