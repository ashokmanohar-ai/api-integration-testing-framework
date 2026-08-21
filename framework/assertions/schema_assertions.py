"""Pydantic and JSON-schema compatible assertion helpers."""

from typing import Any

from pydantic import BaseModel, ValidationError


def assert_model[ModelT: BaseModel](payload: Any, model: type[ModelT]) -> ModelT:
    try:
        return model.model_validate(payload)
    except ValidationError as exc:
        raise AssertionError(f"Payload is incompatible with {model.__name__}: {exc}") from exc


def assert_no_unexpected_keys(payload: dict[str, Any], allowed: set[str]) -> None:
    unexpected = set(payload) - allowed
    assert not unexpected, f"Unexpected response properties: {sorted(unexpected)}"
