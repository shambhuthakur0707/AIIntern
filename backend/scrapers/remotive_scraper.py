"""
Remotive API scraper - completely free, no API key required.
Fetches remote tech internships from https://remotive.com/api/remote-jobs

Docs: https://remotive.com/api/remote-jobs (public, no auth)
"""

import logging
import requests
from datetime import datetime

try:
    from .internship_filters import (
        extract_required_skills,
        is_internship_listing,
        location_matches_hint,
        normalize_india_state_location,
        normalize_text,
    )
except ImportError:
    from scrapers.internship_filters import (  # type: ignore
        extract_required_skills,
        is_internship_listing,
        location_matches_hint,
        normalize_india_state_location,
        normalize_text,
    )

logger = logging.getLogger(__name__)

REMOTIVE_URL = "https://remotive.com/api/remote-jobs"

CATEGORIES = [
    "software-dev",
    "data",
    "devops-sysadmin",
    "product",
    "design",
    "qa",
]

def _map_job(job: dict) -> dict:
    title = job.get("title", "Internship")
    company = job.get("company_name", "Unknown Company")
    description = job.get("description", "")
    raw_location = job.get("candidate_required_location") or ""
    normalized_location = normalize_india_state_location(raw_location)
    if not normalized_location:
        return {}

    tags = job.get("tags") or []
    requirement_text = " ".join(str(tag) for tag in tags if tag)
    skills = extract_required_skills(
        title=title,
        description=description,
        requirement_text=requirement_text,
    )
    if not skills:
        return {}

    return {
        "title": title,
        "company": company,
        "required_skills": skills,
        "description": description[:1200] if description else "",
        "domain": job.get("category", "Software Development"),
        "stipend": job.get("salary") or "Not disclosed",
        "duration": "3–6 months",
        "location": normalized_location,
        "openings": 1,
        "apply_url": job.get("url", ""),
        "source": "remotive",
        "scraped_at": datetime.utcnow(),
    }


def fetch_internships(location: str = "") -> list:
    """
    Fetch remote internships from Remotive API.
    Searches 'intern' across multiple job categories.

    Args:
        location: Optional location to filter results (post-fetch filter since
                  Remotive doesn't support location in API params).

    Returns:
        List of internship dicts ready for MongoDB insertion.
    """
    location_hint = normalize_text(location)
    results = []
    for category in CATEGORIES:
        params = {
            "category": category,
            "search": "intern",
            "limit": 20,
        }
        try:
            resp = requests.get(REMOTIVE_URL, params=params, timeout=20)
            resp.raise_for_status()
            jobs = resp.json().get("jobs", [])
            added = 0
            for job in jobs:
                title = job.get("title", "")
                desc = job.get("description", "")
                if not is_internship_listing(title, desc):
                    continue
                mapped = _map_job(job)
                if not mapped:
                    continue
                if not location_matches_hint(mapped["location"], location_hint):
                    continue
                results.append(mapped)
                added += 1
            logger.info(
                "Remotive: %d internships kept (of %d) in category '%s'",
                added, len(jobs), category,
            )
        except requests.RequestException as exc:
            logger.error("Remotive: request failed for category '%s': %s", category, exc)

    return results
