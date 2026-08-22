from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ROOT = Path(__file__).resolve().parent.parent
_ENV = _ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV),
        env_file_encoding="utf-8",
        extra="ignore",
    )
    app_host: str = "0.0.0.0"
    app_port: int = 8100
    sarvam_api_key: str = ""
    sarvam_base_url: str = "https://api.sarvam.ai"
    sarvam_tts_speaker: str = "shubh"
    sarvam_tts_model: str = "bulbul:v3"
    sarvam_tts_pace: float = 1.0
    sarvam_tts_sample_rate: int = 22050
    default_lang: str = "en"
    knowledge_dir: str = "./knowledge"

    @property
    def sarvam_key(self) -> str:
        key = (self.sarvam_api_key or "").strip()
        if not key or key.upper().startswith("REPLACE_WITH_"):
            return ""
        return key


settings = Settings()
