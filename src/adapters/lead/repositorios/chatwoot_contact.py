import httpx
from src.domain.lead.modelos.lead import Lead
from src.domain.lead.puertos.repositorio import ILeadRepository

class ChatwootContactRepository(ILeadRepository):
    """Implementa la comunicación HTTP asíncrona con el backend de Chatwoot."""
    
    def __init__(self, http_client: httpx.AsyncClient, base_url: str, account_id: int, api_token: str):
        self.client = http_client
        self.base_url = base_url.rstrip("/")
        self.account_id = account_id
        self.api_token = api_token

    async def guardar(self, lead: Lead, inbox_id: int) -> str:
        """
        1. Crea el contacto via POST /api/v1/accounts/{account_id}/contacts
        2. Asocia el contacto al inbox via POST /api/v1/accounts/{account_id}/contacts/{contact_id}/contact_inboxes
        """
        headers = {
            "api_access_token": self.api_token,
            "Content-Type": "application/json"
        }
        
        # 1. Crear contacto
        contact_url = f"{self.base_url}/api/v1/accounts/{self.account_id}/contacts"
        contact_payload = {
            "name": lead.nombre,
            "email": lead.email,
            "phone_number": lead.telefono,
            "identifier": lead.codigo_referencia,
            "custom_attributes": {
                "empresa": lead.empresa,
                "codigo_referencia": lead.codigo_referencia
            }
        }
        
        response = await self.client.post(contact_url, headers=headers, json=contact_payload, timeout=10.0)
        response.raise_for_status()
        
        contact_data = response.json()
        contact_obj = contact_data.get("payload", {}).get("contact", {}) if "payload" in contact_data else contact_data
        contact_id = contact_obj.get("id")
        if not contact_id:
            contact_id = contact_data.get("id")
            
        if not contact_id:
            raise ValueError(f"No se pudo obtener el contact ID de la respuesta de Chatwoot: {contact_data}")

        # 2. Asociar al Inbox
        inbox_url = f"{self.base_url}/api/v1/accounts/{self.account_id}/contacts/{contact_id}/contact_inboxes"
        inbox_payload = {
            "inbox_id": inbox_id
        }
        try:
            inbox_response = await self.client.post(inbox_url, headers=headers, json=inbox_payload, timeout=10.0)
            inbox_response.raise_for_status()
        except Exception:
            # Silenciar error de asociación a Inbox para no romper flujo principal
            pass

        return str(contact_id)
