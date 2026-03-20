import hashlib
import re
from datetime import datetime
from typing import Any
from .tagging import tag_role

INDIA_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa",
    "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala",
    "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland",
    "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
    "Uttar Pradesh", "Uttarakhand", "West Bengal", "Delhi", "Chandigarh", "Puducherry",
]


def extract_state(location: str) -> str:
    lower_loc = (location or "").lower()
    for state in INDIA_STATES:
        if state.lower() in lower_loc:
            return state

    city_to_state = {
        "bengaluru": "Karnataka", "bangalore": "Karnataka", "mumbai": "Maharashtra",
        "pune": "Maharashtra", "hyderabad": "Telangana", "chennai": "Tamil Nadu",
        "delhi": "Delhi", "gurgaon": "Haryana", "gurugram": "Haryana",
        "noida": "Uttar Pradesh", "kolkata": "West Bengal", "ahmedabad": "Gujarat",
        "jaipur": "Rajasthan", "kochi": "Kerala", "bhubaneswar": "Odisha",
    }
    for city, state in city_to_state.items():
        if city in lower_loc:
            return state
    return "Unknown"


def first_non_empty(row: dict[str, Any], keys: list[str], default: str = "") -> str:
    for key in keys:
        val = row.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return default


def to_iso_datetime(raw: str) -> str | None:
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


def normalize_record(row: dict[str, Any], source: str) -> dict[str, Any]:
    title = first_non_empty(row, ["title", "jobTitle", "position", "job_title"], "Internship")
    company = first_non_empty(row, ["company", "companyName", "employer_name", "hiringOrganization"], "Unknown")
    location = first_non_empty(row, ["location", "jobLocation", "candidate_required_location", "job_location"], "")

    if not location:
        city = first_non_empty(row, ["city", "job_city"], "")
        state = first_non_empty(row, ["state", "job_state"], "")
        country = first_non_empty(row, ["country", "job_country"], "")
        location = ", ".join([p for p in [city, state, country] if p])

    posted_raw = first_non_empty(row, ["postedAt", "posted_at", "publishedAt", "datePosted", "createdAt"], "")
    url = first_non_empty(row, ["url", "jobUrl", "job_apply_link", "apply_url", "link"], "")

    description = first_non_empty(row, ["description", "job_description", "summary"], "")

    normalized = {
        "title": title,
        "company": company,
        "location": location,
        "state": extract_state(location),
        "source": source,
        "url": url,
        "posted_at": to_iso_datetime(posted_raw),
        "role_tag": tag_role(title, description),
    }
    normalized["dedupe_key"] = dedupe_key(normalized)
    return normalized


def dedupe_key(item: dict[str, Any]) -> str:
    base = "|".join([
        (item.get("title") or "").strip().lower(),
        (item.get("company") or "").strip().lower(),
        (item.get("location") or "").strip().lower(),
    ])
    base = re.sub(r"\s+", " ", base)
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def dedupe_records(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    out = []
    for item in items:
        key = item.get("dedupe_key")
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out
