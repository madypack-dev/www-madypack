from src.adapters.gateways.hardcoded_catalog_repository import HardcodedCatalogRepository


def test_hardcoded_catalog_repository_operations():
    repo = HardcodedCatalogRepository()

    # 12 productos variables
    productos = repo.obtener_todos()
    assert len(productos) == 12
    assert productos[0].nombre == "Bolsa de Papel Kraft Marrón para Farmacia y Joyería (12x8x19 cm)"
    assert len(productos[0].variaciones) == 6

    # Obtener por id
    assert repo.obtener_por_id(1).nombre == "Bolsa de Papel Kraft Marrón para Farmacia y Joyería (12x8x19 cm)"
    assert repo.obtener_por_id(99) is None

    # Obtener por slug
    assert repo.obtener_por_slug("bolsa-de-papel-blanco-301241").id == 12
    assert repo.obtener_por_slug("no-existe") is None

    # Buscar por texto (ahora buscamos "Farmacia" que devuelve 2 productos: marrón y blanco 12x8x19)
    assert len(repo.buscar("Farmacia")) == 2
    assert len(repo.buscar("inexistente")) == 0
    assert len(repo.buscar("")) == 12

    # Obtener variación por id
    res = repo.obtener_variacion_por_id(1)
    assert res is not None
    prod, var = res
    assert prod.nombre == "Bolsa de Papel Kraft Marrón para Farmacia y Joyería (12x8x19 cm)"
    assert var.sku == "B-120819-M-SOS-L"
    assert var.atributos == {"manija": "Sin Manija", "impresion": "Lisa (sin impresión)"}

    assert repo.obtener_variacion_por_id(999) is None
