"""Resolución de tenant a partir del subdominio y puerto de la petición.

Soporta tres entornos:
- Desarrollo local: se distingue por puerto (8000 default, 8001 madypack, etc.)
- Staging: subdominios bajo datamaq.com.ar (madypack.datamaq.com.ar)
- Producción: dominios propios (madypack.com.ar)
"""

from fastapi import Request

from src.infraestructura.config import (
    MAPEO_PUERTOS,
    MAPEO_TENANTS,
    FALLBACK_TENANT,
    PATRON_EMPRESA,
)


def _extraer_host_puerto(host_header: str) -> tuple[str, str | None]:
    """Separa el host del puerto si viene en el header Host."""
    if ":" in host_header:
        host, port = host_header.rsplit(":", 1)
        return host.lower(), port
    return host_header.lower(), None


def resolutor_tenant(request: Request) -> str:
    """Devuelve el identificador de tenant según el header Host de la petición.

    El orden de resolución es:
    1. Puerto (desarrollo local).
    2. Mapeo explícito de dominio.
    3. Inferencia por patrón empresa-N.
    4. Fallback ``default``.
    """
    host_header = request.headers.get("host", "localhost")
    host, port = _extraer_host_puerto(host_header)

    # 1. Desarrollo local: el puerto define el tenant.
    if port is not None and port in MAPEO_PUERTOS:
        return MAPEO_PUERTOS[port]

    # 2. Mapeo explícito de dominio.
    if host in MAPEO_TENANTS:
        return MAPEO_TENANTS[host]

    # 3. Inferencia por patrón empresa-N (staging/producción).
    match = PATRON_EMPRESA.match(host)
    if match:
        return match.group(1)

    return FALLBACK_TENANT
