"""
internship_agent.py — Orchestrator

Thin controller that wires together the five engine modules:
  matching_engine  →  ranking_engine  →  llm_engine / fallback_engine  →  response_formatter

Called by the route layer via  run_matching_agent(user_profile).
"""

import logging
import sys
import traceback
from pathlib import Path
from typing import Any, Dict

# Allow running this file directly: `python backend/agents/internship_agent.py`
if __package__ in (None, ""):
    backend_dir = Path(__file__).resolve().parents[1]
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))

try:
    from ..engines import (
        matching_engine,
        ranking_engine,
        llm_engine,
        fallback_engine,
        response_formatter,
    )
except ImportError:
    try:
        from backend.engines import (
            matching_engine,
            ranking_engine,
            llm_engine,
            fallback_engine,
            response_formatter,
        )
    except ImportError:
        from engines import matching_engine, ranking_engine, llm_engine, fallback_engine, response_formatter

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def run_matching_agent(user_profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry-point for the AI matching pipeline.

    Pipeline
    --------
    1. matching_engine  — fetch internships, compute overlap, filter < 25%
    2. ranking_engine   — weighted scoring (skill 60 / keyword 20 / exp 20), top 10
    3. llm_engine       — per-internship LLM analysis (strict JSON)
       fallback_engine  — rule-based fallback if LLM fails
    4. response_formatter — assemble final API response

    Returns
    -------
    dict — always contains "success" (bool).
    """
    try:
        logger.info("═══ Starting matching pipeline ═══")

        # ── 1. Filter ────────────────────────────────────────────
        filtered = matching_engine.fetch_and_filter(user_profile)
        total_fetched = len(filtered)  # after DB fetch but counted before filter internally

        if not filtered:
            logger.warning("No internships passed the overlap filter")
            return {
                "success": False,
                "error": (
                    "No internships found with sufficient skill overlap. "
                    "Try adding more skills to your profile."
                ),
            }

        # ── 2. Rank ──────────────────────────────────────────────
        ranked = ranking_engine.rank_internships(user_profile, filtered)

        if not ranked:
            return {"success": False, "error": "Ranking produced no results."}

        # ── 3. LLM / Fallback analysis (per internship) ─────────
        analyses = []
        for internship in ranked:
            llm_result = llm_engine.analyze_single(user_profile, internship)

            if llm_result is not None:
                analyses.append(llm_result)
            else:
                fb = fallback_engine.generate_fallback(user_profile, internship)
                analyses.append(fb)

        # ── 4. Format response ───────────────────────────────────
        result = response_formatter.format_response(
            ranked_results=ranked,
            llm_analyses=analyses,
            model_used=llm_engine.OLLAMA_MODEL,
            total_fetched=total_fetched,
            passed_filter=len(filtered),
        )

        logger.info("═══ Pipeline complete ═══")
        return result

    except Exception as exc:
        logger.error("Agent pipeline crashed:\n%s", traceback.format_exc())
        print(f"FULL AGENT ERROR: {exc}")
        traceback.print_exc()
        return {"success": False, "error": str(exc)}
