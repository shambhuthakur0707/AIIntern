import logging
from datetime import datetime, timezone
from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId

try:
    from ..utils.response_utils import success_response, error_response
    from ..utils.jwt_utils import get_current_user
except ImportError:
    from utils.response_utils import success_response, error_response
    from utils.jwt_utils import get_current_user

logger = logging.getLogger(__name__)

applications_bp = Blueprint("applications", __name__)

VALID_STATUSES = {"saved", "applied", "interview", "final"}
VALID_OUTCOMES = {"offer", "rejected", None}


def _serialize_application(app_doc, internship_doc=None):
    """Convert an application document to a JSON-safe dict."""
    deadline = app_doc.get("deadline")
    return {
        "id": str(app_doc["_id"]),
        "internship_id": str(app_doc.get("internship_id", "")),
        "status": app_doc.get("status", "saved"),
        "outcome": app_doc.get("outcome"),
        "deadline": deadline.isoformat() if deadline else None,
        "notes": app_doc.get("notes", ""),
        "created_at": app_doc.get("created_at", datetime.now(timezone.utc)).isoformat(),
        "updated_at": app_doc.get("updated_at", datetime.now(timezone.utc)).isoformat(),
        # Internship details joined from the internships collection
        "title": internship_doc.get("title", "Untitled") if internship_doc else app_doc.get("title", "Untitled"),
        "company": internship_doc.get("company", "") if internship_doc else app_doc.get("company", ""),
        "domain": internship_doc.get("domain", "") if internship_doc else "",
        "location": internship_doc.get("location", "") if internship_doc else "",
        "stipend": internship_doc.get("stipend", "") if internship_doc else "",
        "apply_url": internship_doc.get("apply_url", "") if internship_doc else "",
    }


@applications_bp.route("", methods=["GET"])
@jwt_required()
def list_applications():
    """GET /api/applications — return all applications for the current user."""
    try:
        user_id = get_jwt_identity()
        db = current_app.config["DB"]

        raw_apps = list(db.applications.find({"user_id": ObjectId(user_id)}))

        # Bulk-fetch internship documents so we only do N lookups for N applications
        internship_ids = [a["internship_id"] for a in raw_apps if a.get("internship_id")]
        internships_map = {}
        if internship_ids:
            for doc in db.internships.find({"_id": {"$in": internship_ids}}):
                internships_map[doc["_id"]] = doc

        applications = [
            _serialize_application(a, internships_map.get(a.get("internship_id")))
            for a in raw_apps
        ]

        return success_response(data={"applications": applications}, message="Applications loaded")
    except Exception:
        logger.exception("Failed to load applications")
        return error_response("Failed to load applications", 500)


@applications_bp.route("", methods=["POST"])
@jwt_required()
def create_application():
    """POST /api/applications — create a new application card for the current user."""
    try:
        user_id = get_jwt_identity()
        db = current_app.config["DB"]
        data = request.get_json() or {}

        internship_id_str = data.get("internship_id", "").strip()
        if not internship_id_str:
            return error_response("internship_id is required", 400)

        try:
            internship_oid = ObjectId(internship_id_str)
        except Exception:
            return error_response("Invalid internship_id", 400)

        # Prevent duplicates — one card per user-internship pair
        existing = db.applications.find_one({
            "user_id": ObjectId(user_id),
            "internship_id": internship_oid,
        })
        if existing:
            internship_doc = db.internships.find_one({"_id": internship_oid})
            return success_response(
                data={"application": _serialize_application(existing, internship_doc)},
                message="Application already tracked",
                status_code=200,
            )

        # Parse optional deadline
        deadline = None
        deadline_str = (data.get("deadline") or "").strip()
        if deadline_str:
            try:
                deadline = datetime.fromisoformat(deadline_str.replace("Z", "+00:00"))
            except ValueError:
                return error_response("Invalid deadline format — use ISO 8601 (YYYY-MM-DD)", 400)

        status = data.get("status", "saved")
        if status not in VALID_STATUSES:
            status = "saved"

        now = datetime.now(timezone.utc)
        app_doc = {
            "user_id": ObjectId(user_id),
            "internship_id": internship_oid,
            "status": status,
            "outcome": None,
            "deadline": deadline,
            "notes": (data.get("notes") or "").strip(),
            "created_at": now,
            "updated_at": now,
        }

        result = db.applications.insert_one(app_doc)
        app_doc["_id"] = result.inserted_id

        internship_doc = db.internships.find_one({"_id": internship_oid})
        return success_response(
            data={"application": _serialize_application(app_doc, internship_doc)},
            message="Application added to tracker",
            status_code=201,
        )
    except Exception:
        logger.exception("Failed to create application")
        return error_response("Failed to create application", 500)


@applications_bp.route("/<app_id>", methods=["PATCH"])
@jwt_required()
def update_application(app_id):
    """PATCH /api/applications/:id — update status, outcome, notes, or deadline."""
    try:
        user_id = get_jwt_identity()
        db = current_app.config["DB"]

        try:
            app_oid = ObjectId(app_id)
        except Exception:
            return error_response("Invalid application id", 400)

        app_doc = db.applications.find_one({
            "_id": app_oid,
            "user_id": ObjectId(user_id),
        })
        if not app_doc:
            return error_response("Application not found", 404)

        data = request.get_json() or {}
        updates = {}

        if "status" in data:
            status = data["status"]
            if status not in VALID_STATUSES:
                return error_response(f"status must be one of {sorted(VALID_STATUSES)}", 400)
            updates["status"] = status

        if "outcome" in data:
            outcome = data["outcome"]
            if outcome not in VALID_OUTCOMES:
                return error_response("outcome must be 'offer', 'rejected', or null", 400)
            updates["outcome"] = outcome

        if "notes" in data:
            updates["notes"] = (data["notes"] or "").strip()

        if "deadline" in data:
            deadline_str = (data["deadline"] or "").strip()
            if deadline_str:
                try:
                    updates["deadline"] = datetime.fromisoformat(deadline_str.replace("Z", "+00:00"))
                except ValueError:
                    return error_response("Invalid deadline format", 400)
            else:
                updates["deadline"] = None

        if not updates:
            return error_response("No valid fields to update", 400)

        updates["updated_at"] = datetime.now(timezone.utc)
        db.applications.update_one({"_id": app_oid}, {"$set": updates})

        updated = db.applications.find_one({"_id": app_oid})
        internship_doc = db.internships.find_one({"_id": updated.get("internship_id")})
        return success_response(
            data={"application": _serialize_application(updated, internship_doc)},
            message="Application updated",
        )
    except Exception:
        logger.exception("Failed to update application")
        return error_response("Failed to update application", 500)


@applications_bp.route("/<app_id>", methods=["DELETE"])
@jwt_required()
def delete_application(app_id):
    """DELETE /api/applications/:id — remove an application card."""
    try:
        user_id = get_jwt_identity()
        db = current_app.config["DB"]
        try:
            app_oid = ObjectId(app_id)
        except Exception:
            return error_response("Invalid application id", 400)

        result = db.applications.delete_one({
            "_id": app_oid,
            "user_id": ObjectId(user_id),
        })
        if result.deleted_count == 0:
            return error_response("Application not found", 404)
        return success_response(message="Application removed")
    except Exception:
        logger.exception("Failed to delete application")
        return error_response("Failed to delete application", 500)
