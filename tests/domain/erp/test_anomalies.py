"""Tests unitarios para el análisis de anomalías (Mediana + MAD) en src/domain/erp/anomalies.py."""

from src.domain.erp.anomalies import (
    analizar_anomalias_items,
    calcular_mad,
    calcular_mediana,
    normalizar_unidad_a_kg,
)


def test_calcular_mediana():
    assert calcular_mediana([10.0, 20.0, 30.0]) == 20.0
    assert calcular_mediana([10.0, 20.0, 30.0, 40.0]) == 25.0
    assert calcular_mediana([]) == 0.0


def test_calcular_mad():
    valores = [10.0, 12.0, 11.0, 15.0, 100.0]  # Mediana = 12.0
    mediana = calcular_mediana(valores)
    mad = calcular_mad(valores, mediana)
    assert mediana == 12.0
    assert mad == 2.0


def test_normalizar_unidad_a_kg():
    assert normalizar_unidad_a_kg(1500000.0, "tonelada") == 1500.0
    assert normalizar_unidad_a_kg(37500.0, "bobina_25kg") == 1500.0
    assert normalizar_unidad_a_kg(1500.0, "kg") == 1500.0


def test_analizar_anomalias_items_detecta_outliers_cero_y_falsos_negativos():
    muestra = [
        {"codigo": "bobina_kg", "precio": 1500.0, "unidad": "kg"},
        {"codigo": "bobina_kg", "precio": 1520.0, "unidad": "kg"},
        {"codigo": "bobina_kg", "precio": 1490.0, "unidad": "kg"},
        {"codigo": "bobina_kg_error", "precio": 150000.0, "unidad": "kg"},
        {"codigo": "BOBMAR100", "precio": 0.0, "unidad": "kg"},
        {"codigo": "kraft_rollo", "precio": 1510.0, "unidad": "kg"},
    ]

    reporte = analizar_anomalias_items(muestra, factor_k=2.5)

    assert reporte["mediana_ars_kg"] == 1510.0
    assert len(reporte["anomalias"]) == 2  # 1 outlier numérico + 1 precio $0.00
    codigos_anomalias = [a["codigo"] for a in reporte["anomalias"]]
    assert "bobina_kg_error" in codigos_anomalias
    assert "BOBMAR100" in codigos_anomalias
    assert len(reporte["falsos_negativos"]) == 1
    assert reporte["falsos_negativos"][0]["codigo"] == "kraft_rollo"
