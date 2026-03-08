"""
Adzuna API scraper - free tier (250 calls/month).
Aggregates listings from multiple job boards globally.

Sign up at https://developer.adzuna.com/
Free tier: 250 API calls/month across all countries.
"""

import logging
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

ADZUNA_BASE = "https://api.adzuna.com/v1/api/jobs"

# Country codes supported by Adzuna
COUNTRIES = ["us", "gb", "in", "au", "ca", "de", "fr"]

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

# Words that confirm the listing is an internship
_INTERN_MARKERS = {
    "intern", "internship", "trainee", "apprentice",
    "co-op", "coop", "working student", "placement",
}


def _is_internship(title: str, description: str) -> bool:
    """Return True only if the listing looks like an actual internship."""
    combined = (title + " " + description).lower()
    return any(marker in combined for marker in _INTERN_MARKERS)


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

SKILL_KEYWORDS = [
    "Python", "JavaScript", "TypeScript", "React", "Node.js", "Java", "C++", "C#",
    "Go", "Rust", "SQL", "MongoDB", "PostgreSQL", "MySQL", "Redis", "Docker",
    "Kubernetes", "AWS", "GCP", "Azure", "TensorFlow", "PyTorch", "Pandas",
    "NumPy", "Scikit-learn", "FastAPI", "Flask", "Django", "Spring Boot",
    "Git", "Linux", "REST API", "GraphQL", "HTML", "CSS", "Vue.js", "Angular",
    "Swift", "Kotlin", "Flutter", "React Native", "Figma", "Kafka", "Terraform",
]


def _infer_domain(title: str, description: str) -> str:
    combined = (title + " " + description).lower()
    for keyword, domain in DOMAIN_KEYWORDS.items():
        if keyword in combined:
            return domain
    return "Software Engineering"


def _extract_skills(description: str) -> list:
    found = []
    desc_lower = description.lower()
    for skill in SKILL_KEYWORDS:
        if skill.lower() in desc_lower:
            found.append(skill)
    return found[:10]


def _build_location(job: dict, country: str) -> str:
    loc = job.get("location", {})
    display = loc.get("display_name", "")
    if display:
        return display
    areas = loc.get("area", [])
    if areas:
        return ", ".join(str(a) for a in areas)
    return country.upper()


def _build_stipend(job: dict) -> str:
    min_sal = job.get("salary_min")
    max_sal = job.get("salary_max")
    if min_sal and max_sal:
        return f"${int(min_sal):,}–${int(max_sal):,}/year"
    if min_sal:
        return f"${int(min_sal):,}/year"
    return "Not disclosed"


def _map_job(job: dict, country: str) -> dict:
    title = job.get("title", "Internship")
    company = (job.get("company") or {}).get("display_name", "Unknown Company")
    description = job.get("description", "")
    return {
        "title": title,
        "company": company,
        "required_skills": _extract_skills(description),
        "description": description[:1200] if description else "",
        "domain": _infer_domain(title, description),
        "stipend": _build_stipend(job),
        "duration": "3–6 months",
        "location": _build_location(job, country),
        "openings": 1,
        "apply_url": job.get("redirect_url", ""),
        "source": "adzuna",
        "scraped_at": datetime.utcnow(),
    }


def fetch_internships(app_id: str, api_key: str) -> list:
    """
    Fetch internships from the Adzuna API.

    Args:
        app_id: Your Adzuna application ID.
        api_key: Your Adzuna API key.

    Returns:
        List of internship dicts ready for MongoDB insertion.
    """
    if not app_id or not api_key:
        logger.warning("Adzuna: ADZUNA_APP_ID or ADZUNA_API_KEY not set — skipping.")
        return []

    results = []
    for country in COUNTRIES:
        for term in SEARCH_TERMS:
            url = f"{ADZUNA_BASE}/{country}/search/1"
            params = {
                "app_id": app_id,
                "app_key": api_key,
                "results_per_page": 20,
                "what": term,
                "content-type": "application/json",
            }
            try:
                resp = requests.get(url, params=params, timeout=20)
                if resp.status_code == 429:
                    logger.warning(
                        "Adzuna: rate limit reached for country '%s' — stopping.", country
                    )
                    break
                resp.raise_for_status()
                jobs = resp.json().get("results", [])
                added = 0
                for job in jobs:
                    title = job.get("title", "")
                    desc = job.get("description", "")
                    if not _is_internship(title, desc):
                        continue
                    results.append(_map_job(job, country))
                    added += 1
                logger.info(
                    "Adzuna: %d internships kept (of %d) for '%s' in '%s'",
                    added, len(jobs), term, country,
                )
            except requests.RequestException as exc:
                logger.error(
                    "Adzuna: request failed for '%s'/'%s': %s", country, term, exc
                )

    return results
