"""
Scraper management routes — manually trigger a scrape run or check its status.

POST  /api/scraper/trigger   — kick off a scrape immediately (admin action)
GET   /api/scraper/status    — return last-run metadata + scheduler state
"""

from flask import Blueprint, current_app, request
from flask_jwt_extended import jwt_required

try:
    from ..utils.response_utils import success_response, error_response
    from ..scrapers.scheduler import run_scraper_job
    from ..scrapers.cleanup import run_cleanup
    from ..scrapers.internship_filters import normalize_india_state_location
except ImportError:
    from utils.response_utils import success_response, error_response
    from scrapers.scheduler import run_scraper_job
    from scrapers.cleanup import run_cleanup
    from scrapers.internship_filters import normalize_india_state_location

scraper_bp = Blueprint("scraper", __name__)


@scraper_bp.route("/trigger", methods=["POST"])
@jwt_required()
def trigger_scraper():
    """Manually trigger India internship scraping for a specific India city/state."""
    try:
        body = request.get_json(silent=True) or {}
        location = (body.get("location") or "").strip()
        if len(location) > 100:
            return error_response("Location must be under 100 characters", 400)

        location_lower = location.lower()
        if location and location_lower not in {"india", "in"}:
            normalized_hint = normalize_india_state_location(location)
            if not normalized_hint:
                return error_response(
                    "Please enter a valid India city or state (for example: Bengaluru, Karnataka, Maharashtra).",
                    400,
                )

        app = current_app._get_current_object()  # noqa: SLF001
        run_location = "" if location_lower in {"india", "in"} else location
        run_scraper_job(app, location=run_location)

        db = current_app.config["DB"]
        meta = db.scraper_meta.find_one({"_id": "last_run"}) or {}

        return success_response(
            data={
                "total_inserted": meta.get("total_inserted", 0),
                "total_updated": meta.get("total_updated", 0),
                "errors": meta.get("errors", []),
                "location": run_location or "India (all states)",
            },
            message="Scraper completed successfully.",
        )
    except Exception as exc:
        return error_response("Scraper failed", 500)


@scraper_bp.route("/status", methods=["GET"])
@jwt_required()
def scraper_status():
    """Return the last scraper run metadata."""
    try:
        db = current_app.config["DB"]
        meta = db.scraper_meta.find_one({"_id": "last_run"}) or {}

        run_at = meta.get("run_at")
        data = {
            "last_run": {
                "run_at": run_at.isoformat() if run_at else None,
                "total_inserted": meta.get("total_inserted", 0),
                "total_updated": meta.get("total_updated", 0),
                "errors": meta.get("errors", []),
            } if meta else None,
        }

        return success_response(data=data, message="Scraper status retrieved.")
    except Exception as exc:
        return error_response(f"Could not retrieve status: {exc}", 500)


@scraper_bp.route("/cleanup", methods=["POST"])
@jwt_required()
def trigger_cleanup():
    """Manually trigger cleanup to remove fake, expired, and dead-link internships."""
    try:
        db = current_app.config["DB"]
        stats = run_cleanup(db)
        return success_response(
            data=stats,
            message=(
                f"Cleanup done: removed {stats['fake']} fake, "
                f"{stats['expired']} expired, {stats['dead_link']} dead-link "
                f"internships (out of {stats['total_checked']} checked)."
            ),
        )
    except Exception as exc:
        return error_response(f"Cleanup failed: {exc}", 500)
