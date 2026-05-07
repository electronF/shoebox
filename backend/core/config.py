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
        upload_dir:     Storage directory for uploaded files.
        debug:          Enables SQL logs and reload mode.
        app_title:      Title displayed in OpenAPI documentation.
        app_version:    API version.
    """

    database_url: str = "sqlite:///./data/shoebox.db"
    upload_dir:   str = "./data/uploads"
    debug:         bool = False
    app_title:    str = "Shoebox API"
    app_version:  str = "0.1.0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def upload_path(self) -> Path:
        """Returns the upload directory as a Path object."""
        path = Path(self.upload_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path


# Singleton — imported throughout the project
settings = Settings()