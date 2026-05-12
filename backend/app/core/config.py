"""Application configuration using Pydantic Settings."""
from functools import lru_cache
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # Application
    APP_NAME: str = "LexChain Sovereign"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False

    # Security
    SECRET_KEY: str = "change-me-in-production-min-32-chars"
    JWT_SECRET: str = "jwt-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ENCRYPTION_KEY: str = ""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://lexchain:password@localhost:5432/lexchain"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str = "redis://:password@localhost:6379/0"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:8000", "http://localhost:3000"]

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000

    # AI APIs
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-opus-20240229"

    # Blockchain
    WEB3_PROVIDER_URL: str = "https://sepolia.infura.io/v3/your-project-id"
    MAINNET_RPC_URL: str = ""
    SEPOLIA_RPC_URL: str = ""
    BASE_RPC_URL: str = ""
    POLYGON_RPC_URL: str = ""
    ARBITRUM_RPC_URL: str = ""

    # Contract Addresses
    LEX_GOVERNOR_ADDRESS: str = ""
    LEX_ASSET_TOKEN_ADDRESS: str = ""
    LEGAL_METADATA_REGISTRY_ADDRESS: str = ""
    COMPLIANCE_REGISTRY_ADDRESS: str = ""
    LEGAL_EVIDENCE_STORE_ADDRESS: str = ""

    # Compliance APIs
    CHAINALYSIS_API_KEY: str = ""
    TRM_LABS_API_KEY: str = ""
    SUMSUB_APP_ID: str = ""
    SUMSUB_SECRET_KEY: str = ""
    SUMSUB_BASE_URL: str = "https://api.sumsub.com"
    PERSONA_API_KEY: str = ""
    STRIPE_IDENTITY_KEY: str = ""

    # Email
    SMTP_HOST: str = "smtp.example.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@lexchain-sovereign.com"
    SMTP_FROM_NAME: str = "LexChain Sovereign"

    # Monitoring
    SENTRY_DSN: str = ""
    PROMETHEUS_ENABLED: bool = True

    # File Storage
    IPFS_GATEWAY_URL: str = "https://ipfs.io"
    IPFS_API_URL: str = "http://localhost:5001"
    MAX_UPLOAD_SIZE_MB: int = 50

    # Logging
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    LOG_FORMAT: Literal["json", "text"] = "json"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.ENCRYPTION_KEY:
            from cryptography.fernet import Fernet
            self.ENCRYPTION_KEY = Fernet.generate_key().decode()

    @property
    def redis_password(self) -> str:
        """Extract Redis password from URL."""
        if ":" in self.REDIS_URL:
            return self.REDIS_URL.split(":")[-1].split("@")[0]
        return ""

    @property
    def alchemy_database_url(self) -> str:
        """Get synchronous database URL for migrations."""
        return self.DATABASE_URL.replace("+asyncpg", "")


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()