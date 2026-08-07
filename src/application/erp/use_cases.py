from src.domain.erp.entities import EmpresaERP, EstadoConexionERP
from src.domain.erp.ports import IErpGateway


class CasoUsoVerificarConexionERP:
    """Caso de uso para verificar el estado y conectividad con el ERP configurado."""

    def __init__(self, erp_gateway: IErpGateway):
        self._erp_gateway = erp_gateway

    async def ejecutar(self) -> EstadoConexionERP:
        return await self._erp_gateway.verificar_conexion()


class CasoUsoObtenerEmpresaERP:
    """Caso de uso para consultar los datos institucionales de la empresa en el ERP."""

    def __init__(self, erp_gateway: IErpGateway):
        self._erp_gateway = erp_gateway

    async def ejecutar(self) -> EmpresaERP:
        return await self._erp_gateway.obtener_datos_empresa()
