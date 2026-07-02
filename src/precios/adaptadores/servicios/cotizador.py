from typing import Callable, Any
from src.comercio.dominio.puertos.servicio_precios import IServicioPrecios
from src.precios.dominio.modelos.tarifas import ConfiguracionTarifas

class CotizadorServicio(IServicioPrecios):
    def __init__(
        self, 
        cargar_tarifas_yaml: Callable[[], dict[str, Any]], 
        registrar_error: Callable[[str], None] = lambda m: None
    ):
        self.cargar_tarifas_yaml = cargar_tarifas_yaml
        self.registrar_error = registrar_error

    def calcular_precio_estimado(self, id_articulo: int, cantidad: int) -> float:
        try:
            datos_yaml = self.cargar_tarifas_yaml()
            config = ConfiguracionTarifas(**datos_yaml)
            tarifas = config.tarifas
        except Exception as err:
            self.registrar_error(f"Error cargando tarifas en cotizador: {err}")
            raise ValueError(f"No se pudieron obtener las tarifas de cotización: {err}")

        # Lógica de cálculo según el artículo
        if id_articulo == 1:
            costo_unitario = tarifas.costo_papel_base + tarifas.costo_manija_plana + tarifas.costo_personalizacion_base
            return (costo_unitario * cantidad) + tarifas.costo_fijo_matriz
        elif id_articulo == 2:
            costo_unitario = tarifas.costo_papel_base + tarifas.costo_manija_cordon
            return costo_unitario * cantidad
        elif id_articulo == 3:
            costo_unitario = tarifas.costo_papel_base
            return costo_unitario * cantidad
        
        return 0.0
