"""Wiring de dependencias compartidas entre rutas de infraestructura."""

import httpx
from fastapi import Request, Depends

from src.infrastructure.config.settings import (
    CHATWOOT_ACCOUNT_ID,
    CHATWOOT_API_TOKEN,
    CHATWOOT_URL,
)
from src.adapters.gateways.lead_chatwoot_repository import ChatwootContactRepository
from src.infrastructure.httpx.http_client import HttpxClientAdapter
from src.domain.lead.http_client import IHttpClient


from src.domain.commerce.cart_repository import IRepositorioCarrito
from src.adapters.gateways.commerce_cookie_repository import RepositorioCarritoCookie
from src.infrastructure.structlog.logger import get_logger

from src.adapters.gateways.pricing_service import CotizadorServicio
from src.infrastructure.pyyaml.providers import obtener_tarifas
from src.infrastructure.reportlab.pdf_generator import GeneradorPresupuestoPDFReportLab
from src.domain.quote.pdf_generator import IGeneradorDocumentoPresupuesto
from src.adapters.gateways.quote_fallback_repository import RegistroFallbackArchivo
from src.domain.quote.fallback_registry import IRegistroFallbackLead
from src.application.quote.generate_quote_pdf import CasoUsoGenerarPresupuestoPDF
from src.application.commerce.cart_use_cases import (
    CasoUsoActualizarCarrito,
    CasoUsoAgregarAlCarrito,
    CasoUsoEliminarDelCarrito,
    CasoUsoObtenerResumenCarrito,
)

logger = get_logger()


def get_repositorio_carrito(request: Request) -> IRepositorioCarrito:
    """Inyecta el repositorio de carrito basado en cookies."""
    return RepositorioCarritoCookie(
        cookies=request.cookies,
        registrar_error=logger.error,
    )


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
        http_client=HttpxClientAdapter(http_client),
        base_url=CHATWOOT_URL,
        account_id=CHATWOOT_ACCOUNT_ID,
        api_token=CHATWOOT_API_TOKEN,
    )


def get_cotizador() -> CotizadorServicio:
    """Inyecta el servicio cotizador."""
    return CotizadorServicio(
        cargar_tarifas_yaml=obtener_tarifas,
        registrar_error=logger.error,
    )


def get_generador_pdf() -> IGeneradorDocumentoPresupuesto:
    """Inyecta el generador de PDF concreto."""
    return GeneradorPresupuestoPDFReportLab()


def get_registro_fallback() -> IRegistroFallbackLead:
    """Inyecta el registro de contingencia (fallback)."""
    return RegistroFallbackArchivo()


def get_caso_uso_generar_pdf(
    generador_pdf: IGeneradorDocumentoPresupuesto = Depends(get_generador_pdf)
) -> CasoUsoGenerarPresupuestoPDF:
    """Inyecta el caso de uso para generar PDF de presupuestos."""
    return CasoUsoGenerarPresupuestoPDF(
        generador_pdf=generador_pdf,
        registrar_error=logger.error,
    )


def get_caso_uso_agregar_carrito(
    repo: IRepositorioCarrito = Depends(get_repositorio_carrito),
) -> CasoUsoAgregarAlCarrito:
    """Inyecta el caso de uso para agregar artículos al carrito."""
    return CasoUsoAgregarAlCarrito(
        repositorio=repo,
        registrar_error=logger.error,
    )


def get_caso_uso_eliminar_carrito(
    repo: IRepositorioCarrito = Depends(get_repositorio_carrito),
) -> CasoUsoEliminarDelCarrito:
    """Inyecta el caso de uso para eliminar artículos del carrito."""
    return CasoUsoEliminarDelCarrito(
        repositorio=repo,
        registrar_error=logger.error,
    )


def get_caso_uso_actualizar_carrito(
    repo: IRepositorioCarrito = Depends(get_repositorio_carrito),
) -> CasoUsoActualizarCarrito:
    """Inyecta el caso de uso para actualizar el carrito."""
    return CasoUsoActualizarCarrito(
        repositorio=repo,
        registrar_error=logger.error,
    )


def get_caso_uso_obtener_resumen_carrito() -> CasoUsoObtenerResumenCarrito:
    """Inyecta el caso de uso para obtener el resumen de bolsas y costo estimado."""
    return CasoUsoObtenerResumenCarrito(
        registrar_error=logger.warning,
    )


def get_http_client_adapter(
    client: httpx.AsyncClient = Depends(get_http_client)
) -> IHttpClient:
    """Inyecta el adaptador HttpxClientAdapter como la interfaz IHttpClient."""
    return HttpxClientAdapter(client)
