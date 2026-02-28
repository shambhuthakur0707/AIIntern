"""
matching_engine.py — Deterministic Skill Matching & Filtering

Computes skill overlap between user and each internship, filters out
internships below a 25% overlap threshold.
"""

import logging
from typing import Any, Dict, List

from flask import current_app

logger = logging.getLogger(__name__)

# ── Config ───────────────────────────────────────────────────────────
MIN_OVERLAP_PCT = 25.0   # Filter out internships below this overlap %
MAX_INTERNSHIPS = 100     # Safety cap on DB fetch


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
    required_lower = {s.lower() for s in required_list}

    matched = [s for s in required_list if s.lower() in user_set]
    missing = [s for s in required_list if s.lower() not in user_set]

    total = len(required_lower)
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

    docs = list(db.internships.find())
    logger.info("Fetched %d internships from DB", len(docs))

    filtered: List[Dict[str, Any]] = []

    for doc in docs[:MAX_INTERNSHIPS]:
        doc["_id"] = str(doc["_id"])
        required = doc.get("required_skills", [])

        overlap = compute_skill_overlap(user_skills, required)

        if overlap["overlap_pct"] < MIN_OVERLAP_PCT:
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
    return filtered
