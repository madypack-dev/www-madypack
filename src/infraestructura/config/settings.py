"""Configuración centralizada de la aplicación.

Las variables sensibles o específicas del entorno se leen desde variables de
entorno. Los valores por defecto corresponden al entorno de desarrollo local.
"""

import os
import re
from typing import Any

from pydantic import BaseModel, Field, computed_field, field_validator


def _parsear_mapeo(valor: Any) -> dict[str, str]:
    """Parsea un string tipo 'CLAVE1=val1,CLAVE2=val2' a un diccionario."""
    if isinstance(valor, dict):
        return {str(k).strip(): str(v).strip() for k, v in valor.items()}

    resultado: dict[str, str] = {}
    if not valor:
        return resultado

    for par in str(valor).split(","):
        if "=" not in par:
            continue
        clave, val = par.split("=", 1)
        clave = clave.strip()
        val = val.strip()
        if clave and val:
            resultado[clave] = val
    return resultado


class Settings(BaseModel):
    """Configuración validada con Pydantic."""

    APP_TITLE: str = Field(default_factory=lambda: os.getenv("APP_TITLE", "Ecommerce"))
    LOG_LEVEL: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    FALLBACK_TENANT: str = Field(default_factory=lambda: os.getenv("FALLBACK_TENANT", "default"))
    CHATWOOT_URL: str = Field(default_factory=lambda: os.getenv("CHATWOOT_URL", "https://chatwoot.com"))
    CHATWOOT_ACCOUNT_ID: int = Field(default_factory=lambda: int(os.getenv("CHATWOOT_ACCOUNT_ID", "1")))
    CHATWOOT_INBOX_ID: int = Field(default_factory=lambda: int(os.getenv("CHATWOOT_INBOX_ID", "1")))
    CHATWOOT_API_TOKEN: str = Field(default_factory=lambda: os.getenv("CHATWOOT_API_TOKEN", ""))

    MAPEO_TENANTS: dict[str, str] = Field(
        default_factory=lambda: {
            "www.madypack.com.ar": "madypack",
            "madypack.com.ar": "madypack",
        }
    )
    MAPEO_PUERTOS: dict[str, str] = Field(
        default_factory=lambda: {
            "8000": "default",
            "8001": "madypack",
            "8002": "eitec",
            "8003": "upp",
            "8004": "plasticoselgringo",
        }
    )

    PATRON_EMPRESA: re.Pattern = Field(
        default=re.compile(r"^(empresa-\d+)(?:\.datamaq\.com\.ar|\.com\.ar)?$")
    )

    @field_validator("MAPEO_TENANTS", "MAPEO_PUERTOS", mode="before")
    @classmethod
    def _validar_mapeo(cls, valor: Any) -> dict[str, str]:
        return _parsear_mapeo(valor)

    def model_post_init(self, __context: Any) -> None:
        """Mergea variables de entorno con los valores por defecto."""
        env_tenants = _parsear_mapeo(os.getenv("MAPEO_TENANTS"))
        env_puertos = _parsear_mapeo(os.getenv("MAPEO_PUERTOS"))
        self.MAPEO_TENANTS = {**self.MAPEO_TENANTS, **env_tenants}
        self.MAPEO_PUERTOS = {**self.MAPEO_PUERTOS, **env_puertos}

    @computed_field
    @property
    def MAPEO_TENANT_PUERTO(self) -> dict[str, str]:
        """Mapeo inverso: tenant -> puerto de desarrollo."""
        return {tenant: puerto for puerto, tenant in self.MAPEO_PUERTOS.items()}


# Instancia única exportada para mantener compatibilidad con el resto de la app.
_settings = Settings()

APP_TITLE: str = _settings.APP_TITLE
LOG_LEVEL: str = _settings.LOG_LEVEL
FALLBACK_TENANT: str = _settings.FALLBACK_TENANT
MAPEO_TENANTS: dict[str, str] = _settings.MAPEO_TENANTS
MAPEO_PUERTOS: dict[str, str] = _settings.MAPEO_PUERTOS
MAPEO_TENANT_PUERTO: dict[str, str] = _settings.MAPEO_TENANT_PUERTO
PATRON_EMPRESA: re.Pattern = _settings.PATRON_EMPRESA
CHATWOOT_URL: str = _settings.CHATWOOT_URL
CHATWOOT_ACCOUNT_ID: int = _settings.CHATWOOT_ACCOUNT_ID
CHATWOOT_INBOX_ID: int = _settings.CHATWOOT_INBOX_ID
CHATWOOT_API_TOKEN: str = _settings.CHATWOOT_API_TOKEN
