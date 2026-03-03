"""
response_formatter.py — Final Response Assembly

Merges ranking data with LLM/fallback analysis for each internship
into a clean, consistent API response.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def format_response(
    ranked_results: List[Dict[str, Any]],
    llm_analyses: List[Dict[str, Any]],
    model_used: str,
    total_fetched: int,
    passed_filter: int,
) -> Dict[str, Any]:
    """
    Merge ranking metadata with LLM/fallback analysis into the final
    API response.

    Parameters
    ----------
    ranked_results : list from ranking_engine (top N internships)
    llm_analyses   : list of dicts (one per ranked result) from
                     llm_engine or fallback_engine, in the same order
    model_used     : name of the Ollama model used
    total_fetched  : total internships fetched from DB
    passed_filter  : internships that passed the 25% overlap filter

    Returns
    -------
    dict ready for jsonify()
    """
    recommendations: List[Dict[str, Any]] = []
    fallback_count = 0

    for rank_data, analysis in zip(ranked_results, llm_analyses):
        if analysis.get("fallback_used"):
            fallback_count += 1

        rec = {
            # ── Internship info ──────────────────────────────
            "title": rank_data.get("title", "Untitled"),
            "company": rank_data.get("company", "Unknown"),
            "domain": rank_data.get("domain", ""),
            "stipend": rank_data.get("stipend", ""),
            "duration": rank_data.get("duration", ""),
            "location": rank_data.get("location", ""),
            "openings": rank_data.get("openings", 0),
            "apply_url": rank_data.get("apply_url", ""),
            # ── Deterministic scores ─────────────────────────
            "weighted_score": rank_data.get("weighted_score", 0),
            "score_breakdown": rank_data.get("score_breakdown", {}),
            "matched_skills": rank_data.get("matched_skills", []),
            # ── LLM / Fallback analysis ──────────────────────
            "confidence_score": analysis.get("confidence_score", 0),
            "reasoning": analysis.get("reasoning", ""),
            "strengths": analysis.get("strengths", []),
            "missing_skills": analysis.get("missing_skills", []),
            "skill_gap_analysis": analysis.get("skill_gap_analysis", ""),
            "learning_roadmap": analysis.get("learning_roadmap", []),
            "improvement_priority": analysis.get("improvement_priority", ""),
            "fallback_used": analysis.get("fallback_used", False),
            "fallback_reason": analysis.get("fallback_reason", ""),
        }
        recommendations.append(rec)

    response = {
        "success": True,
        "data": {
            "recommendations": recommendations,
            "meta": {
                "total_internships": total_fetched,
                "passed_filter": passed_filter,
                "returned": len(recommendations),
                "model_used": model_used,
                "fallback_count": fallback_count,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    }

    logger.info(
        "Formatted response: %d recommendations (%d fallback)",
        len(recommendations),
        fallback_count,
    )
    return response
