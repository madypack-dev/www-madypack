from typing import Callable, Any

from src.domain.comercio.modelos.carrito import ArticuloCarrito
from src.domain.precios.modelos.tarifas import ConfiguracionTarifas
from src.domain.precios.servicios.calculador import CalculadorPrecio


class CotizadorServicio:
    def __init__(
        self,
        cargar_tarifas_yaml: Callable[[], dict[str, Any]],
        registrar_error: Callable[[str], None] = lambda _: None,
    ):
        self.cargar_tarifas_yaml = cargar_tarifas_yaml
        self.registrar_error = registrar_error
        self._calculador = CalculadorPrecio()
        self._conceptos_cache: dict[str, float] | None = None

    def calcular_precio_estimado(self, articulo: ArticuloCarrito) -> float:
        if self._conceptos_cache is None:
            try:
                datos_yaml = self.cargar_tarifas_yaml()
                config = ConfiguracionTarifas(**datos_yaml)
                self._conceptos_cache = config.tarifas.conceptos
            except Exception as err:
                self.registrar_error(f"Error cargando tarifas en cotizador: {err}")
                raise ValueError(f"No se pudieron obtener las tarifas de cotización: {err}")

        try:
            return self._calculador.calcular(
                articulo.calculo, self._conceptos_cache, articulo.cantidad
            )
        except Exception as err:
            self.registrar_error(f"Error calculando precio para artículo {articulo.id}: {err}")
            raise
