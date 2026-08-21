"""Manual Pydantic schema for champion v3 serving inputs."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PredictionRequest(BaseModel):
    """The 50 client-facing fields expected by the champion preprocessing pipeline."""

    model_config = ConfigDict(extra="forbid", validate_by_name=True, validate_by_alias=True)

    payment_credit_ratio: float
    ext_source_2: float = Field(ge=0, le=1, alias="EXT_SOURCE_2")
    ext_source_1: float | None = Field(None, ge=0, le=1, alias="EXT_SOURCE_1")
    ext_source_3: float | None = Field(None, ge=0, le=1, alias="EXT_SOURCE_3")
    days_birth: int = Field(alias="DAYS_BIRTH")
    amt_annuity: float = Field(gt=0, alias="AMT_ANNUITY")
    organization_type: Literal[
        "Advertising",
        "Agriculture",
        "Bank",
        "Business Entity Type 1",
        "Business Entity Type 2",
        "Business Entity Type 3",
        "Cleaning",
        "Construction",
        "Culture",
        "Electricity",
        "Emergency",
        "Government",
        "Hotel",
        "Housing",
        "Industry: type 1",
        "Industry: type 10",
        "Industry: type 11",
        "Industry: type 12",
        "Industry: type 13",
        "Industry: type 2",
        "Industry: type 3",
        "Industry: type 4",
        "Industry: type 5",
        "Industry: type 6",
        "Industry: type 7",
        "Industry: type 8",
        "Industry: type 9",
        "Insurance",
        "Kindergarten",
        "Legal Services",
        "Medicine",
        "Military",
        "Mobile",
        "Other",
        "Police",
        "Postal",
        "Realtor",
        "Religion",
        "Restaurant",
        "School",
        "Security",
        "Security Ministries",
        "Self-employed",
        "Services",
        "Telecom",
        "Trade: type 1",
        "Trade: type 2",
        "Trade: type 3",
        "Trade: type 4",
        "Trade: type 5",
        "Trade: type 6",
        "Trade: type 7",
        "Transport: type 1",
        "Transport: type 2",
        "Transport: type 3",
        "Transport: type 4",
        "University",
        "XNA",
    ] = Field(alias="ORGANIZATION_TYPE")
    previous_approved_cnt_payment_mean: float
    days_employed: float | None = Field(None, alias="DAYS_EMPLOYED")
    days_id_publish: int = Field(alias="DAYS_ID_PUBLISH")
    annuity_income_ratio: float
    previous_cnt_payment_mean: float
    bureau_active_days_credit_max: float | None = None
    installment_days_past_due_mean: float
    amt_credit: float = Field(gt=0, alias="AMT_CREDIT")
    installment_amt_payment_sum: float
    income_credit_ratio: float
    bureau_days_credit_max: float | None = None
    days_registration: float = Field(alias="DAYS_REGISTRATION")
    bureau_closed_days_credit_max: float | None = None
    amt_goods_price: float = Field(gt=0, alias="AMT_GOODS_PRICE")
    code_gender: Literal["F", "M", "XNA"] = Field(alias="CODE_GENDER")
    bureau_active_days_credit_enddate_min: float | None = None
    installment_days_before_due_sum: float
    installment_days_entry_payment_max: float
    pos_months_balance_size: float
    installment_payment_difference_mean: float
    credit_card_cnt_drawings_atm_current_mean: float | None = None
    employment_birth_ratio: float | None = None
    previous_days_decision_mean: float
    bureau_active_amt_credit_sum_sum: float | None = None
    occupation_type: Literal[
        "Accountants",
        "Cleaning staff",
        "Cooking staff",
        "Core staff",
        "Drivers",
        "HR staff",
        "High skill tech staff",
        "IT staff",
        "Laborers",
        "Low-skill Laborers",
        "Managers",
        "Medicine staff",
        "Private service staff",
        "Realty agents",
        "Sales staff",
        "Secretaries",
        "Security staff",
        "Waiters/barmen staff",
        "__MISSING__",
    ] = Field(alias="OCCUPATION_TYPE")
    installment_days_before_due_max: float
    installment_days_entry_payment_mean: float
    previous_application_credit_ratio_mean: float
    previous_approved_days_decision_max: float
    name_family_status: Literal[
        "Civil marriage", "Married", "Separated", "Single / not married", "Unknown", "Widow"
    ] = Field(alias="NAME_FAMILY_STATUS")
    bureau_closed_days_credit_update_mean: float | None = None
    bureau_days_credit_enddate_max: float | None = None
    previous_approved_cnt_payment_sum: float
    bureau_active_amt_credit_max_overdue_mean: float | None = None
    bureau_amt_credit_max_overdue_mean: float | None = None
    installment_amt_instalment_sum: float
    installment_days_entry_payment_sum: float
    pos_sk_dpd_def_mean: float
    name_education_type: Literal[
        "Academic degree",
        "Higher education",
        "Incomplete higher",
        "Lower secondary",
        "Secondary / secondary special",
    ] = Field(alias="NAME_EDUCATION_TYPE")
    bureau_amt_credit_sum_sum: float | None = None
    installment_amt_instalment_max: float
    bureau_active_amt_credit_sum_mean: float | None = None
    bureau_active_days_credit_update_mean: float | None = None

    def model_features(self) -> dict[str, float | int | str | None]:
        """Return model column names without any API-only transformation."""
        return self.model_dump(by_alias=True)


class PredictionResponse(BaseModel):
    """Scoring response returned by the predictions endpoint."""

    prediction_id: str
    probability: float
    decision: int
    model_version: str
