from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_host: str = "0.0.0.0"
    app_port: int = 8090
    mcp_notify_url: str = "http://127.0.0.1:8091"
    advisor_public_url: str = "http://127.0.0.1:8100"
    gst_portal: str = "https://reg.gst.gov.in/registration/"
    sarvam_api_key: str = ""
    openai_api_key: str = ""
    whatsapp_mode: str = "mock"
    notify_log: str = "./data/notifications.jsonl"


settings = Settings()
