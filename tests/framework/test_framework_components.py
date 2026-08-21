"""Framework utilities have deterministic, security-aware behaviour."""

import pytest

from config.settings import ConfigurationError, load_settings
from framework.quality.quality_gate import GateResult, render_decision
from framework.utils.logger import sanitise
from framework.utils.retry import retry_call


def test_dev_configuration_loads() -> None:
    settings = load_settings("dev", environ={})
    assert settings.environment == "dev"
    assert str(settings.api_base_url) == "http://localhost:8000/"


@pytest.mark.negative
def test_qa_configuration_fails_early_without_api_url() -> None:
    with pytest.raises(ConfigurationError, match="API_BASE_URL is required"):
        load_settings("qa", environ={})


def test_recursive_logging_sanitisation() -> None:
    payload = sanitise(
        {
            "Authorization": "Bearer secret",
            "customer": {"email": "person@example.com", "name": "Avery"},
            "items": [{"token": "secret", "sku": "SKU-1"}],
        }
    )
    assert payload["Authorization"] == "***REDACTED***"
    assert payload["customer"]["email"] == "***REDACTED***"
    assert payload["items"][0]["token"] == "***REDACTED***"
    assert payload["items"][0]["sku"] == "SKU-1"


def test_retry_terminates_on_success_without_duplicate_attempt() -> None:
    values = iter([503, 503, 200, 200])
    result = retry_call(lambda: next(values), should_retry=lambda status: status == 503)
    assert result.value == 200
    assert result.attempts == 3
    assert next(values) == 200


@pytest.mark.parametrize(
    ("result", "threshold", "expected"),
    [
        (GateResult(10, 0, 0, 0), 100, True),
        (GateResult(100, 1, 0, 0), 98, False),
    ],
)
def test_quality_gate_decision(
    result: GateResult,
    threshold: float,
    expected: bool,
) -> None:
    output, passed = render_decision(result, threshold)
    assert passed is expected
    assert "RELEASE DECISION" in output
