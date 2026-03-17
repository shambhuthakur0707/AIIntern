"""
llm_engine.py — Multi-Provider LLM Integration (Ollama | Groq)

Provider is selected via the LLM_PROVIDER environment variable:
  LLM_PROVIDER=ollama   (default) — local Ollama runtime
  LLM_PROVIDER=groq               — Groq cloud API

Both providers enforce the same structured JSON output schema.
Retry and timeout behaviour is controlled per-provider via env vars.

analyze_single() returns a 2-tuple: (result_dict | None, fallback_reason: str)
  • On success: (dict_with_analysis, "")
  • On failure: (None, human-readable reason string)
"""

import json
import logging
import os
import re
import traceback
from time import time
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── Provider selection ───────────────────────────────────────────────
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "ollama").lower().strip()

_VALID_PROVIDERS = ("ollama", "groq")
if LLM_PROVIDER not in _VALID_PROVIDERS:
    logger.warning(
        "LLM_PROVIDER=%r is not recognised. Valid values: %s. Defaulting to 'ollama'.",
        LLM_PROVIDER,
        ", ".join(_VALID_PROVIDERS),
    )
    LLM_PROVIDER = "ollama"

logger.info("LLM provider initialised: %s", LLM_PROVIDER)

# ── Shared config ────────────────────────────────────────────────────
MAX_PROMPT_CHARS = 3000
MAX_RETRIES: int = int(os.getenv("LLM_MAX_RETRIES", "1"))

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

# ── Ollama config ────────────────────────────────────────────────────
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3:latest")
OLLAMA_TIMEOUT_SEC: float = float(os.getenv("OLLAMA_TIMEOUT_SEC", "30"))
OLLAMA_HEALTH_TTL_SEC: float = float(os.getenv("OLLAMA_HEALTH_TTL_SEC", "20"))

# ── Groq config ──────────────────────────────────────────────────────
GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama3-8b-8192")
GROQ_TIMEOUT_SEC: float = float(os.getenv("GROQ_TIMEOUT_SEC", "30"))
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

# ── Resolved active-model label (used by callers for logging/response) ──
ACTIVE_MODEL: str = OLLAMA_MODEL if LLM_PROVIDER == "ollama" else GROQ_MODEL

# ─────────────────────────────────────────────────────────────────────
# Lazy client handles — instantiated on first use to avoid import errors
# when a provider's package is not installed.
# ─────────────────────────────────────────────────────────────────────
_ollama_client = None
_ollama_health_client = None
_groq_client = None


def _get_ollama_clients():
    """Return (chat_client, health_client), importing ollama lazily."""
    global _ollama_client, _ollama_health_client
    if _ollama_client is None:
        try:
            import ollama  # noqa: PLC0415
            _ollama_client = ollama.Client(timeout=OLLAMA_TIMEOUT_SEC)
            _ollama_health_client = ollama.Client(timeout=2)
            logger.debug("Ollama client created (timeout=%.1fs)", OLLAMA_TIMEOUT_SEC)
        except ImportError as exc:
            raise ImportError(
                "The 'ollama' package is not installed. Run: pip install ollama"
            ) from exc
    return _ollama_client, _ollama_health_client


def _get_groq_client():
    """Return Groq client, importing groq lazily."""
    global _groq_client
    if _groq_client is None:
        try:
            from groq import Groq  # noqa: PLC0415
            _groq_client = Groq(api_key=GROQ_API_KEY, timeout=GROQ_TIMEOUT_SEC)
            logger.debug("Groq client created (model=%s, timeout=%.1fs)", GROQ_MODEL, GROQ_TIMEOUT_SEC)
        except ImportError as exc:
            raise ImportError(
                "The 'groq' package is not installed. Run: pip install groq"
            ) from exc
    return _groq_client


# ── Ollama health-check (cached) ─────────────────────────────────────
_OLLAMA_STATUS: Dict[str, Any] = {"ok": True, "checked_at": 0.0}


