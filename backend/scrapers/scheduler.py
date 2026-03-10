"""
Background scheduler that periodically fetches internships from external job APIs
and upserts them into MongoDB.

The scheduler runs every SCRAPER_INTERVAL_HOURS hours (default: 6).
Internships are de-duplicated by apply_url so re-runs don't create duplicates.
"""

import logging
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

_scheduler = None


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def _upsert_internships(db, internships: list) -> tuple:
    """
    Insert-or-update internships keyed on apply_url.

    Returns:
        (inserted_count, updated_count)
    """
    inserted = 0
    updated = 0
    for doc in internships:
        apply_url = (doc.get("apply_url") or "").strip()
        if not apply_url:
            continue  # can't deduplicate without a URL

        result = db.internships.update_one(
            {"apply_url": apply_url},
            {
                "$set": doc,
                "$setOnInsert": {"created_at": datetime.utcnow()},
            },
            upsert=True,
        )
        if result.upserted_id:
            inserted += 1
        elif result.modified_count:
            updated += 1

    return inserted, updated


# ---------------------------------------------------------------------------
# Core scraper job
# ---------------------------------------------------------------------------

def run_scraper_job(app):
    """
    Orchestrates all scrapers and stores results in MongoDB.
    Must be called with an active Flask app context (or inside `with app.app_context()`).
    """
    with app.app_context():
        # Import scrapers inside the function so they're always resolved correctly
        try:
            from .jsearch_scraper import fetch_internships as jsearch_fetch
            from .remotive_scraper import fetch_internships as remotive_fetch
            from .adzuna_scraper import fetch_internships as adzuna_fetch
            from .cleanup import run_cleanup
        except ImportError:
            from scrapers.jsearch_scraper import fetch_internships as jsearch_fetch
            from scrapers.remotive_scraper import fetch_internships as remotive_fetch
            from scrapers.adzuna_scraper import fetch_internships as adzuna_fetch
            from scrapers.cleanup import run_cleanup

        try:
            from .config import Config  # type: ignore[import]
        except ImportError:
            from config import Config  # type: ignore[import]

        db = app.config["DB"]
        total_inserted = 0
        total_updated = 0
        errors = []

        logger.info("Internship scraper job started at %s", datetime.utcnow().isoformat())

        # ── 1. Remotive (free, no key required) ───────────────────────────
        try:
            jobs = remotive_fetch()
            ins, upd = _upsert_internships(db, jobs)
            total_inserted += ins
            total_updated += upd
            logger.info("Remotive done: +%d inserted, %d updated", ins, upd)
        except Exception as exc:
            logger.error("Remotive scraper raised: %s", exc)
            errors.append(f"remotive: {exc}")

        # ── 2. JSearch (RapidAPI — covers LinkedIn, Indeed, Glassdoor) ────
        if Config.JSEARCH_API_KEY:
            try:
                jobs = jsearch_fetch(api_key=Config.JSEARCH_API_KEY)
                ins, upd = _upsert_internships(db, jobs)
                total_inserted += ins
                total_updated += upd
                logger.info("JSearch done: +%d inserted, %d updated", ins, upd)
            except Exception as exc:
                logger.error("JSearch scraper raised: %s", exc)
                errors.append(f"jsearch: {exc}")
        else:
            logger.info("JSearch skipped — JSEARCH_API_KEY not configured.")

        # ── 3. Adzuna (free tier) ─────────────────────────────────────────
        if Config.ADZUNA_APP_ID and Config.ADZUNA_API_KEY:
            try:
                jobs = adzuna_fetch(
                    app_id=Config.ADZUNA_APP_ID, api_key=Config.ADZUNA_API_KEY
                )
                ins, upd = _upsert_internships(db, jobs)
                total_inserted += ins
                total_updated += upd
                logger.info("Adzuna done: +%d inserted, %d updated", ins, upd)
            except Exception as exc:
                logger.error("Adzuna scraper raised: %s", exc)
                errors.append(f"adzuna: {exc}")
        else:
            logger.info("Adzuna skipped — ADZUNA_APP_ID / ADZUNA_API_KEY not configured.")

        # ── Persist run metadata ──────────────────────────────────────────
        db.scraper_meta.update_one(
            {"_id": "last_run"},
            {
                "$set": {
                    "run_at": datetime.utcnow(),
                    "total_inserted": total_inserted,
                    "total_updated": total_updated,
                    "errors": errors,
                }
            },
            upsert=True,
        )

        logger.info(
            "Scraper job finished — inserted=%d, updated=%d, errors=%d",
            total_inserted,
            total_updated,
            len(errors),
        )

        # ── 4. Cleanup: remove fake, expired, and dead-link internships ──
        try:
            cleanup_stats = run_cleanup(db)
            logger.info(
                "Cleanup finished — fake=%d, expired=%d, dead_link=%d (of %d checked)",
                cleanup_stats["fake"],
                cleanup_stats["expired"],
                cleanup_stats["dead_link"],
                cleanup_stats["total_checked"],
            )
        except Exception as exc:
            logger.error("Cleanup raised: %s", exc)
            errors.append(f"cleanup: {exc}")


# ---------------------------------------------------------------------------
# Scheduler lifecycle
# ---------------------------------------------------------------------------

def init_scheduler(app, interval_hours: int = 6):
    """
    Start the APScheduler background scheduler.

    Args:
        app: Flask application instance.
        interval_hours: How often to re-run the scraper (default 6 hours).

    Returns:
        The running BackgroundScheduler instance.
    """
    global _scheduler

    if _scheduler and _scheduler.running:
        logger.info("Scheduler is already running — skipping re-init.")
        return _scheduler

    _scheduler = BackgroundScheduler(daemon=True)
    _scheduler.add_job(
        func=run_scraper_job,
        trigger=IntervalTrigger(hours=interval_hours),
        args=[app],
        id="internship_scraper",
        name="Internship Scraper (periodic)",
        replace_existing=True,
        next_run_time=datetime.now(timezone.utc),  # run immediately on startup
    )
    _scheduler.start()
    logger.info(
        "Internship scraper scheduler started — runs every %d hour(s).", interval_hours
    )
    return _scheduler


def get_scheduler():
    """Return the current scheduler instance (may be None if not started)."""
    return _scheduler
