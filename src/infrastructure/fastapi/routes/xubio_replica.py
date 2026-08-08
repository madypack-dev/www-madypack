"""Router de réplica pasiva de SOLO LECTURA (GET) para la API de Xubio v1.1 en el Servidor Privado ERP."""

from fastapi import APIRouter, Depends, Request
from src.domain.erp.ports import IErpGateway
from src.infrastructure.fastapi.dependencies import get_erp_gateway

router = APIRouter(prefix="/api/v1/xubio", tags=["Xubio Proxy Réplica (Solo Lectura)"])


@router.get("/miempresa")
async def replica_get_miempresa(erp_gateway: IErpGateway = Depends(get_erp_gateway)):
    """Réplica directa de GET /miempresa de Xubio v1.1."""
    return await erp_gateway.proxy_request("GET", "/miempresa")


@router.get("/clienteBean")
async def replica_get_clientes(
    request: Request, erp_gateway: IErpGateway = Depends(get_erp_gateway)
):
    """Réplica directa de GET /clienteBean de Xubio v1.1."""
    params = dict(request.query_params)
    return await erp_gateway.proxy_request("GET", "/clienteBean", params=params)


@router.get("/presupuestoBean")
async def replica_get_presupuestos(
    request: Request, erp_gateway: IErpGateway = Depends(get_erp_gateway)
):
    """Réplica directa de GET /presupuestoBean de Xubio v1.1."""
    params = dict(request.query_params)
    return await erp_gateway.proxy_request("GET", "/presupuestoBean", params=params)


@router.get("/productoStock")
async def replica_get_producto_stock(
    request: Request, erp_gateway: IErpGateway = Depends(get_erp_gateway)
):
    """Réplica directa de GET /productoStock de Xubio v1.1."""
    params = dict(request.query_params)
    return await erp_gateway.proxy_request("GET", "/productoStock", params=params)
