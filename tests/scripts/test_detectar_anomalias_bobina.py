"""Tests unitarios para el script de detección estadística de anomalías de bobina de papel."""

from scripts.detectar_anomalias_bobina import (
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
    assert mad == 2.0  # |10-12|=2, |12-12|=0, |11-12|=1, |15-12|=3, |100-12|=88 -> mediana([2,0,1,3,88]) = 2.0


def test_normalizar_unidad_a_kg():
    assert normalizar_unidad_a_kg(1500000.0, "tonelada") == 1500.0
    assert normalizar_unidad_a_kg(37500.0, "bobina_25kg") == 1500.0
    assert normalizar_unidad_a_kg(1500.0, "kg") == 1500.0


def test_analizar_anomalias_items_detecta_outliers_y_falsos_negativos():
    muestra = [
        {"codigo": "bobina_kg", "precio": 1500.0, "unidad": "kg"},
        {"codigo": "bobina_kg", "precio": 1520.0, "unidad": "kg"},
        {"codigo": "bobina_kg", "precio": 1490.0, "unidad": "kg"},
        {"codigo": "bobina_kg_error", "precio": 150000.0, "unidad": "kg"},
        {"codigo": "kraft_rollo", "precio": 1510.0, "unidad": "kg"},
    ]

    reporte = analizar_anomalias_items(muestra, factor_k=2.5)

    assert reporte["mediana_ars_kg"] == 1510.0
    assert len(reporte["anomalias"]) == 1
    assert reporte["anomalias"][0]["codigo"] == "bobina_kg_error"
    assert len(reporte["falsos_negativos"]) == 1
    assert reporte["falsos_negativos"][0]["codigo"] == "kraft_rollo"
