"""Wiring de dependencias compartidas entre rutas de infraestructura."""

from datetime import date
from pathlib import Path

import httpx

from fastapi import Depends, Request
from src.adapters.gateways.catalog.in_memory_catalog_repository import InMemoryCatalogRepository
from src.adapters.gateways.commerce_cookie_repository import RepositorioCarritoCookie
from src.adapters.gateways.json_quote_repository import JsonQuoteRepository
from src.adapters.gateways.lead_chatwoot_repository import ChatwootContactRepository
from src.adapters.gateways.proveedor_ipc_default import ProveedorIPCDefault
from src.adapters.gateways.proveedor_ipc_yaml import ProveedorIPCYaml
from src.adapters.gateways.proveedor_tarifas_default import ProveedorTarifasDefault
from src.adapters.gateways.proveedor_tasa_cambio_default import ProveedorTasaCambioDefault
from src.adapters.gateways.quote_fallback_repository import RegistroFallbackArchivo
from src.application.comercio.cart_use_cases import (
    CasoUsoActualizarCarrito,
    CasoUsoAgregarAlCarrito,
    CasoUsoEliminarDelCarrito,
    CasoUsoObtenerResumenCarrito,
)
from src.application.cotizacion.generate_quote_pdf import CasoUsoGenerarPresupuestoPDF
from src.application.cotizacion.pricing_service import CotizadorServicio
from src.application.erp.use_cases import CasoUsoVerificarConexionERP
from src.domain.comercio.cart_repository import IRepositorioCarrito
from src.domain.comercio.catalog_repository import ICatalogRepository
from src.domain.cotizacion.fallback_registry import IRegistroFallbackLead
from src.domain.cotizacion.pdf_generator import IGeneradorDocumentoPresupuesto
from src.domain.cotizacion.quote_repository import IQuoteRepository
from src.domain.erp.ports import IErpGateway
from src.domain.lead.http_client import IHttpClient
from src.domain.pricing.proveedor_tarifas import IProveedorTarifas
from src.infrastructure.config.settings import (
    BOLSA_SOLAP_CM,
    CHATWOOT_ACCOUNT_ID,
    CHATWOOT_API_TOKEN,
    CHATWOOT_URL,
    IPC_DATA_PATH,
)
from src.infrastructure.httpx.http_client import HttpxClientAdapter
from src.infrastructure.pydantic.models import NegocioConfig
from src.infrastructure.reportlab.pdf_generator import GeneradorPresupuestoPDFReportLab
from src.infrastructure.structlog.logger import get_logger

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


def get_http_client_adapter(client: httpx.AsyncClient = Depends(get_http_client)) -> IHttpClient:
    """Inyecta el adaptador HttpxClientAdapter como la interfaz IHttpClient."""
    return HttpxClientAdapter(client)


def get_chatwoot_repo(
    http_client: IHttpClient = Depends(get_http_client_adapter),
) -> ChatwootContactRepository:
    """Inyecta el puerto IHttpClient para construir el repositorio de Chatwoot Contact."""
    return ChatwootContactRepository(
        http_client=http_client,
        base_url=CHATWOOT_URL,
        account_id=CHATWOOT_ACCOUNT_ID,
        api_token=CHATWOOT_API_TOKEN,
    )


def get_repositorio_catalogo() -> ICatalogRepository:
    """Inyecta el repositorio de catálogo en memoria."""
    return InMemoryCatalogRepository()


def get_erp_gateway(
    http_client: IHttpClient = Depends(get_http_client_adapter),
) -> IErpGateway:
    """Inyecta la implementación de IErpGateway según settings.XUBIO_PROVIDER."""
    from src.adapters.gateways.null_erp_gateway import NullErpGateway
    from src.adapters.gateways.xubio_client import XubioErpGateway
    from src.infrastructure.config import settings

    if settings.XUBIO_PROVIDER == "xubio":
        return XubioErpGateway(
            client=http_client,
            client_id=settings.XUBIO_CLIENT_ID,
            secret_id=settings.XUBIO_SECRET_ID,
            base_url=settings.XUBIO_API_URL,
            logger=logger,
        )
    return NullErpGateway()


def get_proveedor_tarifas(
    erp_gateway: IErpGateway = Depends(get_erp_gateway),
) -> IProveedorTarifas:
    """Inyecta el proveedor de tarifas según settings.XUBIO_PROVIDER."""
    from src.adapters.gateways.proveedor_tarifas_xubio import ProveedorTarifasXubio
    from src.infrastructure.config import settings

    if settings.XUBIO_PROVIDER == "xubio":
        return ProveedorTarifasXubio(erp_gateway=erp_gateway, logger=logger)
    return ProveedorTarifasDefault()


