"""Utilidades para la resolución de archivos estáticos por tenant."""

from pathlib import Path


STATIC_DIR = Path(__file__).resolve().parents[2] / "static"


def resolver_archivo_estatico(tenant: str, relative_path: str) -> Path | None:
    """Busca un archivo estático primero en el tenant y luego en la base.

    Devuelve None si no se encuentra o si el path intenta salir de STATIC_DIR.
    """
    relative_path = relative_path.lstrip("/")
    if ".." in relative_path:
        return None

    candidates = [
        STATIC_DIR / "tenants" / tenant / relative_path,
        STATIC_DIR / relative_path,
    ]

    static_root = STATIC_DIR.resolve()
    for candidate in candidates:
        try:
            full_path = candidate.resolve()
        except (OSError, RuntimeError):
            continue
        if not str(full_path).startswith(str(static_root)):
            continue
        if full_path.is_file():
            return full_path
    return None
