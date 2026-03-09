from flask import Blueprint, current_app, request
from flask_jwt_extended import jwt_required
from urllib.parse import quote_plus
import hashlib
import logging
import re
from datetime import datetime, timedelta, timezone

try:
    from ..utils.response_utils import success_response, error_response
    from ..utils.jwt_utils import get_current_user
    from ..engines import llm_engine, fallback_engine, matching_engine, ranking_engine
except ImportError:
    from utils.response_utils import success_response, error_response
    from utils.jwt_utils import get_current_user
    from engines import llm_engine, fallback_engine, matching_engine, ranking_engine

logger = logging.getLogger(__name__)

ANALYSIS_CACHE_TTL_HOURS = 24

internships_bp = Blueprint("internships", __name__)

DOMAIN_TO_SECTOR = {
    "machine learning": "Artificial Intelligence",
    "natural language processing": "Artificial Intelligence",
    "data science": "Data",
    "data engineering": "Data",
    "web development": "Software Engineering",
    "mobile development": "Software Engineering",
    "devops": "Cloud and DevOps",
    "cybersecurity": "Security",
    "ai / product": "Product",
}


def _normalize(value):
    return (value or "").strip()


def _derive_sector(domain, doc):
    explicit = _normalize(doc.get("sector", ""))
    if explicit:
        return explicit

    key = _normalize(domain).lower()
    if key in DOMAIN_TO_SECTOR:
        return DOMAIN_TO_SECTOR[key]

    return domain or "General"


def _regex_filter(value):
    value = _normalize(value)
    if not value or len(value) > 100:
        return None
    # Escape user-selected values so characters like () are matched literally.
    return {"$regex": re.escape(value), "$options": "i"}


def _build_apply_url(doc):
    for field in ("apply_url", "application_url", "job_url"):
        value = _normalize(doc.get(field, ""))
        if value:
            return value

    title = _normalize(doc.get("title", "Internship"))
    company = _normalize(doc.get("company", ""))
    query = " ".join(part for part in [title, company, "internship"] if part)
    return f"https://www.linkedin.com/jobs/search/?keywords={quote_plus(query)}"


def _to_bool(value, default=True):
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _to_int(value, default, min_value=1, max_value=None):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    if parsed < min_value:
        return min_value
    if max_value is not None and parsed > max_value:
        return max_value
    return parsed


def _analysis_cache_key(user_id: str, internship_id: str) -> str:
    raw = f"{user_id}:{internship_id}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _score_for_user(user_profile, internship):
    overlap = matching_engine.compute_skill_overlap(
        user_profile.get("skills", []),
        internship.get("required_skills", []),
    )
    keyword_score = ranking_engine._keyword_score(  # noqa: SLF001
        user_profile.get("interests", []),
        internship,
    )
    experience_score = ranking_engine._experience_score(  # noqa: SLF001
        user_profile.get("experience_level", "beginner"),
        internship,
    )

    weighted = round(
        ranking_engine.W_SKILL * overlap["overlap_pct"]
        + ranking_engine.W_KEYWORD * keyword_score
        + ranking_engine.W_EXPERIENCE * experience_score,
        2,
    )

    scored = dict(internship)
    scored["matched_skills"] = overlap["matched_skills"]
    scored["missing_skills"] = overlap["missing_skills"]
    scored["weighted_score"] = weighted
    scored["score_breakdown"] = {
        "skill_overlap": overlap["overlap_pct"],
        "keyword_relevance": keyword_score,
        "experience_match": experience_score,
    }
    return scored


