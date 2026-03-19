"""
Targeted source scraper for specific internship platforms.

Sources covered:
- Jobsora
- Internshala
- Skill India Digital Hub
- Accenture

This scraper discovers listing URLs via domain-scoped web search, then
extracts internship details from listing pages.
"""

import logging
import json
import re
from datetime import datetime
from html import unescape
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET

import requests

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

BING_SEARCH_URL = "https://www.bing.com/search"

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

TARGET_SOURCE_DOMAINS = {
    "jobsora": ("jobsora.com",),
    "internshala": ("internshala.com",),
    "skill-india-digital-hub": (
        "skillindiadigital.gov.in",
        "skillindia.gov.in",
        "skillindiadigitalhub.com",
    ),
    "accenture": ("accenture.com",),
}

SOURCE_SEED_URLS = {
    "jobsora": (
        "https://in.jobsora.com/jobs-internship",
        "https://in.jobsora.com/jobs-intern",
    ),
    "internshala": (
        "https://internshala.com/internships/",
        "https://internshala.com/internships/work-from-home-internships/",
    ),
    "skill-india-digital-hub": (
        "https://www.skillindiadigital.gov.in/home",
        "https://www.skillindiadigital.gov.in/",
    ),
    "accenture": (
        "https://www.accenture.com/in-en/careers/jobsearch",
        "https://www.accenture.com/in-en/careers",
    ),
}

SOURCE_DISPLAY_NAMES = {
    "jobsora": "Jobsora",
    "internshala": "Internshala",
    "skill-india-digital-hub": "Skill India Digital Hub",
    "accenture": "Accenture",
}

SEARCH_TERMS = [
    "software engineering",
    "data science",
    "machine learning",
    "web development",
    "cybersecurity",
    "devops",
]

MAX_CANDIDATE_LINKS_PER_SOURCE = 16
MAX_FETCHED_PAGES_PER_SOURCE = 10

DOMAIN_KEYWORDS = {
    "machine learning": "Machine Learning",
    "deep learning": "Machine Learning",
    "data science": "Data Science",
    "data analyst": "Data Science",
    "data engineering": "Data Engineering",
    "web development": "Web Development",
    "frontend": "Web Development",
    "backend": "Web Development",
    "full stack": "Web Development",
    "mobile": "Mobile Development",
    "android": "Mobile Development",
    "ios": "Mobile Development",
    "devops": "DevOps",
    "cloud": "Cloud Computing",
    "cybersecurity": "Cybersecurity",
    "nlp": "NLP",
    "artificial intelligence": "Artificial Intelligence",
    "ui/ux": "UI/UX Design",
    "product": "Product Management",
}

GENERIC_TITLE_PATTERNS = (
    re.compile(r"\bjob\s+vacancies\b", re.IGNORECASE),
    re.compile(r"\bsearch\s+jobs\b", re.IGNORECASE),
    re.compile(r"\bjobs\s+in\s+india\b", re.IGNORECASE),
    re.compile(r"\bregister\b", re.IGNORECASE),
    re.compile(r"\blogin\b", re.IGNORECASE),
    re.compile(r"\bsign\s*up\b", re.IGNORECASE),
)

REQUIREMENT_SIGNAL_PATTERNS = (
    re.compile(r"\brequirements?\b", re.IGNORECASE),
    re.compile(r"\bqualifications?\b", re.IGNORECASE),
    re.compile(r"\bskills?\s+required\b", re.IGNORECASE),
    re.compile(r"\bwho\s+can\s+apply\b", re.IGNORECASE),
    re.compile(r"\bresponsibilities\b", re.IGNORECASE),
    re.compile(r"\babout\s+the\s+internship\b", re.IGNORECASE),
)


def _infer_domain(title: str, description: str) -> str:
    combined = (title + " " + description).lower()
    for keyword, domain in DOMAIN_KEYWORDS.items():
        if keyword in combined:
            return domain
    return "Software Engineering"


def _looks_generic_page(title: str, description: str) -> bool:
    title_norm = normalize_text(title)
    desc_norm = normalize_text(description)
    if not title_norm:
        return True
    if any(pattern.search(title_norm) for pattern in GENERIC_TITLE_PATTERNS):
        return True
    # Generic hubs often include auth/nav clutter in first few hundred chars.
    noisy_markers = ["login", "register", "forgot password", "new to", "home", "contact us"]
    head = desc_norm[:500].lower()
    marker_hits = sum(1 for marker in noisy_markers if marker in head)
    return marker_hits >= 3


