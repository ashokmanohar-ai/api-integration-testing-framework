"""Contract evolution examples distinguish safe additions from breaking renames."""

import pytest
from pydantic import ValidationError

from framework.models.customer import CustomerResponse

BASE = {
    "id": "11111111-1111-4111-8111-111111111111",
    "first_name": "Avery",
    "last_name": "Tester",
    "email": "avery@example.com",
    "status": "ACTIVE",
    "created_at": "2026-01-01T00:00:00Z",
}


@pytest.mark.contract
def test_optional_provider_field_is_non_breaking() -> None:
    evolved = {**BASE, "loyalty_tier": "GOLD"}
    assert CustomerResponse.model_validate(evolved).first_name == "Avery"


@pytest.mark.contract
def test_required_property_rename_is_detected() -> None:
    breaking = {**BASE, "given_name": BASE["first_name"]}
    breaking.pop("first_name")
    with pytest.raises(ValidationError):
        CustomerResponse.model_validate(breaking)
