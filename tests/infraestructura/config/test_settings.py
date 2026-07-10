"""Tests para la configuración de Madypack."""

import pytest

from src.infraestructura.config.settings import Settings


class TestSettingsDefaults:
    def test_valores_por_defecto(self):
        settings = Settings()
        assert settings.APP_TITLE == "Madypack"
        assert settings.LOG_LEVEL == "INFO"


class TestSettingsEnvironment:
    def test_app_title_desde_env(self, monkeypatch):
        monkeypatch.setenv("APP_TITLE", "Mi App")
        settings = Settings()
        assert settings.APP_TITLE == "Mi App"
