
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_env_path = Path(__file__).resolve().parent.parent.parent / ".env"

class Settings(BaseSettings):
    NVIDIA_API_KEY: str = ""
    NVIDIA_MODEL: str = "meta/llama-3.2-11b-vision-instruct"
    NVIDIA_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_FILE_TYPES: str = "csv,xlsx,xls,json"
    MAX_DATASETS_PER_WORKSPACE: int = 10
    DATA_DIR: str = "data"

    model_config = SettingsConfigDict(
        env_file=(_env_path, ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_STORAGE_BUCKET: str = "datly-datasets"

    SARVAM_API_KEY: str = ""
    SARVAM_STT_MODEL: str = "saaras:v4"
    SARVAM_TTS_MODEL: str = "bulbul:v3"
    SARVAM_STT_MODE: str = "transcribe"
    SARVAM_TTS_LANGUAGE: str = "en-IN"
    SARVAM_TTS_SPEAKER: str = "shubh"
    SARVAM_TTS_SAMPLE_RATE: int = 24000
    
    VOICE_MAX_AUDIO_SECONDS: int = 30
    VOICE_MAX_TTS_CHARACTERS: int = 2500

    @property
    def allowed_extensions(self) -> list[str]:
        return [ext.strip().lower() for ext in self.ALLOWED_FILE_TYPES.split(",")]

settings = Settings()
