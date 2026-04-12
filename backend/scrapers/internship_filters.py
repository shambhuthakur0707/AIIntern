"""
Shared internship scraping filters and normalization utilities.

Enforces:
1. Internship-only records
2. Location normalization with worldwide/global noise filtering
3. Required skill extraction from title + requirements + description text
4. Remote vs non-remote tagging
"""

from __future__ import annotations

import re
from typing import Dict, Iterable, List, Optional, Tuple


INTERNSHIP_PATTERNS = (
    re.compile(r"\bintern(?:ship)?\b", re.IGNORECASE),
    re.compile(r"\btrainee\b", re.IGNORECASE),
    re.compile(r"\bapprentice(?:ship)?\b", re.IGNORECASE),
    re.compile(r"\bco[-\s]?op\b", re.IGNORECASE),
)

GLOBAL_LOCATION_PATTERNS = (
    re.compile(r"\bworldwide\b", re.IGNORECASE),
    re.compile(r"\banywhere\b", re.IGNORECASE),
    re.compile(r"\bglobal\b", re.IGNORECASE),
    re.compile(r"\binternational\b", re.IGNORECASE),
)

REMOTE_PATTERNS = (
    re.compile(r"\bremote\b", re.IGNORECASE),
    re.compile(r"\bwfh\b", re.IGNORECASE),
    re.compile(r"\bwork\s+from\s+home\b", re.IGNORECASE),
    re.compile(r"\bdistributed\b", re.IGNORECASE),
)

COUNTRY_ALIASES: Dict[str, Tuple[str, ...]] = {
    "India": ("india", "in"),
    "Nepal": ("nepal", "np"),
    "USA": (
        "usa",
        "us",
        "u.s.",
        "u.s.a.",
        "united states",
        "united states of america",
    ),
}

INDIA_STATE_ALIASES: Dict[str, Tuple[str, ...]] = {
    "Andhra Pradesh": ("andhra pradesh",),
    "Arunachal Pradesh": ("arunachal pradesh",),
    "Assam": ("assam",),
    "Bihar": ("bihar",),
    "Chhattisgarh": ("chhattisgarh",),
    "Goa": ("goa",),
    "Gujarat": ("gujarat",),
    "Haryana": ("haryana",),
    "Himachal Pradesh": ("himachal pradesh",),
    "Jharkhand": ("jharkhand",),
    "Karnataka": ("karnataka",),
    "Kerala": ("kerala",),
    "Madhya Pradesh": ("madhya pradesh",),
    "Maharashtra": ("maharashtra",),
    "Manipur": ("manipur",),
    "Meghalaya": ("meghalaya",),
    "Mizoram": ("mizoram",),
    "Nagaland": ("nagaland",),
    "Odisha": ("odisha", "orissa"),
    "Punjab": ("punjab",),
    "Rajasthan": ("rajasthan",),
    "Sikkim": ("sikkim",),
    "Tamil Nadu": ("tamil nadu",),
    "Telangana": ("telangana",),
    "Tripura": ("tripura",),
    "Uttar Pradesh": ("uttar pradesh",),
    "Uttarakhand": ("uttarakhand",),
    "West Bengal": ("west bengal",),
    "Delhi": ("delhi", "new delhi", "ncr"),
    "Jammu and Kashmir": ("jammu and kashmir", "jammu & kashmir"),
    "Ladakh": ("ladakh",),
    "Chandigarh": ("chandigarh",),
    "Puducherry": ("puducherry", "pondicherry"),
    "Andaman and Nicobar Islands": ("andaman and nicobar",),
    "Dadra and Nagar Haveli and Daman and Diu": (
        "dadra and nagar haveli and daman and diu",
        "daman and diu",
        "dadra and nagar haveli",
    ),
    "Lakshadweep": ("lakshadweep",),
}

