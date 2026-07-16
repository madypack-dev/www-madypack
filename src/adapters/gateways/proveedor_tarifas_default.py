"""Proveedor de tarifas hardcodeadas con fecha de hoy."""

from datetime import date

from src.domain.commerce.manija import FormatoManija
from src.domain.pricing.concepto_tarifa import ConceptoTarifa
from src.domain.pricing.moneda import Moneda
from src.domain.pricing.proveedor_tarifas import IProveedorTarifas


def _tarifas_manija_cordon() -> dict[str, ConceptoTarifa]:
    """Tarifas unitarias derivadas del peso de papel de cada formato de manija."""
    return {
        f"manija_cordon_{fmt.largo_mm}": ConceptoTarifa(
            nombre=f"manija_cordon_{fmt.largo_mm}",
            monto=fmt.peso_kg_por_unidad,
            moneda=Moneda.ARS,
            fecha=date.today(),
        )
        for fmt in [FormatoManija(114), FormatoManija(152), FormatoManija(190)]
    }


# Conceptos de costo por defecto, todos en ARS y a valor de hoy.
TARIFAS: dict[str, ConceptoTarifa] = {
    "base": ConceptoTarifa(nombre="base", monto=0.15, moneda=Moneda.ARS, fecha=date.today()),
    "manija_plana": ConceptoTarifa(nombre="manija_plana", monto=0.35, moneda=Moneda.ARS, fecha=date.today()),
    "personalizacion": ConceptoTarifa(nombre="personalizacion", monto=0.20, moneda=Moneda.ARS, fecha=date.today()),
    "pegado": ConceptoTarifa(nombre="pegado", monto=0.10, moneda=Moneda.ARS, fecha=date.today()),
    "confeccion": ConceptoTarifa(nombre="confeccion", monto=0.08, moneda=Moneda.ARS, fecha=date.today()),
    "fotopolimero": ConceptoTarifa(nombre="fotopolimero", monto=0.05, moneda=Moneda.ARS, fecha=date.today()),
    "bobina_kg": ConceptoTarifa(nombre="bobina_kg", monto=1.0, moneda=Moneda.ARS, fecha=date.today()),
    "corte": ConceptoTarifa(nombre="corte", monto=0.02, moneda=Moneda.ARS, fecha=date.today()),
    "confeccion_cuerdas": ConceptoTarifa(nombre="confeccion_cuerdas", monto=0.05, moneda=Moneda.ARS, fecha=date.today()),
    "fijo_matriz": ConceptoTarifa(nombre="fijo_matriz", monto=1500.00, moneda=Moneda.ARS, fecha=date.today()),
    **_tarifas_manija_cordon(),
}


class ProveedorTarifasDefault(IProveedorTarifas):
    """Proveedor de tarifas en memoria con valores de respaldo.

    Al usar ``fecha=date.today()`` como fecha de referencia, el factor de
    actualización IPC resulta 1.0 hasta que se configure un proveedor de
    tarifas con fechas históricas o una tabla IPC real.
    """

    def obtener_tarifas(self) -> dict[str, ConceptoTarifa]:
        return TARIFAS
