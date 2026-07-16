from src.adapters.gateways.catalog.in_memory_catalog_repository import InMemoryCatalogRepository
from src.adapters.gateways.catalog.builders import (
    calculo_articulo_para_bolsa,
    construir_sku_bolsa,
)
from src.adapters.gateways.catalog.catalog_seed import construir_catalogo
from src.domain.commerce.product import ProductoBien, ProductoServicio


def test_in_memory_catalog_repository_operations():
    repo = InMemoryCatalogRepository()

    # 12 bolsas + 4 componentes + 5 servicios + 5 compuestos predefinidos +
    # 12 compuestos con manija + 24 impresos + 24 impresos con manija = 86
    productos = repo.obtener_todos()
    assert len(productos) == 86
    assert productos[0].nombre == "Bolsa 12x8x19 cm Marrón sin Manija Lisa 100g"
    assert productos[0].tipo == "bien"
    assert not productos[0].es_compuesto
    assert len(productos[0].variaciones) == 6

    # Obtener por id
    assert repo.obtener_por_id(1001).nombre == "Bolsa 12x8x19 cm Marrón sin Manija Lisa 100g"
    assert repo.obtener_por_id(99) is None

    # Obtener por slug
    assert repo.obtener_por_slug("bolsa-de-papel-marron-221030").id == 3004
    assert repo.obtener_por_slug("no-existe") is None

    # Buscar por texto
    # 2 bolsas simples + 3 compuestos predefinidos + 4 impresos + 4 impresos con manija + 2 con manija cordón
    assert len(repo.buscar("Farmacia")) == 15
    assert len(repo.buscar("inexistente")) == 0
    assert len(repo.buscar("")) == 86

    # Obtener variación por id
    res = repo.obtener_variacion_por_id(1)
    assert res is not None
    prod, var = res
    assert prod.nombre == "Bolsa 12x8x19 cm Marrón sin Manija Lisa 100g"
    assert var.sku == "B-120819-M-SOS-L"
    assert var.atributos == {"manija": "Sin Manija", "impresion": "Lisa (sin impresión)"}

    assert repo.obtener_variacion_por_id(999) is None

    # Servicios
    servicio = repo.obtener_por_id(2001)
    assert isinstance(servicio, ProductoServicio)
    assert servicio.nombre == "Pegado de Manijas"

    corte = repo.obtener_por_id(2004)
    assert isinstance(corte, ProductoServicio)
    assert corte.nombre == "Corte de Bobinas"
    assert not corte.visible

    confeccion_cuerdas = repo.obtener_por_id(2005)
    assert isinstance(confeccion_cuerdas, ProductoServicio)
    assert confeccion_cuerdas.nombre == "Confección de Cuerdas de Papel Retorcidas"
    assert not confeccion_cuerdas.visible

    # Compuestos
    compuesto = repo.obtener_por_id(3001)
    assert isinstance(compuesto, ProductoBien)
    assert compuesto.es_compuesto
    assert compuesto.nombre == "Bolsa 12x8x19 cm Marrón con Manija Cordón Lisa 100g"
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

    # Solo el compuesto con manija cordón 22x10x30 Marrón es visible
    compuesto_manija_visible = repo.obtener_por_id(3107)
    assert isinstance(compuesto_manija_visible, ProductoBien)
    assert compuesto_manija_visible.visible
    assert compuesto_manija_visible.es_compuesto
    assert "Manija Cordón" in compuesto_manija_visible.nombre
    assert "22x10x30" in compuesto_manija_visible.nombre
    assert any(c.nombre == "Manija Cordón" for c in compuesto_manija_visible.componentes)
    assert any(c.nombre == "Pegado de Manijas" for c in compuesto_manija_visible.componentes)

    # Los demás compuestos con manija cordón permanecen ocultos
    compuesto_manija_oculto = repo.obtener_por_id(3101)
    assert isinstance(compuesto_manija_oculto, ProductoBien)
    assert not compuesto_manija_oculto.visible
    assert "Manija Cordón" in compuesto_manija_oculto.nombre

    # El compuesto fijo genérico también permanece oculto
    compuesto_fijo_manija = repo.obtener_por_id(3001)
    assert isinstance(compuesto_fijo_manija, ProductoBien)
    assert not compuesto_fijo_manija.visible

    # Solo el compuesto impreso 22x10x30 Marrón es visible (sin manija)
    compuesto_impreso_visible = repo.obtener_por_id(3213)
    assert isinstance(compuesto_impreso_visible, ProductoBien)
    assert compuesto_impreso_visible.visible
    assert compuesto_impreso_visible.es_compuesto
    assert "Impresa" in compuesto_impreso_visible.nombre
    assert "22x10x30" in compuesto_impreso_visible.nombre
    assert any(c.nombre == "Impresión" for c in compuesto_impreso_visible.componentes)

    # Los demás compuestos impresos sin manija permanecen ocultos
    compuesto_impreso_oculto = repo.obtener_por_id(3201)
    assert isinstance(compuesto_impreso_oculto, ProductoBien)
    assert not compuesto_impreso_oculto.visible

    # Solo el compuesto impreso con manija 22x10x30 Marrón es visible
    compuesto_impreso_manija_visible = repo.obtener_por_id(3313)
    assert isinstance(compuesto_impreso_manija_visible, ProductoBien)
    assert compuesto_impreso_manija_visible.visible
    assert compuesto_impreso_manija_visible.es_compuesto
    assert "Impresa" in compuesto_impreso_manija_visible.nombre
    assert "Manija Cordón" in compuesto_impreso_manija_visible.nombre
    assert any(c.nombre == "Impresión" for c in compuesto_impreso_manija_visible.componentes)
    assert any(c.nombre == "Pegado de Manijas" for c in compuesto_impreso_manija_visible.componentes)

    # Los demás compuestos impresos con manija permanecen ocultos
    compuesto_impreso_manija_oculto = repo.obtener_por_id(3301)
    assert isinstance(compuesto_impreso_manija_oculto, ProductoBien)
    assert not compuesto_impreso_manija_oculto.visible

    # Bolsa visible es el compuesto 22x10x30 con medidas
    bolsa_visible = repo.obtener_por_id(3004)
    assert isinstance(bolsa_visible, ProductoBien)
    assert bolsa_visible.visible
    assert bolsa_visible.es_compuesto
    assert bolsa_visible.nombre == "Bolsa 22x10x30 cm Marrón sin Manija Lisa 100g"
    componente_bobina = next(
        c for c in bolsa_visible.componentes if c.nombre == "Bobina de Papel"
    )
    assert componente_bobina.medidas is not None
    assert componente_bobina.medidas.ancho == 22
    assert componente_bobina.gramaje == 100
    assert any(c.nombre == "Confección de Bolsas de Papel" for c in bolsa_visible.componentes)


