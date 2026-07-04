import pytest
from unittest.mock import AsyncMock, MagicMock
import httpx
from src.lead.dominio.modelos.lead import Lead
from src.lead.adaptadores.repositorios.chatwoot_contact import ChatwootContactRepository

@pytest.mark.asyncio
async def test_chatwoot_contact_repository_guardar_success():
    client = AsyncMock(spec=httpx.AsyncClient)
    
    mock_response1 = MagicMock(spec=httpx.Response)
    mock_response1.status_code = 201
    mock_response1.json.return_value = {
        "id": 12345,
        "name": "John Doe"
    }
    
    mock_response2 = MagicMock(spec=httpx.Response)
    mock_response2.status_code = 200
    mock_response2.json.return_value = {"success": True}
    
    client.post.side_effect = [mock_response1, mock_response2]

    repo = ChatwootContactRepository(
        http_client=client,
        base_url="https://chatwoot.com",
        account_id=1,
        api_token="token"
    )
    
    lead = Lead(
        codigo_referencia="COT-123",
        nombre="John Doe",
        empresa="Company",
        telefono="+549",
        email="john@example.com"
    )
    
    lead_id = await repo.guardar(lead, inbox_id=9)
    assert lead_id == "12345"
    assert client.post.call_count == 2

@pytest.mark.asyncio
async def test_chatwoot_contact_repository_obtener_por_id():
    client = AsyncMock(spec=httpx.AsyncClient)
    
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": 12345,
        "name": "John Doe",
        "identifier": "COT-123",
        "phone_number": "+549",
        "email": "john@example.com",
        "custom_attributes": {
            "empresa": "Company"
        }
    }
    client.get.return_value = mock_response

    repo = ChatwootContactRepository(
        http_client=client,
        base_url="https://chatwoot.com",
        account_id=1,
        api_token="token"
    )
    
    lead = await repo.obtener_por_id("12345")
    assert lead is not None
    assert lead.id == "12345"
    assert lead.nombre == "John Doe"
    assert lead.empresa == "Company"
