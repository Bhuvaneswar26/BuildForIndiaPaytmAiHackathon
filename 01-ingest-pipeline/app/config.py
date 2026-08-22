from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8088
    paytm_base_url: str = "http://127.0.0.1:8088"
    paytm_mid: str = "INTEGR77698636129383"
    paytm_merchant_key: str = "mock-merchant-key"
    paytm_skip_checksum: bool = True

    cron_hour: int = 22
    cron_minute: int = 0

    alert_agent_url: str = "http://127.0.0.1:8090"
    sqlite_path: str = "./data/ingest.dev.db"
    advisor_public_url: str = "http://127.0.0.1:8100"
    demo_merchant_id: str = "KIRANA_MH_001"

    @property
    def is_live_paytm(self) -> bool:
        return "paytmpayments.com" in self.paytm_base_url


def load_settings() -> Settings:
    env = (Path(__file__).resolve().parent.parent / f".env.{_detect_env()}")
    if env.exists():
        return Settings(_env_file=str(env), _env_file_encoding="utf-8")
    return Settings()


def _detect_env() -> str:
    import os

    return os.getenv("APP_ENV", "development")


settings = load_settings()
