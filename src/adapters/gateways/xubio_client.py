import base64
import time
from typing import Any

from src.domain.erp.entities import EmpresaERP, EstadoConexionERP
from src.domain.erp.ports import IErpGateway
from src.domain.lead.http_client import IHttpClient


class _DummyLogger:
    def info(self, *args, **kwargs):
        _ = (args, kwargs)

    def warning(self, *args, **kwargs):
        _ = (args, kwargs)

    def error(self, *args, **kwargs):
        _ = (args, kwargs)


class _LoggerAdapter:
    """Adapta loggers de stdlib (logging.Logger) o structlog a la interfaz estructurada."""

    def __init__(self, target_logger: Any):
        self._target = target_logger or _DummyLogger()

    def info(self, event: str, **kwargs: Any) -> None:
        self._log("info", event, kwargs)

    def warning(self, event: str, **kwargs: Any) -> None:
        self._log("warning", event, kwargs)

    def error(self, event: str, **kwargs: Any) -> None:
        self._log("error", event, kwargs)

    def _log(self, level: str, event: str, kwargs: dict[str, Any]) -> None:
        method = getattr(self._target, level, None)
        if not method:
            return
        try:
            method(event, **kwargs)
        except TypeError:
            extra_str = " ".join(f"{k}={v}" for k, v in kwargs.items())
            msg = f"{event} {extra_str}".strip() if extra_str else event
            method(msg)


