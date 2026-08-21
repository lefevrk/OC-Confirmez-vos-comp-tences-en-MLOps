"""Unit tests for the manually maintained serving schema."""

from pydantic import ValidationError
import pytest
from tests.payloads import valid_payload

from api.modules.scoring.presentation.schemas import PredictionRequest


def test_schema_has_all_champion_input_fields() -> None:
    """The manual schema remains aligned to the champion's 50 columns."""
    assert len(PredictionRequest.model_fields) == 50


def test_schema_accepts_aliases_and_preserves_model_column_names() -> None:
    """Client aliases are accepted and passed to the model without renaming."""
    payload = valid_payload()
    payload.pop("ext_source_2")
    payload["EXT_SOURCE_2"] = 0.42

    request = PredictionRequest.model_validate(payload)

    assert request.model_features()["EXT_SOURCE_2"] == 0.42
    assert "ext_source_2" not in request.model_features()


def test_schema_allows_omitting_an_optional_feature() -> None:
    """An omitted optional input reaches the model payload as null."""
    request = PredictionRequest.model_validate(valid_payload())

    assert request.model_features()["EXT_SOURCE_1"] is None


@pytest.mark.parametrize(
    "field_name",
    ["payment_credit_ratio", "days_birth", "organization_type"],
)
def test_schema_rejects_missing_required_feature(field_name: str) -> None:
    """A missing required model input is an invalid API request."""
    payload = valid_payload()
    del payload[field_name]

    with pytest.raises(ValidationError):
        PredictionRequest.model_validate(payload)


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [
        ("payment_credit_ratio", "not-a-number"),
        ("days_birth", "not-an-integer"),
        ("organization_type", "unseen-organization"),
        ("code_gender", "unknown-gender"),
        ("occupation_type", "unknown-occupation"),
        ("name_family_status", "unknown-family-status"),
        ("name_education_type", "unknown-education"),
    ],
)
def test_schema_rejects_invalid_feature_value(
    field_name: str,
    invalid_value: str,
) -> None:
    """Invalid types and values outside closed categories fail validation."""
    payload = valid_payload()
    payload[field_name] = invalid_value

    with pytest.raises(ValidationError):
        PredictionRequest.model_validate(payload)


def test_schema_rejects_unknown_feature() -> None:
    """A field not known by the model contract is not silently accepted."""
    with pytest.raises(ValidationError):
        PredictionRequest.model_validate({**valid_payload(), "unexpected": 1})


def test_schema_rejects_an_ext_source_outside_the_unit_range() -> None:
    """External source scores are normalized and must stay within [0, 1]."""
    with pytest.raises(ValidationError):
        PredictionRequest.model_validate({**valid_payload(), "ext_source_2": 1.5})


def test_schema_rejects_a_non_positive_monetary_amount() -> None:
    """Credit, annuity and goods price amounts cannot be zero or negative."""
    with pytest.raises(ValidationError):
        PredictionRequest.model_validate({**valid_payload(), "amt_credit": 0})
