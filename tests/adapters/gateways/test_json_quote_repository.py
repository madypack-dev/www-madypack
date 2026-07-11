import tempfile
from datetime import date

from src.domain.quote.quote import Presupuesto, DatosSolicitante, LineaPresupuesto
from src.adapters.gateways.json_quote_repository import JsonQuoteRepository


def test_json_quote_repository_guardar_y_recuperar():
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo = JsonQuoteRepository(data_dir=tmp_dir)

        datos_solicitante = DatosSolicitante(
            nombre="Juan Pérez",
            email="juan@example.com",
            telefono="+5491112345678",
            empresa="ACME",
            mensaje="Test",
        )
        lineas = [
            LineaPresupuesto(
                id_articulo=1,
                nombre="Bolsa",
                descripcion="Desc",
                cantidad=1000,
                precio_unitario_estimado=1.5,
                subtotal=1500.0,
            )
        ]
        presupuesto = Presupuesto(
            fecha_emision=date.today(),
            validez_dias=15,
            datos_solicitante=datos_solicitante,
            lineas=lineas,
            condiciones_comerciales=["Test Condición"],
            total_estimado=1500.0,
        )

        ref = "COT-20260711-TEST"
        repo.guardar(ref, presupuesto)

        # Recuperar y verificar
        recuperado = repo.obtener_por_referencia(ref)
        assert recuperado is not None
        assert recuperado.total_estimado == 1500.0
        assert recuperado.datos_solicitante.nombre == "Juan Pérez"
        assert len(recuperado.lineas) == 1
        assert recuperado.lineas[0].nombre == "Bolsa"
        assert recuperado.condiciones_comerciales == ["Test Condición"]


def test_json_quote_repository_obtener_inexistente():
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo = JsonQuoteRepository(data_dir=tmp_dir)
        recuperado = repo.obtener_por_referencia("COT-INEXISTENTE")
        assert recuperado is None
