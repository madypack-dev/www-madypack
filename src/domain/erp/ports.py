from abc import ABC, abstractmethod

from src.domain.erp.entities import EmpresaERP, EstadoConexionERP


class IErpGateway(ABC):
    """Puerto de dominio (Interface) para comunicarse con cualquier ERP (Xubio, Tango, SAP, etc.).

    Sigue el principio de Inversión de Dependencias (DIP) y Segregación de Interfaces (ISP).
    """

    @abstractmethod
    async def verificar_conexion(self) -> EstadoConexionERP:
        """Verifica la conectividad y estado de sesión con el ERP."""
        pass

    @abstractmethod
    async def obtener_datos_empresa(self) -> EmpresaERP:
        """Obtiene la información institucional de la empresa desde el ERP."""
        pass

    async def proxy_request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        json_data: dict | None = None,
    ) -> dict | list:
        """Realiza forwarding de peticiones hacia el ERP si el proveedor lo soporta."""
        raise NotImplementedError("El proveedor actual no soporta proxy_request")