def _has_requirement_signals(text: str) -> bool:
    cleaned = normalize_text(text)
    return any(pattern.search(cleaned) for pattern in REQUIREMENT_SIGNAL_PATTERNS)


def _domain_allowed(url: str, allowed_domains: tuple) -> bool:
    try:
        hostname = urlparse(url).netloc.lower()
    except Exception:
        return False
    return any(domain in hostname for domain in allowed_domains)


def _is_candidate_listing_url(source_key: str, url: str) -> bool:
    """Heuristic URL gate to avoid generic directory/list pages."""
    try:
        parsed = urlparse(url)
    except Exception:
        return False

    path = (parsed.path or "").lower().strip("/")
    if not path:
        return False

    # Reject generic hubs/search pages.
    generic_paths = {
        "jobs",
        "internships",
        "careers",
        "jobsearch",
        "home",
    }
    if path in generic_paths:
        return False

    listing_tokens = {
        "intern",
        "internship",
        "job",
        "jobs",
        "career",
        "position",
        "opportunity",
        "vacancy",
    }
    if not any(token in path for token in listing_tokens):
        return False

    if source_key == "internshala":
        return "internship" in path or "jobs/" in path
    if source_key == "jobsora":
        return "jobs" in path and len(path.split("/")) >= 2
    if source_key == "accenture":
        return "job" in path or "career" in path
    if source_key == "skill-india-digital-hub":
        return "job" in path or "intern" in path or "opportunit" in path

    return True


def _extract_bing_rss_links(rss_xml: str, allowed_domains: tuple) -> list:
    links = []
    seen = set()

    try:
        root = ET.fromstring(rss_xml)
    except ET.ParseError:
        return links

    for item in root.findall("./channel/item"):
        url = normalize_text(item.findtext("link") or "")
        if not url or url in seen:
            continue
        if not _domain_allowed(url, allowed_domains):
            continue
        title = normalize_text(unescape(item.findtext("title") or ""))
        links.append((url, title))
        seen.add(url)

    return links


def _extract_links_from_seed_page(page_url: str, html: str, allowed_domains: tuple) -> list:
    links = []
    seen = set()
    anchor_pattern = re.compile(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL)

    for raw_href, raw_text in anchor_pattern.findall(html):
        href = normalize_text(unescape(raw_href))
        if not href:
            continue
        full_url = urljoin(page_url, href)
        if not full_url.startswith("http"):
            continue
        if full_url in seen:
            continue
        if not _domain_allowed(full_url, allowed_domains):
            continue

        text = normalize_text(re.sub(r"<[^>]+>", " ", raw_text))
        marker_blob = f"{full_url} {text}".lower()
        if "intern" not in marker_blob and "career" not in marker_blob and "job" not in marker_blob:
            continue

        links.append((full_url, text))
        seen.add(full_url)

    return links


def _seed_links(source_key: str, domains: tuple) -> list:
    links = []
    seen = set()

    for seed_url in SOURCE_SEED_URLS.get(source_key, ()): 
        try:
            resp = requests.get(seed_url, headers=REQUEST_HEADERS, timeout=20)
            resp.raise_for_status()
        except requests.RequestException:
            continue

        for url, title in _extract_links_from_seed_page(seed_url, resp.text or "", domains):
            if url in seen:
                continue
            links.append((url, title))
            seen.add(url)
            if len(links) >= MAX_CANDIDATE_LINKS_PER_SOURCE:
                return links

    return links


def _extract_page_title(html: str) -> str:
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if not m:
        return ""
    return normalize_text(m.group(1))


def _iter_jsonld_nodes(payload):
    if isinstance(payload, dict):
        if "@graph" in payload and isinstance(payload["@graph"], list):
            for node in payload["@graph"]:
                yield from _iter_jsonld_nodes(node)
        yield payload
    elif isinstance(payload, list):
        for item in payload:
            yield from _iter_jsonld_nodes(item)