CITY_TO_STATE: Dict[str, str] = {
    "bengaluru": "Karnataka",
    "bangalore": "Karnataka",
    "mysuru": "Karnataka",
    "mumbai": "Maharashtra",
    "pune": "Maharashtra",
    "nagpur": "Maharashtra",
    "hyderabad": "Telangana",
    "warangal": "Telangana",
    "chennai": "Tamil Nadu",
    "coimbatore": "Tamil Nadu",
    "madurai": "Tamil Nadu",
    "delhi": "Delhi",
    "gurugram": "Haryana",
    "gurgaon": "Haryana",
    "noida": "Uttar Pradesh",
    "greater noida": "Uttar Pradesh",
    "lucknow": "Uttar Pradesh",
    "kanpur": "Uttar Pradesh",
    "kolkata": "West Bengal",
    "howrah": "West Bengal",
    "ahmedabad": "Gujarat",
    "surat": "Gujarat",
    "vadodara": "Gujarat",
    "jaipur": "Rajasthan",
    "udaipur": "Rajasthan",
    "indore": "Madhya Pradesh",
    "bhopal": "Madhya Pradesh",
    "kochi": "Kerala",
    "ernakulam": "Kerala",
    "thiruvananthapuram": "Kerala",
    "patna": "Bihar",
    "bhubaneswar": "Odisha",
    "chandigarh": "Chandigarh",
    "guwahati": "Assam",
    "ranchi": "Jharkhand",
    "visakhapatnam": "Andhra Pradesh",
    "vijayawada": "Andhra Pradesh",
}

CITY_TO_COUNTRY: Dict[str, str] = {
    "kathmandu": "Nepal",
    "lalitpur": "Nepal",
    "pokhara": "Nepal",
    "biratnagar": "Nepal",
    "new york": "USA",
    "san francisco": "USA",
    "seattle": "USA",
    "austin": "USA",
    "boston": "USA",
    "chicago": "USA",
    "los angeles": "USA",
}

