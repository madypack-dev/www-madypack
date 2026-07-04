"""Tests para la configuración validada con Pydantic."""

import re

import pytest

from src.infraestructura.config.settings import Settings


class TestSettingsDefaults:
    def test_valores_por_defecto(self):
        settings = Settings()
        assert settings.APP_TITLE == "Ecommerce"
        assert settings.LOG_LEVEL == "INFO"
        assert settings.FALLBACK_TENANT == "default"
        assert "www.madypack.com.ar" in settings.MAPEO_TENANTS
        assert settings.MAPEO_TENANTS["www.madypack.com.ar"] == "madypack"
        assert settings.MAPEO_PUERTOS["8000"] == "default"
        assert settings.MAPEO_TENANT_PUERTO["default"] == "8000"
        assert isinstance(settings.PATRON_EMPRESA, re.Pattern)


class TestSettingsEnvironment:
    def test_mapeo_tenants_desde_env(self, monkeypatch):
        monkeypatch.setenv("MAPEO_TENANTS", "nuevo.dominio.com=nuevo_tenant")
        settings = Settings()
        assert settings.MAPEO_TENANTS["nuevo.dominio.com"] == "nuevo_tenant"
        # Los defaults se mantienen
        assert settings.MAPEO_TENANTS["www.madypack.com.ar"] == "madypack"

    def test_mapeo_puertos_desde_env(self, monkeypatch):
        monkeypatch.setenv("MAPEO_PUERTOS", "9000=otro_tenant")
        settings = Settings()
        assert settings.MAPEO_PUERTOS["9000"] == "otro_tenant"
        # Los defaults se mantienen
        assert settings.MAPEO_PUERTOS["8000"] == "default"
        # El mapeo inverso se actualiza
        assert settings.MAPEO_TENANT_PUERTO["otro_tenant"] == "9000"

    def test_app_title_desde_env(self, monkeypatch):
        monkeypatch.setenv("APP_TITLE", "Mi App")
        settings = Settings()
        assert settings.APP_TITLE == "Mi App"


class TestSettingsValidation:
    def test_mapeo_tenants_invalido_se_ignora(self):
        settings = Settings(MAPEO_TENANTS="sin_igual,otro=si")
        assert "sin_igual" not in settings.MAPEO_TENANTS
        assert settings.MAPEO_TENANTS["otro"] == "si"
