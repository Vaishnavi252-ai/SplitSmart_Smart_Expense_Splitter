from datetime import date

from flask import Blueprint, jsonify, request

from errors import ApiError
from schemas import ExpenseCreateRequest
from services.expense_service import create_expense, get_group_balances, get_group_settlements, list_group_expenses

expenses_bp = Blueprint("expenses", __name__)


@expenses_bp.route("/expenses", methods=["GET"], strict_slashes=False)
def get_expenses(group_id):
    payer_user_id = request.args.get("payer_user_id", type=int)
    start_date = _parse_optional_date(request.args.get("start_date"), "start_date")
    end_date = _parse_optional_date(request.args.get("end_date"), "end_date")
    search = request.args.get("search", type=str)
    expenses = list_group_expenses(
        group_id,
        payer_user_id=payer_user_id,
        start_date=start_date,
        end_date=end_date,
        search=search,
    )
    return jsonify({"expenses": expenses})


@expenses_bp.route("/expenses", methods=["POST"], strict_slashes=False)
def add_expense(group_id):
    payload = ExpenseCreateRequest.model_validate(request.get_json(silent=True) or {})
    return jsonify(create_expense(group_id, payload)), 201


@expenses_bp.route("/balances", methods=["GET"], strict_slashes=False)
def get_balances(group_id):
    return jsonify({"balances": get_group_balances(group_id)})


@expenses_bp.route("/settlements", methods=["GET"], strict_slashes=False)
def get_settlements(group_id):
    return jsonify({"settlements": get_group_settlements(group_id)})


def _parse_optional_date(value, label):
    if not value:
        return None
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as error:
        raise ApiError(f"{label} must be a valid YYYY-MM-DD date.") from error
