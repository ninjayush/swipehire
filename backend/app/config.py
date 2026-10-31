import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Find root directory where .env might live
BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(ROOT_DIR / ".env"), str(BASE_DIR / ".env")),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Crustdata Configuration
    CRUSTDATA_API_KEY: str = ""
    crust_api_key: str = ""  # Support lowercase alias from .env
    CRUSTDATA_BASE_URL: str = "https://api.crustdata.com"
    CRUSTDATA_API_VERSION: str = "2025-11-01"
    CRUSTDATA_TIMEOUT_SECONDS: float = 30.0
    CRUSTDATA_MAX_RETRIES: int = 3

    # Database Configuration
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'swipehire.db'}"

    # App Settings
    DEBUG: bool = True
    UPLOAD_DIR: str = str(BASE_DIR / "uploads")
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    @property
    def api_key(self) -> str:
        """Return the active Crustdata API key checking both env var naming styles."""
        key = self.CRUSTDATA_API_KEY or self.crust_api_key or os.getenv("CRUSTDATA_API_KEY") or os.getenv("crust_api_key") or ""
        return key.strip().strip('"').strip("'")

settings = Settings()
