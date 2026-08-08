"""Análisis estadístico y detección de anomalías para insumos de ERP (Mediana + MAD).

Dominio puro (src/domain/erp/anomalies.py) sin dependencias externas ni de frameworks.
"""

import statistics
from typing import Any

from src.domain.erp.sanitizer import (
    sanitizar_monto,
    sanitizar_texto,
)


def calcular_mediana(valores: list[float]) -> float:
    """Calcula la mediana estadística de una lista de valores flotantes."""
    if not valores:
        return 0.0
    return float(statistics.median(valores))


def calcular_mad(valores: list[float], mediana: float | None = None) -> float:
    """Calcula la Desviación Absoluta de la Mediana (MAD = Median Absolute Deviation)."""
    if not valores:
        return 0.0
    med = mediana if mediana is not None else calcular_mediana(valores)
    desviaciones = [abs(x - med) for x in valores]
    return calcular_mediana(desviaciones)


def normalizar_unidad_a_kg(precio: float, unidad_str: str) -> float:
    """Normaliza un costo a la unidad de medida estándar $/kg."""
    u = unidad_str.lower().strip()
    if "ton" in u or "tn" in u:
        return precio / 1000.0
    if "bobina_25" in u or "25kg" in u:
        return precio / 25.0
    if "bobina_50" in u or "50kg" in u:
        return precio / 50.0
    return precio


def _procesar_candidato(raw: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Clasifica un ítem crudo como candidato válido de bobina o falso negativo."""
    raw_cod = raw.get("codigo") or raw.get("nombre") or raw.get("usrcode")
    codigo = sanitizar_texto(raw_cod, max_len=100).lower()
    precio_raw = sanitizar_monto(
        raw.get("precio") or raw.get("monto") or raw.get("precioUltCompra")
    )
    unidad = sanitizar_texto(raw.get("unidad") or raw.get("medida") or "kg", max_len=20)

    if not codigo or precio_raw <= 0:
        return None, None

    precio_kg = normalizar_unidad_a_kg(precio_raw, unidad)
    es_bobina_oficial = "bobina_kg" in codigo or "bobmar100" in codigo
    es_posible_bobina = any(palabra in codigo for palabra in ["bobina", "papel", "kraft"])

    if es_bobina_oficial:
        return {"raw": raw, "codigo": codigo, "precio_kg": precio_kg, "unidad": unidad}, None
    if es_posible_bobina:
        return None, {
            "codigo": codigo,
            "precio_kg": precio_kg,
            "motivo": "Ítem relevante en ERP no asignado al código estándar 'bobina_kg'.",
        }
    return None, None


def analizar_anomalias_items(
    items: list[dict[str, Any]], factor_k: float = 2.5
) -> dict[str, Any]:
    """Analiza una lista de ítems de productos del ERP utilizando Mediana + MAD."""
    candidatos_validos: list[dict[str, Any]] = []
    precios_normalizados: list[float] = []
    falsos_negativos: list[dict[str, Any]] = []

    for raw in items:
        cand, fn = _procesar_candidato(raw)
        if cand:
            candidatos_validos.append(cand)
            precios_normalizados.append(cand["precio_kg"])
        elif fn:
            falsos_negativos.append(fn)

    if not precios_normalizados:
        return {
            "mediana_ars_kg": 0.0,
            "mad": 0.0,
            "cota_tolerancia": 0.0,
            "total_analizados": 0,
            "anomalias": [],
            "falsos_negativos": falsos_negativos,
            "mensaje": "No se encontraron ítems oficiales 'bobina_kg' para analizar.",
        }

    mediana = calcular_mediana(precios_normalizados)
    mad = calcular_mad(precios_normalizados, mediana)
    cota = factor_k * mad if mad > 0 else (0.2 * mediana * factor_k)

    anomalias = [
        {
            "codigo": i["codigo"],
            "precio_kg": i["precio_kg"],
            "desviacion_mediana": abs(i["precio_kg"] - mediana),
            "cota_maxima": cota,
            "motivo": f"Precio de ${i['precio_kg']:.2f}/kg se desvía de la mediana de ${mediana:.2f}/kg.",
        }
        for i in candidatos_validos
        if abs(i["precio_kg"] - mediana) > cota
    ]

    return {
        "mediana_ars_kg": mediana,
        "mad": mad,
        "cota_tolerancia": cota,
        "total_analizados": len(candidatos_validos),
        "anomalias": anomalias,
        "falsos_negativos": falsos_negativos,
    }
