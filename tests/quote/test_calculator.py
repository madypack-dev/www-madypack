"""Tests para el motor genérico de cálculo de precios."""

import pytest

from src.domain.commerce.cart import CalculoArticulo
from src.domain.pricing.calculator import CalculadorPrecio


class TestCalculadorPrecio:
    def test_suma_por_unidad(self):
        calculo = CalculoArticulo(
            tipo="suma_por_unidad",
            conceptos=["base", "manija"],
        )
        conceptos = {"base": 0.15, "manija": 0.35}
        resultado = CalculadorPrecio().calcular(calculo, conceptos, 1000)
        assert resultado == 500.0

    def test_suma_por_unidad_mas_fijo(self):
        calculo = CalculoArticulo(
            tipo="suma_por_unidad_mas_fijo",
            conceptos=["base", "manija", "personalizacion"],
            concepto_fijo="fijo_matriz",
        )
        conceptos = {"base": 0.15, "manija": 0.35, "personalizacion": 0.20, "fijo_matriz": 1500.0}
        resultado = CalculadorPrecio().calcular(calculo, conceptos, 1000)
        assert resultado == 2200.0

    def test_concepto_inexistente_se_toma_como_cero(self):
        calculo = CalculoArticulo(
            tipo="suma_por_unidad",
            conceptos=["base", "concepto_que_no_existe"],
        )
        conceptos = {"base": 1.0}
        resultado = CalculadorPrecio().calcular(calculo, conceptos, 100)
        assert resultado == 100.0

    def test_calculo_nulo_lanza_error(self):
        with pytest.raises(ValueError, match="no tiene configuración de cálculo"):
            CalculadorPrecio().calcular(None, {}, 100)

    def test_tipo_desconocido_lanza_error(self):
        calculo = CalculoArticulo(tipo="desconocido", conceptos=["base"])
        with pytest.raises(ValueError, match="Tipo de cálculo desconocido"):
            CalculadorPrecio().calcular(calculo, {"base": 1.0}, 100)

    def test_registrar_estrategia_personalizada(self):
        class EstrategiaDescuentoMitad:
            def calcular(self, calculo, conceptos, cantidad):
                return (conceptos.get("base", 0.0) * cantidad) / 2.0

        CalculadorPrecio.registrar_estrategia("mitad_precio", EstrategiaDescuentoMitad())

        calculo = CalculoArticulo(tipo="mitad_precio", conceptos=["base"])
        conceptos = {"base": 10.0}
        resultado = CalculadorPrecio().calcular(calculo, conceptos, 100)
        assert resultado == 500.0
