"""
matching_engine.py — Deterministic Skill Matching & Filtering

Computes skill overlap between user and each internship, filters out
internships below a 25% overlap threshold.
"""

import logging
import re
from typing import Any, Dict, List

from flask import current_app

try:
    from ..scrapers.internship_filters import extract_required_skills
except ImportError:
    from scrapers.internship_filters import extract_required_skills  # type: ignore

logger = logging.getLogger(__name__)

# ── Config ───────────────────────────────────────────────────────────
MIN_OVERLAP_PCT = 25.0   # Filter out internships below this overlap %
MAX_INTERNSHIPS = 100     # Safety cap on DB fetch


def _normalize_location_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def _location_is_match(user_location: str, internship: Dict[str, Any]) -> bool:
    user_loc = _normalize_location_text(user_location)
    if not user_loc:
        return True

    intern_loc = _normalize_location_text(internship.get("location", ""))
    if not intern_loc:
        return False

    if internship.get("is_remote") is True or "remote" in intern_loc:
        return True

    # Match if one side contains the other, useful for city/state/country granularity.
    return user_loc in intern_loc or intern_loc in user_loc


def compute_skill_overlap(
    user_skills: List[str], required_skills: List[str]
) -> Dict[str, Any]:
    """
    Case-insensitive set intersection between user skills and
    internship required skills.

    Returns
    -------
    dict with keys:
      - overlap_pct    : float 0–100
      - matched_skills : list[str]  (original casing from internship)
      - missing_skills : list[str]  (original casing from internship)
    """
    user_set = {s.strip().lower() for s in user_skills if s.strip()}
    required_list = [s.strip() for s in required_skills if s.strip()]

    # De-duplicate required skills case-insensitively while preserving order.
    required_unique: List[str] = []
    seen_required = set()
    for skill in required_list:
        key = skill.lower()
        if key in seen_required:
            continue
        seen_required.add(key)
        required_unique.append(skill)

    matched = [s for s in required_unique if s.lower() in user_set]
    missing = [s for s in required_unique if s.lower() not in user_set]

    total = len(required_unique)
    overlap_pct = round((len(matched) / total) * 100, 2) if total > 0 else 0.0

    return {
        "overlap_pct": overlap_pct,
        "matched_skills": matched,
        "missing_skills": missing,
    }


def fetch_and_filter(user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Fetch all internships from MongoDB, compute skill overlap for each,
    and discard those below MIN_OVERLAP_PCT.

    Each returned dict is the original internship document enriched with:
      - overlap_pct, matched_skills, missing_skills

    Parameters
    ----------
    user_profile : dict with at least {"skills": [...]}

    Returns
    -------
    list[dict] — filtered internships with overlap metadata attached.
    """
    db = current_app.config["DB"]
    user_skills: List[str] = user_profile.get("skills", [])
    user_location: str = user_profile.get("location", "")

    docs = list(db.internships.find())
    logger.info("Fetched %d internships from DB", len(docs))

    filtered: List[Dict[str, Any]] = []

    for doc in docs[:MAX_INTERNSHIPS]:
        doc["_id"] = str(doc["_id"])
        required = doc.get("required_skills", [])
        if len(required) < 2:
            primary = extract_required_skills(
                title=doc.get("title", ""),
                description=doc.get("description", ""),
                requirement_text=doc.get("requirement_text", ""),
            )
            expanded = extract_required_skills(
                title=doc.get("title", ""),
                description=doc.get("description", ""),
                requirement_text=doc.get("description", ""),
                limit=12,
            )
            merged = []
            seen = set()
            for skill in (required + primary + expanded):
                key = skill.lower()
                if key in seen:
                    continue
                seen.add(key)
                merged.append(skill)
            required = merged[:12]
            if required:
                doc["required_skills"] = required

        overlap = compute_skill_overlap(user_skills, required)

        # Keep listings that have no structured skill tags; external scrapers
        # often return empty required_skills even for valid internships.
        if required and overlap["overlap_pct"] < MIN_OVERLAP_PCT:
            continue

        # Attach overlap metadata to the doc
        doc["overlap_pct"] = overlap["overlap_pct"]
        doc["matched_skills"] = overlap["matched_skills"]
        doc["missing_skills"] = overlap["missing_skills"]
        filtered.append(doc)

    logger.info(
        "Filtered to %d internships (>= %.0f%% overlap)",
        len(filtered),
        MIN_OVERLAP_PCT,
    )

    if not user_location:
        return filtered

    preferred = [doc for doc in filtered if _location_is_match(user_location, doc)]
    if preferred:
        logger.info(
            "Location-aware filter kept %d/%d internships for user location '%s'",
            len(preferred),
            len(filtered),
            user_location,
        )
        return preferred

    logger.info(
        "No internships matched user location '%s'; returning %d fallback results",
        user_location,
        len(filtered),
    )
    return filtered
