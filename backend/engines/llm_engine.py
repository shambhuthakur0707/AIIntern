"""
llm_engine.py — Ollama Strict-JSON LLM Integration

Sends each top-ranked internship to Ollama (llama3:8b-instruct-q4_0) and
enforces structured JSON output.  Retries once on parse failure with a
stricter prompt.
"""

import json
import logging
import re
import traceback
from typing import Any, Dict, List, Optional

import ollama

logger = logging.getLogger(__name__)

# ── Config ───────────────────────────────────────────────────────────
OLLAMA_MODEL = "llama3:latest"
MAX_PROMPT_CHARS = 3000
MAX_RETRIES = 1

# Keys the LLM JSON *must* contain
REQUIRED_KEYS = {
    "confidence_score",
    "reasoning",
    "strengths",
    "missing_skills",
    "skill_gap_analysis",
    "learning_roadmap",
    "improvement_priority",
}


# ── Prompt builder ───────────────────────────────────────────────────
def _build_prompt(
    user_profile: Dict[str, Any],
    internship: Dict[str, Any],
    strict: bool = False,
) -> str:
    """Build a prompt for a single internship analysis."""

    strictness = (
        "\nIMPORTANT: Your previous response was invalid. "
        "Return ONLY the JSON object below, nothing else.\n"
        if strict
        else ""
    )

    prompt = (
        "You are an AI career advisor. Respond with ONLY valid JSON. "
        "No markdown. No explanation. No text before or after the JSON.\n"
        f"{strictness}\n"
        f"USER: {user_profile.get('name', 'N/A')}, "
        f"{user_profile.get('education', 'N/A')}, "
        f"{user_profile.get('experience_level', 'beginner')}\n"
        f"USER SKILLS: {', '.join(user_profile.get('skills', []))}\n"
        f"USER INTERESTS: {', '.join(user_profile.get('interests', []))}\n\n"
        f"INTERNSHIP: {internship.get('title', '')} at {internship.get('company', '')}\n"
        f"DOMAIN: {internship.get('domain', '')}\n"
        f"REQUIRED SKILLS: {', '.join(internship.get('required_skills', []))}\n"
        f"MATCH SCORE: {internship.get('weighted_score', 0)}%\n"
        f"MATCHED SKILLS: {', '.join(internship.get('matched_skills', []))}\n"
        f"MISSING SKILLS: {', '.join(internship.get('missing_skills', []))}\n\n"
        "Return this EXACT JSON structure (fill in all values):\n"
        "{\n"
        '  "confidence_score": <number 0-100>,\n'
        '  "reasoning": "<why this internship matches or does not match>",\n'
        '  "strengths": ["<matching skill 1>", "<matching skill 2>"],\n'
        '  "missing_skills": ["<missing skill 1>", "<missing skill 2>"],\n'
        '  "skill_gap_analysis": "<how far user is from ideal candidate>",\n'
        '  "learning_roadmap": [\n'
        '    {"week": 1, "focus": "<topic>", "tasks": ["<task1>", "<task2>"]},\n'
        '    {"week": 2, "focus": "<topic>", "tasks": ["<task1>", "<task2>"]},\n'
        '    {"week": 3, "focus": "<topic>", "tasks": ["<task1>", "<task2>"]},\n'
        '    {"week": 4, "focus": "<topic>", "tasks": ["<task1>", "<task2>"]}\n'
        "  ],\n"
        '  "improvement_priority": "<what to learn first and why>"\n'
        "}"
    )

    # Hard-cap prompt length for small models
    if len(prompt) > MAX_PROMPT_CHARS:
        prompt = prompt[:MAX_PROMPT_CHARS] + "\n...(truncated)"

    return prompt


# ── JSON parser ──────────────────────────────────────────────────────
def _parse_llm_json(raw: str) -> Optional[Dict[str, Any]]:
    """
    Extract and validate JSON from raw LLM output.
    Handles common issues: markdown fences, trailing text, etc.
    """
    if not raw or not raw.strip():
        return None

    text = raw.strip()

    # Strip markdown code fences if present
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"```\s*$", "", text, flags=re.MULTILINE)
    text = text.strip()

    # Try to find a JSON object in the text
    # Look for the outermost { ... }
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None

    json_str = text[start : end + 1]

    try:
        parsed = json.loads(json_str)
    except json.JSONDecodeError:
        return None

    if not isinstance(parsed, dict):
        return None

    # Validate required keys exist
    if not REQUIRED_KEYS.issubset(parsed.keys()):
        missing = REQUIRED_KEYS - parsed.keys()
        logger.warning("LLM JSON missing keys: %s", missing)
        return None

    # Validate types
    try:
        parsed["confidence_score"] = float(parsed["confidence_score"])
        parsed["confidence_score"] = max(0, min(100, parsed["confidence_score"]))
    except (TypeError, ValueError):
        parsed["confidence_score"] = 50.0

    if not isinstance(parsed.get("strengths"), list):
        parsed["strengths"] = []
    if not isinstance(parsed.get("missing_skills"), list):
        parsed["missing_skills"] = []
    if not isinstance(parsed.get("learning_roadmap"), list):
        parsed["learning_roadmap"] = []

    return parsed


# ── Single-internship LLM call ──────────────────────────────────────
def analyze_single(
    user_profile: Dict[str, Any],
    internship: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """
    Call Ollama for one internship. Retries once with a stricter prompt
    if JSON parsing fails.

    Returns
    -------
    dict with LLM analysis fields, or None if all attempts fail.
    """
    for attempt in range(MAX_RETRIES + 1):
        strict = attempt > 0
        prompt = _build_prompt(user_profile, internship, strict=strict)

        try:
            logger.info(
                "LLM call [attempt %d] for '%s'",
                attempt + 1,
                internship.get("title", "?"),
            )

            response = ollama.chat(
                model=OLLAMA_MODEL,
                messages=[{"role": "user", "content": prompt}],
                options={"num_predict": 800, "temperature": 0.3},
            )

            raw = response.get("message", {}).get("content", "")
            parsed = _parse_llm_json(raw)

            if parsed is not None:
                parsed["fallback_used"] = False
                logger.info(
                    "LLM success for '%s' (confidence=%s)",
                    internship.get("title", "?"),
                    parsed.get("confidence_score"),
                )
                return parsed

            logger.warning(
                "LLM returned unparseable JSON for '%s' (attempt %d). Raw: %s",
                internship.get("title", "?"),
                attempt + 1,
                raw[:200],
            )

        except Exception:
            logger.error(
                "Ollama call failed for '%s' (attempt %d):\n%s",
                internship.get("title", "?"),
                attempt + 1,
                traceback.format_exc(),
            )

    return None
