"""
Internship scraper orchestrator.

Scraping is triggered on-demand by the user (via the API) and results
are persisted in MongoDB until their deadline expires.

Internships are de-duplicated by apply_url so re-runs don't create duplicates.

Configured source policy:
- JSearch (restricted to requested publishers: LinkedIn, Indeed, Jobsora,
  Internshala, Skill India Digital Hub, Accenture)
- Targeted source scraper (Jobsora, Internshala, Skill India Digital Hub, Accenture)
"""

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


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

def run_scraper_job(app, location: str = ""):
    """
    Orchestrates all scrapers and stores results in MongoDB.
    Must be called with an active Flask app context (or inside `with app.app_context()`).

    Args:
        app: Flask application instance.
        location: Optional location to narrow scraping (e.g. "New York", "India").
    """
    with app.app_context():
        # Import scrapers inside the function so they're always resolved correctly
        try:
            from .jsearch_scraper import fetch_internships as jsearch_fetch
            from .target_sources_scraper import fetch_internships as target_sources_fetch
            from .cleanup import run_cleanup
            from .internship_filters import (
                extract_required_skills,
                is_internship_listing,
                location_matches_hint,
                normalize_india_state_location,
            )
        except ImportError:
            from scrapers.jsearch_scraper import fetch_internships as jsearch_fetch
            from scrapers.target_sources_scraper import fetch_internships as target_sources_fetch
            from scrapers.cleanup import run_cleanup
            from scrapers.internship_filters import (  # type: ignore
                extract_required_skills,
                is_internship_listing,
                location_matches_hint,
                normalize_india_state_location,
            )

        try:
            from ..config import Config  # type: ignore[import]
        except ImportError:
            try:
                from backend.config import Config  # type: ignore[import]
            except ImportError:
                from config import Config  # type: ignore[import]

        db = app.config["DB"]
        total_inserted = 0
        total_updated = 0
        errors = []

        logger.info("Internship scraper job started at %s", datetime.utcnow().isoformat())

        logger.info("Scraping with location filter: '%s'", location or "(all)")

        def sanitize_records(records: list) -> list:
            """Final safety gate: internship-only + India state location + concrete skills."""
            kept = []
            for record in records:
                title = (record.get("title") or "").strip()
                description = record.get("description") or ""
                if not is_internship_listing(title, description):
                    continue

                normalized_location = normalize_india_state_location(record.get("location", ""))
                if not normalized_location:
                    continue
                if not location_matches_hint(normalized_location, location):
                    continue

                requirement_text = " ".join(record.get("required_skills") or [])
                skills = extract_required_skills(
                    title=title,
                    description=description,
                    requirement_text=requirement_text,
                )
                if not skills:
                    continue

                clean = dict(record)
                clean["location"] = normalized_location
                clean["required_skills"] = skills
                kept.append(clean)
            return kept

        # ── 1. JSearch (restricted to requested publishers) ────────────────
        if Config.JSEARCH_API_KEY:
            try:
                jobs = jsearch_fetch(
                    api_key=Config.JSEARCH_API_KEY,
                    location=location,
                    allowed_publishers=[
                        "linkedin",
                        "indeed",
                        "jobsora",
                        "internshala",
                        "skill-india-digital-hub",
                        "accenture",
                    ],
                )
                jobs = sanitize_records(jobs)
                ins, upd = _upsert_internships(db, jobs)
                total_inserted += ins
                total_updated += upd
                logger.info("JSearch (requested publishers) done: +%d inserted, %d updated", ins, upd)
            except Exception as exc:
                logger.error("JSearch scraper raised: %s", exc)
                errors.append(f"jsearch: {exc}")
        else:
            logger.info("JSearch skipped — JSEARCH_API_KEY not configured.")

        # ── 2. Targeted sources: Jobsora, Internshala, Skill India DH, Accenture ──
        try:
            jobs = target_sources_fetch(location=location)
            jobs = sanitize_records(jobs)
            ins, upd = _upsert_internships(db, jobs)
            total_inserted += ins
            total_updated += upd
            logger.info("Target sources done: +%d inserted, %d updated", ins, upd)
        except Exception as exc:
            logger.error("Target source scraper raised: %s", exc)
            errors.append(f"target_sources: {exc}")

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