def _ollama_available() -> Tuple[bool, str]:
    """Return (available, reason_if_not)."""
    now = time()
    if now - _OLLAMA_STATUS["checked_at"] <= OLLAMA_HEALTH_TTL_SEC:
        return _OLLAMA_STATUS["ok"], _OLLAMA_STATUS.get("reason", "")

    try:
        _, health_client = _get_ollama_clients()
        health_client.ps()
        _OLLAMA_STATUS.update({"ok": True, "reason": "", "checked_at": now})
        logger.debug("Ollama health-check passed.")
    except ImportError as exc:
        reason = str(exc)
        _OLLAMA_STATUS.update({"ok": False, "reason": reason, "checked_at": now})
        logger.error("Ollama package missing — %s", reason)
    except Exception as exc:
        reason = f"Ollama health-check failed: {exc}"
        _OLLAMA_STATUS.update({"ok": False, "reason": reason, "checked_at": now})
        logger.warning(
            "Ollama health-check failed — falling back to rule-based analysis. Cause: %s", exc
        )

    return _OLLAMA_STATUS["ok"], _OLLAMA_STATUS.get("reason", "")



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
        "IMPORTANT: The learning_roadmap must focus ONLY on acquiring the MISSING SKILLS listed above.\n"
        "Each week should build skills needed to fill the gaps for this internship.\n"
        "Return this EXACT JSON structure (fill in all values):\n"
        "{\n"
        '  "confidence_score": <number 0-100>,\n'
        '  "reasoning": "<why this internship matches or does not match>",\n'
        '  "strengths": ["<matching skill 1>", "<matching skill 2>"],\n'
        '  "missing_skills": ["<missing skill 1>", "<missing skill 2>"],\n'
        '  "skill_gap_analysis": "<how far user is from ideal candidate>",\n'
        '  "learning_roadmap": [\n'
        '    {"week": 1, "focus": "<MISSING SKILL 1 or topic>", "tasks": ["<task1>", "<task2>"]},\n'
        '    {"week": 2, "focus": "<MISSING SKILL 2 or related topic>", "tasks": ["<task1>", "<task2>"]},\n'
        '    {"week": 3, "focus": "<MISSING SKILL 3 or related topic>", "tasks": ["<task1>", "<task2>"]},\n'
        '    {"week": 4, "focus": "<MISSING SKILL 4 or synthesis>", "tasks": ["<task1>", "<task2>"]}\n'
        "  ],\n"
        '  "improvement_priority": "<what to learn first from MISSING SKILLS and why>"\n'
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

    # Find the outermost { ... }
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        logger.debug("_parse_llm_json: no JSON object boundaries found in output.")
        return None

    json_str = text[start : end + 1]

    try:
        parsed = json.loads(json_str)
    except json.JSONDecodeError as exc:
        logger.debug("_parse_llm_json: JSONDecodeError — %s", exc)
        return None

    if not isinstance(parsed, dict):
        logger.debug("_parse_llm_json: top-level value is not a dict.")
        return None

    # Validate required keys
    missing_keys = REQUIRED_KEYS - parsed.keys()
    if missing_keys:
        logger.warning(
            "_parse_llm_json: response missing required keys: %s",
            sorted(missing_keys),
        )
        return None

    # Normalise types
    try:
        parsed["confidence_score"] = float(parsed["confidence_score"])
        parsed["confidence_score"] = max(0.0, min(100.0, parsed["confidence_score"]))
    except (TypeError, ValueError):
        logger.warning("_parse_llm_json: confidence_score is not numeric; defaulting to 50.")
        parsed["confidence_score"] = 50.0

    if not isinstance(parsed.get("strengths"), list):
        parsed["strengths"] = []
    if not isinstance(parsed.get("missing_skills"), list):
        parsed["missing_skills"] = []
    if not isinstance(parsed.get("learning_roadmap"), list):
        parsed["learning_roadmap"] = []

    return parsed


# ── Provider-specific callers ─────────────────────────────────────────
def _call_ollama(
    prompt: str,
    internship_title: str,
    attempt: int,
) -> Tuple[Optional[str], str]:
    """
    Fire one Ollama chat request.

    Returns (raw_content, error_reason).
    On success: (str, "").
    On failure: (None, human-readable reason).
    """
    try:
        client, _ = _get_ollama_clients()
        response = client.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"num_predict": 350, "temperature": 0.3},
        )
        raw: str = response.get("message", {}).get("content", "")
        return raw, ""
    except Exception as exc:
        reason = f"Ollama API error on attempt {attempt + 1} for '{internship_title}': {exc}"
        logger.error(
            "Ollama call failed [attempt %d] for '%s':\n%s",
            attempt + 1,
            internship_title,
            traceback.format_exc(),
        )
        # Mark Ollama as unhealthy so the TTL cache avoids repeated health checks
        _OLLAMA_STATUS.update({"ok": False, "reason": reason, "checked_at": time()})
        return None, reason