def get_configuracion_negocio() -> NegocioConfig:
    """Inyecta la configuración comercial cargada y validada desde data/negocio.yml."""
    from src.infrastructure.pyyaml.loaders import cargar_configuracion_negocio

    return cargar_configuracion_negocio()


def get_cotizador(
    repo_catalogo: ICatalogRepository = Depends(get_repositorio_catalogo),
    proveedor_tarifas: IProveedorTarifas = Depends(get_proveedor_tarifas),
    config_negocio: NegocioConfig = Depends(get_configuracion_negocio),
) -> CotizadorServicio:
    """Inyecta el servicio cotizador con tarifas, tasa de cambio e IPC."""
    from src.domain.pricing.margen import MargenComercial

    ruta_ipc = Path(IPC_DATA_PATH)
    proveedor_ipc = ProveedorIPCYaml(str(ruta_ipc)) if ruta_ipc.exists() else ProveedorIPCDefault()

    margen = MargenComercial(porcentaje=config_negocio.margen_comercial)

    return CotizadorServicio(
        catalogo=repo_catalogo,
        registrar_error=logger.error,
        proveedor_tarifas=proveedor_tarifas,
        proveedor_tasa=ProveedorTasaCambioDefault(),
        proveedor_ipc=proveedor_ipc,
        fecha_presente=date.today(),
        bolsa_solap_cm=BOLSA_SOLAP_CM,
        margen_comercial=margen,
    )







def get_generador_pdf() -> IGeneradorDocumentoPresupuesto:
    """Inyecta el generador de PDF concreto."""
    return GeneradorPresupuestoPDFReportLab()


def get_registro_fallback() -> IRegistroFallbackLead:
    """Inyecta el registro de contingencia (fallback)."""
    return RegistroFallbackArchivo()


def get_caso_uso_generar_pdf(
    generador_pdf: IGeneradorDocumentoPresupuesto = Depends(get_generador_pdf),
) -> CasoUsoGenerarPresupuestoPDF:
    """Inyecta el caso de uso para generar PDF de presupuestos."""
    return CasoUsoGenerarPresupuestoPDF(
        generador_pdf=generador_pdf,
        registrar_error=logger.error,
    )


def get_caso_uso_agregar_carrito(
    repo: IRepositorioCarrito = Depends(get_repositorio_carrito),
    repositorio_catalogo: ICatalogRepository = Depends(get_repositorio_catalogo),
) -> CasoUsoAgregarAlCarrito:
    """Inyecta el caso de uso para agregar artículos al carrito."""
    return CasoUsoAgregarAlCarrito(
        repositorio=repo,
        repositorio_catalogo=repositorio_catalogo,
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
    repo_catalogo: ICatalogRepository = Depends(get_repositorio_catalogo),
) -> CasoUsoActualizarCarrito:
    """Inyecta el caso de uso para actualizar el carrito."""
    return CasoUsoActualizarCarrito(
        repositorio=repo,
        repositorio_catalogo=repo_catalogo,
        registrar_error=logger.error,
    )


def get_caso_uso_obtener_resumen_carrito() -> CasoUsoObtenerResumenCarrito:
    """Inyecta el caso de uso para obtener el resumen de bolsas y costo estimado."""
    return CasoUsoObtenerResumenCarrito(
        registrar_error=logger.warning,
    )


def get_quote_repo() -> IQuoteRepository:
    """Inyecta el repositorio de presupuestos (JSON local)."""
    return JsonQuoteRepository()


def get_caso_uso_personalizacion():
    """Inyecta el caso de uso para generar la personalización de la bolsa y el fotopolímero."""
    from src.adapters.gateways.personalizacion.generador_fotopolimero_pillow import (
        GeneradorFotopolimeroPillowAdapter,
    )
    from src.adapters.gateways.personalizacion.generador_mockup_svg import (
        GeneradorMockupBolsaSVGAdapter,
    )
    from src.application.personalizacion.generate_customization import CasoUsoGenerarPersonalizacion

    return CasoUsoGenerarPersonalizacion(
        generador_fotopolimero=GeneradorFotopolimeroPillowAdapter(),
        generador_mockup=GeneradorMockupBolsaSVGAdapter(),
        registrar_error=logger.error,
    )



def get_caso_uso_verificar_conexion_erp(
    erp_gateway: IErpGateway = Depends(get_erp_gateway),
) -> CasoUsoVerificarConexionERP:
    """Inyecta el caso de uso para verificar la conexión al ERP."""
    return CasoUsoVerificarConexionERP(erp_gateway=erp_gateway)
