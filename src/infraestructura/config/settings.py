"""Configuración centralizada de la aplicación.

Las variables sensibles o específicas del entorno se leen desde variables de
entorno. Los valores por defecto corresponden al entorno de desarrollo local.
"""

import os
import re

APP_TITLE: str = os.getenv("APP_TITLE", "Ecommerce")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

# Tenant por defecto cuando no se puede resolver otro.
FALLBACK_TENANT: str = os.getenv("FALLBACK_TENANT", "default")

# Mapeo explícito de dominios a tenant.
# Formato esperado en la variable de entorno:
#   DOMINIO1=tenant1,DOMINIO2=tenant2
_env_tenants = os.getenv("MAPEO_TENANTS", "")
MAPEO_TENANTS: dict[str, str] = {
    "www.madypack.com.ar": "madypack",
    "madypack.com.ar": "madypack",
}
if _env_tenants:
    for par in _env_tenants.split(","):
        if "=" in par:
            dominio, tenant = par.split("=", 1)
            MAPEO_TENANTS[dominio.strip()] = tenant.strip()

# Mapeo de puertos para desarrollo local.
# Formato esperado en la variable de entorno:
#   PUERTO1=tenant1,PUERTO2=tenant2
_env_puertos = os.getenv("MAPEO_PUERTOS", "")
MAPEO_PUERTOS: dict[str, str] = {
    "8000": "default",
    "8001": "madypack",
    "8002": "eitec",
    "8003": "upp",
    "8004": "plasticoselgringo",
}
if _env_puertos:
    for par in _env_puertos.split(","):
        if "=" in par:
            puerto, tenant = par.split("=", 1)
            MAPEO_PUERTOS[puerto.strip()] = tenant.strip()

# Mapeo inverso: tenant -> puerto de desarrollo.
MAPEO_TENANT_PUERTO: dict[str, str] = {
    tenant: puerto for puerto, tenant in MAPEO_PUERTOS.items()
}

# Patrón para inferir tenants del tipo empresa-N en staging/producción.
PATRON_EMPRESA = re.compile(r"^(empresa-\d+)(?:\.datamaq\.com\.ar|\.com\.ar)?$")
