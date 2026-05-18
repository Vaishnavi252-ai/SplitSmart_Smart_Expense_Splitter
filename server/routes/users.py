from flask import Blueprint, jsonify, request

from schemas import UserCreateRequest
from services.expense_service import create_user, list_users

users_bp = Blueprint("users", __name__)


@users_bp.route("/", methods=["GET"], strict_slashes=False)
def get_users():
    return jsonify({"users": list_users()})


@users_bp.route("/", methods=["POST"], strict_slashes=False)
def add_user():
    payload = UserCreateRequest.model_validate(request.get_json(silent=True) or {})
    return jsonify(create_user(payload)), 201
