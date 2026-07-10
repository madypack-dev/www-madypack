"""Wiring de dependencias compartidas entre rutas de infraestructura."""

import httpx
from fastapi import Request, Depends

from src.infraestructura.config.settings import (
    CHATWOOT_ACCOUNT_ID,
    CHATWOOT_API_TOKEN,
    CHATWOOT_URL,
)
from src.lead.adaptadores.repositorios.chatwoot_contact import ChatwootContactRepository


def get_http_client(request: Request) -> httpx.AsyncClient:
    """Obtiene el cliente HTTP singleton de la aplicación FastAPI."""
    if not hasattr(request.app.state, "http_client"):
        request.app.state.http_client = httpx.AsyncClient(timeout=10.0)
    return request.app.state.http_client


def get_chatwoot_repo(
    http_client: httpx.AsyncClient = Depends(get_http_client),
) -> ChatwootContactRepository:
    """Inyecta el cliente HTTP singleton para construir el repositorio de Chatwoot Contact."""
    return ChatwootContactRepository(
        http_client=http_client,
        base_url=CHATWOOT_URL,
        account_id=CHATWOOT_ACCOUNT_ID,
        api_token=CHATWOOT_API_TOKEN,
    )
