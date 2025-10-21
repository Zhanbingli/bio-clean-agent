"""Application configuration management using pydantic-settings.

This module provides centralized configuration management with environment
variable support, validation, and type safety.
"""

from pathlib import Path
from typing import List, Optional

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:
    # Fallback for older pydantic or when pydantic-settings not installed
    from pydantic import BaseSettings

    class SettingsConfigDict:  # type: ignore
        """Dummy settings config dict for backward compatibility."""

        def __init__(self, **kwargs):
            pass


class Settings(BaseSettings):
    """Application settings with environment variable support.

    All settings can be overridden via environment variables with the same name.
    Example: API_HOST environment variable overrides api_host setting.

    Load from .env file if present.
    """

    # Try to use new pydantic-settings API, fall back to old if not available
    try:
        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            case_sensitive=False,
            extra="ignore",
        )
    except:
        class Config:
            env_file = ".env"
            env_file_encoding = "utf-8"
            case_sensitive = False
            extra = "ignore"

    # API Server Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8080
    api_workers: int = 4
    api_reload: bool = False

    # LLM Settings
    openai_api_key: Optional[str] = None
    llm_model: str = "gpt-3.5-turbo"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2000
    llm_top_p: float = 1.0

    # Security Settings
    max_file_size: int = 100 * 1024 * 1024  # 100MB in bytes
    allowed_origins: str = "http://localhost:8080,http://localhost:3000"
    secret_key: Optional[str] = None
    enable_auth: bool = False

    # Data Processing Settings
    default_output_dir: str = "outputs"
    default_data_dir: str = "data"
    enable_phi_masking: bool = True
    phi_hash_salt: str = "bio-clean-agent-default-salt"  # Should be overridden in production

    # Logging Settings
    log_level: str = "INFO"
    log_dir: str = "logs"
    log_format: str = "json"  # json or text
    log_max_size: int = 10 * 1024 * 1024  # 10MB
    log_backup_count: int = 5

    # Feature Flags
    enable_web_interface: bool = True
    enable_api: bool = True
    enable_metrics: bool = False
    enable_llm: bool = True

    # Quality Thresholds
    min_quality_score: float = 0.6
    warn_quality_score: float = 0.8

    # Performance Settings
    max_concurrent_jobs: int = 10
    job_timeout_seconds: int = 3600  # 1 hour
    cleanup_completed_jobs_after_hours: int = 24

    # Database Settings (for future use)
    database_url: Optional[str] = None
    database_pool_size: int = 5

    def get_allowed_origins_list(self) -> List[str]:
        """Get allowed origins as a list.

        Returns:
            List of allowed origin URLs
        """
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    def get_output_path(self) -> Path:
        """Get output directory as Path object.

        Returns:
            Path object for output directory
        """
        return Path(self.default_output_dir)

    def get_data_path(self) -> Path:
        """Get data directory as Path object.

        Returns:
            Path object for data directory
        """
        return Path(self.default_data_dir)

    def get_log_path(self) -> Path:
        """Get log directory as Path object.

        Returns:
            Path object for log directory
        """
        return Path(self.log_dir)

    def validate_paths(self) -> None:
        """Create necessary directories if they don't exist."""
        self.get_output_path().mkdir(parents=True, exist_ok=True)
        self.get_log_path().mkdir(parents=True, exist_ok=True)

    def is_production(self) -> bool:
        """Check if running in production mode.

        Returns:
            True if production mode based on configuration
        """
        return (
            not self.api_reload
            and self.log_level.upper() in ["INFO", "WARNING", "ERROR"]
            and self.enable_auth
        )

    def is_development(self) -> bool:
        """Check if running in development mode.

        Returns:
            True if development mode
        """
        return not self.is_production()


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get global settings instance.

    Returns:
        Settings instance

    Example:
        >>> settings = get_settings()
        >>> print(settings.api_port)
        8080
    """
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.validate_paths()
    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment.

    Useful for testing or when environment changes.

    Returns:
        New Settings instance
    """
    global _settings
    _settings = Settings()
    _settings.validate_paths()
    return _settings


# Convenience functions


def get_api_base_url() -> str:
    """Get base API URL.

    Returns:
        Base URL for API (e.g., http://localhost:8080)
    """
    settings = get_settings()
    return f"http://{settings.api_host}:{settings.api_port}"


def is_llm_enabled() -> bool:
    """Check if LLM features are enabled.

    Returns:
        True if LLM is enabled and API key is configured
    """
    settings = get_settings()
    return settings.enable_llm and settings.openai_api_key is not None


def get_max_file_size_mb() -> float:
    """Get maximum file size in megabytes.

    Returns:
        Max file size in MB
    """
    settings = get_settings()
    return settings.max_file_size / (1024 * 1024)
