import os
from datetime import date
from typing import Literal

from flask import current_app
from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field

from errors import ApiError


class ParsedExpenseParticipant(BaseModel):
    user_id: int | None = None
    display_name: str
    selected: bool = True
    amount_paise: int | None = None
    weight: int | None = None


class ParsedExpenseDraft(BaseModel):
    confidence: float
    description: str | None = None
    amount_paise: int | None = None
    currency_code: str = "INR"
    expense_date: str | None = None
    payer_user_id: int | None = None
    payer_name: str | None = None
    split_mode: Literal["equal_all", "equal_subset", "custom", "weights"] | None = None
    participants: list[ParsedExpenseParticipant] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class ParsedBillItem(BaseModel):
    item_name: str
    amount_paise: int


class ParsedBillDraft(BaseModel):
    confidence: float
    merchant_name: str | None = None
    description: str | None = None
    bill_date: str | None = None
    currency_code: str = "INR"
    total_paise: int | None = None
    line_items: list[ParsedBillItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


def parse_expense_text(text: str, group_members, current_user, today: date | None = None):
    client = _get_client()
    if client is None:
        return {
            "success": False,
            "fallback_message": "AI parsing is unavailable because OPENAI_API_KEY is not configured.",
        }

    today = today or date.today()
    instructions = f"""
You extract shared expense drafts for a Splitwise-style app.

Today's date is {today.isoformat()}.
The current user is {current_user['name']} (user_id={current_user['id']}).
Allowed group members are:
{_format_member_context(group_members)}

Rules:
- Return a draft that matches the schema exactly.
- Use amount_paise, never floating-point rupees.
- Resolve relative dates like "last night" against today's date.
- Only use payer_user_id or participant user_id values from the allowed members.
- If a member name is ambiguous or missing, keep user_id null and add a warning.
- If the request implies reduced or uneven shares, use split_mode "custom" and fill amount_paise values.
- If the request implies proportional shares, use split_mode "weights" and fill weight values.
- If the request clearly means everyone in the group, use split_mode "equal_all" and leave participants empty.
- Never invent amounts, members, or dates. Lower confidence and add warnings instead.
"""

    try:
        response = client.responses.parse(
            model=current_app.config["OPENAI_MODEL"],
            instructions=instructions.strip(),
            input=f"Expense text: {text}",
            temperature=0.1,
            text_format=ParsedExpenseDraft,
            max_output_tokens=900,
        )
    except Exception as error:
        return {
            "success": False,
            "fallback_message": "We couldn't parse that expense right now. Please review the manual form instead.",
            "error": str(error),
        }

    draft = response.output_parsed
    if draft is None:
        return {
            "success": False,
            "fallback_message": "The AI response was empty. Please use the manual form.",
        }

    warnings = list(draft.warnings)
    unresolved = [participant.display_name for participant in draft.participants if participant.user_id is None]
    if unresolved:
        warnings.append(f"Unresolved members: {', '.join(unresolved)}.")

    critical_missing = any(
        value in (None, "", [])
        for value in [draft.description, draft.amount_paise, draft.expense_date, draft.payer_user_id, draft.split_mode]
    )

    if draft.confidence < 0.45 or critical_missing or unresolved:
        return {
            "success": False,
            "fallback_message": "The AI draft needs too much manual cleanup, so we switched back to the manual form.",
            "draft": _serialize_expense_draft(draft, warnings),
        }

    return {
        "success": True,
        "draft": _serialize_expense_draft(draft, warnings),
        "message": "Draft parsed. Please review it before saving.",
    }


def parse_bill_text(text: str, today: date | None = None):
    client = _get_client()
    if client is None:
        return {
            "success": False,
            "fallback_message": "AI bill parsing is unavailable because OPENAI_API_KEY is not configured.",
        }

    today = today or date.today()
    instructions = f"""
You extract structured restaurant or receipt bill data.

Today's date is {today.isoformat()}.

Rules:
- Return the schema exactly.
- All money must be in amount_paise or total_paise.
- Extract every usable line item when present.
- If taxes, tips, or service charges appear, include them as line items too.
- Do not invent missing items. If you cannot confidently recover line items, lower confidence and add warnings.
- Description should be a clean human-readable label such as "Restaurant bill at X".
"""

    try:
        response = client.responses.parse(
            model=current_app.config["OPENAI_MODEL"],
            instructions=instructions.strip(),
            input=f"Bill text: {text}",
            temperature=0.1,
            text_format=ParsedBillDraft,
            max_output_tokens=900,
        )
    except Exception as error:
        return {
            "success": False,
            "fallback_message": "We couldn't parse that bill right now. Please add the expense manually.",
            "error": str(error),
        }

    draft = response.output_parsed
    if draft is None:
        return {
            "success": False,
            "fallback_message": "The AI response was empty. Please add the bill manually.",
        }

    critical_missing = draft.total_paise is None or not draft.line_items
    if draft.confidence < 0.45 or critical_missing:
        return {
            "success": False,
            "fallback_message": "The bill text wasn't clear enough to safely extract line items.",
            "draft": _serialize_bill_draft(draft),
        }

    line_item_total = sum(item.amount_paise for item in draft.line_items)
    if line_item_total != draft.total_paise:
        warning = "Line items did not match the detected total, so the draft may need manual review."
        draft.warnings.append(warning)

    return {
        "success": True,
        "draft": _serialize_bill_draft(draft),
        "message": "Bill parsed. Assign each line item to members before saving.",
    }


def _get_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def _format_member_context(group_members):
    return "\n".join(f"- user_id={member['id']}: {member['name']} <{member['email']}>" for member in group_members)


def _serialize_expense_draft(draft: ParsedExpenseDraft, warnings):
    return {
        "confidence": draft.confidence,
        "description": draft.description,
        "amount_paise": draft.amount_paise,
        "currency_code": draft.currency_code,
        "expense_date": draft.expense_date,
        "payer_user_id": draft.payer_user_id,
        "payer_name": draft.payer_name,
        "split_mode": draft.split_mode,
        "participants": [participant.model_dump() for participant in draft.participants],
        "warnings": warnings,
        "notes": draft.notes,
    }


def _serialize_bill_draft(draft: ParsedBillDraft):
    return {
        "confidence": draft.confidence,
        "merchant_name": draft.merchant_name,
        "description": draft.description,
        "bill_date": draft.bill_date,
        "currency_code": draft.currency_code,
        "total_paise": draft.total_paise,
        "line_items": [item.model_dump() for item in draft.line_items],
        "warnings": draft.warnings,
        "notes": draft.notes,
    }
