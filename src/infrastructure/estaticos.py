"""Utilidades para la resolución de archivos estáticos."""

from pathlib import Path


STATIC_DIR = Path(__file__).resolve().parents[2] / "static"


def resolver_archivo_estatico(relative_path: str) -> Path | None:
    """Busca un archivo estático en la carpeta base ``static/``.

    Devuelve None si no se encuentra o si el path intenta salir de
    STATIC_DIR.
    """
    relative_path = relative_path.lstrip("/")
    if ".." in relative_path:
        return None

    candidate = STATIC_DIR / relative_path
    static_root = STATIC_DIR.resolve()
    try:
        full_path = candidate.resolve()
    except (OSError, RuntimeError):
        return None

    if not str(full_path).startswith(str(static_root)):
        return None

    if full_path.is_file():
        return full_path
    return None
