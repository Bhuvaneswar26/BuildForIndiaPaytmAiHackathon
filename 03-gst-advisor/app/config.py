from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent / ".env"),
        extra="ignore",
    )
    app_host: str = "0.0.0.0"
    app_port: int = 8100
    sarvam_api_key: str = ""
    sarvam_base_url: str = "https://api.sarvam.ai"
    default_lang: str = "en"
    knowledge_dir: str = "./knowledge"


settings = Settings()
