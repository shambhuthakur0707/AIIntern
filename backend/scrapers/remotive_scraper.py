"""
Remotive API scraper - completely free, no API key required.
Fetches remote tech internships from https://remotive.com/api/remote-jobs

Docs: https://remotive.com/api/remote-jobs (public, no auth)
"""

import logging
import requests
from datetime import datetime

try:
    from ..tools.skill_extraction import extract_skills_from_title_and_description
except ImportError:
    from tools.skill_extraction import extract_skills_from_title_and_description

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

# Words that confirm the listing is an internship
_INTERN_MARKERS = {
    "intern", "internship", "trainee", "apprentice",
    "co-op", "coop", "working student", "placement",
}


def _is_internship(title: str, description: str) -> bool:
    """Return True only if the listing looks like an actual internship."""
    combined = (title + " " + description).lower()
    return any(marker in combined for marker in _INTERN_MARKERS)


def _map_job(job: dict) -> dict:
    title = job.get("title", "Internship")
    company = job.get("company_name", "Unknown Company")
    description = job.get("description", "")
    location = job.get("candidate_required_location") or ""
    if not location or location.lower() in ("", "worldwide", "anywhere"):
        location = "Remote"

    return {
        "title": title,
        "company": company,
        "required_skills": extract_skills_from_title_and_description(title, description),
        "description": description[:1200] if description else "",
        "domain": job.get("category", "Software Development"),
        "stipend": job.get("salary") or "Not disclosed",
        "duration": "3–6 months",
        "location": location,
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
    loc_lower = (location or "").strip().lower()
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
                if not _is_internship(title, desc):
                    continue
                mapped = _map_job(job)
                # Post-filter by location if the user specified one
                if loc_lower and loc_lower not in mapped["location"].lower():
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
