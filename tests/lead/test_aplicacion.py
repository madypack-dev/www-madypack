import json
import pytest
import urllib.parse
from unittest.mock import AsyncMock, MagicMock
from pydantic import ValidationError

from src.lead.aplicacion.dtos.lead_dtos import CrearLeadRequest
from src.presupuesto.aplicacion.casos_uso.procesar_solicitud_presupuesto import (
    ProcesarSolicitudPresupuesto,
)
from src.lead.dominio.puertos.repositorio import ILeadRepository
from src.comercio.dominio.modelos.carrito import Carrito


def test_crear_lead_request_telefono_normalization():
    # Caso 1: ya viene internacional
    req = CrearLeadRequest(nombre="A", empresa="B", telefono="+5491112345678", email="a@example.com")
    assert req.telefono == "+5491112345678"

    # Caso 2: con 54 sin +
    req = CrearLeadRequest(nombre="A", empresa="B", telefono="5491112345678", email="a@example.com")
    assert req.telefono == "+5491112345678"

    # Caso 3: número local sin 54
    req = CrearLeadRequest(nombre="A", empresa="B", telefono="1112345678", email="a@example.com")
    assert req.telefono == "+5491112345678"

    # Caso 4: número local con 9
    req = CrearLeadRequest(nombre="A", empresa="B", telefono="91112345678", email="a@example.com")
    assert req.telefono == "+5491112345678"

    # Caso inválido
    with pytest.raises(ValidationError):
        CrearLeadRequest(nombre="A", empresa="B", telefono="abc", email="a@example.com")


@pytest.mark.asyncio
async def test_procesar_solicitud_presupuesto_con_carrito_success():
    repo = AsyncMock(spec=ILeadRepository)
    repo.guardar.return_value = "chatwoot-contact-123"

    request = CrearLeadRequest(
        nombre="John", empresa="ACME", telefono="+5491125794649", email="john@example.com"
    )
    carrito = Carrito()
    from src.comercio.dominio.modelos.carrito import ArticuloCarrito
    carrito.agregar_articulo(
        ArticuloCarrito(id=1, nombre="Bolsa", descripcion="Desc", cantidad=100, imagen="img.png")
    )

    caso_uso = ProcesarSolicitudPresupuesto(
        repositorio=repo,
        chatwoot_inbox_id=10,
        whatsapp_phone="5491125794649",
    )

    response = await caso_uso.ejecutar(request, carrito=carrito)

    assert response.lead_id == "chatwoot-contact-123"
    assert response.codigo_referencia.startswith("COT-")
    assert "COT-" in response.whatsapp_url
    assert "John" in urllib.parse.unquote(response.whatsapp_url)
    assert "ACME" in urllib.parse.unquote(response.whatsapp_url)
    assert "1" in urllib.parse.unquote(response.whatsapp_url)
    assert "descargar" in response.pdf_url

    repo.guardar.assert_called_once()


@pytest.mark.asyncio
async def test_procesar_solicitud_presupuesto_fallback(tmp_path):
    repo = AsyncMock(spec=ILeadRepository)
    repo.guardar.side_effect = Exception("Chatwoot is down")
    registrar_error = MagicMock()

    request = CrearLeadRequest(
        nombre="John", empresa="ACME", telefono="+5491125794649", email="john@example.com"
    )
    carrito = Carrito()
    fallback_file = tmp_path / "failed_leads.log"

    caso_uso = ProcesarSolicitudPresupuesto(
        repositorio=repo,
        chatwoot_inbox_id=10,
        whatsapp_phone="5491125794649",
        registrar_error=registrar_error,
        fallback_file_path=str(fallback_file),
    )

    response = await caso_uso.ejecutar(request, carrito=carrito)

    assert response.lead_id.startswith("FALLBACK-")
    registrar_error.assert_called_once()

    # Verificar que se escribió el lead de contingencia
    assert fallback_file.exists()
    lines = fallback_file.read_text().splitlines()
    assert len(lines) == 1
    assert "ACME" in lines[0]
    assert "Chatwoot is down" in lines[0]


@pytest.mark.asyncio
async def test_procesar_solicitud_presupuesto_sin_carrito():
    repo = AsyncMock(spec=ILeadRepository)
    repo.guardar.return_value = "chatwoot-contact-456"

    request = CrearLeadRequest(
        nombre="Jane", empresa="Particular", telefono="+5491125794649", email="jane@example.com"
    )
    carrito = Carrito()

    caso_uso = ProcesarSolicitudPresupuesto(
        repositorio=repo,
        chatwoot_inbox_id=10,
        whatsapp_phone="5491125794649",
    )

    response = await caso_uso.ejecutar(request, carrito=carrito, mensaje="Consulta general")

    assert response.lead_id == "chatwoot-contact-456"
    assert response.codigo_referencia.startswith("COT-GEN-")
    assert response.pdf_url is None
    assert "Consulta general" in urllib.parse.unquote(response.whatsapp_url)


@pytest.mark.asyncio
async def test_procesar_solicitud_presupuesto_respuesta_emergencia(tmp_path):
    repo = AsyncMock(spec=ILeadRepository)
    request = CrearLeadRequest(
        nombre="John", empresa="ACME", telefono="+5491125794649", email="john@example.com"
    )
    carrito = Carrito()
    from src.comercio.dominio.modelos.carrito import ArticuloCarrito
    carrito.agregar_articulo(
        ArticuloCarrito(id=1, nombre="Bolsa", descripcion="Desc", cantidad=100, imagen="img.png")
    )

    fallback_file = tmp_path / "failed_leads.log"
    caso_uso = ProcesarSolicitudPresupuesto(
        repositorio=repo,
        chatwoot_inbox_id=10,
        whatsapp_phone="5491125794649",
        fallback_file_path=str(fallback_file),
    )

    async def _falla_critica(self, request, carrito, mensaje):
        raise RuntimeError("Critical Mocked Crash")

    caso_uso._procesar_con_carrito = _falla_critica.__get__(caso_uso, ProcesarSolicitudPresupuesto)

    response = await caso_uso.ejecutar(request, carrito, mensaje="Urgente")

    assert response.codigo_referencia.startswith("COT-ERR-")
    assert "5491125794649" in response.whatsapp_url
    assert response.pdf_url is not None
    assert fallback_file.exists()
    lines = fallback_file.read_text().splitlines()
    leads = [json.loads(line) for line in lines]
    assert any("COT-ERR-" in lead["codigo_referencia"] for lead in leads)
    assert any("Falla crítica de infraestructura" in lead["error"] for lead in leads)