def _extract_jobposting_jsonld(html: str) -> dict:
    scripts = re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    for raw in scripts:
        body = (raw or "").strip()
        if not body:
            continue
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            continue

        for node in _iter_jsonld_nodes(parsed):
            node_type = str(node.get("@type") or "").lower()
            if "jobposting" in node_type:
                return node
    return {}


def _extract_meta_description(html: str) -> str:
    m = re.search(
        r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']',
        html,
        re.IGNORECASE | re.DOTALL,
    )
    if not m:
        return ""
    return normalize_text(m.group(1))


def _html_to_text(html: str) -> str:
    cleaned = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.IGNORECASE)
    cleaned = re.sub(r"<style[\s\S]*?</style>", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    return normalize_text(cleaned)


def _extract_location(title: str, description: str, location_hint: str) -> str:
    candidates = []

    title_norm = normalize_text(title)
    desc_norm = normalize_text(description)
    scoped_desc = desc_norm[:6000]

    patterns = [
        re.compile(r"(?:location|job location|work location|city|state)\s*[:\-]\s*([A-Za-z][A-Za-z,&()\- ]{2,100})", re.IGNORECASE),
        re.compile(r"\bin\s+([A-Za-z][A-Za-z,&()\- ]{2,60}),\s*India\b", re.IGNORECASE),
        re.compile(r"\b([A-Za-z][A-Za-z &\-]{2,40}),\s*([A-Za-z][A-Za-z &\-]{2,40}),\s*India\b", re.IGNORECASE),
    ]

    for pattern in patterns:
        for match in pattern.findall(scoped_desc):
            if isinstance(match, tuple):
                candidate = ", ".join([part for part in match if part])
            else:
                candidate = match
            if candidate:
                candidates.append(candidate)

    if title_norm:
        candidates.append(title_norm)
    if location_hint:
        candidates.append(location_hint)

    for candidate in candidates:
        normalized = normalize_india_state_location(candidate)
        if normalized:
            return normalized

    return ""


def _extract_location_from_jobposting(jobposting: dict) -> str:
    job_location = jobposting.get("jobLocation")
    if not job_location:
        return ""

    if isinstance(job_location, list):
        locations = job_location
    else:
        locations = [job_location]

    for loc in locations:
        if not isinstance(loc, dict):
            continue
        address = loc.get("address") or {}
        if not isinstance(address, dict):
            continue
        city = normalize_text(address.get("addressLocality") or "")
        state = normalize_text(address.get("addressRegion") or "")
        country = normalize_text(address.get("addressCountry") or "")

        fallback = ", ".join(
            part for part in [city, state, country] if part
        )
        normalized = normalize_india_state_location(
            fallback,
            city=city,
            state=state,
            country=country,
        )
        if normalized:
            return normalized

    return ""


def _extract_company_from_jobposting(source_key: str, jobposting: dict) -> str:
    org = jobposting.get("hiringOrganization") or {}
    if isinstance(org, dict):
        name = normalize_text(org.get("name") or "")
        if name:
            return name
    if isinstance(org, str):
        name = normalize_text(org)
        if name:
            return name
    return SOURCE_DISPLAY_NAMES.get(source_key, "Unknown Company")


def _extract_company(source_key: str, title: str, description: str) -> str:
    if source_key == "accenture":
        return "Accenture"

    title_norm = normalize_text(title)
    title_match = re.search(r"\bat\s+([A-Za-z0-9&.,'\- ]{2,70})", title_norm, re.IGNORECASE)
    if title_match:
        return normalize_text(title_match.group(1))

    desc_head = normalize_text(description)[:2500]
    desc_match = re.search(
        r"(?:company|employer|organization)\s*[:\-]\s*([A-Za-z0-9&.,'\- ]{2,80})",
        desc_head,
        re.IGNORECASE,
    )
    if desc_match:
        return normalize_text(desc_match.group(1))

    return SOURCE_DISPLAY_NAMES.get(source_key, "Unknown Company")


def _extract_stipend(description: str) -> str:
    text = normalize_text(description)[:4000]
    m = re.search(
        r"(₹\s?[0-9,]+(?:\s?[-–]\s?₹?\s?[0-9,]+)?(?:\s*/\s*(?:month|year))?)",
        text,
        re.IGNORECASE,
    )
    if m:
        return normalize_text(m.group(1))
    return "Not disclosed"


def _search_source_links(source_key: str, domains: tuple, location_clause: str) -> list:
    links = _seed_links(source_key, domains)
    seen = set()
    for url, _ in links:
        seen.add(url)

    for domain in domains:
        for term in SEARCH_TERMS:
            query = f"site:{domain} {term} internship {location_clause}".strip()
            try:
                resp = requests.get(
                    BING_SEARCH_URL,
                    params={"q": query, "format": "rss", "setlang": "en"},
                    headers=REQUEST_HEADERS,
                    timeout=20,
                )
                resp.raise_for_status()
            except requests.RequestException as exc:
                logger.warning("Target source search failed for %s/%s: %s", source_key, term, exc)
                continue

            for url, title in _extract_bing_rss_links(resp.text, domains):
                if url in seen:
                    continue
                if not _is_candidate_listing_url(source_key, url):
                    continue
                links.append((url, title))
                seen.add(url)
                if len(links) >= MAX_CANDIDATE_LINKS_PER_SOURCE:
                    return links

    return links


def fetch_internships(location: str = "") -> list:
    """
    Fetch internships from targeted source websites.

    Args:
        location: Optional India city/state hint.

    Returns:
        Internship docs ready for persistence.
    """
    location_hint = normalize_text(location)
    if location_hint and "india" not in location_hint.lower():
        location_clause = f"{location_hint} India"
    elif location_hint:
        location_clause = location_hint
    else:
        location_clause = "India"

    results = []
    seen_apply_urls = set()

    for source_key, domains in TARGET_SOURCE_DOMAINS.items():
        candidate_links = _search_source_links(source_key, domains, location_clause)
        kept = 0

        for apply_url, result_title in candidate_links[:MAX_FETCHED_PAGES_PER_SOURCE]:
            if apply_url in seen_apply_urls:
                continue
            if not _is_candidate_listing_url(source_key, apply_url):
                continue

            try:
                resp = requests.get(apply_url, headers=REQUEST_HEADERS, timeout=20)
                resp.raise_for_status()
            except requests.RequestException:
                continue

            html = resp.text or ""
            jobposting = _extract_jobposting_jsonld(html)

            if jobposting:
                page_title = normalize_text(jobposting.get("title") or "") or _extract_page_title(html) or result_title or "Internship"
                jp_description = normalize_text(jobposting.get("description") or "")
                qualifications = normalize_text(jobposting.get("qualifications") or "")
                skills_hint = normalize_text(jobposting.get("skills") or "")
                requirement_blob = normalize_text(" ".join([qualifications, skills_hint]))
                description = jp_description or normalize_text(f"{_extract_meta_description(html)} {_html_to_text(html)}")
                normalized_location = _extract_location_from_jobposting(jobposting)
                company = _extract_company_from_jobposting(source_key, jobposting)
            else:
                page_title = _extract_page_title(html) or result_title or "Internship"
                description = normalize_text(f"{_extract_meta_description(html)} {_html_to_text(html)}")
                requirement_blob = description

                # Controlled fallback: keep only detail-like internship pages.
                if "intern" not in page_title.lower():
                    continue
                if _looks_generic_page(page_title, description):
                    continue
                if not _has_requirement_signals(description):
                    continue

                normalized_location = _extract_location(page_title, description, location_hint)
                company = _extract_company(source_key, page_title, description)

            if not is_internship_listing(page_title, description):
                continue

            if not normalized_location:
                normalized_location = _extract_location(page_title, description, location_hint)
            if not normalized_location:
                continue
            if not location_matches_hint(normalized_location, location_hint):
                continue

            skills = extract_required_skills(
                title=page_title,
                description=description,
                requirement_text=requirement_blob if jobposting else description,
            )
            if not skills:
                continue

            internship_doc = {
                "title": page_title[:140],
                "company": company,
                "required_skills": skills,
                "description": description[:1200],
                "domain": _infer_domain(page_title, description),
                "stipend": _extract_stipend(description),
                "duration": "3–6 months",
                "location": normalized_location,
                "openings": 1,
                "apply_url": apply_url,
                "source": source_key,
                "scraped_at": datetime.utcnow(),
            }

            results.append(internship_doc)
            seen_apply_urls.add(apply_url)
            kept += 1

        logger.info(
            "TargetSources: kept %d internships from %s (candidates=%d)",
            kept,
            source_key,
            len(candidate_links),
        )

    return results
