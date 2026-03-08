"""
Remotive API scraper - completely free, no API key required.
Fetches remote tech internships from https://remotive.com/api/remote-jobs

Docs: https://remotive.com/api/remote-jobs (public, no auth)
"""

import logging
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

REMOTIVE_URL = "https://remotive.com/api/remote-jobs"

SKILL_KEYWORDS = [
    "Python", "JavaScript", "TypeScript", "React", "Node.js", "Java", "C++", "C#",
    "Go", "Rust", "SQL", "MongoDB", "PostgreSQL", "MySQL", "Redis", "Docker",
    "Kubernetes", "AWS", "GCP", "Azure", "TensorFlow", "PyTorch", "Pandas",
    "NumPy", "Scikit-learn", "FastAPI", "Flask", "Django", "Spring Boot",
    "Git", "Linux", "REST API", "GraphQL", "HTML", "CSS", "Vue.js", "Angular",
    "Swift", "Kotlin", "Flutter", "React Native", "Figma", "Kafka", "Terraform",
]

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


def _extract_skills(description: str) -> list:
    found = []
    desc_lower = description.lower()
    for skill in SKILL_KEYWORDS:
        if skill.lower() in desc_lower:
            found.append(skill)
    return found[:10]


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
        "required_skills": _extract_skills(description),
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


def fetch_internships() -> list:
    """
    Fetch remote internships from Remotive API.
    Searches 'intern' across multiple job categories.

    Returns:
        List of internship dicts ready for MongoDB insertion.
    """
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
                results.append(_map_job(job))
                added += 1
            logger.info(
                "Remotive: %d internships kept (of %d) in category '%s'",
                added, len(jobs), category,
            )
        except requests.RequestException as exc:
            logger.error("Remotive: request failed for category '%s': %s", category, exc)

    return results
