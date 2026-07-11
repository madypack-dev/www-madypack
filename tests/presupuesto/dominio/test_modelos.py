"""Tests para los modelos de dominio del agregado Presupuesto."""

from datetime import date

import pytest
from pydantic import ValidationError

from src.domain.presupuesto.modelos.identidad_visual import IdentidadVisual
from src.domain.presupuesto.modelos.presupuesto import (
    DatosSolicitante,
    LineaPresupuesto,
    Presupuesto,
)


class TestDatosSolicitante:
    def test_crea_datos_solicitante_con_campos_obligatorios(self):
        datos = DatosSolicitante(email="cliente@example.com", telefono="5491112345678")
        assert datos.nombre is None
        assert datos.email == "cliente@example.com"
        assert datos.telefono == "5491112345678"

    def test_email_invalido_lanza_validation_error(self):
        with pytest.raises(ValidationError):
            DatosSolicitante(email="no-es-email", telefono="5491112345678")


class TestLineaPresupuesto:
    def test_crea_linea_valida(self):
        linea = LineaPresupuesto(
            id_articulo=1,
            nombre="Bolsas personalizadas",
            descripcion="Manija plana",
            cantidad=1000,
            precio_unitario_estimado=0.85,
            subtotal=850.0,
        )
        assert linea.subtotal == 850.0

    def test_cantidad_no_multiplo_de_100_lanza_error(self):
        with pytest.raises(ValidationError):
            LineaPresupuesto(
                id_articulo=1,
                nombre="Bolsas",
                descripcion="Desc",
                cantidad=150,
                precio_unitario_estimado=1.0,
                subtotal=150.0,
            )

    def test_cantidad_menor_a_100_lanza_error(self):
        with pytest.raises(ValidationError):
            LineaPresupuesto(
                id_articulo=1,
                nombre="Bolsas",
                descripcion="Desc",
                cantidad=50,
                precio_unitario_estimado=1.0,
                subtotal=50.0,
            )


class TestPresupuesto:
    def test_crea_presupuesto_con_total_correcto(self):
        presupuesto = Presupuesto(
            fecha_emision=date.today(),
            validez_dias=15,
            datos_solicitante=DatosSolicitante(email="a@example.com", telefono="5491112345678"),
            lineas=[
                LineaPresupuesto(
                    id_articulo=1,
                    nombre="A",
                    descripcion="Desc",
                    cantidad=1000,
                    precio_unitario_estimado=1.0,
                    subtotal=1000.0,
                ),
                LineaPresupuesto(
                    id_articulo=2,
                    nombre="B",
                    descripcion="Desc",
                    cantidad=500,
                    precio_unitario_estimado=2.0,
                    subtotal=1000.0,
                ),
            ],
            condiciones_comerciales=["Condición 1"],
            total_estimado=2000.0,
        )
        assert presupuesto.total_estimado == 2000.0
        assert len(presupuesto.lineas) == 2

    def test_validez_dias_menor_a_1_lanza_error(self):
        with pytest.raises(ValidationError):
            Presupuesto(
                fecha_emision=date.today(),
                validez_dias=0,
                datos_solicitante=DatosSolicitante(email="a@example.com", telefono="5491112345678"),
                lineas=[],
                condiciones_comerciales=[],
                total_estimado=0.0,
            )


class TestIdentidadVisual:
    def test_crea_identidad_visual(self):
        identidad = IdentidadVisual(
            brand="Madypack",
            logo_path="/app/static/images/logo.svg",
            email="ventas@example.com",
            telefono="5491112345678",
            direccion="Garín, Buenos Aires",
        )
        assert identidad.brand == "Madypack"
        assert identidad.logo_path == "/app/static/images/logo.svg"
