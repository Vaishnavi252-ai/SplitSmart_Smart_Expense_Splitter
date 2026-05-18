from flask import Blueprint, jsonify, request

from schemas import GroupCreateRequest
from services.expense_service import create_group, get_group, list_groups

groups_bp = Blueprint("groups", __name__)


@groups_bp.route("/", methods=["GET"], strict_slashes=False)
def get_groups():
    current_user_id = request.args.get("user_id", type=int)
    return jsonify({"groups": list_groups(current_user_id=current_user_id)})


@groups_bp.route("/", methods=["POST"], strict_slashes=False)
def add_group():
    payload = GroupCreateRequest.model_validate(request.get_json(silent=True) or {})
    return jsonify(create_group(payload)), 201


@groups_bp.route("/<int:group_id>", methods=["GET"], strict_slashes=False)
def get_group_detail(group_id):
    return jsonify(get_group(group_id))
