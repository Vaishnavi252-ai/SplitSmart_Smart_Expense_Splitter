from datetime import date

from flask import Blueprint, jsonify, request

from schemas import AIBillParseRequest, AIExpenseParseRequest
from services.ai_service import parse_bill_text, parse_expense_text
from services.expense_service import get_group_members, get_user

ai_bp = Blueprint("ai", __name__)


@ai_bp.route("/parse-expense", methods=["POST"], strict_slashes=False)
def parse_expense(group_id):
    payload = AIExpenseParseRequest.model_validate(request.get_json(silent=True) or {})
    group_members = get_group_members(group_id)
    current_user = get_user(payload.current_user_id)
    result = parse_expense_text(payload.text, group_members, current_user, today=date.today())
    return jsonify(result), 200 if result.get("success") else 422


@ai_bp.route("/parse-bill", methods=["POST"], strict_slashes=False)
def parse_bill(group_id):
    payload = AIBillParseRequest.model_validate(request.get_json(silent=True) or {})
    result = parse_bill_text(payload.text, today=date.today())
    return jsonify(result), 200 if result.get("success") else 422
