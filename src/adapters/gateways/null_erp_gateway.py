from src.domain.erp.entities import EmpresaERP, EstadoConexionERP
from src.domain.erp.ports import IErpGateway


class NullErpGateway(IErpGateway):
    """Adaptador Nulo (Null Object Pattern) para el gateway de ERP.

    Se utiliza para desarrollo local, desacoplamiento y testing sin dependencias de red.
    """

    async def verificar_conexion(self) -> EstadoConexionERP:
        return EstadoConexionERP(
            activo=True,
            mensaje="Null ERP Gateway activo (Modo Desacoplado / Test)",
            proveedor="NullERP",
        )

    async def obtener_datos_empresa(self) -> EmpresaERP:
        return EmpresaERP(
            id="0",
            nombre="Empresa Dummy Madypack",
            identificacion_tributaria="30-00000000-0",
            email="contacto@madypack.local",
        )

    async def proxy_request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        json_data: dict | None = None,
    ) -> dict | list:
        _ = (method, params)
        return {"status": "ok", "mock": True, "path": path, "body": json_data}
