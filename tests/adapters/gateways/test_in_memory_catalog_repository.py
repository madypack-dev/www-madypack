from src.adapters.gateways.catalog import InMemoryCatalogRepository
from src.adapters.gateways.catalog.catalog_seed import (
    _construir_sku_bolsa,
    _crear_calculo_para_bolsa,
    construir_catalogo,
)
from src.domain.commerce.product import ProductoBien, ProductoServicio


def test_in_memory_catalog_repository_operations():
    repo = InMemoryCatalogRepository()

    # 12 bolsas + 4 componentes + 3 servicios + 4 compuestos fijos + 12 compuestos con manija = 35
    productos = repo.obtener_todos()
    assert len(productos) == 35
    assert productos[0].nombre == "Bolsa de Papel Kraft Marrón para Farmacia y Joyería (12x8x19 cm)"
    assert productos[0].tipo == "bien"
    assert not productos[0].es_compuesto
    assert len(productos[0].variaciones) == 6

    # Obtener por id
    assert repo.obtener_por_id(1001).nombre == "Bolsa de Papel Kraft Marrón para Farmacia y Joyería (12x8x19 cm)"
    assert repo.obtener_por_id(99) is None

    # Obtener por slug
    assert repo.obtener_por_slug("bolsa-de-papel-marron-221030").id == 3004
    assert repo.obtener_por_slug("no-existe") is None

    # Buscar por texto
    assert len(repo.buscar("Farmacia")) == 4
    assert len(repo.buscar("inexistente")) == 0
    assert len(repo.buscar("")) == 35

    # Obtener variación por id
    res = repo.obtener_variacion_por_id(1)
    assert res is not None
    prod, var = res
    assert prod.nombre == "Bolsa de Papel Kraft Marrón para Farmacia y Joyería (12x8x19 cm)"
    assert var.sku == "B-120819-M-SOS-L"
    assert var.atributos == {"manija": "Sin Manija", "impresion": "Lisa (sin impresión)"}

    assert repo.obtener_variacion_por_id(999) is None

    # Servicios
    servicio = repo.obtener_por_id(2001)
    assert isinstance(servicio, ProductoServicio)
    assert servicio.nombre == "Pegado de Manijas"

    # Compuestos
    compuesto = repo.obtener_por_id(3001)
    assert isinstance(compuesto, ProductoBien)
    assert compuesto.es_compuesto
    assert compuesto.nombre == "Bolsa de Papel con Manija Cordón"
    assert len(compuesto.componentes) == 3

    # Bobina de papel visible, cotizada en kg
    bobina = repo.obtener_por_id(1104)
    assert isinstance(bobina, ProductoBien)
    assert bobina.visible
    assert bobina.nombre == "Bobina de Papel"
    assert bobina.unidad == "kg"
    assert bobina.variaciones[0].cantidad_por_defecto == 100
    assert bobina.variaciones[0].calculo.conceptos == ["bobina_kg"]

    # Servicio de confección visible
    confeccion = repo.obtener_por_id(2003)
    assert isinstance(confeccion, ProductoServicio)
    assert confeccion.visible

    # Manija Cordón y Pegado de Manijas visibles
    manija_cordon = repo.obtener_por_id(1102)
    assert isinstance(manija_cordon, ProductoBien)
    assert manija_cordon.visible
    pegado = repo.obtener_por_id(2001)
    assert isinstance(pegado, ProductoServicio)
    assert pegado.visible

    # Compuesto con manija cordón para cada bolsa simple
    compuesto_manija = repo.obtener_por_id(3005)
    assert isinstance(compuesto_manija, ProductoBien)
    assert compuesto_manija.visible
    assert compuesto_manija.es_compuesto
    assert "Manija Cordón" in compuesto_manija.nombre
    assert any(c.nombre == "Manija Cordón" for c in compuesto_manija.componentes)
    assert any(c.nombre == "Pegado de Manijas" for c in compuesto_manija.componentes)

    # Bolsa visible es el compuesto 22x10x30 con medidas
    bolsa_visible = repo.obtener_por_id(3004)
    assert isinstance(bolsa_visible, ProductoBien)
    assert bolsa_visible.visible
    assert bolsa_visible.es_compuesto
    assert bolsa_visible.nombre == "Bolsa de Papel Kraft Marrón para Hamburguesas y Delivery (22x10x30 cm)"
    componente_bobina = next(
        c for c in bolsa_visible.componentes if c.nombre == "Bobina de Papel"
    )
    assert componente_bobina.medidas is not None
    assert componente_bobina.medidas.ancho == 22
    assert componente_bobina.gramaje == 100
    assert any(c.nombre == "Confección de Bolsas de Papel" for c in bolsa_visible.componentes)


def test_construir_sku_bolsa():
    assert _construir_sku_bolsa("221030", "M", "SOS", "L") == "B-221030-M-SOS-L"
    assert _construir_sku_bolsa("120841", "B", "CRD", "C") == "B-120841-B-CRD-C"


def test_crear_calculo_para_bolsa_sin_personalizacion():
    calculo = _crear_calculo_para_bolsa("Sin Manija", "Lisa (sin impresión)")
    assert calculo.tipo == "suma_por_unidad"
    assert calculo.conceptos == ["base"]
    assert calculo.concepto_fijo is None


def test_crear_calculo_para_bolsa_con_manija_y_personalizacion():
    calculo = _crear_calculo_para_bolsa("Manija Cordón", "Impresa 1 o 2 colores")
    assert calculo.tipo == "suma_por_unidad_mas_fijo"
    assert calculo.conceptos == ["base", "manija_cordon", "personalizacion"]
    assert calculo.concepto_fijo == "fijo_matriz"


def test_catalogo_mantiene_rangos_de_ids():
    productos, variaciones, servicios = construir_catalogo()

    ids_productos = {p.id for p in productos}
    ids_variaciones = set(variaciones.keys())
    ids_servicios = set(servicios.keys())

    # No debe haber colisiones entre variaciones y productos (bienes/servicios).
    assert ids_productos & ids_variaciones == set()
    # Los servicios son productos, por lo que sus IDs deben estar incluidos.
    assert ids_servicios.issubset(ids_productos)
    # Las variaciones tampoco deben colisionar con servicios.
    assert ids_variaciones & ids_servicios == set()
    # Sin IDs duplicados dentro de cada colección.
    assert len(ids_productos) == len(productos)
    assert len(ids_variaciones) == len(variaciones)
