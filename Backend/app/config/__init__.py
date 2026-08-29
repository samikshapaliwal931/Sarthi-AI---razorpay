from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "sarthi"
    app_env: Environment = Environment.DEVELOPMENT
    debug: bool = True
    secret_key: str = "change-me-in-production"
    api_base_url: str = "http://localhost:8000"

    database_url: str = "postgresql+asyncpg://sarthi:sarthi@localhost:5432/sarthi"
    redis_url: str = "redis://localhost:6379/0"

    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""

    openai_api_key: str = ""
    anthropic_api_key: str = ""
    openrouter_api_key: str = ""
    openrouter_model: str = "z-ai/glm-5.2:free"
    openrouter_fallback_models: str = "openrouter/free,google/gemma-4-31b-it:free,minimax/minimax-m3:free"
    default_llm_provider: str = "openrouter"
    default_llm_model: str = "z-ai/glm-5.2:free"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    @property
    def openrouter_fallback_list(self) -> list[str]:
        return [m.strip() for m in self.openrouter_fallback_models.split(",") if m.strip()]

    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 1440

    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    log_level: str = "INFO"

    recommendation_exploration_rate: float = 0.1
    recommendation_weights: dict[str, float] = Field(
        default_factory=lambda: {
            "semantic_similarity": 0.25,
            "purchase_affinity": 0.20,
            "popularity": 0.15,
            "margin_signal": 0.15,
            "inventory_signal": 0.10,
            "contextual_relevance": 0.10,
            "repetition_penalty": 0.05,
        }
    )

    @property
    def is_production(self) -> bool:
        return self.app_env == Environment.PRODUCTION

    @property
    def sync_database_url(self) -> str:
        return self.database_url.replace("+asyncpg", "+psycopg2").replace(
            "postgresql+psycopg2", "postgresql"
        )


settings = Settings()
