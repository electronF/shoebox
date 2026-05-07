"""
Centralized configuration via pydantic-settings.

Reads variables from .env or system environment variables.
All application configuration passes through this object.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Application settings loaded from .env.

    Attributes:
        database_url:   SQLAlchemy connection URL.
        upload_dir:     Directory for stored uploaded files.
        debug:          Enables SQL logging and verbose output.
        testing:        When True, the lifespan skips create_all_tables().
                        Set automatically by the test suite via conftest.py.
        app_title:      Title shown in the OpenAPI docs.
        app_version:    API version string.
    """

    database_url: str  = "sqlite:///./data/shoebox.db"
    upload_dir:   str  = "./data/uploads"
    debug:        bool = False
    testing:      bool = False        # ← was missing
    app_title:    str  = "Shoebox API"
    app_version:  str  = "0.1.0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def upload_path(self) -> Path:
        """Returns the upload directory as a resolved Path, creating it if needed."""
        path = Path(self.upload_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

# Singleton — imported throughout the project
settings = Settings()