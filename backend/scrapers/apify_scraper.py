"""
Apify-backed scraper for internship sources.

Implements two source fetchers:
- fetch_linkedin_jobs()
- fetch_ats_jobs()

Both are normalized into the project's internship schema.
"""

import logging
from datetime import datetime
from typing import Any

import requests

try:
    from .internship_filters import (
        extract_requirement_text,
        extract_required_skills,
        infer_work_mode,
        is_internship_listing,
        location_matches_hint,
        normalize_supported_location,
        normalize_text,
    )
except ImportError:
    from scrapers.internship_filters import (  # type: ignore
        extract_requirement_text,
        extract_required_skills,
        infer_work_mode,
        is_internship_listing,
        location_matches_hint,
        normalize_supported_location,
        normalize_text,
    )


logger = logging.getLogger(__name__)

APIFY_BASE = "https://api.apify.com/v2"


def _first_non_empty(row: dict[str, Any], keys: list[str]) -> str:
    for key in keys:
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _normalize_source(source: str) -> str:
    s = normalize_text(source).lower()
    if "linkedin" in s:
        return "linkedin"
    if "ats" in s:
        return "ats"
    return s or "apify"


def _infer_domain(title: str, description: str) -> str:
    combined = (title + " " + description).lower()
    if any(k in combined for k in ["machine learning", "deep learning", "nlp", "computer vision"]):
        return "Machine Learning"
    if any(k in combined for k in ["data science", "data analyst", "data engineering"]):
        return "Data Science"
    if any(k in combined for k in ["frontend", "backend", "full stack", "web"]):
        return "Web Development"
    if "devops" in combined:
        return "DevOps"
    return "Software Engineering"


def _to_iso(raw: str) -> str | None:
    if not raw:
        return None
    candidates = [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]
    for fmt in candidates:
        try:
            return datetime.strptime(raw, fmt).isoformat()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).isoformat()
    except ValueError:
        return None


def _map_row(row: dict[str, Any], source: str, location_hint: str) -> dict:
    title = _first_non_empty(row, ["title", "jobTitle", "position", "job_title", "job_title_text"]) or "Internship"
    company = _first_non_empty(row, ["company", "companyName", "employer_name", "hiringOrganization"]) or "Unknown Company"

    location = _first_non_empty(row, ["location", "jobLocation", "job_location", "candidate_required_location"])
    if not location:
        city = _first_non_empty(row, ["city", "job_city"])
        state = _first_non_empty(row, ["state", "job_state"])
        country = _first_non_empty(row, ["country", "job_country"])
        location = ", ".join(part for part in [city, state, country] if part)

    normalized_location = normalize_supported_location(location, description=_first_non_empty(row, ["description", "job_description", "summary"]))
    if not normalized_location:
        return {}
    if not location_matches_hint(normalized_location, location_hint):
        return {}

    description = _first_non_empty(row, ["description", "job_description", "summary"])
    if not is_internship_listing(title, description):
        return {}

    raw_requirements = _first_non_empty(row, ["requirements", "qualifications", "skills", "jobRequirements"])
    requirement_text = extract_requirement_text(description=description, explicit_requirements=raw_requirements)
    skills = extract_required_skills(title=title, description=description, requirement_text=requirement_text)
    if len(skills) < 2:
        expanded = extract_required_skills(
            title=title,
            description=description,
            requirement_text=description,
            limit=12,
        )
        merged = []
        seen = set()
        for skill in (skills + expanded):
            key = skill.lower()
            if key in seen:
                continue
            seen.add(key)
            merged.append(skill)
        skills = merged[:12]
    if not skills:
        return {}

    url = _first_non_empty(row, ["url", "jobUrl", "job_apply_link", "apply_url", "link"])
    if not url:
        return {}

    posted_raw = _first_non_empty(row, ["postedAt", "posted_at", "publishedAt", "datePosted", "createdAt"])

    return {
        "title": title,
        "company": company,
        "required_skills": skills,
        "requirement_text": requirement_text,
        "description": (description or "")[:1200],
        "domain": _infer_domain(title, description),
        "stipend": "Not disclosed",
        "duration": "3–6 months",
        "location": normalized_location,
        "is_remote": normalized_location.lower().startswith("remote"),
        "work_mode": infer_work_mode(normalized_location, description),
        "openings": 1,
        "apply_url": url,
        "posted_at": _to_iso(posted_raw),
        "source": _normalize_source(source),
        "scraped_at": datetime.utcnow(),
    }


def _run_actor(token: str, actor_id: str, actor_input: dict[str, Any], max_items: int) -> list[dict[str, Any]]:
    if not token or not actor_id:
        return []

    url = f"{APIFY_BASE}/acts/{actor_id}/run-sync-get-dataset-items"
    params = {
        "token": token,
        "format": "json",
        "clean": "true",
        "limit": max_items,
    }

    try:
        resp = requests.post(url, params=params, json=actor_input, timeout=120)
        resp.raise_for_status()
        payload = resp.json()
        return payload if isinstance(payload, list) else []
    except requests.RequestException as exc:
        logger.error("Apify actor call failed for actor=%s: %s", actor_id, exc)
        return []


def fetch_linkedin_jobs(token: str, actor_id: str, location: str = "", max_items: int = 100) -> list:
    hint = normalize_text(location)
    actor_input = {
        "keywords": "internship OR intern",
        "location": hint,
        "maxItems": max_items,
    }
    rows = _run_actor(token, actor_id, actor_input, max_items)
    return [mapped for row in rows if (mapped := _map_row(row, "apify-linkedin", hint))]


def fetch_ats_jobs(token: str, actor_id: str, location: str = "", max_items: int = 100) -> list:
    hint = normalize_text(location)
    actor_input = {
        "query": "internship OR intern",
        "location": hint,
        "maxItems": max_items,
    }
    rows = _run_actor(token, actor_id, actor_input, max_items)
    return [mapped for row in rows if (mapped := _map_row(row, "apify-ats", hint))]


def fetch_internships(
    apify_token: str,
    linkedin_actor_id: str,
    ats_actor_id: str,
    location: str = "",
    max_items: int = 100,
) -> list:
    all_rows = []
    all_rows.extend(fetch_linkedin_jobs(apify_token, linkedin_actor_id, location=location, max_items=max_items))
    all_rows.extend(fetch_ats_jobs(apify_token, ats_actor_id, location=location, max_items=max_items))
    return all_rows
