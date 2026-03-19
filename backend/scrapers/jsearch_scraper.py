"""
JSearch API scraper - aggregates internships from LinkedIn, Indeed, Glassdoor,
ZipRecruiter and more via RapidAPI.

Sign up at https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
Free tier: 200 requests/month.
"""

import logging
import requests
from datetime import datetime
from urllib.parse import urlparse

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

JSEARCH_BASE_URL = "https://jsearch.p.rapidapi.com/search"

DOMAIN_KEYWORDS = {
    "machine learning": "Machine Learning",
    "deep learning": "Machine Learning",
    "data science": "Data Science",
    "data analyst": "Data Science",
    "data engineer": "Data Engineering",
    "web development": "Web Development",
    "web developer": "Web Development",
    "frontend": "Web Development",
    "front-end": "Web Development",
    "backend": "Web Development",
    "back-end": "Web Development",
    "full stack": "Web Development",
    "fullstack": "Web Development",
    "mobile": "Mobile Development",
    "android": "Mobile Development",
    "ios": "Mobile Development",
    "flutter": "Mobile Development",
    "devops": "DevOps",
    "cloud": "Cloud Computing",
    "aws": "Cloud Computing",
    "azure": "Cloud Computing",
    "gcp": "Cloud Computing",
    "cybersecurity": "Cybersecurity",
    "security engineer": "Cybersecurity",
    "nlp": "NLP",
    "natural language": "NLP",
    "artificial intelligence": "Artificial Intelligence",
    "blockchain": "Blockchain",
    "product manager": "Product Management",
    "ui/ux": "UI/UX Design",
    "ux designer": "UI/UX Design",
}

INTERNSHIP_QUERIES = [
    "software engineering internship",
    "data science internship",
    "machine learning internship",
    "web development internship",
    "cybersecurity internship",
    "cloud computing internship",
    "frontend developer internship",
    "backend developer internship",
    "devops internship",
    "mobile app development internship",
    "AI internship",
    "product management internship",
    "UI UX design internship",
]
def _infer_domain(title: str, description: str) -> str:
    combined = (title + " " + description).lower()
    for keyword, domain in DOMAIN_KEYWORDS.items():
        if keyword in combined:
            return domain
    return "Software Engineering"


def _normalize_source_name(job: dict) -> str:
    """Map JSearch publisher/apply URL to a stable source label."""
    publisher = normalize_text(job.get("job_publisher") or job.get("job_publisher_name") or "").lower()
    apply_url = normalize_text(job.get("job_apply_link") or job.get("job_google_link") or "").lower()

    candidates = [publisher, apply_url]
    for text in candidates:
        if "linkedin" in text:
            return "linkedin"
        if "indeed" in text:
            return "indeed"
        if "jobsora" in text:
            return "jobsora"
        if "internshala" in text:
            return "internshala"
        if "skillindiadigital" in text or "skill india" in text:
            return "skill-india-digital-hub"
        if "accenture" in text:
            return "accenture"

    if apply_url:
        try:
            hostname = urlparse(apply_url).netloc.lower()
            if hostname:
                return hostname.replace("www.", "")
        except Exception:
            pass

    return "jsearch"


def _publisher_allowed(job: dict, allowed_publishers: list) -> bool:
    """Return True if this JSearch row belongs to one of the allowed publishers."""
    if not allowed_publishers:
        return True

    normalized = _normalize_source_name(job)
    allowed = {normalize_text(p).lower() for p in allowed_publishers if p}
    if normalized in allowed:
        return True

    publisher = normalize_text(job.get("job_publisher") or job.get("job_publisher_name") or "").lower()
    apply_url = normalize_text(job.get("job_apply_link") or job.get("job_google_link") or "").lower()
    return any(token in publisher or token in apply_url for token in allowed)


def _build_location(job: dict) -> str:
    raw_location = job.get("job_location", "")
    city = job.get("job_city", "")
    state = job.get("job_state", "")
    country = job.get("job_country", "")
    return normalize_india_state_location(
        raw_location,
        city=city,
        state=state,
        country=country,
    )


