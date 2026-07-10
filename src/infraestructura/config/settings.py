"""Configuración centralizada de la aplicación Madypack.

Las variables sensibles o específicas del entorno se leen desde variables de
entorno. Los valores por defecto corresponden al entorno de desarrollo local.
"""

import os
import re
from typing import Any

from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Configuración validada con Pydantic."""

    APP_TITLE: str = Field(default_factory=lambda: os.getenv("APP_TITLE", "Madypack"))
    LOG_LEVEL: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    CHATWOOT_URL: str = Field(default_factory=lambda: os.getenv("CHATWOOT_URL", "http://localhost:3000"))
    CHATWOOT_ACCOUNT_ID: int = Field(default_factory=lambda: int(os.getenv("CHATWOOT_ACCOUNT_ID", "1")))
    CHATWOOT_INBOX_ID: int = Field(default_factory=lambda: int(os.getenv("CHATWOOT_INBOX_ID", "1")))
    CHATWOOT_API_TOKEN: str = Field(default_factory=lambda: os.getenv("CHATWOOT_API_TOKEN", ""))


_settings = Settings()

APP_TITLE: str = _settings.APP_TITLE
LOG_LEVEL: str = _settings.LOG_LEVEL
CHATWOOT_URL: str = _settings.CHATWOOT_URL
CHATWOOT_ACCOUNT_ID: int = _settings.CHATWOOT_ACCOUNT_ID
CHATWOOT_INBOX_ID: int = _settings.CHATWOOT_INBOX_ID
CHATWOOT_API_TOKEN: str = _settings.CHATWOOT_API_TOKEN

# Variables de compatibilidad para evitar roturas de imports
FALLBACK_TENANT: str = "madypack"
MAPEO_TENANTS: dict[str, str] = {"madypack.com.ar": "madypack", "www.madypack.com.ar": "madypack"}
MAPEO_PUERTOS: dict[str, str] = {"8000": "madypack", "8001": "madypack"}
MAPEO_TENANT_PUERTO: dict[str, str] = {"madypack": "8000"}
PATRON_EMPRESA: re.Pattern = re.compile(r"^()$")
