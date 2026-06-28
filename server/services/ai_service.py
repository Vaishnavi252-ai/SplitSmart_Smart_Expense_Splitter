import os
from datetime import date
from typing import Literal

from flask import current_app
from pydantic import BaseModel, ConfigDict, Field, model_validator

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
    # The model sometimes returns other keys like `confidence` nested/strings,
    # or uses `date`/`payments`/`split_allocations` from a different schema.
    # We support common aliases and ignore unrelated fields.
    confidence: float | None = None
    merchant_name: str | None = None
    description: str | None = None
    # Support both `bill_date` and `date`.
    bill_date: str | None = None
    currency_code: str = "INR"
    total_paise: int | None = None
    line_items: list[ParsedBillItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")

    @model_validator(mode="before")
    @classmethod
    def normalize_aliases(cls, data):
        if not isinstance(data, dict):
            return data

        # alias `date` -> `bill_date`
        if data.get("bill_date") is None and data.get("date") is not None:
            data["bill_date"] = data.get("date")

        # alias `total` / `amount_paise` style keys if present (best-effort)
        if data.get("total_paise") is None:
            for key in ("total", "grand_total_paise", "amount_paise"):
                if key in data and isinstance(data[key], int):
                    data["total_paise"] = data[key]
                    break

        # Some LLM outputs may use `line_items` objects with `item_name` under different keys.
        if isinstance(data.get("line_items"), list):
            normalized = []
            for li in data["line_items"]:
                if isinstance(li, dict):
                    # alias: item_name might be under `description` or `name`
                    if li.get("item_name") is None:
                        if li.get("description") is not None:
                            li["item_name"] = li["description"]
                        elif li.get("name") is not None:
                            li["item_name"] = li["name"]
                    # amount_paise might be under `amount`.
                    if li.get("amount_paise") is None and isinstance(li.get("amount"), int):
                        li["amount_paise"] = li["amount"]
                normalized.append(li)
            data["line_items"] = normalized

        # confidence alias: some outputs may provide `confidence` as string.
        if isinstance(data.get("confidence"), str):
            try:
                data["confidence"] = float(data["confidence"])
            except Exception:
                pass

        # notes may come back as a single string in some outputs.
        if isinstance(data.get("notes"), str):
            data["notes"] = [data["notes"]]

        return data




def parse_expense_text(text: str, group_members, current_user, today: date | None = None):
    client = _get_client()
    if client is None:
        return {
            "success": False,
            "fallback_message": "AI parsing is unavailable because GEMINI_API_KEY is not configured.",
        }

    today = today or date.today()

    instructions = f"""
You extract shared expense drafts for a Splitwise-style app.

Today's date is {today.isoformat()}.
The current user is {current_user['name']} (user_id={current_user['id']}).
Allowed group members are:
{_format_member_context(group_members)}

Rules:
- Return ONLY valid JSON (no markdown, no commentary) matching the schema exactly.
- Use amount_paise, never floating-point rupees.
- Resolve relative dates like "last night" against today's date.
- Only use payer_user_id or participant user_id values from the allowed members.
- If a member name is ambiguous or missing, keep user_id null and add a warning.
- If the request implies reduced or uneven shares, use split_mode "custom" and fill amount_paise values.
- If the request implies proportional shares, use split_mode "weights" and fill weight values.
- If the request clearly means everyone in the group, use split_mode "equal_all" and leave participants empty.
- Never invent amounts, members, or dates. Lower confidence and add warnings instead.

Schema:
- confidence: number between 0 and 1
- description: string|null
- amount_paise: integer|null
- currency_code: "INR"
- expense_date: string|null (ISO date)
- payer_user_id: integer|null
- payer_name: string|null
- split_mode: one of ["equal_all","equal_subset","custom","weights"] or null
- participants: array of {{"user_id", "display_name", "selected", "amount_paise", "weight"}}
- warnings: array of strings
- notes: array of strings
""".strip()

    try:
        raw = client.models.generate_content(
            model=current_app.config.get("GEMINI_MODEL", os.getenv("GEMINI_MODEL", "gemini-1.5-flash")),
            contents=[{"role": "user", "parts": [{"text": instructions + "\n\nExpense text: " + text}]}],
            config={"temperature": 0.1},
        )

        candidate = raw.text or ""
        data = _extract_json(candidate)
        draft = ParsedExpenseDraft.model_validate(data)
    except Exception as error:
        return {
            "success": False,
            "fallback_message": "AI parsing is unavailable because GEMINI_API_KEY is not configured.",
            "error": str(error),
        }

    warnings = list(draft.warnings)
    unresolved = [p.display_name for p in draft.participants if p.user_id is None]
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
            "fallback_message": "AI bill parsing is unavailable because GEMINI_API_KEY is not configured.",
        }

    today = today or date.today()

    # Strong production prompt (JSON schema-first)
    instructions = f"""
You are an expert receipt and restaurant bill parser.

Your job is to extract structured data from restaurant bills, invoices, receipts, OCR text, or natural language descriptions.
Return ONLY valid JSON.
Never return markdown.
Never explain your answer.

Schema:
{{
"confidence": number,
"merchant_name": string|null,
"description": string|null,
"bill_date": string|null,
"currency_code": "INR",
"total_paise": integer|null,
"line_items": [
{{
"item_name": string,
"amount_paise": integer
}}
],
"warnings": [string],
"notes": [string]
}}

Rules:
* Convert every rupee value into paise.
* Detect merchant name.
* Detect bill date.
* Detect subtotal.
* Detect GST.
* Detect taxes.
* Detect service charges.
* Detect discounts.
* Detect grand total.
* Include taxes and service charges as separate line items.
* If merchant is missing return null.
* If date is missing return null.
* If line items cannot be recovered return an empty array.
* Never invent prices.
* Confidence should reflect extraction quality.

Examples:
Input:
Restaurant bill at Barbeque Nation

Paneer Tikka ₹450
Butter Naan ₹120
GST ₹80
Service Charge ₹100
Total ₹750

Output:
{{
"confidence":0.98,
"merchant_name":"Barbeque Nation",
"description":"Restaurant bill at Barbeque Nation",
"bill_date":null,
"currency_code":"INR",
"total_paise":75000,
"line_items":[
{{"item_name":"Paneer Tikka","amount_paise":45000}},
{{"item_name":"Butter Naan","amount_paise":12000}},
{{"item_name":"GST","amount_paise":8000}},
{{"item_name":"Service Charge","amount_paise":10000}}
],
"warnings":[],
"notes":[]
}}

Input:
We had dinner at Barbeque Nation.
Total bill was ₹3450.

Output:
{{
"confidence":0.8,
"merchant_name":"Barbeque Nation",
"description":"We had dinner at Barbeque Nation. Total bill was ₹3450.",
"bill_date":null,
"currency_code":"INR",
"total_paise":345000,
"line_items":[],
"warnings":["Line items were not clearly listed."],
"notes":[]
}}

Extra context:
Today's date is {today.isoformat()}.

Now parse this input text:
{text}
""".strip()

    last_error = None
    attempts = 0
    max_attempts = 3

    primary_model = current_app.config.get(
        "GEMINI_MODEL", os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    )

    models_to_try: list[str] = [primary_model]

    def _ensure_flash_models_loaded():
        nonlocal models_to_try
        try:
            available = client.models.list()
            for m in available:
                name = getattr(m, "name", None) or getattr(m, "id", None)
                if not name:
                    continue
                name_l = str(name).lower()
                if "flash" in name_l:
                    if name not in models_to_try:
                        models_to_try.append(name)
        except Exception:
            # Listing is best-effort.
            pass

    while attempts < max_attempts:
        model_used = models_to_try[min(attempts, len(models_to_try) - 1)]
        current_app.logger.info(
            f"[ai_service] parse_bill_text using model={model_used} attempt={attempts + 1}/{max_attempts}"
        )

        try:
            raw = client.models.generate_content(
                model=model_used,
                contents=[{"role": "user", "parts": [{"text": instructions}]}],
                config={"temperature": 0},
            )

            candidate = getattr(raw, "text", None) or ""
            if not candidate and hasattr(raw, "candidates"):
                try:
                    parts = raw.candidates[0].content.parts
                    candidate = "\n".join(getattr(p, "text", "") for p in (parts or []))
                except Exception:
                    candidate = ""

            data = _extract_json(candidate)
            draft = ParsedBillDraft.model_validate(data)

            # Validation changes
            # Only fail when BOTH are missing: total_paise and line_items
            both_missing = (not draft.line_items) and (draft.total_paise is None)

            confidence = draft.confidence if isinstance(draft.confidence, (int, float)) else None
            if confidence is None:
                draft.warnings.append(
                    "AI did not return confidence; extracted data may be incomplete, please review carefully."
                )

            if both_missing:
                return {
                    "success": False,
                    "fallback_message": "The bill text wasn't clear enough to extract a usable total or line items.",
                    "draft": _serialize_bill_draft(draft),
                }

            # If we have both total and line items, check consistency.
            if draft.total_paise is not None and draft.line_items:
                line_item_total = sum(item.amount_paise for item in draft.line_items)
                if line_item_total != draft.total_paise:
                    draft.warnings.append(
                        "Line items did not match the detected total, so the draft may need manual review."
                    )

            return {
                "success": True,
                "draft": _serialize_bill_draft(draft),
                "message": "Bill parsed. Assign each line item to members before saving.",
            }

        except Exception as error:
            last_error = error
            msg = str(error)
            current_app.logger.warning(f"[ai_service] parse_bill_text model={model_used} failed: {msg}")

            is_503 = "503" in msg or "UNAVAILABLE" in msg
            is_404 = "404" in msg

            if is_404 or is_503:
                _ensure_flash_models_loaded()

            # Retry automatically on 503 using exponential backoff.
            if is_503 and attempts < max_attempts - 1:
                import time

                backoff_seconds = 2**attempts
                time.sleep(backoff_seconds)
                attempts += 1
                continue

            retry_hint = None
            if is_503:
                retry_hint = "Gemini is temporarily unavailable. Please try again in a few seconds."

            return {
                "success": False,
                "fallback_message": retry_hint
                or "We couldn't parse that bill right now. Please add the expense manually.",
                "error": msg,
                "ai_status": "gemini_unavailable" if is_503 else "gemini_error",
                "retry_after_seconds": 10 if is_503 else None,
            }

    msg = str(last_error) if last_error else "Unknown error"
    return {
        "success": False,
        "fallback_message": "We couldn't parse that bill right now. Please add the expense manually.",
        "error": msg,
        "ai_status": "gemini_error",
        "retry_after_seconds": None,
    }


def _get_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None

    # Prefer the newer google-genai client.
    import google.genai as genai

    client = genai.Client(api_key=api_key)
    return client



def _format_member_context(group_members):
    return "\n".join(
        f"- user_id={member['id']}: {member['name']} <{member['email']}>" for member in group_members
    )


def _extract_json(text: str):
    import json
    import re

    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError("No JSON object found in model output")

    return json.loads(match.group(0))


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

