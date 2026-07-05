import pytest
import urllib.parse
from unittest.mock import AsyncMock, MagicMock
from pydantic import ValidationError
from src.lead.aplicacion.dtos.lead_dtos import CrearLeadRequest
from src.lead.aplicacion.casos_uso.crear_lead import CrearLeadDesdePresupuesto

from src.lead.dominio.puertos.repositorio import ILeadRepository
from src.lead.dominio.puertos.publicador_eventos import IPublicadorEventos

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
async def test_crear_lead_desde_presupuesto_caso_uso_success():
    repo = AsyncMock(spec=ILeadRepository)
    repo.guardar.return_value = "chatwoot-contact-123"
    
    pub = AsyncMock(spec=IPublicadorEventos)
    
    request = CrearLeadRequest(nombre="John", empresa="ACME", telefono="+5491125794649", email="john@example.com")
    
    caso_uso = CrearLeadDesdePresupuesto(
        repositorio=repo,
        publicador_eventos=pub,
        chatwoot_inbox_id=10,
        whatsapp_phone="5491125794649"
    )

    response = await caso_uso.ejecutar(request, total_articulos=1)
    
    assert response.lead_id == "chatwoot-contact-123"
    assert response.codigo_referencia.startswith("COT-")
    assert "COT-" in response.whatsapp_url
    assert "John" in urllib.parse.unquote(response.whatsapp_url)
    assert "ACME" in urllib.parse.unquote(response.whatsapp_url)
    assert "1" in urllib.parse.unquote(response.whatsapp_url)
    assert "descargar" in response.pdf_url
    
    repo.guardar.assert_called_once()
    pub.publicar_lead_creado.assert_called_once()

@pytest.mark.asyncio
async def test_crear_lead_desde_presupuesto_caso_uso_fallback(tmp_path):
    repo = AsyncMock(spec=ILeadRepository)
    repo.guardar.side_effect = Exception("Chatwoot is down")
    
    pub = AsyncMock(spec=IPublicadorEventos)
    registrar_error = MagicMock()
    
    request = CrearLeadRequest(nombre="John", empresa="ACME", telefono="+5491125794649", email="john@example.com")
    fallback_file = tmp_path / "failed_leads.log"

    caso_uso = CrearLeadDesdePresupuesto(
        repositorio=repo,
        publicador_eventos=pub,
        chatwoot_inbox_id=10,
        whatsapp_phone="5491125794649",
        registrar_error=registrar_error,
        fallback_file_path=str(fallback_file)
    )

    response = await caso_uso.ejecutar(request, total_articulos=0)
    
    assert response.lead_id.startswith("FALLBACK-")
    registrar_error.assert_called_once()
    pub.publicar_lead_creado.assert_called_once()
    
    # Verificar que se escribió el lead de contingencia
    assert fallback_file.exists()
    lines = fallback_file.read_text().splitlines()
    assert len(lines) == 1
    assert "ACME" in lines[0]
    assert "Chatwoot is down" in lines[0]
