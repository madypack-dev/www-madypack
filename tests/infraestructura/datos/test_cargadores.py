"""Tests para la carga y validación de archivos YAML por tenant."""

import pytest
import yaml
from pydantic import ValidationError

from src.infraestructura.datos import cargadores
from src.infraestructura.datos.cargadores import (
    cargar_site,
    cargar_productos_tienda,
    cargar_tarifas,
)
from src.infraestructura.datos.modelos import SiteConfig, CatalogoConfig
from src.precios.dominio.modelos.tarifas import ConfiguracionTarifas


class TestCargarDefault:
    def test_cargar_site_default_devuelve_site_config(self):
        site = cargar_site("default")
        assert isinstance(site, SiteConfig)
        assert site.site.brand == "Tu Empresa"

    def test_cargar_productos_tienda_default_devuelve_catalogo_config(self):
        catalogo = cargar_productos_tienda("default")
        assert isinstance(catalogo, CatalogoConfig)
        assert len(catalogo.articulos) == 3
        assert catalogo.articulos[0].cantidad_por_defecto == 1000

    def test_cargar_tarifas_default_devuelve_configuracion_tarifas(self):
        tarifas = cargar_tarifas("default")
        assert isinstance(tarifas, ConfiguracionTarifas)
        assert tarifas.tarifas.costo_papel_base == 0.10


