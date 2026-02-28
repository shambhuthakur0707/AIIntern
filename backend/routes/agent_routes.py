from flask import Blueprint
from flask_jwt_extended import jwt_required
from utils.jwt_utils import get_current_user
from utils.response_utils import success_response, error_response
from agents.internship_agent import run_matching_agent
from services.user_service import update_user_match_result
from models.user_model import sanitize_user

agent_bp = Blueprint("agent", __name__)


@agent_bp.route("/match", methods=["POST"])
@jwt_required()
def match_internships():
    """
    POST /api/agent/match
    Runs the internship matching agent for the authenticated user.
    """
    try:
        # Get authenticated user from JWT
        user = get_current_user()
        if not user:
            return error_response("User not found", 404)

        # Build user profile for agent
        user_profile = {
            "name": user.get("name"),
            "education": user.get("education"),
            "experience_level": user.get("experience_level"),
            "skills": user.get("skills", []),
            "interests": user.get("interests", []),
        }

        # Run AI matching agent
        result = run_matching_agent(user_profile)

        if not result or not result.get("success"):
            return error_response(
                message="Agent execution failed",
                status_code=500,
                errors=result.get("error") if result else "Unknown error"
            )

        match_data = result.get("data", {})

        # Save match results to database
        update_user_match_result(str(user["_id"]), match_data)

        return success_response(
            data={
                "user": sanitize_user(user),
                "match_result": match_data,
            },
            message="Internship matching completed successfully"
        )

    except Exception as e:
        print("FULL ERROR:", e)
        raise e