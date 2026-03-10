import re
import logging
import secrets
from datetime import datetime, timedelta, timezone

from flask import Blueprint, request, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask_mail import Message
from bson import ObjectId
import bcrypt
import requests as http_requests

try:
    from ..models.user_model import create_user_document, sanitize_user
    from ..utils.response_utils import success_response, error_response
    from ..config import Config
    from ..app import limiter, mail
except ImportError:
    from models.user_model import create_user_document, sanitize_user
    from utils.response_utils import success_response, error_response
    from config import Config
    from app import limiter, mail

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__)

EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
OTP_EXPIRY_MINUTES = 10


def _validate_password(password):
    if len(password) < 8:
        return "Password must be at least 8 characters"
    if not re.search(r"[A-Z]", password):
        return "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return "Password must contain at least one lowercase letter"
    if not re.search(r"[0-9]", password):
        return "Password must contain at least one number"
    return None


def _generate_otp():
    return f"{secrets.randbelow(900000) + 100000}"


def _send_otp_email(email, otp):
    msg = Message(
        subject="AIIntern - Verify your email",
        recipients=[email],
        html=f"""
        <div style="font-family: sans-serif; max-width: 400px; margin: auto; padding: 24px;">
            <h2 style="color: #6366f1;">AIIntern Email Verification</h2>
            <p>Your verification code is:</p>
            <div style="background: #f3f4f6; padding: 16px; border-radius: 8px; text-align: center; margin: 16px 0;">
                <span style="font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #1f2937;">{otp}</span>
            </div>
            <p style="color: #6b7280; font-size: 14px;">This code expires in {OTP_EXPIRY_MINUTES} minutes.</p>
            <p style="color: #9ca3af; font-size: 12px;">If you didn't request this, please ignore this email.</p>
        </div>
        """,
    )
    mail.send(msg)


@auth_bp.route("/register", methods=["POST"])
@limiter.limit("5 per minute")
def register():
    data = request.get_json()
    if not data:
        return error_response("Request body is required", 400)

    required_fields = ["name", "email", "password", "skills"]
    for field in required_fields:
        if not data.get(field):
            return error_response(f"'{field}' is required", 400)

    email = data["email"].lower().strip()
    if not EMAIL_RE.match(email):
        return error_response("Invalid email format", 400)

    password_error = _validate_password(data["password"])
    if password_error:
        return error_response(password_error, 400)

    name = data["name"].strip()
    if len(name) < 2 or len(name) > 100:
        return error_response("Name must be between 2 and 100 characters", 400)

    db = current_app.config["DB"]

    if db.users.find_one({"email": email}):
        return error_response("Email already registered", 409)

    password_hash = bcrypt.hashpw(
        data["password"].encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")

    user_doc = create_user_document(
        name=name,
        email=email,
        password_hash=password_hash,
        skills=data.get("skills", []),
        interests=data.get("interests", []),
        experience_level=data.get("experience_level", "beginner"),
        education=data.get("education", ""),
    )
    user_doc["email_verified"] = False

    result = db.users.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id

    # Generate and send OTP
    otp = _generate_otp()
    db.otp_codes.insert_one({
        "email": email,
        "otp": otp,
        "purpose": "email_verification",
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRY_MINUTES),
        "created_at": datetime.now(timezone.utc),
    })

    try:
        _send_otp_email(email, otp)
    except Exception as exc:
        logger.error("Failed to send OTP email to %s: %s", email, exc)

    token = create_access_token(identity=str(result.inserted_id))

    logger.info("User registered: %s", email)
    return success_response(
        data={"token": token, "user": sanitize_user(user_doc), "email_verified": False},
        message="User registered. Please verify your email with the OTP sent.",
        status_code=201,
    )


@auth_bp.route("/verify-email", methods=["POST"])
@limiter.limit("10 per minute")
def verify_email():
    data = request.get_json()
    if not data:
        return error_response("Request body is required", 400)

    email = (data.get("email") or "").lower().strip()
    otp = (data.get("otp") or "").strip()

    if not email or not otp:
        return error_response("Email and OTP are required", 400)

    db = current_app.config["DB"]

    record = db.otp_codes.find_one({
        "email": email,
        "otp": otp,
        "purpose": "email_verification",
        "expires_at": {"$gt": datetime.now(timezone.utc)},
    })

    if not record:
        return error_response("Invalid or expired OTP", 400)

    db.users.update_one({"email": email}, {"$set": {"email_verified": True}})
    db.otp_codes.delete_many({"email": email, "purpose": "email_verification"})

    user = db.users.find_one({"email": email})
    logger.info("Email verified: %s", email)
    return success_response(
        data={"user": sanitize_user(user)},
        message="Email verified successfully",
    )


