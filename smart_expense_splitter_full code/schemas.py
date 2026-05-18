from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


ALLOWED_SPLIT_MODES = ("equal_all", "equal_subset", "custom", "weights")
ALLOWED_SOURCES = ("manual", "ai_natural_language", "ai_bill_text")


def _trimmed(value: str) -> str:
    trimmed = value.strip()
    if not trimmed:
        raise ValueError("This field cannot be empty.")
    return trimmed


class UserCreateRequest(BaseModel):
    name: str
    email: str

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return _trimmed(value)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        email = _trimmed(value).lower()
        if "@" not in email or "." not in email.split("@")[-1]:
            raise ValueError("Enter a valid email address.")
        return email


class GroupCreateRequest(BaseModel):
    name: str
    description: str | None = None
    created_by_user_id: int
    member_ids: list[int]
    currency_code: str = "INR"

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return _trimmed(value)

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str | None) -> str | None:
        return value.strip() if value else None

    @field_validator("currency_code")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        currency = value.strip().upper()
        if len(currency) != 3:
            raise ValueError("Currency code must be a 3-letter ISO code.")
        return currency

    @model_validator(mode="after")
    def validate_members(self):
        unique_member_ids = list(dict.fromkeys(self.member_ids))
        if len(unique_member_ids) < 2:
            raise ValueError("A group must have at least 2 members.")
        if self.created_by_user_id not in unique_member_ids:
            raise ValueError("The creator must be part of the group.")
        self.member_ids = unique_member_ids
        return self


class ExpenseParticipantInput(BaseModel):
    user_id: int
    selected: bool = True
    amount_paise: int | None = None
    weight: int | None = None

    @field_validator("amount_paise")
    @classmethod
    def validate_amount(cls, value: int | None) -> int | None:
        if value is not None and value < 0:
            raise ValueError("Participant amounts cannot be negative.")
        return value

    @field_validator("weight")
    @classmethod
    def validate_weight(cls, value: int | None) -> int | None:
        if value is not None and value <= 0:
            raise ValueError("Weights must be positive integers.")
        return value


class ExpenseItemInput(BaseModel):
    item_name: str
    amount_paise: int
    assigned_user_ids: list[int]

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("item_name")
    @classmethod
    def validate_item_name(cls, value: str) -> str:
        return _trimmed(value)

    @field_validator("amount_paise")
    @classmethod
    def validate_item_amount(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Line item amounts must be positive.")
        return value

    @model_validator(mode="after")
    def validate_assignees(self):
        unique_assignees = list(dict.fromkeys(self.assigned_user_ids))
        if not unique_assignees:
            raise ValueError("Each line item must be assigned to at least one member.")
        self.assigned_user_ids = unique_assignees
        return self


class ExpenseCreateRequest(BaseModel):
    payer_user_id: int
    created_by_user_id: int
    description: str
    amount_paise: int
    currency_code: str = "INR"
    expense_date: date
    split_mode: Literal["equal_all", "equal_subset", "custom", "weights"]
    participants: list[ExpenseParticipantInput] = Field(default_factory=list)
    notes: str | None = None
    source_type: Literal["manual", "ai_natural_language", "ai_bill_text"] = "manual"
    ai_confidence: float | None = None
    line_items: list[ExpenseItemInput] = Field(default_factory=list)

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str) -> str:
        return _trimmed(value)

    @field_validator("amount_paise")
    @classmethod
    def validate_amount(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Expense amount must be greater than zero.")
        return value

    @field_validator("currency_code")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        currency = value.strip().upper()
        if len(currency) != 3:
            raise ValueError("Currency code must be a 3-letter ISO code.")
        return currency

    @field_validator("notes")
    @classmethod
    def validate_notes(cls, value: str | None) -> str | None:
        return value.strip() if value else None

    @field_validator("ai_confidence")
    @classmethod
    def validate_confidence(cls, value: float | None) -> float | None:
        if value is not None and not 0 <= value <= 1:
            raise ValueError("AI confidence must be between 0 and 1.")
        return value

    @model_validator(mode="after")
    def validate_structure(self):
        if self.split_mode != "equal_all" and not self.participants:
            raise ValueError("Participants are required for the selected split mode.")
        if self.source_type == "ai_bill_text" and not self.line_items:
            raise ValueError("Bill-based expenses must include parsed line items.")
        return self


class AIExpenseParseRequest(BaseModel):
    text: str
    current_user_id: int

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        return _trimmed(value)


class AIBillParseRequest(BaseModel):
    text: str

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        return _trimmed(value)
