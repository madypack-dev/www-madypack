"""Router de replica directa para la API de Xubio v1.1 en el Servidor Privado ERP."""

from typing import Any

from fastapi import APIRouter, Depends, Request
from src.domain.erp.ports import IErpGateway
from src.infrastructure.fastapi.dependencies import get_erp_gateway

router = APIRouter(prefix="/api/v1/xubio", tags=["Xubio Proxy Réplica"])


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


@router.post("/clienteBean")
async def replica_post_cliente(
    body: dict[str, Any], erp_gateway: IErpGateway = Depends(get_erp_gateway)
):
    """Réplica directa de POST /clienteBean de Xubio v1.1."""
    return await erp_gateway.proxy_request("POST", "/clienteBean", json_data=body)


@router.get("/presupuestoBean")
async def replica_get_presupuestos(
    request: Request, erp_gateway: IErpGateway = Depends(get_erp_gateway)
):
    """Réplica directa de GET /presupuestoBean de Xubio v1.1."""
    params = dict(request.query_params)
    return await erp_gateway.proxy_request("GET", "/presupuestoBean", params=params)


@router.post("/presupuestoBean")
async def replica_post_presupuesto(
    body: dict[str, Any], erp_gateway: IErpGateway = Depends(get_erp_gateway)
):
    """Réplica directa de POST /presupuestoBean de Xubio v1.1."""
    return await erp_gateway.proxy_request("POST", "/presupuestoBean", json_data=body)


@router.get("/productoStock")
async def replica_get_producto_stock(
    request: Request, erp_gateway: IErpGateway = Depends(get_erp_gateway)
):
    """Réplica directa de GET /productoStock de Xubio v1.1."""
    params = dict(request.query_params)
    return await erp_gateway.proxy_request("GET", "/productoStock", params=params)


@router.post("/facturar")
async def replica_post_facturar(
    body: dict[str, Any], erp_gateway: IErpGateway = Depends(get_erp_gateway)
):
    """Réplica directa de POST /facturar de Xubio v1.1."""
    return await erp_gateway.proxy_request("POST", "/facturar", json_data=body)