class TestValidacionErrores:
    def test_site_yaml_invalido_lanza_validation_error(self, tmp_path, monkeypatch):
        data_dir = tmp_path / "data"
        tenant_dir = data_dir / "default"
        tenant_dir.mkdir(parents=True)
        (tenant_dir / "site.yml").write_text(
            yaml.safe_dump({"analytics": {"gtm_id": "GTM-XXXXXXX"}}), encoding="utf-8"
        )
        # Archivos mínimos para que no falle por fallback
        (tenant_dir / "productos_tienda.yml").write_text(
            yaml.safe_dump({
                "articulos": [
                    {"id": 1, "nombre": "A", "descripcion": "Desc", "cantidad_por_defecto": 1000, "imagen": "a.svg"}
                ]
            }),
            encoding="utf-8",
        )
        (tenant_dir / "tarifas.yml").write_text(
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

        monkeypatch.setattr(cargadores, "DATA_DIR", data_dir)

        with pytest.raises(ValidationError):
            cargar_site("default")

    def test_productos_tienda_cantidad_no_multiplo_de_100_lanza_error(self, tmp_path, monkeypatch):
        data_dir = tmp_path / "data"
        tenant_dir = data_dir / "default"
        tenant_dir.mkdir(parents=True)
        (tenant_dir / "productos_tienda.yml").write_text(
            yaml.safe_dump({
                "articulos": [
                    {"id": 1, "nombre": "A", "descripcion": "Desc", "cantidad_por_defecto": 150, "imagen": "a.svg"}
                ]
            }),
            encoding="utf-8",
        )

        monkeypatch.setattr(cargadores, "DATA_DIR", data_dir)

        with pytest.raises(ValidationError):
            cargar_productos_tienda("default")


class TestFallback:
    def test_tenant_inexistente_usa_default(self, tmp_path, monkeypatch):
        data_dir = tmp_path / "data"
        default_dir = data_dir / "default"
        default_dir.mkdir(parents=True)
        (default_dir / "site.yml").write_text(
            yaml.safe_dump({
                "analytics": {"gtm_id": "GTM-XXXXXXX", "ga_id": "G-XXXXXXXXXX"},
                "whatsapp": {"phone": "5490000000000", "message": "Hola"},
                "site": {
                    "lang": "es-AR",
                    "brand": "Fallback",
                    "tagline": "Tagline",
                    "title_default": "Fallback",
                    "charset": "UTF-8",
                    "viewport": "width=device-width",
                    "robots": "max-image-preview:large",
                    "profile_url": "https://gmpg.org/xfn/11",
                    "logo": {"width": 100, "height": 50, "alt": "Fallback", "url": "/"},
                },
                "socials": [],
                "header": {
                    "top_bar": {"text": "TOP"},
                    "logo": {"src": "logo.svg"},
                    "menu": [],
                    "actions": {"search": "Buscar", "account": "Cuenta", "cart": "Carrito", "menu": "Menú"},
                    "account_modal": {
                        "title": "Acceso",
                        "close_label": "Cerrar",
                        "email_label": "Email",
                        "email_placeholder": "a@a.com",
                        "password_label": "Contraseña",
                        "password_placeholder": "••••••••",
                        "submit_button": "Ingresar",
                        "no_account_text": "¿No tenés cuenta?",
                        "contact_link_text": "Contactanos",
                        "contact_url": "/contacto/",
                    },
                },
                "footer": {"logo": {"src": "logo.svg"}, "menu": []},
                "home": {
                    "hero": {"title": "H", "subtitle": "S"},
                    "cta": {"title": "T", "before_link": "B", "link_text": "L", "after_link": "A"},
                    "product_types": {"title": "P", "products": []},
                    "quote_form": {
                        "title": "Q",
                        "meta_title": "Q",
                        "meta_description": "D",
                        "description": "D",
                        "submit": "S",
                        "success_title": "OK",
                        "success_message": "OK",
                        "required_marker": "*",
                        "required_abbreviation": "req",
                        "details": [],
                        "fields": [],
                    },
                    "about": {
                        "title": "A",
                        "meta_title": "A",
                        "meta_description": "D",
                        "text": "T",
                        "button_text": "B",
                        "button_url": "/",
                        "image": "a.jpg",
                        "details": [],
                    },
                    "newsletter": {"title": "N", "placeholder": "P", "submit": "S", "success_title": "OK", "success_message": "OK"},
                    "contact": {
                        "title": "C",
                        "meta_title": "C",
                        "meta_description": "D",
                        "email": "a@a.com",
                        "whatsapp_label": "5490000000000",
                        "address": "A",
                        "map_url": "#",
                        "map_link": "#",
                        "map_title": "M",
                        "labels": {"customer_service": "CS", "whatsapp": "W", "location": "L"},
                        "details": [],
                    },
                },
                "cart": {
                    "title": "C",
                    "meta_description": "D",
                    "heading": "H",
                    "items_heading": "I",
                    "pending_quote_label": "P",
                    "items": [],
                    "summary": {
                        "heading": "H",
                        "total_label": "T",
                        "total_value": "0",
                        "estimated_cost_label": "E",
                        "estimated_cost_value": "0",
                        "note": "N",
                        "submit_button": "S",
                    },
                },
                "schema": {
                    "type": "Organization",
                    "name": "Fallback",
                    "image": "#",
                    "logo": "#",
                    "url": "#",
                    "telephone": "+5490000000000",
                    "email": "a@a.com",
                    "description": "D",
                    "address": {
                        "streetAddress": "Calle",
                        "addressLocality": "Loc",
                        "addressRegion": "Prov",
                        "postalCode": "0000",
                        "addressCountry": "AR",
                    },
                    "geo": {"latitude": "-34.000", "longitude": "-58.000"},
                    "opening_hours": {"days": ["Monday"], "opens": "08:00", "closes": "17:00"},
                },
            }),
            encoding="utf-8",
        )
        (default_dir / "productos_tienda.yml").write_text(
            yaml.safe_dump({
                "articulos": [
                    {"id": 1, "nombre": "A", "descripcion": "Desc", "cantidad_por_defecto": 1000, "imagen": "a.svg"}
                ]
            }),
            encoding="utf-8",
        )
        (default_dir / "tarifas.yml").write_text(
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

        monkeypatch.setattr(cargadores, "DATA_DIR", data_dir)

        site = cargar_site("tenant_que_no_existe")
        assert site.site.brand == "Fallback"
