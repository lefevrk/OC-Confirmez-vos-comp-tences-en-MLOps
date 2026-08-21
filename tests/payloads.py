"""Shared payload builder for the champion serving schema, used across test suites."""

from api.modules.scoring.presentation.schemas import PredictionRequest


def valid_payload() -> dict[str, float | int | str]:
    """Build a payload containing every required model feature."""
    categorical_values = {
        "organization_type": "Bank",
        "code_gender": "F",
        "occupation_type": "Accountants",
        "name_family_status": "Married",
        "name_education_type": "Higher education",
    }
    integer_fields = {"days_birth", "days_id_publish"}

    return {
        field_name: categorical_values.get(field_name, -1 if field_name in integer_fields else 1.0)
        for field_name, field in PredictionRequest.model_fields.items()
        if field.is_required()
    }
