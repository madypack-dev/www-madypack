"""Tests unitarios para el Sanitizador Zero-Trust de Xubio ERP."""

import math
from datetime import date

from src.domain.erp.sanitizer import (
    sanitizar_fecha,
    sanitizar_item_tarifa,
    sanitizar_moneda,
    sanitizar_monto,
    sanitizar_texto,
)
from src.domain.pricing.moneda import Moneda


def test_sanitizar_texto_xss_y_tags():
    assert sanitizar_texto("<script>alert('xss')</script>bobina_kg") == "alert('xss')bobina_kg"
    assert sanitizar_texto("  manija_plana  ") == "manija_plana"
    assert sanitizar_texto(None, default="fallback") == "fallback"


def test_sanitizar_monto_nan_inf_negativo():
    assert sanitizar_monto(150.50) == 150.50
    assert sanitizar_monto("200.0") == 200.0
    assert sanitizar_monto(math.nan, default=0.0) == 0.0
    assert sanitizar_monto(math.inf, default=0.0) == 0.0
    assert sanitizar_monto(-50.0, min_val=0.0) == 0.0
    assert sanitizar_monto("invalid", default=10.0) == 10.0


def test_sanitizar_fecha_iso_y_corrupta():
    assert sanitizar_fecha("2026-08-07") == date(2026, 8, 7)
    assert sanitizar_fecha("2026-08-07T12:30:00Z") == date(2026, 8, 7)
    assert sanitizar_fecha("fecha_invalida") == date.today()
    assert sanitizar_fecha(None) == date.today()


def test_sanitizar_moneda_ars_y_usd():
    assert sanitizar_moneda("ARS") == Moneda.ARS
    assert sanitizar_moneda("USD") == Moneda.USD
    assert sanitizar_moneda("DOLAR") == Moneda.USD
    assert sanitizar_moneda(None) == Moneda.ARS


def test_sanitizar_item_tarifa_valido():
    raw = {
        "codigo": "  bobina_kg  ",
        "precio": "1250.75",
        "moneda": "ARS",
        "fecha": "2026-08-01",
    }
    concepto = sanitizar_item_tarifa(raw)
    assert concepto is not None
    assert concepto.nombre == "bobina_kg"
    assert concepto.monto == 1250.75
    assert concepto.moneda == Moneda.ARS
    assert concepto.fecha == date(2026, 8, 1)


def test_sanitizar_item_tarifa_invalido():
    assert sanitizar_item_tarifa(None) is None
    assert sanitizar_item_tarifa({}) is None
    assert sanitizar_item_tarifa({"precio": 100}) is None  # Falta código
