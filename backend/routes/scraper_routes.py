"""
Scraper management routes — manually trigger a scrape run or check its status.

POST  /api/scraper/trigger   — kick off a scrape immediately (admin action)
GET   /api/scraper/status    — return last-run metadata + scheduler state
"""

from flask import Blueprint, current_app
from flask_jwt_extended import jwt_required

try:
    from ..utils.response_utils import success_response, error_response
    from ..scrapers.scheduler import run_scraper_job, get_scheduler
except ImportError:
    from utils.response_utils import success_response, error_response
    from scrapers.scheduler import run_scraper_job, get_scheduler

scraper_bp = Blueprint("scraper", __name__)


@scraper_bp.route("/trigger", methods=["POST"])
@jwt_required()
def trigger_scraper():
    """Manually trigger the internship scraper (runs synchronously in the request)."""
    try:
        app = current_app._get_current_object()  # noqa: SLF001
        run_scraper_job(app)

        db = current_app.config["DB"]
        meta = db.scraper_meta.find_one({"_id": "last_run"}) or {}

        return success_response(
            data={
                "total_inserted": meta.get("total_inserted", 0),
                "total_updated": meta.get("total_updated", 0),
                "errors": meta.get("errors", []),
            },
            message="Scraper completed successfully.",
        )
    except Exception as exc:
        return error_response(f"Scraper failed: {exc}", 500)


@scraper_bp.route("/status", methods=["GET"])
@jwt_required()
def scraper_status():
    """Return the last scraper run metadata and whether the scheduler is active."""
    try:
        db = current_app.config["DB"]
        meta = db.scraper_meta.find_one({"_id": "last_run"}) or {}
        scheduler = get_scheduler()

        run_at = meta.get("run_at")
        data = {
            "scheduler_running": bool(scheduler and scheduler.running),
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
