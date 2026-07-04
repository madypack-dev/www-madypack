"""Smoke tests para el generador de PDF con ReportLab."""

from datetime import date

import pytest

from src.comercio.dominio.modelos.carrito import CalculoArticulo
from src.infraestructura.adaptadores.generador_pdf_reportlab import (
    GeneradorPresupuestoPDFReportLab,
)
from src.presupuesto.dominio.modelos.identidad_visual import IdentidadVisual
from src.presupuesto.dominio.modelos.presupuesto import (
    DatosSolicitante,
    LineaPresupuesto,
    Presupuesto,
)


class TestGeneradorPresupuestoPDFReportLab:
    def test_genera_pdf_no_vacio(self):
        presupuesto = Presupuesto(
            fecha_emision=date.today(),
            validez_dias=15,
            datos_solicitante=DatosSolicitante(
                nombre="Juan Pérez",
                email="juan@example.com",
                telefono="5491112345678",
                empresa="ACME",
                mensaje="Necesito 1000 bolsas",
            ),
            lineas=[
                LineaPresupuesto(
                    id_articulo=1,
                    nombre="Bolsas de Papel Kraft Personalizadas",
                    descripcion="Impresión Flexográfica | Manijas planas",
                    cantidad=1000,
                    precio_unitario_estimado=2.20,
                    subtotal=2200.0,
                ),
            ],
            condiciones_comerciales=["Oferta preliminar sujeta a confirmación."],
            total_estimado=2200.0,
        )
        identidad = IdentidadVisual(
            brand="Madypack",
            tagline="Bolsas Sustentables",
            email="ventas@madypack.com.ar",
            telefono="5491125794649",
            direccion="Ruta Panamericana km 36.7, Garín",
            whatsapp="5491125794649",
            url="https://www.madypack.com.ar",
        )

        generador = GeneradorPresupuestoPDFReportLab()
        pdf_bytes = generador.generar(presupuesto, identidad)

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 100
        assert pdf_bytes.startswith(b"%PDF")

    def test_genera_pdf_sin_logo(self):
        presupuesto = Presupuesto(
            fecha_emision=date.today(),
            validez_dias=10,
            datos_solicitante=DatosSolicitante(
                email="a@example.com", telefono="5491112345678"
            ),
            lineas=[
                LineaPresupuesto(
                    id_articulo=2,
                    nombre="Bolsas con cordón",
                    descripcion="Lisas",
                    cantidad=500,
                    precio_unitario_estimado=2.0,
                    subtotal=1000.0,
                )
            ],
            condiciones_comerciales=[],
            total_estimado=1000.0,
        )
        identidad = IdentidadVisual(
            brand="Test",
            email="a@a.com",
            telefono="1",
            direccion="X",
        )

        generador = GeneradorPresupuestoPDFReportLab()
        pdf_bytes = generador.generar(presupuesto, identidad)

        assert pdf_bytes.startswith(b"%PDF")
