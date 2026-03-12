"""
JSearch API scraper - aggregates internships from LinkedIn, Indeed, Glassdoor,
ZipRecruiter and more via RapidAPI.

Sign up at https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
Free tier: 200 requests/month.
"""

import logging
import requests
from datetime import datetime

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

SKILL_KEYWORDS = [
    "Python", "JavaScript", "TypeScript", "React", "Node.js", "Java", "C++", "C#",
    "Go", "Rust", "SQL", "MongoDB", "PostgreSQL", "MySQL", "Redis", "Docker",
    "Kubernetes", "AWS", "GCP", "Azure", "TensorFlow", "PyTorch", "Pandas",
    "NumPy", "Scikit-learn", "FastAPI", "Flask", "Django", "Spring Boot",
    "Git", "Linux", "REST API", "GraphQL", "HTML", "CSS", "Vue.js", "Angular",
    "Swift", "Kotlin", "Flutter", "React Native", "Figma", "Apache Spark", "Kafka",
    "Hadoop", "R", "MATLAB", "Tableau", "Power BI", "Selenium", "Jenkins", "Terraform",
]

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

# Words that confirm the listing is an internship
_INTERN_MARKERS = {
    "intern", "internship", "trainee", "apprentice",
    "co-op", "coop", "working student", "placement",
}


def _is_internship(title: str, description: str) -> bool:
    """Return True only if the listing looks like an actual internship."""
    combined = (title + " " + description).lower()
    return any(marker in combined for marker in _INTERN_MARKERS)


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


def _build_location(job: dict) -> str:
    if job.get("job_is_remote"):
        return "Remote"
    city = job.get("job_city", "")
    state = job.get("job_state", "")
    country = job.get("job_country", "")
    if city and state:
        return f"{city}, {state}"
    if city and country:
        return f"{city}, {country}"
    if state:
        return state
    if country:
        return country
    return "Remote"


def _build_stipend(job: dict) -> str:
    min_sal = job.get("job_min_salary")
    max_sal = job.get("job_max_salary")
    period = (job.get("job_salary_period") or "").lower() or "year"
    if min_sal and max_sal:
        return f"${int(min_sal):,}–${int(max_sal):,}/{period}"
    if min_sal:
        return f"${int(min_sal):,}/{period}"
    return "Not disclosed"


def _map_job(job: dict) -> dict:
    title = job.get("job_title", "Internship")
    company = job.get("employer_name", "Unknown Company")
    description = job.get("job_description", "")
    return {
        "title": title,
        "company": company,
        "required_skills": _extract_skills(description),
        "description": description[:1200] if description else "",
        "domain": _infer_domain(title, description),
        "stipend": _build_stipend(job),
        "duration": "3–6 months",
        "location": _build_location(job),
        "openings": 1,
        "apply_url": job.get("job_apply_link") or job.get("job_google_link") or "",
        "source": "jsearch",
        "scraped_at": datetime.utcnow(),
    }


def fetch_internships(api_key: str, location: str = "", pages_per_query: int = 2) -> list:
    """
    Fetch internships from JSearch API.

    Args:
        api_key: RapidAPI key with JSearch access.
        location: Optional location to narrow the search (e.g. "New York", "India").
        pages_per_query: How many pages to fetch per search query (each page = ~10 results).

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

    results = []
    for query in INTERNSHIP_QUERIES:
        # Append location to query for geo-targeted results
        search_query = f"{query} in {location}" if location else query
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
                    if not _is_internship(title, desc):
                        continue
                    results.append(_map_job(job))
                    added += 1
                logger.info(
                    "JSearch: %d internships kept (of %d) for '%s' (page %d)",
                    added, len(jobs), query, page,
                )
            except requests.RequestException as exc:
                logger.error("JSearch: request failed for '%s': %s", query, exc)
                break  # skip remaining pages for this query on network error

    return results