SKILL_PATTERNS: Dict[str, Tuple[re.Pattern[str], ...]] = {
    "Python": (re.compile(r"\bpython(?:3)?\b", re.IGNORECASE),),
    "Java": (re.compile(r"\bjava\b", re.IGNORECASE),),
    "JavaScript": (
        re.compile(r"\bjavascript\b", re.IGNORECASE),
        re.compile(r"\bjs\b", re.IGNORECASE),
    ),
    "TypeScript": (re.compile(r"\btypescript\b", re.IGNORECASE),),
    "React": (re.compile(r"\breact(?:\.js)?\b", re.IGNORECASE),),
    "Node.js": (
        re.compile(r"\bnode(?:\.js)?\b", re.IGNORECASE),
        re.compile(r"\bnodejs\b", re.IGNORECASE),
    ),
    "Express.js": (re.compile(r"\bexpress(?:\.js)?\b", re.IGNORECASE),),
    "Django": (re.compile(r"\bdjango\b", re.IGNORECASE),),
    "Flask": (re.compile(r"\bflask\b", re.IGNORECASE),),
    "FastAPI": (re.compile(r"\bfastapi\b", re.IGNORECASE),),
    "Spring Boot": (re.compile(r"\bspring\s+boot\b", re.IGNORECASE),),
    "SQL": (re.compile(r"\bsql\b", re.IGNORECASE),),
    "PostgreSQL": (re.compile(r"\bpostgres(?:ql)?\b", re.IGNORECASE),),
    "MySQL": (re.compile(r"\bmysql\b", re.IGNORECASE),),
    "MongoDB": (re.compile(r"\bmongo(?:db)?\b", re.IGNORECASE),),
    "Redis": (re.compile(r"\bredis\b", re.IGNORECASE),),
    "Docker": (re.compile(r"\bdocker\b", re.IGNORECASE),),
    "Kubernetes": (re.compile(r"\bkubernetes\b", re.IGNORECASE),),
    "AWS": (
        re.compile(r"\baws\b", re.IGNORECASE),
        re.compile(r"\bamazon\s+web\s+services\b", re.IGNORECASE),
    ),
    "Azure": (re.compile(r"\bazure\b", re.IGNORECASE),),
    "GCP": (
        re.compile(r"\bgcp\b", re.IGNORECASE),
        re.compile(r"\bgoogle\s+cloud\b", re.IGNORECASE),
    ),
    "Git": (re.compile(r"\bgit\b", re.IGNORECASE),),
    "Linux": (re.compile(r"\blinux\b", re.IGNORECASE),),
    "HTML": (re.compile(r"\bhtml(?:5)?\b", re.IGNORECASE),),
    "CSS": (re.compile(r"\bcss(?:3)?\b", re.IGNORECASE),),
    "REST API": (re.compile(r"\brest(?:ful)?\s+api(?:s)?\b", re.IGNORECASE),),
    "GraphQL": (re.compile(r"\bgraphql\b", re.IGNORECASE),),
    "TensorFlow": (re.compile(r"\btensorflow\b", re.IGNORECASE),),
    "PyTorch": (re.compile(r"\bpytorch\b", re.IGNORECASE),),
    "Scikit-learn": (
        re.compile(r"\bscikit[-\s]?learn\b", re.IGNORECASE),
        re.compile(r"\bsklearn\b", re.IGNORECASE),
    ),
    "Pandas": (re.compile(r"\bpandas\b", re.IGNORECASE),),
    "NumPy": (re.compile(r"\bnumpy\b", re.IGNORECASE),),
    "OpenCV": (re.compile(r"\bopencv\b", re.IGNORECASE),),
    "Machine Learning": (re.compile(r"\bmachine\s+learning\b", re.IGNORECASE),),
    "Deep Learning": (re.compile(r"\bdeep\s+learning\b", re.IGNORECASE),),
    "NLP": (
        re.compile(r"\bnlp\b", re.IGNORECASE),
        re.compile(r"\bnatural\s+language\s+processing\b", re.IGNORECASE),
    ),
    "Data Analysis": (re.compile(r"\bdata\s+analysis\b", re.IGNORECASE),),
    "C++": (re.compile(r"\bc\+\+\b", re.IGNORECASE),),
    "C#": (
        re.compile(r"\bc#\b", re.IGNORECASE),
        re.compile(r"\bcsharp\b", re.IGNORECASE),
    ),
    "Go": (
        re.compile(r"\bgolang\b", re.IGNORECASE),
        re.compile(r"\bgo\s+language\b", re.IGNORECASE),
    ),
    "Rust": (re.compile(r"\brust\b", re.IGNORECASE),),
    "Kotlin": (re.compile(r"\bkotlin\b", re.IGNORECASE),),
    "Swift": (re.compile(r"\bswift\b", re.IGNORECASE),),
    "Flutter": (re.compile(r"\bflutter\b", re.IGNORECASE),),
    "React Native": (re.compile(r"\breact\s+native\b", re.IGNORECASE),),
    "Firebase": (re.compile(r"\bfirebase\b", re.IGNORECASE),),
    "Selenium": (re.compile(r"\bselenium\b", re.IGNORECASE),),
    "Apache Spark": (re.compile(r"\bapache\s+spark\b", re.IGNORECASE), re.compile(r"\bspark\b", re.IGNORECASE)),
    "Hadoop": (re.compile(r"\bhadoop\b", re.IGNORECASE),),
    "Kafka": (re.compile(r"\bkafka\b", re.IGNORECASE),),
    "Airflow": (re.compile(r"\bairflow\b", re.IGNORECASE),),
    "Terraform": (re.compile(r"\bterraform\b", re.IGNORECASE),),
    "CI/CD": (
        re.compile(r"\bci\s*/\s*cd\b", re.IGNORECASE),
        re.compile(r"\bcontinuous\s+integration\b", re.IGNORECASE),
        re.compile(r"\bcontinuous\s+delivery\b", re.IGNORECASE),
    ),
    "Tableau": (re.compile(r"\btableau\b", re.IGNORECASE),),
    "Power BI": (re.compile(r"\bpower\s+bi\b", re.IGNORECASE),),
    "Communication": (re.compile(r"\bcommunication\s+skills?\b", re.IGNORECASE),),
    "Problem Solving": (re.compile(r"\bproblem\s+solving\b", re.IGNORECASE),),
}

REQUIREMENT_HINTS = (
    "requirements",
    "requirement",
    "qualifications",
    "must have",
    "skills required",
    "what we are looking for",
    "what we're looking for",
    "eligibility",
)


def normalize_text(value: str) -> str:
    """Strip HTML-like markup and collapse whitespace."""
    if not value:
        return ""
    no_html = re.sub(r"<[^>]+>", " ", value)
    no_entities = re.sub(r"&[a-zA-Z#0-9]+;", " ", no_html)
    return re.sub(r"\s+", " ", no_entities).strip()


def is_internship_listing(title: str, description: str = "") -> bool:
    """True when the listing clearly represents an internship role."""
    title_text = normalize_text(title)
    desc_text = normalize_text(description)
    combined = f"{title_text} {desc_text}".strip()
    if not combined:
        return False
    return any(pattern.search(combined) for pattern in INTERNSHIP_PATTERNS)


