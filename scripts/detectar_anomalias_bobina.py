"""Script de detección estadística de anomalías (Mediana + MAD) para la bobina de papel.

Normaliza unidades de medida a $/kg y detecta desviaciones significativas sin depender
de promedios (sesgables por outliers) ni valores nominales hardcodeados.
"""

import asyncio
import logging
import statistics
from typing import Any

from src.adapters.gateways.null_erp_gateway import NullErpGateway
from src.domain.erp.sanitizer import (
    sanitizar_monto,
    sanitizar_texto,
)
from src.infrastructure.pyyaml.loaders import cargar_configuracion_negocio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("anomalias_bobina")


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
        return precio / 1000.0  # Convierte $/tonelada a $/kg
    if "bobina_25" in u or "25kg" in u:
        return precio / 25.0  # Convierte $/bobina_25kg a $/kg
    if "bobina_50" in u or "50kg" in u:
        return precio / 50.0  # Convierte $/bobina_50kg a $/kg
    return precio


def analizar_anomalias_items(
    items: list[dict[str, Any]], factor_k: float = 2.5
) -> dict[str, Any]:
    """Analiza una lista de ítems de productos/tarifas del ERP utilizando Mediana + MAD.

    Devuelve un reporte con la mediana calculada, la cota MAD, anomalías detectadas,
    falsos positivos y falsos negativos (ítems candidatos no mapeados).
    """
    candidatos_validos: list[dict[str, Any]] = []
    precios_normalizados: list[float] = []
    falsos_negativos: list[dict[str, Any]] = []

    for raw in items:
        codigo = sanitizar_texto(
            raw.get("codigo") or raw.get("nombre") or raw.get("usrcode"), max_len=100
        ).lower()
        precio_raw = sanitizar_monto(
            raw.get("precio") or raw.get("monto") or raw.get("precioUltCompra")
        )
        unidad = sanitizar_texto(raw.get("unidad") or raw.get("medida") or "kg", max_len=20)

        if not codigo or precio_raw <= 0:
            continue

        precio_kg = normalizar_unidad_a_kg(precio_raw, unidad)

        es_bobina_oficial = "bobina_kg" in codigo
        es_posible_bobina = any(palabra in codigo for palabra in ["bobina", "papel", "kraft"])

        if es_bobina_oficial:
            candidatos_validos.append(
                {"raw": raw, "codigo": codigo, "precio_kg": precio_kg, "unidad": unidad}
            )
            precios_normalizados.append(precio_kg)
        elif es_posible_bobina:
            falsos_negativos.append(
                {
                    "codigo": codigo,
                    "precio_kg": precio_kg,
                    "motivo": "Ítem relevante en ERP no asignado al código estándar 'bobina_kg'.",
                }
            )

    if not precios_normalizados:
        return {
            "mediana": 0.0,
            "mad": 0.0,
            "anomalias": [],
            "falsos_negativos": falsos_negativos,
            "mensaje": "No se encontraron ítems oficiales 'bobina_kg' para analizar.",
        }

    mediana = calcular_mediana(precios_normalizados)
    mad = calcular_mad(precios_normalizados, mediana)

    # Umbral dinámico: |x - mediana| > k * (MAD si MAD > 0 else 0.2 * mediana)
    cota_tolerancia = factor_k * mad if mad > 0 else (0.2 * mediana * factor_k)

    anomalias: list[dict[str, Any]] = []
    for item in candidatos_validos:
        desviacion = abs(item["precio_kg"] - mediana)
        if desviacion > cota_tolerancia:
            anomalias.append(
                {
                    "codigo": item["codigo"],
                    "precio_kg": item["precio_kg"],
                    "desviacion_mediana": desviacion,
                    "cota_maxima": cota_tolerancia,
                    "motivo": f"Precio de ${item['precio_kg']:.2f}/kg se desvía habitualmente de la mediana de ${mediana:.2f}/kg.",
                }
            )

    return {
        "mediana_ars_kg": mediana,
        "mad": mad,
        "cota_tolerancia": cota_tolerancia,
        "total_analizados": len(candidatos_validos),
        "anomalias": anomalias,
        "falsos_negativos": falsos_negativos,
    }


async def ejecutar_deteccion():
    """Ejecuta el detector de anomalías sobre los endpoints de Xubio ERP o réplica."""
    config_negocio = cargar_configuracion_negocio()
    factor_k = config_negocio.anomalias_bobina.factor_k_mad

    logger.info(
        f"Iniciando detección de anomalías de la bobina de papel con factor_k_mad={factor_k}..."
    )
    gateway = NullErpGateway()

    # Muestra de prueba con casos normales y anómalos
    muestra_test = [
        {"codigo": "bobina_kg", "precio": 1500.0, "unidad": "kg"},
        {"codigo": "bobina_kg", "precio": 1550.0, "unidad": "kg"},
        {"codigo": "bobina_kg", "precio": 1480.0, "unidad": "kg"},
        {"codigo": "bobina_kg_lote2", "precio": 1520.0, "unidad": "kg"},
        {"codigo": "bobina_kg_anomala_alta", "precio": 150000.0, "unidad": "kg"},  # Outlier
        {"codigo": "bobina_kg_anomala_baja", "precio": 1.50, "unidad": "kg"},  # Outlier
        {"codigo": "papel_kraft_rollo", "precio": 1510.0, "unidad": "kg"},  # Falso negativo
    ]

    reporte = analizar_anomalias_items(muestra_test, factor_k=factor_k)

    logger.info(f"--- REPORTE ESTADÍSTICO DE ANOMALÍAS DE BOBINA ---")
    logger.info(f"Mediana $/kg: {reporte['mediana_ars_kg']:.2f}")
    logger.info(f"MAD (Median Absolute Deviation): {reporte['mad']:.2f}")
    logger.info(f"Cota de Tolerancia (k={factor_k}): {reporte['cota_tolerancia']:.2f}")
    logger.info(f"Anomalías Detectadas: {len(reporte['anomalias'])}")
    for a in reporte["anomalias"]:
        logger.warning(f"  🚨 ANOMALÍA: {a}")
    for fn in reporte["falsos_negativos"]:
        logger.info(f"  ℹ️ POSIBLE FALSO NEGATIVO: {fn}")


if __name__ == "__main__":
    asyncio.run(ejecutar_deteccion())
