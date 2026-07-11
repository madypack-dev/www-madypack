import urllib.parse

import pytest

from src.domain.comercio.modelos.carrito import Carrito, ArticuloCarrito
from src.domain.lead.modelos.lead import Lead
from src.adapters.presupuesto.presentadores.confirmacion import (
    PresentadorConfirmacionPresupuesto,
)


class TestPresentadorConfirmacionPresupuesto:
    @pytest.fixture
    def presentador(self):
        return PresentadorConfirmacionPresupuesto(whatsapp_phone="5491125794649")

    def test_presentar_con_carrito_incluye_pdf(self, presentador):
        lead = Lead.crear(
            nombre="John", empresa="ACME", telefono="+5491125794649", email="john@example.com"
        )
        lead.id = "chatwoot-contact-123"
        carrito = Carrito()
        carrito.agregar_articulo(
            ArticuloCarrito(id=1, nombre="Bolsa", descripcion="Desc", cantidad=100, imagen="img.png")
        )

        response = presentador.presentar(lead, carrito)

        assert response.lead_id == "chatwoot-contact-123"
        assert response.codigo_referencia == lead.codigo_referencia
        assert response.pdf_url is not None
        assert "descargar" in response.pdf_url
        assert "John" in urllib.parse.unquote(response.whatsapp_url)
        assert "ACME" in urllib.parse.unquote(response.whatsapp_url)
        assert "1" in urllib.parse.unquote(response.whatsapp_url)

    def test_presentar_sin_carrito_no_incluye_pdf(self, presentador):
        lead = Lead.crear_cotizacion_general(
            nombre="Jane", empresa="Particular", telefono="+5491125794649", email="jane@example.com"
        )
        lead.id = "chatwoot-contact-456"
        carrito = Carrito()

        response = presentador.presentar(lead, carrito, mensaje="Consulta general")

        assert response.pdf_url is None
        assert "Consulta general" in urllib.parse.unquote(response.whatsapp_url)
        assert "COT-GEN-" in urllib.parse.unquote(response.whatsapp_url)

    def test_presentar_emergencia(self, presentador):
        lead = Lead.crear_emergencia(
            nombre="John", empresa="ACME", telefono="+5491125794649", email="john@example.com"
        )
        lead.id = "ERR-12345"

        response = presentador.presentar_emergencia(lead, "COT-ERR-ABCD1234")

        assert response.lead_id == "ERR-12345"
        assert response.codigo_referencia == "COT-ERR-ABCD1234"
        assert response.pdf_url is not None
        assert "COT-ERR-ABCD1234" in urllib.parse.unquote(response.whatsapp_url)
        assert "inconveniente" in urllib.parse.unquote(response.whatsapp_url)
