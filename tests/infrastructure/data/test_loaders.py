"""Tests para la carga y validación de archivos YAML."""

import pytest
import yaml
from pydantic import ValidationError

from src.infrastructure.data import loaders
from src.infrastructure.data.loaders import (
    cargar_site,
    cargar_productos_tienda,
    cargar_tarifas,
)
from src.infrastructure.data.models import (
    CatalogoConfig,
    QuoteFormConfig,
    QuoteFormFieldConfig,
    SiteConfig,
)
from src.domain.pricing.rates import ConfiguracionTarifas


class TestCargarDefault:
    def test_cargar_site_devuelve_site_config(self):
        site = cargar_site()
        assert isinstance(site, SiteConfig)
        assert site.site.brand == "Madypack"

    def test_cargar_productos_tienda_devuelve_catalogo_config(self):
        catalogo = cargar_productos_tienda()
        assert isinstance(catalogo, CatalogoConfig)
        assert len(catalogo.articulos) == 3
        assert catalogo.articulos[0].cantidad_por_defecto == 1000

    def test_cargar_tarifas_devuelve_configuracion_tarifas(self):
        tarifas = cargar_tarifas()
        assert isinstance(tarifas, ConfiguracionTarifas)
        assert tarifas.tarifas.conceptos["base"] == 0.15


class TestValidacionErrores:
    def test_site_yaml_invalido_lanza_validation_error(self, tmp_path, monkeypatch):
        data_dir = tmp_path / "data"
        data_dir.mkdir(parents=True)
        (data_dir / "site.yml").write_text(
            yaml.safe_dump({"analytics": {"gtm_id": "GTM-XXXXXXX"}}), encoding="utf-8"
        )
        (data_dir / "productos_tienda.yml").write_text(
            yaml.safe_dump({
                "articulos": [
                    {"id": 1, "nombre": "A", "descripcion": "Desc", "cantidad_por_defecto": 1000, "imagen": "a.svg"}
                ]
            }),
            encoding="utf-8",
        )
        (data_dir / "tarifas.yml").write_text(
            yaml.safe_dump({
                "tarifas": {
                    "costo_papel_base": 0.1,
                    "costo_manija_plana": 0.2,
                    "costo_manija_cordon": 0.3,
                    "costo_personalizacion_base": 0.1,
                    "costo_fijo_matriz": 1000.0,
                }
            }),
            encoding="utf-8",
        )

        monkeypatch.setattr(loaders, "DATA_DIR", data_dir)

        with pytest.raises(ValidationError):
            cargar_site()

    def test_productos_tienda_cantidad_no_multiplo_de_100_lanza_error(self, tmp_path, monkeypatch):
        data_dir = tmp_path / "data"
        data_dir.mkdir(parents=True)
        (data_dir / "productos_tienda.yml").write_text(
            yaml.safe_dump({
                "articulos": [
                    {"id": 1, "nombre": "A", "descripcion": "Desc", "cantidad_por_defecto": 150, "imagen": "a.svg"}
                ]
            }),
            encoding="utf-8",
        )

        monkeypatch.setattr(loaders, "DATA_DIR", data_dir)

        with pytest.raises(ValidationError):
            cargar_productos_tienda()


class TestValidacionCamposQuoteForm:
    def test_campo_con_nombre_invalido_lanza_validation_error(self):
        with pytest.raises(ValidationError) as exc_info:
            QuoteFormConfig(
                title="Q",
                meta_title="Q",
                meta_description="D",
                description="D",
                submit="S",
                success_title="OK",
                success_message="OK",
                required_marker="*",
                required_abbreviation="req",
                details=[],
                fields=[
                    QuoteFormFieldConfig(
                        name="telefono", label="Tel", type="tel", required=True
                    )
                ],
            )
        assert "telefono" in str(exc_info.value)
        assert "phone" in str(exc_info.value)

    def test_campos_validos_cargan_correctamente(self):
        config = QuoteFormConfig(
            title="Q",
            meta_title="Q",
            meta_description="D",
            description="D",
            submit="S",
            success_title="OK",
            success_message="OK",
            required_marker="*",
            required_abbreviation="req",
            details=[],
            fields=[
                QuoteFormFieldConfig(
                    name="name", label="Nombre", type="text", required=True
                ),
                QuoteFormFieldConfig(
                    name="company", label="Empresa", type="text", required=True
                ),
                QuoteFormFieldConfig(
                    name="email", label="Email", type="email", required=True
                ),
                QuoteFormFieldConfig(
                    name="phone", label="Tel", type="tel", required=True
                ),
                QuoteFormFieldConfig(
                    name="message",
                    label="Mensaje",
                    type="textarea",
                    required=False,
                    rows=4,
                ),
            ],
        )
        assert len(config.fields) == 5

    def test_site_actual_tiene_campos_validos(self):
        site = cargar_site()
        nombres = {field.name for field in site.home.quote_form.fields}
        assert nombres.issubset({"name", "company", "email", "phone", "message"})
