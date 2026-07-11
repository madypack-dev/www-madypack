from src.domain.commerce.catalog import ArticuloCatalogo
from src.infrastructure.pyyaml.models import CatalogoConfig
from src.adapters.gateways.pyyaml_catalog_repository import YamlCatalogRepository


def test_yaml_catalog_repository_operations():
    # Mock loaded config
    catalog_config = CatalogoConfig(
        articulos=[
            ArticuloCatalogo(
                id=1,
                nombre="Bolsas Kraft",
                descripcion="Descripción A",
                cantidad_por_defecto=1000,
                imagen="img1.png",
                slug="bolsas-kraft",
            ),
            ArticuloCatalogo(
                id=2,
                nombre="Bolsas Cordon",
                descripcion="Descripción B",
                cantidad_por_defecto=2000,
                imagen="img2.png",
                slug="bolsas-cordon",
            ),
        ]
    )

    loader_mock = lambda: catalog_config
    repo = YamlCatalogRepository(cargar_catalogo_yaml=loader_mock)

    assert len(repo.obtener_todos()) == 2

    # Test obtener_por_id
    assert repo.obtener_por_id(1).nombre == "Bolsas Kraft"
    assert repo.obtener_por_id(3) is None

    # Test obtener_por_slug
    assert repo.obtener_por_slug("bolsas-cordon").id == 2
    assert repo.obtener_por_slug("no-existe") is None

    # Test buscar
    results = repo.buscar("Kraft")
    assert len(results) == 1
    assert results[0].id == 1

    results_desc = repo.buscar("Descripción")
    assert len(results_desc) == 2

    results_empty = repo.buscar("")
    assert len(results_empty) == 2
