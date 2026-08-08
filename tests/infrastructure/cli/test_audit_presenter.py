"""Tests unitarios para los componentes de presentación CLI en src/infrastructure/cli/audit_presenter.py."""

from src.infrastructure.cli.audit_presenter import (
    presentar_analisis_anomalias,
    presentar_casos_zero_trust,
    presentar_listas_precio,
    presentar_perfil_empresa,
    presentar_productos_stock,
)


def test_presentar_perfil_empresa_no_lanza_excepcion():
    empresa = {
        "nombreEmpresa": "Madygraf LTDA",
        "cuit": "33-71465177-9",
        "telefono": "03327-443353",
        "email": "contacto@madygraf.com",
    }
    presentar_perfil_empresa(empresa)


def test_presentar_listas_precio_no_lanza_excepcion():
    listas = [
        {"listaPrecioID": 9797, "nombre": "tinta", "tipo": 2, "activo": True},
        {"listaPrecioID": 9798, "nombre": "amarillo", "tipo": 2, "activo": True},
    ]
    presentar_listas_precio(listas)


def test_presentar_productos_stock_destaca_bobmar100():
    productos = [
        {"codigo": "BOBMAR100", "nombre": "BOBINA PAPEL KRAFT MARRON 100 GS", "precio": 0.0},
        {"codigo": "PROD01", "nombre": "Insumo Válido", "precio": 1500.0},
    ]
    presentar_productos_stock(productos)


def test_presentar_analisis_anomalias_no_lanza_excepcion():
    reporte = {
        "mediana_ars_kg": 1500.0,
        "mad": 25.0,
        "cota_tolerancia": 62.5,
        "anomalias": [],
        "falsos_negativos": [],
    }
    presentar_analisis_anomalias(reporte)


def test_presentar_casos_zero_trust_no_lanza_excepcion():
    casos = [{"entrada": {"precio": "invalid"}, "codigo": "confeccion", "monto": 0.0, "fecha": None}]
    presentar_casos_zero_trust(casos)