def _build_stipend(job: dict) -> str:
    min_sal = job.get("job_min_salary")
    max_sal = job.get("job_max_salary")
    period = (job.get("job_salary_period") or "").lower() or "year"
    currency = (job.get("job_salary_currency") or "").upper() or "INR"
    symbol = "INR" if currency == "INR" else currency
    if min_sal and max_sal:
        return f"{symbol} {int(min_sal):,}-{int(max_sal):,}/{period}"
    if min_sal:
        return f"{symbol} {int(min_sal):,}/{period}"
    return "Not disclosed"


def _map_job(job: dict) -> dict:
    title = job.get("job_title", "Internship")
    company = job.get("employer_name", "Unknown Company")
    description = job.get("job_description", "")
    highlights = job.get("job_highlights") or {}
    highlight_parts = []
    if isinstance(highlights, dict):
        for value in highlights.values():
            if isinstance(value, list):
                highlight_parts.extend(str(item) for item in value if item)
            elif value:
                highlight_parts.append(str(value))
    requirement_text = " ".join(highlight_parts)
    normalized_location = _build_location(job)
    if not normalized_location:
        return {}

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
        "domain": _infer_domain(title, description),
        "stipend": _build_stipend(job),
        "duration": "3–6 months",
        "location": normalized_location,
        "openings": 1,
        "apply_url": job.get("job_apply_link") or job.get("job_google_link") or "",
        "source": _normalize_source_name(job),
        "scraped_at": datetime.utcnow(),
    }


def fetch_internships(
    api_key: str,
    location: str = "",
    pages_per_query: int = 2,
    allowed_publishers: list = None,
) -> list:
    """
    Fetch internships from JSearch API.

    Args:
        api_key: RapidAPI key with JSearch access.
        location: Optional location to narrow the search (e.g. "New York", "India").
        pages_per_query: How many pages to fetch per search query (each page = ~10 results).
        allowed_publishers: Optional list of source names to keep (e.g. ["linkedin", "indeed"]).

    Returns:
        List of internship dicts ready for MongoDB insertion.
    """
    if not api_key:
        logger.warning("JSearch: JSEARCH_API_KEY not set — skipping.")
        return []

    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
    }

    location_hint = normalize_text(location)
    if location_hint and "india" not in location_hint.lower():
        location_clause = f"{location_hint}, India"
    elif location_hint:
        location_clause = location_hint
    else:
        location_clause = "India"

    results = []
    for query in INTERNSHIP_QUERIES:
        # Always force India-targeted queries.
        search_query = f"{query} in {location_clause}"
        for page in range(1, pages_per_query + 1):
            params = {
                "query": search_query,
                "page": str(page),
                "num_pages": "1",
                "employment_types": "INTERN",
                "date_posted": "month",
            }
            try:
                resp = requests.get(
                    JSEARCH_BASE_URL, headers=headers, params=params, timeout=20
                )
                if resp.status_code == 429:
                    logger.warning("JSearch: rate limit reached — stopping early.")
                    return results
                resp.raise_for_status()
                jobs = resp.json().get("data", [])
                added = 0
                for job in jobs:
                    title = job.get("job_title", "")
                    desc = job.get("job_description", "")
                    if not is_internship_listing(title, desc):
                        continue
                    if not _publisher_allowed(job, allowed_publishers or []):
                        continue
                    mapped = _map_job(job)
                    if not mapped:
                        continue
                    if not location_matches_hint(mapped["location"], location_hint):
                        continue
                    results.append(mapped)
                    added += 1
                logger.info(
                    "JSearch: %d internships kept (of %d) for '%s' (page %d)",
                    added, len(jobs), query, page,
                )
            except requests.RequestException as exc:
                logger.error("JSearch: request failed for '%s': %s", query, exc)
                break  # skip remaining pages for this query on network error

    return results
