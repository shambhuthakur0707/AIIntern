from flask import Blueprint
from flask_jwt_extended import jwt_required
from utils.jwt_utils import get_current_user
from utils.response_utils import success_response, error_response
from models.user_model import sanitize_user

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard", methods=["GET"])
@jwt_required()
def get_dashboard():
    """
    GET /api/dashboard
    Returns the user profile and their last persisted agent match result.
    """

    user = get_current_user()
    if not user:
        return error_response("User not found", 404)

    last_match = user.get("match_result")  

    return success_response(
        data={
            "user": sanitize_user(user),
            "has_results": last_match is not None,
            "match_result": last_match,
        },
        message="Dashboard data loaded",
    )