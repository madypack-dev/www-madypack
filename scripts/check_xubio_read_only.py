"""Guardia de Arquitectura Estática (AST) para verificar el cumplimiento estricto de SOLO LECTURA (GET únicamente) en Xubio ERP."""

import ast
import sys
from pathlib import Path

METODOS_PROHIBIDOS = {"post", "put", "delete", "patch"}


def _es_llamada_prohibida(node: ast.AST) -> str | None:
    """Inspecciona un nodo AST y devuelve el nombre del método prohibido si detecta una infracción."""
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
        return None

    if node.func.attr == "proxy_request" and node.args:
        metodo_arg = node.args[0]
        if isinstance(metodo_arg, ast.Constant) and isinstance(metodo_arg.value, str):
            metodo = metodo_arg.value.lower()
            if metodo in METODOS_PROHIBIDOS:
                return metodo
    return None


def _analizar_archivo(archivo: Path) -> list[str]:
    """Analiza un único archivo Python y devuelve la lista de violaciones encontradas."""
    violaciones = []
    try:
        tree = ast.parse(archivo.read_text(encoding="utf-8"), filename=str(archivo))
    except Exception as exc:
        print(f"❌ Error analizando {archivo}: {exc}")
        return violaciones

    for node in ast.walk(tree):
        metodo = _es_llamada_prohibida(node)
        if metodo and hasattr(node, "lineno"):
            violaciones.append(
                f"{archivo}:{node.lineno} -> Llamada proxy_request con método prohibido '{metodo.upper()}'"
            )

    return violaciones


def verificar_solo_lectura_xubio(archivos: list[Path]) -> bool:
    """Escanea los archivos indicados y valida la prohibición de métodos de escritura en Xubio."""
    violaciones = []
    for archivo in archivos:
        violaciones.extend(_analizar_archivo(archivo))

    if violaciones:
        print("❌ [GUARDIA AST READ-ONLY] SE DETECTARON VIOLACIONES DE SOLO LECTURA EN XUBIO:")
        for v in violaciones:
            print(f"   🚨 {v}")
        return False

    print(
        "👑 [GUARDIA AST READ-ONLY] Sin violaciones. Toda la integración con Xubio ERP es 100% READ-ONLY (GET)."
    )
    return True


if __name__ == "__main__":
    archivos_a_escanear = [
        Path("src/adapters/gateways/xubio_client.py"),
        Path("src/adapters/gateways/proveedor_tarifas_xubio.py"),
        Path("src/infrastructure/fastapi/routes/xubio_replica.py"),
        Path("scripts/auditar_datos_xubio.py"),
    ]
    existentes = [f for f in archivos_a_escanear if f.exists()]
    if not verificar_solo_lectura_xubio(existentes):
        sys.exit(1)
