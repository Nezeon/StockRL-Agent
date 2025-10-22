"""Application configuration from environment variables"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    app_name: str = "StockRL-Agent"
    app_version: str = "0.1.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: str = "sqlite+aiosqlite:///./stockrl_dev.db"

    # Redis (optional, for WebSocket scaling)
    redis_url: Optional[str] = None

    # Security
    secret_key: str = "dev-secret-key-change-in-production-min-32-chars"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # Data Provider Configuration
    data_mode: str = "demo"  # demo or live
    data_provider: str = "mock"  # mock, yahoo, alphavantage, finnhub
    data_fetch_interval_seconds: int = 60

    # API Keys (only needed if data_mode=live)
    alpha_vantage_key: str = ""
    finnhub_key: str = ""

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # RL Agent Configuration
    checkpoint_dir: str = "./checkpoints"

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
