"""Tests para el conversor de moneda del cotizador."""

from datetime import date
from decimal import Decimal

import pytest

from src.domain.pricing.concepto_tarifa import ConceptoTarifa
from src.domain.pricing.conversor_moneda import ConversorMoneda
from src.domain.pricing.dinero import Dinero
from src.domain.pricing.moneda import Moneda
from src.domain.pricing.tasa_cambio import TasaCambio


class TestConversorMoneda:
    def test_concepto_ars_no_se_convierte(self):
        fecha_tarifa = date(2024, 1, 1)
        tasa = TasaCambio(fecha=date(2024, 6, 1), ars_por_usd=1000.0, fuente="BNA")
        conversor = ConversorMoneda(tasa)

        resultado = conversor.convertir_conceptos(
            {"base": ConceptoTarifa(nombre="base", monto=0.15, moneda=Moneda.ARS, fecha=fecha_tarifa)}
        )

        assert resultado["base"] == Dinero(
            monto=Decimal("0.15"), moneda=Moneda.ARS, fecha_referencia=fecha_tarifa
        )

    def test_concepto_usd_se_convierte_a_ars(self):
        fecha_tasa = date(2024, 6, 1)
        tasa = TasaCambio(fecha=fecha_tasa, ars_por_usd=1000.0, fuente="BNA")
        conversor = ConversorMoneda(tasa)

        resultado = conversor.convertir_conceptos(
            {"base": ConceptoTarifa(nombre="base", monto=0.15, moneda=Moneda.USD)}
        )

        assert resultado["base"] == Dinero(
            monto=Decimal("150.0"), moneda=Moneda.ARS, fecha_referencia=fecha_tasa
        )

    def test_mezcla_de_monedas_se_convierte_correctamente(self):
        fecha_tasa = date(2024, 6, 1)
        tasa = TasaCambio(fecha=fecha_tasa, ars_por_usd=500.0, fuente="BNA")
        conversor = ConversorMoneda(tasa)

        resultado = conversor.convertir_conceptos(
            {
                "ars": ConceptoTarifa(nombre="ars", monto=10.0, moneda=Moneda.ARS),
                "usd": ConceptoTarifa(nombre="usd", monto=2.0, moneda=Moneda.USD),
            }
        )

        assert resultado["ars"].monto == Decimal("10.0")
        assert resultado["ars"].moneda == Moneda.ARS
        assert resultado["usd"].monto == Decimal("1000.0")
        assert resultado["usd"].moneda == Moneda.ARS
        assert resultado["usd"].fecha_referencia == fecha_tasa

    def test_concepto_inexistente_en_diccionario_no_aparece(self):
        tasa = TasaCambio(fecha=date.today(), ars_por_usd=1.0, fuente="default")
        conversor = ConversorMoneda(tasa)

        resultado = conversor.convertir_conceptos({})

        assert resultado == {}