def test_construir_sku_bolsa():
    assert construir_sku_bolsa("221030", "M", "SOS", "L") == "B-221030-M-SOS-L"
    assert construir_sku_bolsa("120841", "B", "CRD", "C") == "B-120841-B-CRD-C"


def test_calculo_articulo_para_bolsa_sin_personalizacion():
    calculo = calculo_articulo_para_bolsa("Sin Manija", "Lisa (sin impresión)")
    assert calculo.tipo == "suma_por_unidad"
    assert calculo.conceptos == ["base"]
    assert calculo.concepto_fijo is None


def test_calculo_articulo_para_bolsa_con_manija_y_personalizacion():
    calculo = calculo_articulo_para_bolsa("Manija Cordón", "Impresa 1 o 2 colores")
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

    # Rangos disjuntos entre familias de compuestos.
    compuestos_predefinidos = {p.id for p in productos if 3001 <= p.id <= 3005}
    compuestos_con_manija = {p.id for p in productos if 3101 <= p.id <= 3112}
    compuestos_impresos = {p.id for p in productos if 3201 <= p.id <= 3224}
    compuestos_impresos_con_manija = {p.id for p in productos if 3301 <= p.id <= 3324}

    assert len(compuestos_predefinidos & compuestos_con_manija) == 0
    assert len(compuestos_predefinidos & compuestos_impresos) == 0
    assert len(compuestos_predefinidos & compuestos_impresos_con_manija) == 0
    assert len(compuestos_con_manija & compuestos_impresos) == 0
    assert len(compuestos_con_manija & compuestos_impresos_con_manija) == 0
    assert len(compuestos_impresos & compuestos_impresos_con_manija) == 0
