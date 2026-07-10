import pytest
from pydantic import ValidationError
from unittest.mock import AsyncMock, MagicMock

from src.comercio.dominio.modelos.carrito import Carrito, ArticuloCarrito
from src.lead.aplicacion.dtos.lead_dtos import CrearLeadRequest
from src.lead.dominio.puertos.repositorio import ILeadRepository
from src.presupuesto.aplicacion.casos_uso.procesar_solicitud_presupuesto import (
    ProcesarSolicitudPresupuesto,
)
from src.presupuesto.dominio.puertos.registro_fallback import IRegistroFallbackLead


def test_crear_lead_request_telefono_normalization():
    req = CrearLeadRequest(nombre="A", empresa="B", telefono="+5491112345678", email="a@example.com")
    assert req.telefono == "+5491112345678"

    req = CrearLeadRequest(nombre="A", empresa="B", telefono="5491112345678", email="a@example.com")
    assert req.telefono == "+5491112345678"

    req = CrearLeadRequest(nombre="A", empresa="B", telefono="1112345678", email="a@example.com")
    assert req.telefono == "+5491112345678"

    req = CrearLeadRequest(nombre="A", empresa="B", telefono="91112345678", email="a@example.com")
    assert req.telefono == "+5491112345678"

    with pytest.raises(ValidationError):
        CrearLeadRequest(nombre="A", empresa="B", telefono="abc", email="a@example.com")


@pytest.mark.asyncio
async def test_procesar_solicitud_presupuesto_con_carrito_success():
    repo = AsyncMock(spec=ILeadRepository)
    repo.guardar.return_value = "chatwoot-contact-123"
    registro_fallback = MagicMock(spec=IRegistroFallbackLead)

    request = CrearLeadRequest(
        nombre="John", empresa="ACME", telefono="+5491125794649", email="john@example.com"
    )
    carrito = Carrito()
    carrito.agregar_articulo(
        ArticuloCarrito(id=1, nombre="Bolsa", descripcion="Desc", cantidad=100, imagen="img.png")
    )

    caso_uso = ProcesarSolicitudPresupuesto(
        repositorio=repo,
        chatwoot_inbox_id=10,
        registro_fallback=registro_fallback,
    )

    lead = await caso_uso.ejecutar(request, carrito=carrito)

    assert lead.id == "chatwoot-contact-123"
    assert lead.codigo_referencia.startswith("COT-")
    assert "COT-GEN-" not in lead.codigo_referencia
    repo.guardar.assert_called_once()
    registro_fallback.guardar.assert_not_called()


@pytest.mark.asyncio
async def test_procesar_solicitud_presupuesto_fallback():
    repo = AsyncMock(spec=ILeadRepository)
    repo.guardar.side_effect = Exception("Chatwoot is down")
    registrar_error = MagicMock()
    registro_fallback = MagicMock(spec=IRegistroFallbackLead)

    request = CrearLeadRequest(
        nombre="John", empresa="ACME", telefono="+5491125794649", email="john@example.com"
    )
    carrito = Carrito()

    caso_uso = ProcesarSolicitudPresupuesto(
        repositorio=repo,
        chatwoot_inbox_id=10,
        registro_fallback=registro_fallback,
        registrar_error=registrar_error,
    )

    lead = await caso_uso.ejecutar(request, carrito=carrito)

    assert lead.id.startswith("FALLBACK-")
    assert lead.codigo_referencia.startswith("COT-")
    registrar_error.assert_called_once()
    registro_fallback.guardar.assert_called_once()


@pytest.mark.asyncio
async def test_procesar_solicitud_presupuesto_sin_carrito():
    repo = AsyncMock(spec=ILeadRepository)
    repo.guardar.return_value = "chatwoot-contact-456"
    registro_fallback = MagicMock(spec=IRegistroFallbackLead)

    request = CrearLeadRequest(
        nombre="Jane", empresa="Particular", telefono="+5491125794649", email="jane@example.com"
    )
    carrito = Carrito()

    caso_uso = ProcesarSolicitudPresupuesto(
        repositorio=repo,
        chatwoot_inbox_id=10,
        registro_fallback=registro_fallback,
    )

    lead = await caso_uso.ejecutar(request, carrito=carrito)

    assert lead.id == "chatwoot-contact-456"
    assert lead.codigo_referencia.startswith("COT-GEN-")
    repo.guardar.assert_called_once()


