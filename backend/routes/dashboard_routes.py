from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required
try:
    from ..utils.jwt_utils import get_current_user
    from ..utils.response_utils import success_response, error_response
    from ..models.user_model import sanitize_user
    from ..services.user_service import add_user_skill, remove_user_skill, update_user_profile_sources
    from ..services.profile_import_service import extract_profile_from_sources
except ImportError:
    from utils.jwt_utils import get_current_user
    from utils.response_utils import success_response, error_response
    from models.user_model import sanitize_user
    from services.user_service import add_user_skill, remove_user_skill, update_user_profile_sources
    from services.profile_import_service import extract_profile_from_sources

dashboard_bp = Blueprint("dashboard", __name__)

ALLOWED_CV_EXTENSIONS = {".txt", ".md", ".rtf"}


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

    last_match = user.get("last_match_result")

    return success_response(
        data={
            "user": sanitize_user(user),
            "has_results": last_match is not None,
            "match_result": last_match,
        },
        message="Dashboard data loaded",
    )


@dashboard_bp.route("/profile/skills/add", methods=["PATCH"])
@jwt_required()
def add_skill():
    user = get_current_user()
    if not user:
        return error_response("User not found", 404)

    payload = request.get_json() or {}
    skill = payload.get("skill", "").strip()
    if not skill:
        return error_response("Skill is required", 400)

    updated_user = add_user_skill(str(user["_id"]), skill)
    if not updated_user:
        return error_response("Could not update skills", 400)

    return success_response(
        data={"user": sanitize_user(updated_user)},
        message=f"Added skill: {skill}",
    )


@dashboard_bp.route("/profile/skills/remove", methods=["PATCH"])
@jwt_required()
def remove_skill():
    user = get_current_user()
    if not user:
        return error_response("User not found", 404)

    payload = request.get_json() or {}
    skill = payload.get("skill", "").strip()
    if not skill:
        return error_response("Skill is required", 400)

    updated_user = remove_user_skill(str(user["_id"]), skill)
    if not updated_user:
        return error_response("Could not update skills", 400)

    return success_response(
        data={"user": sanitize_user(updated_user)},
        message=f"Removed skill: {skill}",
    )


def _read_cv_text(uploaded_file):
    if not uploaded_file:
        return "", ""

    filename = uploaded_file.filename or ""
    if "." not in filename:
        return "", "CV file must include an extension (.txt, .md, .rtf)."

    ext = "." + filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_CV_EXTENSIONS:
        return "", "Unsupported CV format. Use .txt, .md, or .rtf."

    raw = uploaded_file.read()
    try:
        text = raw.decode("utf-8", errors="ignore")
    except Exception:
        return "", "Could not read CV file."

    cleaned = " ".join(text.split())
    if not cleaned:
        return "", "CV file is empty."
    return cleaned[:20000], ""


@dashboard_bp.route("/profile/import", methods=["POST"])
@jwt_required()
def import_profile_sources():
    user = get_current_user()
    if not user:
        return error_response("User not found", 404)

    payload = request.get_json(silent=True) if request.is_json else {}
    linkedin_url = (request.form.get("linkedin_url") or payload.get("linkedin_url") or "").strip()
    github_url = (request.form.get("github_url") or payload.get("github_url") or "").strip()

    cv_text = ""
    cv_filename = ""
    if "cv" in request.files:
        uploaded_file = request.files["cv"]
        cv_filename = uploaded_file.filename or ""
        cv_text, cv_error = _read_cv_text(uploaded_file)
        if cv_error:
            return error_response(cv_error, 400)
    elif request.is_json:
        cv_text = (payload or {}).get("cv_text", "")

    db = current_app.config["DB"]
    extracted = extract_profile_from_sources(db, cv_text, linkedin_url, github_url)
    updated_user = update_user_profile_sources(
        user_id=str(user["_id"]),
        linkedin_url=linkedin_url or user.get("linkedin_url", ""),
        github_url=github_url or user.get("github_url", ""),
        resume_filename=cv_filename or user.get("resume_filename", ""),
        resume_text=cv_text or user.get("resume_text", ""),
        imported_skills=extracted["skills"],
        imported_interests=extracted["interests"],
    )

    return success_response(
        data={
            "user": sanitize_user(updated_user),
            "imported_skills": extracted["skills"],
            "imported_interests": extracted["interests"],
            "resume_uploaded": bool(cv_text),
        },
        message="Profile imported from CV and platform links.",
    )
