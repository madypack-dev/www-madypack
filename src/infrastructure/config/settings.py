import os

from pydantic import BaseModel, Field


class Settings(BaseModel):
    APP_TITLE: str = Field(default_factory=lambda: os.getenv("APP_TITLE", "Madypack"))
    LOG_LEVEL: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    CHATWOOT_URL: str = Field(default_factory=lambda: os.getenv("CHATWOOT_URL", "http://localhost:3000"))
    CHATWOOT_ACCOUNT_ID: int = Field(default_factory=lambda: int(os.getenv("CHATWOOT_ACCOUNT_ID", "1")))
    CHATWOOT_INBOX_ID: int = Field(default_factory=lambda: int(os.getenv("CHATWOOT_INBOX_ID", "1")))
    CHATWOOT_API_TOKEN: str = Field(default_factory=lambda: os.getenv("CHATWOOT_API_TOKEN", ""))
    BOLSA_SOLAP_CM: float = Field(default_factory=lambda: float(os.getenv("BOLSA_SOLAP_CM", "3.5")))
    IPC_DATA_PATH: str = Field(default_factory=lambda: os.getenv("IPC_DATA_PATH", "data/ipc.yml"))


_settings = Settings()

APP_TITLE: str = _settings.APP_TITLE
LOG_LEVEL: str = _settings.LOG_LEVEL
CHATWOOT_URL: str = _settings.CHATWOOT_URL
CHATWOOT_ACCOUNT_ID: int = _settings.CHATWOOT_ACCOUNT_ID
CHATWOOT_INBOX_ID: int = _settings.CHATWOOT_INBOX_ID
CHATWOOT_API_TOKEN: str = _settings.CHATWOOT_API_TOKEN
BOLSA_SOLAP_CM: float = _settings.BOLSA_SOLAP_CM
IPC_DATA_PATH: str = _settings.IPC_DATA_PATH
