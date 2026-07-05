"""Tests para el caso de uso GenerarPresupuestoPDF."""

from datetime import date
from typing import Callable

import pytest

from src.presupuesto.aplicacion.casos_uso.generar_presupuesto_pdf import (
    CasoUsoGenerarPresupuestoPDF,
)
from src.presupuesto.dominio.modelos.identidad_visual import IdentidadVisual
from src.presupuesto.dominio.modelos.presupuesto import DatosSolicitante, LineaPresupuesto
from src.presupuesto.dominio.puertos.generador_pdf import IGeneradorDocumentoPresupuesto


class GeneradorPDFFake(IGeneradorDocumentoPresupuesto):
    def __init__(self):
        self.ultimo_presupuesto = None
        self.ultima_identidad = None

    def generar(self, presupuesto, identidad_visual) -> bytes:
        self.ultimo_presupuesto = presupuesto
        self.ultima_identidad = identidad_visual
        return b"PDF_FAKE"


class TestCasoUsoGenerarPresupuestoPDF:
    def test_genera_pdf_con_lineas_y_datos_correctos(self):
        lineas = [
            LineaPresupuesto(
                id_articulo=1,
                nombre="Bolsas de Papel Kraft Personalizadas",
                descripcion="Manija plana",
                cantidad=1000,
                precio_unitario_estimado=1.5,
                subtotal=1500.0,
            ),
            LineaPresupuesto(
                id_articulo=2,
                nombre="Bolsas con cordón",
                descripcion="Lisas",
                cantidad=500,
                precio_unitario_estimado=1.5,
                subtotal=750.0,
            ),
        ]
        generador = GeneradorPDFFake()

        caso_uso = CasoUsoGenerarPresupuestoPDF(
            generador_pdf=generador,
        )

        datos = DatosSolicitante(
            nombre="Juan Pérez",
            email="juan@example.com",
            telefono="5491112345678",
            empresa="ACME",
            mensaje="Urgente",
        )
        identidad = IdentidadVisual(
            brand="Madypack",
            email="ventas@madypack.com.ar",
            telefono="5491125794649",
            direccion="Garín",
        )

        resultado = caso_uso.ejecutar(
            datos_solicitante=datos,
            lineas=lineas,
            identidad_visual=identidad,
            validez_dias=15,
            condiciones_comerciales=["Condición 1"],
        )

        assert resultado == b"PDF_FAKE"
        assert generador.ultimo_presupuesto is not None
        assert generador.ultimo_presupuesto.total_estimado == 2250.0
        assert len(generador.ultimo_presupuesto.lineas) == 2
        assert generador.ultimo_presupuesto.datos_solicitante.email == "juan@example.com"
        assert generador.ultima_identidad.brand == "Madypack"

    def test_lanza_error_si_lineas_esta_vacio(self):
        generador = GeneradorPDFFake()

        caso_uso = CasoUsoGenerarPresupuestoPDF(
            generador_pdf=generador,
        )

        datos = DatosSolicitante(email="a@example.com", telefono="5491112345678")
        identidad = IdentidadVisual(brand="M", email="a@a.com", telefono="1", direccion="X")

        with pytest.raises(ValueError, match="contener al menos una línea"):
            caso_uso.ejecutar(
                datos_solicitante=datos,
                lineas=[],
                identidad_visual=identidad,
                validez_dias=15,
                condiciones_comerciales=[],
            )
