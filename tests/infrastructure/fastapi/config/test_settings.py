"""Tests para la configuración de Madypack."""

import pytest

from src.infrastructure.config.settings import Settings


class TestSettingsDefaults:
    def test_valores_por_defecto(self):
        settings = Settings()
        assert settings.APP_TITLE == "Madypack"
        assert settings.LOG_LEVEL == "INFO"
        assert settings.BOLSA_SOLAP_CM == 3.5


class TestSettingsEnvironment:
    def test_app_title_desde_env(self, monkeypatch):
        monkeypatch.setenv("APP_TITLE", "Mi App")
        settings = Settings()
        assert settings.APP_TITLE == "Mi App"

    def test_bolsa_solap_cm_desde_env(self, monkeypatch):
        monkeypatch.setenv("BOLSA_SOLAP_CM", "4.0")
        settings = Settings()
        assert settings.BOLSA_SOLAP_CM == 4.0