def _canonical_state_from_text(text: str) -> Optional[str]:
    text_lower = text.lower()
    for state, aliases in INDIA_STATE_ALIASES.items():
        for alias in aliases:
            if re.search(rf"\b{re.escape(alias)}\b", text_lower):
                return state
    return None


def _city_state_from_text(text: str) -> Optional[str]:
    text_lower = text.lower()
    for city, state in CITY_TO_STATE.items():
        if re.search(rf"\b{re.escape(city)}\b", text_lower):
            return state
    return None


def _canonical_country_from_text(text: str) -> Optional[str]:
    text_lower = normalize_text(text).lower()
    if not text_lower:
        return None
    for canonical, aliases in COUNTRY_ALIASES.items():
        for alias in aliases:
            if re.search(rf"\b{re.escape(alias)}\b", text_lower):
                return canonical

    # Generic fallback: use the last comma-separated token as country candidate
    # when it appears to be alphabetic and not a global placeholder.
    parts = [p.strip() for p in text_lower.split(",") if p.strip()]
    if parts:
        tail = parts[-1]
        if re.fullmatch(r"[a-z][a-z\s.&-]{1,40}", tail):
            if tail not in {
                "remote",
                "worldwide",
                "global",
                "anywhere",
                "international",
            }:
                return tail.title()
    return None


def is_remote_listing(*values: str) -> bool:
    """Return True when text strongly signals a remote role."""
    haystack = normalize_text(" ".join(v for v in values if v))
    if not haystack:
        return False
    return any(pattern.search(haystack) for pattern in REMOTE_PATTERNS)


def infer_work_mode(*values: str) -> str:
    """Return a compact mode label used by API/UI."""
    return "Remote" if is_remote_listing(*values) else "On-site/Hybrid"


def normalize_india_state_location(
    raw_location: str = "",
    *,
    city: str = "",
    state: str = "",
    country: str = "",
) -> Optional[str]:
    """
    Return normalized location as '<City>, <State>, India' or '<State>, India'.
    Return None when location is non-India, global/remote, or missing state signal.
    """
    joined = normalize_text(
        ", ".join(part for part in [raw_location, city, state, country] if part)
    )
    if not joined:
        return None

    if any(pattern.search(joined) for pattern in GLOBAL_LOCATION_PATTERNS):
        return None

    canonical_state = _canonical_state_from_text(state) or _canonical_state_from_text(joined)
    if not canonical_state:
        canonical_state = _city_state_from_text(city) or _city_state_from_text(joined)
    if not canonical_state:
        return None

    joined_lower = joined.lower()
    country_lower = normalize_text(country).lower()
    has_india_signal = (
        "india" in joined_lower
        or country_lower in {"india", "in"}
        or canonical_state is not None
    )
    if not has_india_signal:
        return None

    city_text = normalize_text(city)
    if not city_text and raw_location:
        candidate = normalize_text(raw_location.split(",", 1)[0])
        if candidate and not _canonical_state_from_text(candidate) and candidate.lower() not in {
            "india",
            "remote",
        }:
            city_text = candidate

    if city_text:
        return f"{city_text}, {canonical_state}, India"
    return f"{canonical_state}, India"


def normalize_supported_location(
    raw_location: str = "",
    *,
    city: str = "",
    state: str = "",
    country: str = "",
    description: str = "",
) -> Optional[str]:
    """
    Return normalized location for any country with optional locality and remote tag.

    Examples:
    - "Bengaluru, Karnataka, India"
    - "Kathmandu, Nepal"
    - "Berlin, Germany"
    - "Remote - Austin, USA"

    Returns None for worldwide/global placeholders with no concrete location.
    """
    joined = normalize_text(
        ", ".join(part for part in [raw_location, city, state, country] if part)
    )
    if not joined:
        return None

    joined_lower = joined.lower()
    if any(pattern.search(joined_lower) for pattern in GLOBAL_LOCATION_PATTERNS):
        if not _canonical_country_from_text(joined):
            return None

    # Prefer India's detailed normalizer when country/state hints indicate India.
    india_first = normalize_india_state_location(raw_location, city=city, state=state, country=country)
    if india_first:
        base_location = india_first
    else:
        canonical_country = (
            _canonical_country_from_text(country)
            or _canonical_country_from_text(joined)
            or CITY_TO_COUNTRY.get(normalize_text(city).lower())
            or CITY_TO_COUNTRY.get(normalize_text(raw_location).split(",", 1)[0].strip().lower())
        )
        if not canonical_country:
            return None

        locality = normalize_text(city) or normalize_text(state)
        if not locality and raw_location:
            candidate = normalize_text(raw_location.split(",", 1)[0])
            candidate_lower = candidate.lower()
            if candidate and candidate_lower not in {
                "remote",
                "india",
                "nepal",
                "usa",
                "us",
                "united states",
                "united states of america",
            }:
                locality = candidate

        if locality:
            base_location = f"{locality}, {canonical_country}"
        else:
            base_location = canonical_country

    if is_remote_listing(raw_location, description, state, city):
        return f"Remote - {base_location}"
    return base_location


