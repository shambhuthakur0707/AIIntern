from flask import Blueprint, request, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from bson import ObjectId
import bcrypt
try:
    from ..models.user_model import create_user_document, sanitize_user
    from ..utils.response_utils import success_response, error_response
except ImportError:
    from models.user_model import create_user_document, sanitize_user
    from utils.response_utils import success_response, error_response

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data:
        return error_response("Request body is required", 400)

    required_fields = ["name", "email", "password", "skills"]
    for field in required_fields:
        if not data.get(field):
            return error_response(f"'{field}' is required", 400)

    # ✅ Get DB from Flask app config
    db = current_app.config["DB"]

    # Check email uniqueness
    if db.users.find_one({"email": data["email"].lower().strip()}):
        return error_response("Email already registered", 409)

    # Hash password
    password_hash = bcrypt.hashpw(
        data["password"].encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")

    user_doc = create_user_document(
        name=data["name"],
        email=data["email"],
        password_hash=password_hash,
        skills=data.get("skills", []),
        interests=data.get("interests", []),
        experience_level=data.get("experience_level", "beginner"),
        education=data.get("education", ""),
    )

    result = db.users.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id
    token = create_access_token(identity=str(result.inserted_id))

    return success_response(
        data={"token": token, "user": sanitize_user(user_doc)},
        message="User registered successfully",
        status_code=201,
    )


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data:
        return error_response("Request body is required", 400)

    email = data.get("email", "").lower().strip()
    password = data.get("password", "")

    if not email or not password:
        return error_response("Email and password are required", 400)

    # ✅ Get DB from Flask app config
    db = current_app.config["DB"]

    user = db.users.find_one({"email": email})

    if not user:
        return error_response("Invalid credentials", 401)

    if not bcrypt.checkpw(
        password.encode("utf-8"),
        user["password_hash"].encode("utf-8")
    ):
        return error_response("Invalid credentials", 401)

    token = create_access_token(identity=str(user["_id"]))

    return success_response(
        data={"token": token, "user": sanitize_user(user)},
        message="Login successful",
    )


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_me():
    user_id = get_jwt_identity()
    db = current_app.config["DB"]
    user = db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return error_response("User not found", 404)
    return success_response(data={"user": sanitize_user(user)})


@auth_bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    db = current_app.config["DB"]
    data = request.get_json() or {}

    allowed = [
        "name", "education", "experience_level",
        "linkedin_url", "github_url", "portfolio_url",
        "location", "bio", "skills", "interests",
    ]
    updates = {k: v for k, v in data.items() if k in allowed}

    if not updates:
        return error_response("No valid fields to update", 400)

    db.users.update_one({"_id": ObjectId(user_id)}, {"$set": updates})
    user = db.users.find_one({"_id": ObjectId(user_id)})
    return success_response(data={"user": sanitize_user(user)}, message="Profile updated")
