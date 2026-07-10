import pytest
from unittest.mock import AsyncMock, MagicMock
import httpx
from src.lead.adaptadores.repositorios.chatwoot_contact import ChatwootContactRepository
from src.lead.dominio.modelos.lead import Lead


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
