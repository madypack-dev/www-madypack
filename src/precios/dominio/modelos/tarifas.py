from pydantic import BaseModel

class TarifasCalculo(BaseModel):
    costo_papel_base: float
    costo_manija_plana: float
    costo_manija_cordon: float
    costo_personalizacion_base: float
    costo_fijo_matriz: float


class ConfiguracionTarifas(BaseModel):
    tarifas: TarifasCalculo
