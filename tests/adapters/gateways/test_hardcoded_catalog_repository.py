from src.adapters.gateways.hardcoded_catalog_repository import HardcodedCatalogRepository
from src.domain.commerce.product import ProductoBien, ProductoServicio


def test_hardcoded_catalog_repository_operations():
    repo = HardcodedCatalogRepository()

    # 12 bolsas + 4 componentes + 4 compuestos + 3 servicios = 23
    productos = repo.obtener_todos()
    assert len(productos) == 23
    assert productos[0].nombre == "Bolsa de Papel Kraft Marrón para Farmacia y Joyería (12x8x19 cm)"
    assert productos[0].tipo == "bien"
    assert not productos[0].es_compuesto
    assert len(productos[0].variaciones) == 6

    # Obtener por id
    assert repo.obtener_por_id(1001).nombre == "Bolsa de Papel Kraft Marrón para Farmacia y Joyería (12x8x19 cm)"
    assert repo.obtener_por_id(99) is None

    # Obtener por slug
    assert repo.obtener_por_slug("bolsa-de-papel-marron-221030").id == 1007
    assert repo.obtener_por_slug("no-existe") is None

    # Buscar por texto
    assert len(repo.buscar("Farmacia")) == 2
    assert len(repo.buscar("inexistente")) == 0
    assert len(repo.buscar("")) == 23

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

    # Bobina de papel visible
    bobina = repo.obtener_por_id(1104)
    assert isinstance(bobina, ProductoBien)
    assert bobina.visible
    assert bobina.nombre == "Bobina de Papel"

    # Servicio de confección visible
    confeccion = repo.obtener_por_id(2003)
    assert isinstance(confeccion, ProductoServicio)
    assert confeccion.visible

    # Ejemplo: bolsas de papel = bobina + confección
    bolsas = repo.obtener_por_id(3004)
    assert isinstance(bolsas, ProductoBien)
    assert bolsas.es_compuesto
    assert bolsas.nombre == "Bolsas de Papel"
    assert any(c.nombre == "Confección de Bolsas de Papel" for c in bolsas.componentes)
    assert any(c.nombre == "Bobina de Papel" for c in bolsas.componentes)
