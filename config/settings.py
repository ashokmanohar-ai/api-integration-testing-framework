"""Fail-fast configuration loading with explicit secret precedence."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

import yaml
from pydantic import ValidationError

from config.schema import FrameworkSettings

ROOT = Path(__file__).resolve().parents[1]


class ConfigurationError(RuntimeError):
    """Raised before a test runs when configuration is unusable."""


ENV_MAPPING = {
    "API_BASE_URL": "api_base_url",
    "GRAPHQL_URL": "graphql_url",
    "DATABASE_URL": "database_url",
    "WIREMOCK_URL": "wiremock_url",
    "BROKER_URL": "broker_url",
    "REQUEST_TIMEOUT": "request_timeout",
    "LOG_LEVEL": "log_level",
    "CLIENT_ID": "client_id",
    "CLIENT_SECRET": "client_secret",
}


def load_settings(
    environment: str | None = None,
    *,
    environ: Mapping[str, str] | None = None,
) -> FrameworkSettings:
    """Load non-secrets from YAML and overrides/secrets from the environment."""

    source = os.environ if environ is None else environ
    selected = (environment or source.get("TEST_ENV") or "dev").lower()
    config_path = ROOT / "config" / "environments" / f"{selected}.yaml"
    if not config_path.exists():
        raise ConfigurationError(f"Unknown TEST_ENV '{selected}': {config_path} does not exist")

    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    raw["environment"] = selected
    for env_name, setting_name in ENV_MAPPING.items():
        if value := source.get(env_name):
            raw[setting_name] = value

    if selected != "dev" and not source.get("API_BASE_URL"):
        raise ConfigurationError(
            f"API_BASE_URL is required for environment '{selected}'. "
            "Supply it through an environment variable or CI secret."
        )
    if selected != "dev" and not source.get("GRAPHQL_URL"):
        raise ConfigurationError(
            f"GRAPHQL_URL is required for environment '{selected}'. "
            "Supply it through an environment variable or CI secret."
        )
    if selected != "dev" and not source.get("DATABASE_URL"):
        raise ConfigurationError(
            f"DATABASE_URL is required for environment '{selected}'. "
            "Supply it through an environment variable or CI secret."
        )
    try:
        return FrameworkSettings.model_validate(raw)
    except ValidationError as exc:
        raise ConfigurationError(f"Invalid configuration for '{selected}': {exc}") from exc
