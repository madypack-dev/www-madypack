"""Tests para la carga y validación de archivos YAML."""

import pytest
import yaml
from pydantic import ValidationError

from src.infrastructure.pyyaml import loaders
from src.infrastructure.pyyaml.loaders import cargar_site
from src.infrastructure.pyyaml.models import (
    QuoteFormConfig,
    QuoteFormFieldConfig,
    SiteConfig,
)


class TestCargarDefault:
    def test_cargar_site_devuelve_site_config(self):
        site = cargar_site()
        assert isinstance(site, SiteConfig)
        assert site.site.brand == "Madypack"


class TestValidacionErrores:
    def test_site_yaml_invalido_lanza_validation_error(self, tmp_path, monkeypatch):
        data_dir = tmp_path / "data"
        data_dir.mkdir(parents=True)
        (data_dir / "site.yml").write_text(
            yaml.safe_dump({"analytics": {"gtm_id": "GTM-XXXXXXX"}}), encoding="utf-8"
        )

        monkeypatch.setattr(loaders, "DATA_DIR", data_dir)

        with pytest.raises(ValidationError):
            cargar_site()


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
