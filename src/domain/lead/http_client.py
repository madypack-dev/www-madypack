from abc import ABC, abstractmethod
from typing import Any, Dict


class IHttpResponse(ABC):
    """Interfaz abstracta para la respuesta de un cliente HTTP."""

    @abstractmethod
    def json(self) -> Any:
        """Retorna el cuerpo de la respuesta parseado como JSON."""
        pass

    @abstractmethod
    def raise_for_status(self) -> None:
        """Lanza una excepción si el status code indica un error."""
        pass


class IHttpClient(ABC):
    """Interfaz abstracta para un cliente HTTP asíncrono."""

    @abstractmethod
    async def post(
        self,
        url: str,
        headers: Dict[str, str] | None = None,
        json: Any = None,
        timeout: float | None = None,
    ) -> IHttpResponse:
        """Realiza una petición POST asíncrona."""
        pass
