"""Tests para el conversor de moneda del cotizador."""

from datetime import date

import pytest

from src.domain.pricing.concepto_tarifa import ConceptoTarifa
from src.domain.pricing.conversor_moneda import ConversorMoneda
from src.domain.pricing.moneda import Moneda
from src.domain.pricing.tasa_cambio import TasaCambio


class TestConversorMoneda:
    def test_concepto_ars_no_se_convierte(self):
        tasa = TasaCambio(fecha=date.today(), ars_por_usd=1000.0, fuente="BNA")
        conversor = ConversorMoneda(tasa)

        resultado = conversor.convertir_conceptos(
            {"base": ConceptoTarifa(nombre="base", monto=0.15, moneda=Moneda.ARS)}
        )

        assert resultado["base"] == 0.15

    def test_concepto_usd_se_convierte_a_ars(self):
        tasa = TasaCambio(fecha=date.today(), ars_por_usd=1000.0, fuente="BNA")
        conversor = ConversorMoneda(tasa)

        resultado = conversor.convertir_conceptos(
            {"base": ConceptoTarifa(nombre="base", monto=0.15, moneda=Moneda.USD)}
        )

        assert resultado["base"] == 150.0

    def test_mezcla_de_monedas_se_convierte_correctamente(self):
        tasa = TasaCambio(fecha=date.today(), ars_por_usd=500.0, fuente="BNA")
        conversor = ConversorMoneda(tasa)

        resultado = conversor.convertir_conceptos(
            {
                "ars": ConceptoTarifa(nombre="ars", monto=10.0, moneda=Moneda.ARS),
                "usd": ConceptoTarifa(nombre="usd", monto=2.0, moneda=Moneda.USD),
            }
        )

        assert resultado["ars"] == 10.0
        assert resultado["usd"] == 1000.0

    def test_concepto_inexistente_en_diccionario_no_aparece(self):
        tasa = TasaCambio(fecha=date.today(), ars_por_usd=1.0, fuente="default")
        conversor = ConversorMoneda(tasa)

        resultado = conversor.convertir_conceptos({})

        assert resultado == {}
