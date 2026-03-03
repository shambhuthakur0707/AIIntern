"""
ranking_engine.py — Multi-Factor Weighted Ranking with Explainability

Produces a weighted score (0–100) for each internship using:
  60%  skill overlap
  20%  keyword relevance  (TF-IDF of interests vs description/domain)
  20%  experience-level match
"""

import logging
from typing import Any, Dict, List
from urllib.parse import quote_plus

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

# ── Weights ──────────────────────────────────────────────────────────
W_SKILL = 0.60
W_KEYWORD = 0.20
W_EXPERIENCE = 0.20

TOP_N = 5  # Max internships forwarded to LLM layer (kept low for faster API responses)

# ── Experience keywords ──────────────────────────────────────────────
EXPERIENCE_KEYWORDS: Dict[str, List[str]] = {
    "beginner":     ["beginner", "entry", "junior", "intern", "fresher", "trainee"],
    "intermediate": ["intermediate", "mid", "associate", "analyst"],
    "advanced":     ["senior", "lead", "advanced", "expert", "principal", "staff"],
}


def _build_apply_url(internship: Dict[str, Any]) -> str:
    for field in ("apply_url", "application_url", "job_url"):
        value = str(internship.get(field, "")).strip()
        if value:
            return value

    title = str(internship.get("title", "Internship")).strip()
    company = str(internship.get("company", "")).strip()
    query = " ".join(part for part in [title, company, "internship"] if part)
    return f"https://www.linkedin.com/jobs/search/?keywords={quote_plus(query)}"


# ── Keyword relevance (TF-IDF) ──────────────────────────────────────
def _keyword_score(user_interests: List[str], internship: Dict[str, Any]) -> float:
    """
    Cosine similarity between the user's interests and the
    internship's title + domain + description.  Returns 0–100.
    """
    interest_text = " ".join(i.strip().lower() for i in user_interests if i.strip())
    intern_text = " ".join([
        internship.get("title", "").lower(),
        internship.get("domain", "").lower(),
        internship.get("description", "").lower(),
    ])

    if not interest_text.strip() or not intern_text.strip():
        return 0.0

    try:
        vectorizer = TfidfVectorizer(analyzer="word", ngram_range=(1, 2))
        matrix = vectorizer.fit_transform([interest_text, intern_text])
        sim = cosine_similarity(matrix[0:1], matrix[1:2])[0][0]
        return round(float(sim) * 100, 2)
    except Exception:
        return 0.0


# ── Experience-level match ───────────────────────────────────────────
def _experience_score(user_level: str, internship: Dict[str, Any]) -> float:
    """
    Returns 100 if the internship text contains keywords matching
    the user's experience level, 50 for adjacent levels, 25 otherwise.
    """
    user_level = (user_level or "beginner").lower().strip()
    searchable = " ".join([
        internship.get("title", ""),
        internship.get("description", ""),
    ]).lower()

    # Direct match
    keywords = EXPERIENCE_KEYWORDS.get(user_level, [])
    if any(kw in searchable for kw in keywords):
        return 100.0

    # Adjacent level (one step away)
    levels = ["beginner", "intermediate", "advanced"]
    idx = levels.index(user_level) if user_level in levels else 0
    adjacent = []
    if idx > 0:
        adjacent.extend(EXPERIENCE_KEYWORDS[levels[idx - 1]])
    if idx < len(levels) - 1:
        adjacent.extend(EXPERIENCE_KEYWORDS[levels[idx + 1]])
    if any(kw in searchable for kw in adjacent):
        return 50.0

    # Most internship listings don't explicitly mention levels,
    # so give a generous baseline instead of penalising.
    return 60.0


# ── Public API ───────────────────────────────────────────────────────
def rank_internships(
    user_profile: Dict[str, Any],
    filtered_internships: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Compute weighted score for each internship and return the top N,
    sorted descending.  Each result includes a full score breakdown
    for explainability.

    Parameters
    ----------
    user_profile : dict with skills, interests, experience_level, etc.
    filtered_internships : list of dicts from matching_engine (already
                           enriched with overlap_pct, matched_skills, missing_skills).

    Returns
    -------
    list[dict] — top N results, each containing:
        title, company, domain, stipend, duration, location, openings,
        weighted_score, score_breakdown, matched_skills, missing_skills
    """
    user_interests = user_profile.get("interests", [])
    user_level = user_profile.get("experience_level", "beginner")

    scored: List[Dict[str, Any]] = []

    for intern in filtered_internships:
        skill_score = intern.get("overlap_pct", 0.0)
        kw_score = _keyword_score(user_interests, intern)
        exp_score = _experience_score(user_level, intern)

        weighted = round(
            W_SKILL * skill_score
            + W_KEYWORD * kw_score
            + W_EXPERIENCE * exp_score,
            2,
        )

        scored.append({
            # Internship metadata
            "title": intern.get("title", "Untitled"),
            "company": intern.get("company", "Unknown"),
            "domain": intern.get("domain", ""),
            "stipend": intern.get("stipend", ""),
            "duration": intern.get("duration", ""),
            "location": intern.get("location", ""),
            "openings": intern.get("openings", 0),
            "required_skills": intern.get("required_skills", []),
            "apply_url": _build_apply_url(intern),
            # Scores
            "weighted_score": weighted,
            "score_breakdown": {
                "skill_overlap": skill_score,
                "keyword_relevance": kw_score,
                "experience_match": exp_score,
            },
            # Skill analysis
            "matched_skills": intern.get("matched_skills", []),
            "missing_skills": intern.get("missing_skills", []),
        })

    # Sort descending by weighted score, take top N
    scored.sort(key=lambda x: x["weighted_score"], reverse=True)
    top = scored[:TOP_N]

    logger.info(
        "Ranked %d → top %d. Scores: %s",
        len(scored),
        len(top),
        [r["weighted_score"] for r in top],
    )
    return top
