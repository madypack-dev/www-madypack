from src.adapters.gateways.hardcoded_catalog_repository import HardcodedCatalogRepository


def test_hardcoded_catalog_repository_operations():
    repo = HardcodedCatalogRepository()

    # 4 artículos
    articulos = repo.obtener_todos()
    assert len(articulos) == 4

    # Obtener por id
    assert repo.obtener_por_id(1).nombre == "Bolsas de Papel Kraft Marrón sin Manija"
    assert repo.obtener_por_id(99) is None

    # Obtener por slug
    assert repo.obtener_por_slug("bolsas-blancas-sin-manija").id == 2
    assert repo.obtener_por_slug("no-existe") is None

    # Buscar por texto
    assert len(repo.buscar("Kraft")) == 2
    assert len(repo.buscar("Blanco")) == 2
    assert len(repo.buscar("")) == 4