@auth_bp.route("/resend-otp", methods=["POST"])
@limiter.limit("3 per minute")
def resend_otp():
    data = request.get_json()
    if not data:
        return error_response("Request body is required", 400)

    email = (data.get("email") or "").lower().strip()
    if not email:
        return error_response("Email is required", 400)

    db = current_app.config["DB"]
    user = db.users.find_one({"email": email})
    if not user:
        return error_response("User not found", 404)

    if user.get("email_verified"):
        return error_response("Email already verified", 400)

    db.otp_codes.delete_many({"email": email, "purpose": "email_verification"})

    otp = _generate_otp()
    db.otp_codes.insert_one({
        "email": email,
        "otp": otp,
        "purpose": "email_verification",
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRY_MINUTES),
        "created_at": datetime.now(timezone.utc),
    })

    try:
        _send_otp_email(email, otp)
    except Exception as exc:
        logger.error("Failed to resend OTP to %s: %s", email, exc)
        return error_response("Failed to send OTP email", 500)

    return success_response(message="OTP resent successfully")


@auth_bp.route("/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():
    data = request.get_json()
    if not data:
        return error_response("Request body is required", 400)

    email = data.get("email", "").lower().strip()
    password = data.get("password", "")

    if not email or not password:
        return error_response("Email and password are required", 400)

    db = current_app.config["DB"]
    user = db.users.find_one({"email": email})

    if not user:
        return error_response("Invalid credentials", 401)

    # Google-only accounts don't have a password
    if not user.get("password_hash"):
        return error_response("This account uses Google sign-in. Please sign in with Google.", 400)

    if not bcrypt.checkpw(
        password.encode("utf-8"),
        user["password_hash"].encode("utf-8")
    ):
        return error_response("Invalid credentials", 401)

    token = create_access_token(identity=str(user["_id"]))

    return success_response(
        data={
            "token": token,
            "user": sanitize_user(user),
            "email_verified": user.get("email_verified", False),
        },
        message="Login successful",
    )


@auth_bp.route("/google", methods=["POST"])
@limiter.limit("10 per minute")
def google_auth():
    """
    Accepts a Google OAuth credential (id_token) from the frontend,
    verifies it with Google, and creates/logs in the user.
    """
    data = request.get_json()
    if not data or not data.get("credential"):
        return error_response("Google credential is required", 400)

    credential = data["credential"]

    # Verify the token with Google's tokeninfo endpoint
    try:
        google_resp = http_requests.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": credential},
            timeout=10,
        )
        if google_resp.status_code != 200:
            return error_response("Invalid Google credential", 401)

        google_user = google_resp.json()
    except http_requests.RequestException as exc:
        logger.error("Google token verification failed: %s", exc)
        return error_response("Could not verify Google credential", 500)

    # Validate audience matches our client ID
    if google_user.get("aud") != Config.GOOGLE_CLIENT_ID:
        return error_response("Google credential not intended for this app", 401)

    email = google_user.get("email", "").lower().strip()
    name = google_user.get("name", email.split("@")[0])

    if not email:
        return error_response("Could not get email from Google", 400)

    db = current_app.config["DB"]
    user = db.users.find_one({"email": email})

    if user:
        # Existing user — log in
        if not user.get("email_verified"):
            db.users.update_one({"_id": user["_id"]}, {"$set": {"email_verified": True}})
            user["email_verified"] = True
    else:
        # New user — register
        user_doc = create_user_document(
            name=name,
            email=email,
            password_hash="",
            skills=data.get("skills", []),
            interests=[],
            experience_level="beginner",
            education="",
        )
        user_doc["email_verified"] = True
        user_doc["auth_provider"] = "google"
        result = db.users.insert_one(user_doc)
        user_doc["_id"] = result.inserted_id
        user = user_doc
        logger.info("Google user registered: %s", email)

    token = create_access_token(identity=str(user["_id"]))

    return success_response(
        data={
            "token": token,
            "user": sanitize_user(user),
            "email_verified": True,
            "is_new_user": not bool(user.get("skills")),
        },
        message="Google sign-in successful",
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


PHONE_RE = re.compile(r"^\+?[1-9]\d{6,14}$")


@auth_bp.route("/phone", methods=["PATCH"])
@jwt_required()
def update_phone():
    """PATCH /api/auth/phone — add or update phone number."""
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    phone = (data.get("phone") or "").strip()

    if not phone:
        return error_response("Phone number is required", 400)
    if not PHONE_RE.match(phone):
        return error_response("Invalid phone number. Use international format e.g. +919876543210", 400)

    db = current_app.config["DB"]
    db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"phone": phone, "updated_at": datetime.now(timezone.utc)}},
    )
    user = db.users.find_one({"_id": ObjectId(user_id)})
    return success_response(data={"user": sanitize_user(user)}, message="Phone number updated")


