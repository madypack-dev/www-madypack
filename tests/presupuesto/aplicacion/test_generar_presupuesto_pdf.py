"""Tests para el caso de uso GenerarPresupuestoPDF."""

from datetime import date
from typing import Callable

import pytest

from src.comercio.dominio.modelos.carrito import ArticuloCarrito, Carrito, CalculoArticulo
from src.comercio.dominio.puertos.repositorio import IRepositorioCarrito
from src.comercio.dominio.puertos.servicio_precios import IServicioPrecios
from src.presupuesto.aplicacion.casos_uso.generar_presupuesto_pdf import (
    CasoUsoGenerarPresupuestoPDF,
)
from src.presupuesto.dominio.modelos.identidad_visual import IdentidadVisual
from src.presupuesto.dominio.modelos.presupuesto import DatosSolicitante
from src.presupuesto.dominio.puertos.generador_pdf import IGeneradorDocumentoPresupuesto


class RepositorioCarritoFake(IRepositorioCarrito):
    def __init__(self, carrito: Carrito):
        self._carrito = carrito

    def obtener_carrito(self) -> Carrito:
        return self._carrito

    def guardar_carrito(self, carrito: Carrito) -> None:
        self._carrito = carrito


class ServicioPreciosFake(IServicioPrecios):
    def calcular_precio_estimado(self, articulo: ArticuloCarrito) -> float:
        return articulo.cantidad * 1.5


class GeneradorPDFFake(IGeneradorDocumentoPresupuesto):
    def __init__(self):
        self.ultimo_presupuesto = None
        self.ultima_identidad = None

    def generar(self, presupuesto, identidad_visual) -> bytes:
        self.ultimo_presupuesto = presupuesto
        self.ultima_identidad = identidad_visual
        return b"PDF_FAKE"


class TestCasoUsoGenerarPresupuestoPDF:
    def test_genera_pdf_con_carrito_y_datos_correctos(self):
        carrito = Carrito(
            articulos=[
                ArticuloCarrito(
                    id=1,
                    nombre="Bolsas de Papel Kraft Personalizadas",
                    descripcion="Manija plana",
                    cantidad=1000,
                    imagen="bolsas-personalizadas.svg",
                    calculo=CalculoArticulo(
                        tipo="suma_por_unidad_mas_fijo",
                        conceptos=["base", "manija_plana", "personalizacion"],
                        concepto_fijo="fijo_matriz",
                    ),
                ),
                ArticuloCarrito(
                    id=2,
                    nombre="Bolsas con cordón",
                    descripcion="Lisas",
                    cantidad=500,
                    imagen="bolsas-con-m.svg",
                    calculo=CalculoArticulo(
                        tipo="suma_por_unidad",
                        conceptos=["base", "manija_cordon"],
                    ),
                ),
            ]
        )
        repositorio = RepositorioCarritoFake(carrito)
        servicio_precios = ServicioPreciosFake()
        generador = GeneradorPDFFake()

        caso_uso = CasoUsoGenerarPresupuestoPDF(
            repositorio_carrito=repositorio,
            servicio_precios=servicio_precios,
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

    def test_lanza_error_si_carrito_esta_vacio(self):
        repositorio = RepositorioCarritoFake(Carrito(articulos=[]))
        servicio_precios = ServicioPreciosFake()
        generador = GeneradorPDFFake()

        caso_uso = CasoUsoGenerarPresupuestoPDF(
            repositorio_carrito=repositorio,
            servicio_precios=servicio_precios,
            generador_pdf=generador,
        )

        datos = DatosSolicitante(email="a@example.com", telefono="5491112345678")
        identidad = IdentidadVisual(brand="M", email="a@a.com", telefono="1", direccion="X")

        with pytest.raises(ValueError, match="carrito está vacío"):
            caso_uso.ejecutar(
                datos_solicitante=datos,
                identidad_visual=identidad,
                validez_dias=15,
                condiciones_comerciales=[],
            )
