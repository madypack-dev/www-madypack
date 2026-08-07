import base64
import time
from typing import Optional

import httpx

from src.domain.erp.entities import EmpresaERP, EstadoConexionERP
from src.domain.erp.ports import IErpGateway
from src.infrastructure.config import settings
from src.infrastructure.structlog.logger import get_logger

logger = get_logger()


class XubioErpGateway(IErpGateway):
    """Adaptador HTTP para la API v1.1 de Xubio.

    Sigue la interfaz de dominio IErpGateway y la arquitectura Hexagonal.
    Garantiza que NINGÚN secreto o token quede expuesto en los logs de observabilidad.
    """

    def __init__(
        self,
        client_id: Optional[str] = None,
        secret_id: Optional[str] = None,
        base_url: Optional[str] = None,
        client: Optional[httpx.AsyncClient] = None,
    ):
        self._client_id = client_id or settings.XUBIO_CLIENT_ID
        self._secret_id = secret_id or settings.XUBIO_SECRET_ID
        self._base_url = (base_url or settings.XUBIO_API_URL).rstrip("/")
        self._custom_client = client
        self._access_token: Optional[str] = None

    def _get_client(self) -> httpx.AsyncClient:
        return self._custom_client if self._custom_client else httpx.AsyncClient()

    def _build_basic_auth_header(self) -> str:
        credentials = f"{self._client_id}:{self._secret_id}"
        encoded = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
        return f"Basic {encoded}"

    async def obtener_token(self, force_refresh: bool = False) -> str:
        """Solicita o reutiliza el token de acceso de Xubio via OAuth2 client_credentials.

        Las credenciales NUNCA se registran en los logs.
        """
        if self._access_token and not force_refresh:
            return self._access_token

        token_url = f"{self._base_url}/TokenEndpoint"
        headers = {
            "Authorization": self._build_basic_auth_header(),
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = "scope=&grant_type=client_credentials"

        logger.info(
            "xubio.token.request",
            endpoint="/TokenEndpoint",
            client_id_configured=bool(self._client_id),
        )

        start_time = time.perf_counter()
        try:
            if self._custom_client:
                response = await self._custom_client.post(token_url, headers=headers, content=data)
            else:
                async with httpx.AsyncClient() as http:
                    response = await http.post(token_url, headers=headers, content=data)

            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

            if response.status_code == 200:
                body = response.json()
                token = body.get("access_token")
                if not token:
                    logger.error(
                        "xubio.token.error",
                        error="Respuesta 200 de Xubio sin access_token",
                        latency_ms=latency_ms,
                    )
                    raise ValueError("Respuesta de Xubio no contiene access_token")

                self._access_token = token
                logger.info(
                    "xubio.token.success",
                    status_code=200,
                    latency_ms=latency_ms,
                    token_obtained=True,
                )
                return self._access_token
            else:
                logger.error(
                    "xubio.token.failed",
                    status_code=response.status_code,
                    latency_ms=latency_ms,
                    error_summary="Fallo en autenticación con Xubio",
                )
                raise RuntimeError(f"Error {response.status_code} al solicitar token en Xubio")
        except Exception as exc:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                "xubio.token.exception",
                error_type=exc.__class__.__name__,
                latency_ms=latency_ms,
            )
            raise

    async def verificar_conexion(self) -> EstadoConexionERP:
        """Verifica la conexión solicitando el token y obteniendo los datos de la empresa."""
        logger.info("xubio.conexion.verificando")
        try:
            empresa = await self.obtener_datos_empresa()
            logger.info("xubio.conexion.exitosa", empresa_id=empresa.id)
            return EstadoConexionERP(
                activo=True,
                mensaje=f"Conectado a Xubio ({empresa.nombre})",
                proveedor="Xubio",
            )
        except Exception as exc:
            logger.error("xubio.conexion.fallida", error=str(exc))
            return EstadoConexionERP(
                activo=False,
                mensaje=f"Fallo de conexión a Xubio: {str(exc)}",
                proveedor="Xubio",
            )

    async def obtener_datos_empresa(self) -> EmpresaERP:
        """Invoca GET /miempresa para obtener el perfil de la empresa autenticada en Xubio."""
        token = await self.obtener_token()
        url = f"{self._base_url}/miempresa"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

        logger.info("xubio.api.request", endpoint="/miempresa", method="GET")

        start_time = time.perf_counter()
        try:
            if self._custom_client:
                response = await self._custom_client.get(url, headers=headers)
            else:
                async with httpx.AsyncClient() as http:
                    response = await http.get(url, headers=headers)

            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

            # Si el token expiró (401), reintentar una vez forzando refresh
            if response.status_code == 401:
                logger.warning(
                    "xubio.api.unauthorized_retry",
                    endpoint="/miempresa",
                    latency_ms=latency_ms,
                )
                token = await self.obtener_token(force_refresh=True)
                headers["Authorization"] = f"Bearer {token}"
                if self._custom_client:
                    response = await self._custom_client.get(url, headers=headers)
                else:
                    async with httpx.AsyncClient() as http:
                        response = await http.get(url, headers=headers)

            if response.status_code != 200:
                logger.error(
                    "xubio.api.error",
                    endpoint="/miempresa",
                    status_code=response.status_code,
                    latency_ms=latency_ms,
                )
                raise RuntimeError(f"Error {response.status_code} al obtener /miempresa de Xubio")

            data = response.json()
            logger.info(
                "xubio.api.success",
                endpoint="/miempresa",
                status_code=200,
                latency_ms=latency_ms,
            )

            # Extraer campos de respuesta sin exponer credenciales
            empresa_id = str(data.get("id", data.get("ID", "1")))
            nombre = data.get("nombre", data.get("razonSocial", data.get("nombreFantasia", "Empresa Xubio")))
            cuit = data.get("cuit", data.get("numeroIdentificacion"))
            email = data.get("email")

            return EmpresaERP(
                id=empresa_id,
                nombre=nombre,
                identificacion_tributaria=cuit,
                email=email,
            )
        except Exception as exc:
            logger.error("xubio.api.exception", endpoint="/miempresa", error_type=exc.__class__.__name__)
            raise