def location_matches_hint(normalized_location: str, location_hint: str) -> bool:
    """Return True if normalized location matches optional country/city/remote hint."""
    hint = normalize_text(location_hint).lower()
    if not hint:
        return True
    normalized_lower = normalized_location.lower()

    if hint in {"remote", "wfh", "work from home"}:
        return "remote" in normalized_lower

    hint_country = _canonical_country_from_text(hint)
    if hint_country:
        return hint_country.lower() in normalized_lower

    hint_state = _canonical_state_from_text(hint)
    if hint_state:
        return hint_state.lower() in normalized_lower

    hint_city_state = _city_state_from_text(hint)
    if hint_city_state:
        return hint_city_state.lower() in normalized_lower

    return hint in normalized_lower


def is_supported_location_hint(location_hint: str) -> bool:
    """Validate that a location hint is concrete enough for searching."""
    hint = normalize_text(location_hint)
    if not hint:
        return True
    hint_lower = hint.lower()
    if hint_lower in {"worldwide", "global", "anywhere", "international"}:
        return False
    return True


def _requirement_focus_text(text: str) -> str:
    """Extract requirement-like segments to prioritize skill matches."""
    if not text:
        return ""
    parts = re.split(r"[\n\r.;]", text)
    focused: List[str] = []
    for part in parts:
        p = part.strip()
        if not p:
            continue
        p_lower = p.lower()
        if any(hint in p_lower for hint in REQUIREMENT_HINTS):
            focused.append(p)
            continue
        if p.startswith(("-", "*")):
            focused.append(p)
    return " ".join(focused)


def extract_requirement_text(
    *,
    description: str = "",
    explicit_requirements: str = "",
    limit_chars: int = 900,
) -> str:
    """
    Return a compact requirements-focused text extracted from the post.

    Preference order:
    1) Explicit requirement fields from source payload (if present)
    2) Requirement-like segments mined from description
    """
    explicit = normalize_text(explicit_requirements)
    if explicit:
        return explicit[:limit_chars]

    focused = _requirement_focus_text(normalize_text(description))
    if focused:
        return focused[:limit_chars]

    # Fallback to description slice so downstream extraction still has context.
    return normalize_text(description)[:limit_chars]


def _score_skill(skill_patterns: Iterable[re.Pattern[str]], text: str) -> int:
    score = 0
    for pattern in skill_patterns:
        score += len(pattern.findall(text))
    return score


def extract_required_skills(
    title: str = "",
    description: str = "",
    requirement_text: str = "",
    limit: int = 12,
) -> List[str]:
    """Extract required skills from internship text with requirement-section priority."""
    title_text = normalize_text(title)
    desc_text = normalize_text(description)
    req_text = normalize_text(requirement_text)

    combined = " ".join(part for part in [title_text, req_text, desc_text] if part).strip()
    if not combined:
        return []

    focus = extract_requirement_text(description=desc_text, explicit_requirements=req_text)
    focus_text = f"{title_text} {focus}".strip()

    scored: List[Tuple[str, int]] = []
    for skill, patterns in SKILL_PATTERNS.items():
        base_score = _score_skill(patterns, combined)
        if base_score <= 0:
            continue
        focus_bonus = _score_skill(patterns, focus_text)
        scored.append((skill, base_score + focus_bonus))

    scored.sort(key=lambda item: (-item[1], item[0]))
    return [skill for skill, _ in scored[:limit]]