def _ensure_utc(dt):
    """Make a datetime timezone-aware (UTC) if it's naive."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


@internships_bp.route("", methods=["GET"])
@jwt_required()
def list_internships():
    """
    GET /api/internships?sector=&domain=&location=
    Returns internships with optional filters and available filter values.
    """
    try:
        db = current_app.config["DB"]
        user = get_current_user()
        if not user:
            return error_response("User not found", 404)

        user_profile = {
            "name": user.get("name"),
            "education": user.get("education"),
            "experience_level": user.get("experience_level"),
            "skills": user.get("skills", []),
            "interests": user.get("interests", []),
        }

        domain = _normalize(request.args.get("domain", ""))
        location = _normalize(request.args.get("location", ""))
        sector = _normalize(request.args.get("sector", ""))
        include_ai = _to_bool(request.args.get("include_ai"), True)
        page = _to_int(request.args.get("page"), 1, min_value=1)
        page_size = _to_int(request.args.get("page_size"), 10, min_value=1, max_value=50)

        # ── Build MongoDB filter ──────────────────────────────────────
        mongo_query = {}

        domain_q = _regex_filter(domain)
        if domain_q:
            mongo_query["domain"] = domain_q

        location_q = _regex_filter(location)
        if location_q:
            mongo_query["location"] = location_q

        # ── Fetch filter options (lightweight projection, unfiltered) ─
        filter_pipeline = [
            {"$group": {
                "_id": None,
                "domains": {"$addToSet": "$domain"},
                "locations": {"$addToSet": "$location"},
                "sectors": {"$addToSet": "$sector"},
            }}
        ]
        filter_agg = list(db.internships.aggregate(filter_pipeline))
        if filter_agg:
            raw_domains = sorted(d for d in filter_agg[0].get("domains", []) if d and d.strip())
            raw_locations = sorted(l for l in filter_agg[0].get("locations", []) if l and l.strip())
            raw_sectors_explicit = {s.strip() for s in filter_agg[0].get("sectors", []) if s and s.strip()}
        else:
            raw_domains = []
            raw_locations = []
            raw_sectors_explicit = set()

        # Build full sector list from domains + explicit sectors
        all_sectors = set(raw_sectors_explicit)
        for d in raw_domains:
            all_sectors.add(DOMAIN_TO_SECTOR.get(d.lower(), d))
        domains = raw_domains
        locations = raw_locations
        sectors = sorted(all_sectors)

        # ── Count + paginate filtered docs ────────────────────────────
        # For sector filtering we need Python-side logic since sector is derived
        if sector:
            # Fetch only IDs + domain + sector fields for sector filtering
            cursor = db.internships.find(mongo_query, {"domain": 1, "sector": 1}).sort("title", 1)
            matching_ids = []
            for doc in cursor:
                doc_domain = _normalize(doc.get("domain", ""))
                doc_sector = _derive_sector(doc_domain, doc)
                if doc_sector.lower() == sector.lower():
                    matching_ids.append(doc["_id"])

            total = len(matching_ids)
            total_pages = max(1, (total + page_size - 1) // page_size)
            if page > total_pages:
                page = total_pages
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            page_ids = matching_ids[start_idx:end_idx]
            page_docs_cursor = db.internships.find({"_id": {"$in": page_ids}}).sort("title", 1)
        else:
            total = db.internships.count_documents(mongo_query)
            total_pages = max(1, (total + page_size - 1) // page_size)
            if page > total_pages:
                page = total_pages
            skip = (page - 1) * page_size
            page_docs_cursor = db.internships.find(mongo_query).sort("title", 1).skip(skip).limit(page_size)

        # ── Process page docs ─────────────────────────────────────────
        internships = []
        analyzed_count = 0
        fallback_count = 0
        now_utc = datetime.now(timezone.utc)
        user_id_str = str(user.get("_id", ""))

        for doc in page_docs_cursor:
            doc_id = str(doc.get("_id", ""))
            doc_domain = _normalize(doc.get("domain", ""))
            doc_sector = _derive_sector(doc_domain, doc)

            internship = {
                "_id": doc_id,
                "title": doc.get("title", "Untitled"),
                "company": doc.get("company", "Unknown"),
                "domain": doc_domain,
                "sector": doc_sector,
                "location": _normalize(doc.get("location", "")),
                "duration": _normalize(doc.get("duration", "")),
                "stipend": _normalize(doc.get("stipend", "")),
                "openings": doc.get("openings", 0),
                "required_skills": doc.get("required_skills", []),
                "description": _normalize(doc.get("description", "")),
                "apply_url": _build_apply_url(doc),
            }

            if include_ai:
                scored = _score_for_user(user_profile, internship)
                # Check cache first (timezone-safe comparison)
                cache_key = _analysis_cache_key(user_id_str, doc_id)
                cached = db.internship_analyses.find_one({"cache_key": cache_key})
                cache_valid = False
                if cached:
                    expires = _ensure_utc(cached.get("expires_at"))
                    cache_valid = expires is not None and expires > now_utc

                if cache_valid:
                    analysis = cached["analysis"]
                else:
                    llm_result, fallback_reason = llm_engine.analyze_single(user_profile, scored)
                    if llm_result is None:
                        analysis = fallback_engine.generate_fallback(user_profile, scored, fallback_reason)
                    else:
                        analysis = llm_result
                    # Store in cache
                    db.internship_analyses.update_one(
                        {"cache_key": cache_key},
                        {"$set": {
                            "cache_key": cache_key,
                            "analysis": analysis,
                            "expires_at": now_utc + timedelta(hours=ANALYSIS_CACHE_TTL_HOURS),
                        }},
                        upsert=True,
                    )
                if analysis.get("fallback_used"):
                    fallback_count += 1
                analyzed_count += 1
                internship.update(
                    {
                        "weighted_score": scored.get("weighted_score", 0),
                        "score_breakdown": scored.get("score_breakdown", {}),
                        "matched_skills": scored.get("matched_skills", []),
                        "missing_skills": scored.get("missing_skills", []),
                        "confidence_score": analysis.get("confidence_score", 0),
                        "reasoning": analysis.get("reasoning", ""),
                        "skill_gap_analysis": analysis.get("skill_gap_analysis", ""),
                        "learning_roadmap": analysis.get("learning_roadmap", []),
                        "improvement_priority": analysis.get("improvement_priority", ""),
                        "fallback_used": analysis.get("fallback_used", False),
                    }
                )

            internships.append(internship)

        return success_response(
            data={
                "internships": internships,
                "filters": {
                    "available": {
                        "sectors": sectors,
                        "domains": domains,
                        "locations": locations,
                    },
                    "selected": {
                        "sector": sector,
                        "domain": domain,
                        "location": location,
                    },
                },
                "meta": {
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": total_pages,
                    "has_prev": page > 1,
                    "has_next": page < total_pages,
                    "include_ai": include_ai,
                    "analyzed_count": analyzed_count,
                    "fallback_count": fallback_count,
                },
            },
            message="Internships loaded",
        )
    except Exception as exc:
        logger.exception("Failed to load internships")
        return error_response("Failed to load internships", 500)
