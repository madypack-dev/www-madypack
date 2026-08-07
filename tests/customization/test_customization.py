"""Tests unitarios e integrados para el Bounded Context de Personalización Visual y Fotopolímero."""

import pytest
from io import BytesIO
from PIL import Image
from fastapi.testclient import TestClient

from src.infrastructure.fastapi.app import app
from src.domain.customization.customization import (
    EspecificacionBolsa,
    ImagenDiseno,
    PersonalizacionBolsa,
)
from src.adapters.gateways.customization.generador_fotopolimero_pillow import (
    GeneradorFotopolimeroPillowAdapter,
)
from src.adapters.gateways.customization.generador_mockup_svg import (
    GeneradorMockupBolsaSVGAdapter,
)
from src.application.customization.generate_customization import (
    CasoUsoGenerarPersonalizacion,
    SolicitudPersonalizacionDTO,
)


client = TestClient(app)


def _crear_imagen_test_bytes() -> bytes:
    img = Image.new("RGB", (100, 100), color="red")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


class TestCustomizationDomain:
    def test_especificacion_bolsa_validaciones(self):
        esp = EspecificacionBolsa(
            ancho_cm=20.0,
            alto_cm=30.0,
            fuelle_cm=10.0,
            color_papel="#D2B48C",
            color_tinta="#000000",
            tipo_manija="manija_retorcida",
        )
        assert esp.ancho_cm == 20.0
        assert esp.alto_cm == 30.0

        with pytest.raises(ValueError):
            EspecificacionBolsa(
                ancho_cm=2.0,
                alto_cm=30.0,
                fuelle_cm=10.0,
            )

    def test_personalizacion_area_util(self):
        esp = EspecificacionBolsa(ancho_cm=20.0, alto_cm=30.0, fuelle_cm=10.0)
        diseno = ImagenDiseno(contenido_bytes=_crear_imagen_test_bytes(), mime_type="image/png")
        pers = PersonalizacionBolsa(especificacion=esp, diseno=diseno)

        ancho_util, alto_util = pers.calcular_area_util_impresion()
        assert ancho_util == 17.0
        assert alto_util == 26.0


class TestCustomizationAdapters:
    def test_generador_fotopolimero_pillow_svg(self):
        esp = EspecificacionBolsa(ancho_cm=20.0, alto_cm=30.0, fuelle_cm=10.0)
        diseno = ImagenDiseno(contenido_bytes=_crear_imagen_test_bytes(), mime_type="image/png")
        pers = PersonalizacionBolsa(especificacion=esp, diseno=diseno)

        adapter = GeneradorFotopolimeroPillowAdapter()
        svg = adapter.generar_svg_fotopolimero(pers)

        assert "<svg" in svg
        assert "FOTOPOLÍMERO INDUSTRIAL" in svg
        assert "data:image/png;base64," in svg

    def test_generador_mockup_svg(self):
        esp = EspecificacionBolsa(ancho_cm=20.0, alto_cm=30.0, fuelle_cm=10.0, tipo_manija="manija_plana")
        diseno = ImagenDiseno(contenido_bytes=_crear_imagen_test_bytes(), mime_type="image/png")
        pers = PersonalizacionBolsa(especificacion=esp, diseno=diseno)

        adapter = GeneradorMockupBolsaSVGAdapter()
        svg = adapter.generar_svg_mockup(pers)

        assert "<svg" in svg
        assert esp.color_papel in svg


class TestCustomizationEndpoints:
    def test_get_personalizar_renderiza_ok(self):
        response = client.get("/personalizar/")
        assert response.status_code == 200
        assert "Personalizador Visual de Bolsas" in response.text

    def test_post_personalizar_procesar_retorna_svgs(self):
        files = {"diseno": ("logo.png", _crear_imagen_test_bytes(), "image/png")}
        data = {
            "ancho_cm": "25",
            "alto_cm": "35",
            "fuelle_cm": "12",
            "color_papel": "#FFFFFF",
            "color_tinta": "#C8102E",
            "tipo_manija": "manija_retorcida",
        }

        response = client.post("/personalizar/procesar", data=data, files=files)
        assert response.status_code == 200
        assert "Previsualización 2D de Bolsa" in response.text
        assert "svg-fotopolimero-data" in response.text
