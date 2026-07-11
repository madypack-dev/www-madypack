from src.adapters.gateways.hardcoded_catalog_repository import HardcodedCatalogRepository


def test_hardcoded_catalog_repository_operations():
    repo = HardcodedCatalogRepository()

    # 1 producto variable
    productos = repo.obtener_todos()
    assert len(productos) == 1
    assert productos[0].nombre == "Bolsa de Papel"
    assert len(productos[0].variaciones) == 12

    # Obtener por id
    assert repo.obtener_por_id(1).nombre == "Bolsa de Papel"
    assert repo.obtener_por_id(99) is None

    # Obtener por slug
    assert repo.obtener_por_slug("bolsa-de-papel").id == 1
    assert repo.obtener_por_slug("no-existe") is None

    # Buscar por texto
    assert len(repo.buscar("Kraft")) == 1
    assert len(repo.buscar("inexistente")) == 0
    assert len(repo.buscar("")) == 1

    # Obtener variación por id
    res = repo.obtener_variacion_por_id(1)
    assert res is not None
    prod, var = res
    assert prod.nombre == "Bolsa de Papel"
    assert var.sku == "B-SOS-M-L"
    assert var.atributos == {"color": "Marrón", "manija": "Sin Manija", "impresion": "Lisa (sin impresión)"}

    assert repo.obtener_variacion_por_id(99) is None
