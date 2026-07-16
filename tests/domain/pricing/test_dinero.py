"""Tests para el value object Dinero."""

from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from src.domain.pricing.dinero import Dinero
from src.domain.pricing.moneda import Moneda


class TestDinero:
    def test_crea_dinero_ars(self):
        dinero = Dinero(monto=Decimal("150.50"), moneda=Moneda.ARS, fecha_referencia=date(2024, 1, 1))

        assert dinero.monto == Decimal("150.50")
        assert dinero.moneda == Moneda.ARS
        assert dinero.fecha_referencia == date(2024, 1, 1)

    def test_dinero_es_inmutable(self):
        dinero = Dinero(monto=Decimal("100"), moneda=Moneda.ARS, fecha_referencia=date(2024, 1, 1))

        with pytest.raises(ValidationError):
            dinero.monto = Decimal("200")

    def test_monto_negativo_lanza_error(self):
        with pytest.raises(ValidationError):
            Dinero(monto=Decimal("-10"), moneda=Moneda.ARS, fecha_referencia=date(2024, 1, 1))

    def test_igualdad_por_valor(self):
        a = Dinero(monto=Decimal("100"), moneda=Moneda.ARS, fecha_referencia=date(2024, 1, 1))
        b = Dinero(monto=Decimal("100"), moneda=Moneda.ARS, fecha_referencia=date(2024, 1, 1))

        assert a == b

    def test_diferencia_en_fecha_cambia_igualdad(self):
        a = Dinero(monto=Decimal("100"), moneda=Moneda.ARS, fecha_referencia=date(2024, 1, 1))
        b = Dinero(monto=Decimal("100"), moneda=Moneda.ARS, fecha_referencia=date(2024, 2, 1))

        assert a != b
