"""Tests unitarios para el Value Object MargenComercial."""

import pytest
from src.domain.pricing.margen import MargenComercial


def test_margen_comercial_por_defecto():
    margen = MargenComercial()
    assert margen.porcentaje == 0.20
    assert margen.aplicar(100.0) == 120.0


def test_margen_comercial_personalizado():
    margen = MargenComercial(porcentaje=0.30)
    assert margen.porcentaje == 0.30
    assert margen.aplicar(100.0) == 130.0


def test_margen_comercial_porcentaje_negativo():
    with pytest.raises(ValueError, match="no puede ser negativo"):
        MargenComercial(porcentaje=-0.10)


def test_margen_comercial_costo_negativo():
    margen = MargenComercial()
    with pytest.raises(ValueError, match="no puede ser negativo"):
        margen.aplicar(-50.0)
