"""Tests para las reglas de dominio de manijas de papel."""

from src.domain.commerce.manija import FormatoManija, formato_manija_para_ancho


class TestFormatoManija:
    def test_peso_kg_por_unidad_114mm(self):
        formato = FormatoManija(largo_mm=114)
        assert round(formato.peso_kg_por_unidad, 6) == 0.000912

    def test_peso_kg_por_unidad_152mm(self):
        formato = FormatoManija(largo_mm=152)
        assert round(formato.peso_kg_por_unidad, 6) == 0.001216

    def test_peso_kg_por_unidad_190mm(self):
        formato = FormatoManija(largo_mm=190)
        assert round(formato.peso_kg_por_unidad, 6) == 0.001520

    def test_etiqueta(self):
        assert FormatoManija(largo_mm=114).etiqueta == "114mm"


class TestFormatoManijaParaAncho:
    def test_bolsa_hasta_125mm_usa_manija_114mm(self):
        assert formato_manija_para_ancho(120).largo_mm == 114
        assert formato_manija_para_ancho(125).largo_mm == 114

    def test_bolsa_hasta_160mm_usa_manija_152mm(self):
        assert formato_manija_para_ancho(126).largo_mm == 152
        assert formato_manija_para_ancho(160).largo_mm == 152

    def test_bolsa_mayor_a_160mm_usa_manija_190mm(self):
        assert formato_manija_para_ancho(161).largo_mm == 190
        assert formato_manija_para_ancho(300).largo_mm == 190

    def test_limite_exacto_125(self):
        assert formato_manija_para_ancho(125).largo_mm == 114

    def test_limite_exacto_160(self):
        assert formato_manija_para_ancho(160).largo_mm == 152
