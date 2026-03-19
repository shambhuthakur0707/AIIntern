"""
Adzuna API scraper - free tier (250 calls/month).
Aggregates listings from multiple job boards globally.

Sign up at https://developer.adzuna.com/
Free tier: 250 API calls/month across all countries.
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

ADZUNA_BASE = "https://api.adzuna.com/v1/api/jobs"

INDIA_COUNTRY_CODE = "in"

SEARCH_TERMS = [
    "software internship",
    "data science internship",
    "machine learning internship",
    "web development internship",
    "cybersecurity internship",
    "cloud computing internship",
    "AI internship",
    "frontend internship",
    "backend internship",
    "devops internship",
]

DOMAIN_KEYWORDS = {
    "machine learning": "Machine Learning",
    "deep learning": "Machine Learning",
    "data science": "Data Science",
    "data analyst": "Data Science",
    "web developer": "Web Development",
    "frontend": "Web Development",
    "backend": "Web Development",
    "devops": "DevOps",
    "cloud": "Cloud Computing",
    "aws": "Cloud Computing",
    "cybersecurity": "Cybersecurity",
    "artificial intelligence": "Artificial Intelligence",
    "nlp": "NLP",
    "mobile": "Mobile Development",
    "android": "Mobile Development",
    "ios": "Mobile Development",
    "blockchain": "Blockchain",
    "ui/ux": "UI/UX Design",
}

def _infer_domain(title: str, description: str) -> str:
    combined = (title + " " + description).lower()
    for keyword, domain in DOMAIN_KEYWORDS.items():
        if keyword in combined:
            return domain
    return "Software Engineering"


def _build_location(job: dict, country: str) -> str:
    loc = job.get("location", {})
    display = loc.get("display_name", "")
    area = loc.get("area", [])
    area_text = ", ".join(str(a) for a in area if a)
    normalized = normalize_india_state_location(
        display or area_text,
        state=area_text,
        country=country,
    )
    if normalized:
        return normalized

    # Try fallback using latitude/longitude area strings when display is noisy.
    if area_text:
        return normalize_india_state_location(area_text, country=country)

    return ""


def _build_stipend(job: dict) -> str:
    min_sal = job.get("salary_min")
    max_sal = job.get("salary_max")
    currency = (job.get("salary_currency") or "INR").upper()
    symbol = "INR" if currency == "INR" else currency
    if min_sal and max_sal:
        return f"{symbol} {int(min_sal):,}-{int(max_sal):,}/year"
    if min_sal:
        return f"{symbol} {int(min_sal):,}/year"
    return "Not disclosed"


def _map_job(job: dict, country: str) -> dict:
    title = job.get("title", "Internship")
    company = (job.get("company") or {}).get("display_name", "Unknown Company")
    description = job.get("description", "")
    normalized_location = _build_location(job, country)
    if not normalized_location:
        return {}

    skills = extract_required_skills(
        title=title,
        description=description,
        requirement_text=description,
    )
    if not skills:
        return {}

    return {
        "title": title,
        "company": company,
        "required_skills": skills,
        "description": description[:1200] if description else "",
        "domain": _infer_domain(title, description),
        "stipend": _build_stipend(job),
        "duration": "3–6 months",
        "location": normalized_location,
        "openings": 1,
        "apply_url": job.get("redirect_url", ""),
        "source": "adzuna",
        "scraped_at": datetime.utcnow(),
    }


def fetch_internships(app_id: str, api_key: str, location: str = "") -> list:
    """
    Fetch internships from the Adzuna API.

    Args:
        app_id: Your Adzuna application ID.
        api_key: Your Adzuna API key.
        location: Optional location to narrow the search.

    Returns:
        List of internship dicts ready for MongoDB insertion.
    """
    if not app_id or not api_key:
        logger.warning("Adzuna: ADZUNA_APP_ID or ADZUNA_API_KEY not set — skipping.")
        return []

    location_hint = normalize_text(location)
    if location_hint and "india" not in location_hint.lower():
        location_clause = f"{location_hint}, India"
    elif location_hint:
        location_clause = location_hint
    else:
        location_clause = "India"

    results = []
    for term in SEARCH_TERMS:
        url = f"{ADZUNA_BASE}/{INDIA_COUNTRY_CODE}/search/1"
        params = {
            "app_id": app_id,
            "app_key": api_key,
            "results_per_page": 20,
            "what": f"{term} {location_clause}".strip(),
            "content-type": "application/json",
        }
        try:
            resp = requests.get(url, params=params, timeout=20)
            if resp.status_code == 429:
                logger.warning("Adzuna: rate limit reached for India endpoint.")
                break
            resp.raise_for_status()
            jobs = resp.json().get("results", [])
            added = 0
            for job in jobs:
                title = job.get("title", "")
                desc = job.get("description", "")
                if not is_internship_listing(title, desc):
                    continue
                mapped = _map_job(job, "India")
                if not mapped:
                    continue
                if not location_matches_hint(mapped["location"], location_hint):
                    continue
                results.append(mapped)
                added += 1
            logger.info(
                "Adzuna: %d internships kept (of %d) for '%s' in India",
                added,
                len(jobs),
                term,
            )
        except requests.RequestException as exc:
            logger.error("Adzuna: request failed for '%s': %s", term, exc)

    return results