@auth_bp.route("/change-password", methods=["PUT"])
@jwt_required()
@limiter.limit("5 per minute")
def change_password():
    """PUT /api/auth/change-password — change password using current password."""
    user_id = get_jwt_identity()
    data = request.get_json() or {}

    current_password = data.get("current_password", "")
    new_password = data.get("new_password", "")

    if not current_password or not new_password:
        return error_response("current_password and new_password are required", 400)

    db = current_app.config["DB"]
    user = db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return error_response("User not found", 404)

    if not user.get("password_hash"):
        return error_response("This account uses Google sign-in and has no password", 400)

    if not bcrypt.checkpw(current_password.encode("utf-8"), user["password_hash"].encode("utf-8")):
        return error_response("Current password is incorrect", 401)

    if current_password == new_password:
        return error_response("New password must be different from current password", 400)

    pw_error = _validate_password(new_password)
    if pw_error:
        return error_response(pw_error, 400)

    new_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"password_hash": new_hash, "updated_at": datetime.now(timezone.utc)}},
    )
    logger.info("Password changed for user %s", user_id)
    return success_response(message="Password changed successfully")


@auth_bp.route("/change-email", methods=["POST"])
@jwt_required()
@limiter.limit("3 per minute")
def change_email_request():
    """POST /api/auth/change-email — send OTP to new email to verify ownership."""
    user_id = get_jwt_identity()
    data = request.get_json() or {}

    new_email = (data.get("new_email") or "").lower().strip()
    if not new_email:
        return error_response("new_email is required", 400)
    if not EMAIL_RE.match(new_email):
        return error_response("Invalid email format", 400)

    db = current_app.config["DB"]

    if db.users.find_one({"email": new_email}):
        return error_response("This email is already in use", 409)

    current_user = db.users.find_one({"_id": ObjectId(user_id)})
    if not current_user:
        return error_response("User not found", 404)

    if current_user.get("email") == new_email:
        return error_response("New email must be different from current email", 400)

    # Store OTP against new email for verification
    db.otp_codes.delete_many({"user_id": user_id, "purpose": "email_change"})
    otp = _generate_otp()
    db.otp_codes.insert_one({
        "user_id": user_id,
        "email": new_email,
        "otp": otp,
        "purpose": "email_change",
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRY_MINUTES),
        "created_at": datetime.now(timezone.utc),
    })

    try:
        msg = Message(
            subject="AIIntern - Confirm your new email",
            recipients=[new_email],
            html=f"""
            <div style="font-family: sans-serif; max-width: 400px; margin: auto; padding: 24px;">
                <h2 style="color: #6366f1;">Confirm Email Change</h2>
                <p>Enter this code in AIIntern to confirm your new email address:</p>
                <div style="background: #f3f4f6; padding: 16px; border-radius: 8px; text-align: center; margin: 16px 0;">
                    <span style="font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #1f2937;">{otp}</span>
                </div>
                <p style="color: #6b7280; font-size: 14px;">This code expires in {OTP_EXPIRY_MINUTES} minutes.</p>
                <p style="color: #9ca3af; font-size: 12px;">If you didn't request this, please ignore this email.</p>
            </div>
            """,
        )
        mail.send(msg)
    except Exception as exc:
        logger.error("Failed to send email-change OTP to %s: %s", new_email, exc)
        return error_response("Failed to send verification email", 500)

    return success_response(message=f"Verification code sent to {new_email}")


@auth_bp.route("/verify-email-change", methods=["POST"])
@jwt_required()
@limiter.limit("5 per minute")
def verify_email_change():
    """POST /api/auth/verify-email-change — confirm OTP and update email."""
    user_id = get_jwt_identity()
    data = request.get_json() or {}

    new_email = (data.get("new_email") or "").lower().strip()
    otp = (data.get("otp") or "").strip()

    if not new_email or not otp:
        return error_response("new_email and otp are required", 400)

    db = current_app.config["DB"]

    record = db.otp_codes.find_one({
        "user_id": user_id,
        "email": new_email,
        "otp": otp,
        "purpose": "email_change",
        "expires_at": {"$gt": datetime.now(timezone.utc)},
    })

    if not record:
        return error_response("Invalid or expired verification code", 400)

    # Double-check email not taken (race condition guard)
    if db.users.find_one({"email": new_email}):
        return error_response("This email is already in use", 409)

    db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"email": new_email, "email_verified": True, "updated_at": datetime.now(timezone.utc)}},
    )
    db.otp_codes.delete_many({"user_id": user_id, "purpose": "email_change"})

    user = db.users.find_one({"_id": ObjectId(user_id)})
    logger.info("Email changed for user %s to %s", user_id, new_email)
    return success_response(data={"user": sanitize_user(user)}, message="Email updated successfully")