def _call_groq(
    prompt: str,
    internship_title: str,
    attempt: int,
) -> Tuple[Optional[str], str]:
    """
    Fire one Groq chat-completion request.

    Returns (raw_content, error_reason).
    On success: (str, "").
    On failure: (None, human-readable reason).
    """
    try:
        client = _get_groq_client()
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512,
            temperature=0.3,
        )
        raw: str = completion.choices[0].message.content or ""
        return raw, ""
    except Exception as exc:
        reason = f"Groq API error on attempt {attempt + 1} for '{internship_title}': {exc}"
        logger.error(
            "Groq call failed [attempt %d] for '%s':\n%s",
            attempt + 1,
            internship_title,
            traceback.format_exc(),
        )
        return None, reason


# ── Single-internship LLM call ────────────────────────────────────────
def analyze_single(
    user_profile: Dict[str, Any],
    internship: Dict[str, Any],
) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    Analyse one internship with the configured LLM provider.

    Retries up to LLM_MAX_RETRIES times with an increasingly strict prompt
    when JSON parsing fails.

    Returns
    -------
    (result, fallback_reason)
      result          — dict with analysis fields, or None on total failure.
      fallback_reason — "" on success; human-readable reason string on failure.
    """
    internship_title: str = internship.get("title", "unknown")

    # ── Pre-flight availability checks ───────────────────────────────
    if LLM_PROVIDER == "ollama":
        available, avail_reason = _ollama_available()
        if not available:
            fallback_reason = f"Ollama unavailable: {avail_reason}"
            logger.warning(
                "Skipping LLM call for '%s' — %s", internship_title, fallback_reason
            )
            return None, fallback_reason

    elif LLM_PROVIDER == "groq":
        if not GROQ_API_KEY:
            fallback_reason = "GROQ_API_KEY is not set; cannot use Groq provider."
            logger.error(fallback_reason)
            return None, fallback_reason
        try:
            _get_groq_client()
        except ImportError as exc:
            fallback_reason = str(exc)
            logger.error(fallback_reason)
            return None, fallback_reason

    # ── Retry loop ────────────────────────────────────────────────────
    last_error: str = ""

    for attempt in range(MAX_RETRIES + 1):
        strict = attempt > 0
        prompt = _build_prompt(user_profile, internship, strict=strict)

        logger.info(
            "[%s] LLM call [attempt %d/%d] for '%s'",
            LLM_PROVIDER.upper(),
            attempt + 1,
            MAX_RETRIES + 1,
            internship_title,
        )

        # -- Dispatch to provider ----------------------------------------
        if LLM_PROVIDER == "ollama":
            raw, call_error = _call_ollama(prompt, internship_title, attempt)
        else:
            raw, call_error = _call_groq(prompt, internship_title, attempt)

        if raw is None:
            last_error = call_error
            logger.warning(
                "[%s] Provider call failed on attempt %d for '%s': %s",
                LLM_PROVIDER.upper(),
                attempt + 1,
                internship_title,
                call_error,
            )
            continue  # retry

        # -- Parse & validate ----------------------------------------
        parsed = _parse_llm_json(raw)

        if parsed is not None:
            parsed["fallback_used"] = False
            parsed["fallback_reason"] = ""
            logger.info(
                "[%s] LLM success for '%s' (confidence=%.1f, attempt=%d)",
                LLM_PROVIDER.upper(),
                internship_title,
                parsed.get("confidence_score", 0),
                attempt + 1,
            )
            return parsed, ""

        last_error = (
            f"{LLM_PROVIDER.capitalize()} returned unparseable JSON "
            f"for '{internship_title}' on attempt {attempt + 1}. "
            f"Raw preview: {raw[:200]!r}"
        )
        logger.warning(
            "[%s] Unparseable JSON for '%s' (attempt %d/%d). Raw (first 200 chars): %s",
            LLM_PROVIDER.upper(),
            internship_title,
            attempt + 1,
            MAX_RETRIES + 1,
            raw[:200],
        )

    # All attempts exhausted
    fallback_reason = (
        f"LLM analysis failed after {MAX_RETRIES + 1} attempt(s) "
        f"[provider={LLM_PROVIDER}]. Last error: {last_error}"
    )
    logger.error(
        "[%s] All %d attempt(s) failed for '%s'. Falling back to rule-based analysis. "
        "Last error: %s",
        LLM_PROVIDER.upper(),
        MAX_RETRIES + 1,
        internship_title,
        last_error,
    )
    return None, fallback_reason