class XubioErpGateway(IErpGateway):
    """Adaptador HTTP para la API v1.1 de Xubio.

    Sigue la interfaz de dominio IErpGateway y la arquitectura Hexagonal.
    No depende de la capa de infraestructura ni de httpx directamente.
    Consume la interfaz de dominio IHttpClient.
    Garantiza que NINGÚN secreto o token quede expuesto en los logs de observabilidad.
    """

    def __init__(
        self,
        client: IHttpClient,
        client_id: str = "",
        secret_id: str = "",  # nosec B107
        base_url: str = "https://xubio.com/API/1.1",
        logger: Any = None,
    ):
        self._client = client
        self._client_id = client_id
        self._secret_id = secret_id
        self._base_url = (base_url or "https://xubio.com/API/1.1").rstrip("/")
        self._logger = _LoggerAdapter(logger)
        self._access_token: str | None = None


    def _build_basic_auth_header(self) -> str:
        credentials = f"{self._client_id}:{self._secret_id}"
        encoded = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
        return f"Basic {encoded}"

    async def obtener_token(self, force_refresh: bool = False) -> str:
        """Solicita o reutiliza el token de acceso de Xubio via OAuth2 client_credentials."""
        if self._access_token is not None and not force_refresh:
            return self._access_token

        token_url = f"{self._base_url}/TokenEndpoint"
        headers = {
            "Authorization": self._build_basic_auth_header(),
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = "scope=&grant_type=client_credentials"

        self._logger.info(
            "xubio.token.request",
            endpoint="/TokenEndpoint",
            client_id_configured=bool(self._client_id),
        )

        start_time = time.perf_counter()
        try:
            response = await self._client.post(token_url, headers=headers, content=data)
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

            if response.status_code == 200:
                body = response.json()
                token = body.get("access_token")
                if not token:
                    self._logger.error(
                        "xubio.token.error",
                        error="Respuesta 200 de Xubio sin access_token",
                        latency_ms=latency_ms,
                    )
                    raise ValueError("Respuesta de Xubio no contiene access_token")

                token_str = str(token)
                self._access_token = token_str
                self._logger.info(
                    "xubio.token.success",
                    status_code=200,
                    latency_ms=latency_ms,
                    token_obtained=True,
                )
                return token_str
            else:
                self._logger.error(
                    "xubio.token.failed",
                    status_code=response.status_code,
                    latency_ms=latency_ms,
                    error_summary="Fallo en autenticación con Xubio",
                )
                raise RuntimeError(f"Error {response.status_code} al solicitar token en Xubio")
        except Exception as exc:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            self._logger.error(
                "xubio.token.exception",
                error_type=exc.__class__.__name__,
                latency_ms=latency_ms,
            )
            raise

    async def verificar_conexion(self) -> EstadoConexionERP:
        """Verifica la conexión solicitando el token y obteniendo los datos de la empresa."""
        self._logger.info("xubio.conexion.verificando")
        try:
            empresa = await self.obtener_datos_empresa()
            self._logger.info("xubio.conexion.exitosa", empresa_id=empresa.id)
            return EstadoConexionERP(
                activo=True,
                mensaje=f"Conectado a Xubio ({empresa.nombre})",
                proveedor="Xubio",
            )
        except Exception as exc:
            self._logger.error("xubio.conexion.fallida", error=str(exc))
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
            "token": token,
            "Accept": "application/json",
        }

        self._logger.info("xubio.api.request", endpoint="/miempresa", method="GET")

        start_time = time.perf_counter()
        try:
            response = await self._client.get(url, headers=headers)
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

            if response.status_code == 401:
                self._logger.warning(
                    "xubio.api.unauthorized_retry",
                    endpoint="/miempresa",
                    latency_ms=latency_ms,
                )
                token = await self.obtener_token(force_refresh=True)
                headers["Authorization"] = f"Bearer {token}"
                response = await self._client.get(url, headers=headers)

            if response.status_code != 200:
                self._logger.error(
                    "xubio.api.error",
                    endpoint="/miempresa",
                    status_code=response.status_code,
                    latency_ms=latency_ms,
                )
                raise RuntimeError(f"Error {response.status_code} al obtener /miempresa de Xubio")

            data = response.json()
            self._logger.info(
                "xubio.api.success",
                endpoint="/miempresa",
                status_code=200,
                latency_ms=latency_ms,
            )

            empresa_id = str(data.get("id", data.get("ID", "1")))
            nombre = data.get(
                "nombre", data.get("razonSocial", data.get("nombreFantasia", "Empresa Xubio"))
            )
            cuit = data.get("cuit", data.get("numeroIdentificacion"))
            email = data.get("email")

            return EmpresaERP(
                id=empresa_id,
                nombre=nombre,
                identificacion_tributaria=cuit,
                email=email,
            )
        except Exception as exc:
            self._logger.error(
                "xubio.api.exception", endpoint="/miempresa", error_type=exc.__class__.__name__
            )
            raise

    async def proxy_request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        json_data: dict | None = None,
    ) -> dict | list:
        """Forwarding directo de un endpoint Xubio v1.1 con autenticación y sanitización."""
        token = await self.obtener_token()
        path_clean = f"/{path.lstrip('/')}"
        url = f"{self._base_url}{path_clean}"
        headers = {
            "Authorization": f"Bearer {token}",
            "token": token,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        self._logger.info("xubio.proxy.request", method=method, endpoint=path_clean)

        start_time = time.perf_counter()
        try:
            response = await self._client.request(
                method=method, url=url, headers=headers, params=params, json=json_data
            )
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

            if response.status_code == 401:
                self._logger.warning(
                    "xubio.proxy.unauthorized_retry", endpoint=path_clean, latency_ms=latency_ms
                )
                token = await self.obtener_token(force_refresh=True)
                headers["Authorization"] = f"Bearer {token}"
                response = await self._client.request(
                    method=method, url=url, headers=headers, params=params, json=json_data
                )

            self._logger.info(
                "xubio.proxy.response", status_code=response.status_code, latency_ms=latency_ms
            )
            if response.status_code >= 400:
                raise RuntimeError(f"Error {response.status_code} desde Xubio en {path_clean}")

            return response.json()
        except Exception as exc:
            self._logger.error(
                "xubio.proxy.exception", endpoint=path_clean, error_type=exc.__class__.__name__
            )
            raise
