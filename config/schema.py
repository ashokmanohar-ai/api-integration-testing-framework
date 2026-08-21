"""Configuration schema shared by tests and command-line helpers."""

from pydantic import AnyHttpUrl, BaseModel, Field, SecretStr


class FrameworkSettings(BaseModel):
    """Validated, immutable settings for one target environment."""

    environment: str = "dev"
    api_base_url: AnyHttpUrl
    graphql_url: AnyHttpUrl
    database_url: str = "sqlite:///./acme-commerce.db"
    wiremock_url: AnyHttpUrl = "http://localhost:8080"  # type: ignore[assignment]
    broker_url: str = "localhost:19092"
    request_timeout: float = Field(default=5.0, gt=0, le=60)
    log_level: str = "INFO"
    client_id: str | None = None
    client_secret: SecretStr | None = None

    model_config = {"frozen": True, "extra": "forbid"}
