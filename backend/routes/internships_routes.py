from flask import Blueprint, current_app, request
from flask_jwt_extended import jwt_required
from urllib.parse import quote_plus
from bson import ObjectId
import hashlib
import logging
import re
from datetime import datetime, timedelta, timezone

try:
    from ..utils.response_utils import success_response, error_response
    from ..utils.jwt_utils import get_current_user
    from ..engines import llm_engine, fallback_engine, matching_engine, ranking_engine
    from ..models.internship_model import sanitize_internship
except ImportError:
    from utils.response_utils import success_response, error_response
    from utils.jwt_utils import get_current_user
    from engines import llm_engine, fallback_engine, matching_engine, ranking_engine
    from models.internship_model import sanitize_internship

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
            "location": user.get("location", ""),
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
                "is_remote": bool(doc.get("is_remote", False)),
                "work_mode": _normalize(doc.get("work_mode", "")) or ("Remote" if bool(doc.get("is_remote", False)) else "On-site/Hybrid"),
                "required_skills": doc.get("required_skills", []),
                "requirement_text": _normalize(doc.get("requirement_text", "")),
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


# ── Saved internships ─────────────────────────────────────────────────────────

@internships_bp.route("/saved", methods=["GET"])
@jwt_required()
def list_saved_internships():
    """GET /api/internships/saved — return all internships bookmarked by the user."""
    try:
        db = current_app.config["DB"]
        user = get_current_user()
        if not user:
            return error_response("User not found", 404)

        saved_ids = user.get("saved_internships", [])
        if not saved_ids:
            return success_response(data={"internships": []}, message="No saved internships")

        docs = list(db.internships.find({"_id": {"$in": saved_ids}}))
        internships = []
        for doc in docs:
            item = sanitize_internship(doc)
            item["saved"] = True
            internships.append(item)

        return success_response(data={"internships": internships}, message="Saved internships loaded")
    except Exception:
        logger.exception("Failed to load saved internships")
        return error_response("Failed to load saved internships", 500)


@internships_bp.route("/<internship_id>/save", methods=["POST"])
@jwt_required()
def toggle_save_internship(internship_id):
    """POST /api/internships/:id/save — toggle save/unsave for the current user."""
    try:
        db = current_app.config["DB"]
        user = get_current_user()
        if not user:
            return error_response("User not found", 404)

        try:
            iid = ObjectId(internship_id)
        except Exception:
            return error_response("Invalid internship id", 400)

        if not db.internships.find_one({"_id": iid}):
            return error_response("Internship not found", 404)

        user_id = user["_id"]
        saved_ids = user.get("saved_internships", [])
        currently_saved = iid in saved_ids

        if currently_saved:
            db.users.update_one({"_id": user_id}, {"$pull": {"saved_internships": iid}})
        else:
            db.users.update_one({"_id": user_id}, {"$addToSet": {"saved_internships": iid}})

        return success_response(
            data={"saved": not currently_saved, "internship_id": internship_id},
            message="Saved" if not currently_saved else "Unsaved",
        )
    except Exception:
        logger.exception("Failed to toggle save")
        return error_response("Failed to toggle save", 500)


# ── Interview prep ────────────────────────────────────────────────────────────

# Hard-coded question bank per domain (used as fallback when LLM is unavailable)
QUESTION_BANK = {
    "default": [
        {"question": "Tell me about yourself and why you're interested in this role.",
         "type": "behavioral",
         "tip": "Use the Present–Past–Future structure: where you are now, what led you here, and where you're headed."},
        {"question": "Describe a challenging project you worked on and how you handled it.",
         "type": "behavioral",
         "tip": "Use the STAR method: Situation, Task, Action, Result. Quantify the result wherever possible."},
        {"question": "How do you prioritize tasks when working on multiple deadlines?",
         "type": "situational",
         "tip": "Mention a concrete framework (Eisenhower matrix, time-blocking) and give a brief real example."},
        {"question": "Walk me through a technical problem you solved recently.",
         "type": "technical",
         "tip": "Break your answer into: problem definition → your investigation → solution chosen → trade-offs considered."},
        {"question": "How do you stay current with industry trends and new technologies?",
         "type": "behavioral",
         "tip": "Name specific resources: newsletters, papers, communities. Shows genuine intellectual curiosity."},
        {"question": "Describe a situation where you disagreed with a teammate. How did you resolve it?",
         "type": "behavioral",
         "tip": "Focus on listening first, finding common ground, and the positive outcome — not on being right."},
        {"question": "Where do you see yourself in 2–3 years, and how does this internship fit that path?",
         "type": "situational",
         "tip": "Show a coherent story: this role teaches X, which feeds into your goal Y. Avoid generic answers."},
    ],
    "machine learning": [
        {"question": "Explain the bias-variance tradeoff and how you handle it in practice.",
         "type": "technical",
         "tip": "Give a concrete model example — e.g., deep network vs. linear model — and mention cross-validation."},
        {"question": "How would you debug a model that performs well on training data but poorly in production?",
         "type": "technical",
         "tip": "Cover distribution shift, feature leakage, missing values in prod, and monitoring strategies."},
        {"question": "Walk me through how you would design an end-to-end ML pipeline.",
         "type": "technical",
         "tip": "Mention data ingestion → feature engineering → training → evaluation → deployment → monitoring."},
        {"question": "What evaluation metrics would you choose for a class-imbalanced dataset? Why?",
         "type": "technical",
         "tip": "Precision-recall AUC, F1, and Cohen's kappa are stronger than accuracy here — explain why briefly."},
        {"question": "Describe a data preprocessing challenge you encountered and how you solved it.",
         "type": "behavioral",
         "tip": "Be specific: missing values strategy, outlier handling, or encoding choice. Show you think critically."},
        {"question": "How do you explain a complex ML result to a non-technical stakeholder?",
         "type": "behavioral",
         "tip": "Use analogies, avoid jargon, and anchor to business impact. SHAP plots are a great concrete example."},
        {"question": "If you had to choose between model accuracy and model interpretability, how would you decide?",
         "type": "situational",
         "tip": "It depends on the domain: healthcare/finance favor interpretability; recommendation systems can tolerate black-boxes."},
    ],
    "web development": [
        {"question": "Explain the difference between server-side rendering and client-side rendering.",
         "type": "technical",
         "tip": "Mention SEO, first-contentful paint, and suitable use cases for each approach."},
        {"question": "How do you optimize the performance of a web application?",
         "type": "technical",
         "tip": "Cover code splitting, lazy loading, caching (CDN, HTTP cache), image optimization, and critical CSS."},
        {"question": "Walk me through how a browser handles an HTTP request from start to screen.",
         "type": "technical",
         "tip": "DNS → TCP → TLS → HTTP → parsing HTML → CSSOM → render tree → layout → paint. Show you know the stack."},
        {"question": "Describe a bug that was difficult to reproduce and how you tracked it down.",
         "type": "behavioral",
         "tip": "Methodical debugging story: logs, browser dev tools, minimal reproduction case, bisect approach."},
        {"question": "How do you ensure that your UI is accessible to all users?",
         "type": "technical",
         "tip": "ARIA roles, semantic HTML, keyboard navigation, contrast ratios (WCAG 2.1), and screen-reader testing."},
        {"question": "How do you decide whether to store state on the client or the server?",
         "type": "situational",
         "tip": "Client for UI ephemera; server for authoritative data. Mention security implications of client-side state."},
        {"question": "What steps do you take to secure a web application before deployment?",
         "type": "technical",
         "tip": "HTTPS, CSP, input validation, parameterized queries, dependency audits, least-privilege principles."},
    ],
    "data science": [
        {"question": "How do you approach exploratory data analysis on a new dataset?",
         "type": "technical",
         "tip": "Shape/dtypes → nulls → distributions → correlations → outliers → domain sanity checks."},
        {"question": "Explain the difference between correlation and causation with an example.",
         "type": "technical",
         "tip": "Ice cream / drowning classic, then pivot to how you'd design an experiment to establish causation."},
        {"question": "How would you handle missing data in a dataset with 30% nulls in one column?",
         "type": "technical",
         "tip": "Ask: is it MCAR, MAR, or MNAR? Options: drop, mean/median/mode impute, KNN impute, model-based."},
        {"question": "Describe a time you presented data findings to stakeholders. What made it effective?",
         "type": "behavioral",
         "tip": "Lead with the business question, show the insight visually, quantify impact, then show the analysis. Not vice versa."},
        {"question": "What's the difference between a z-test and a t-test? When do you use each?",
         "type": "technical",
         "tip": "Z: known population variance or large n (>30). T: unknown variance or small n. Emphasize assumptions."},
        {"question": "How do you validate that your analysis hasn't been affected by survivorship bias?",
         "type": "technical",
         "tip": "Think about what data is absent. Ask: who/what didn't make it into the dataset and why?"},
        {"question": "Tell me about a project where the data didn't tell the story you expected.",
         "type": "behavioral",
         "tip": "Shows intellectual honesty. Walk through how you revised your hypothesis and what you concluded."},
    ],
}


def _get_question_bank_for_domain(domain: str) -> list:
    """Return the best-matching question bank for a given domain."""
    domain_lower = (domain or "").lower()
    for key in QUESTION_BANK:
        if key != "default" and key in domain_lower:
            return QUESTION_BANK[key]
    return QUESTION_BANK["default"]


@internships_bp.route("/<internship_id>/interview-prep", methods=["POST"])
@jwt_required()
def interview_prep(internship_id):
    """POST /api/internships/:id/interview-prep — generates 7 interview questions."""
    try:
        db = current_app.config["DB"]
        user = get_current_user()
        if not user:
            return error_response("User not found", 404)

        try:
            iid = ObjectId(internship_id)
        except Exception:
            return error_response("Invalid internship id", 400)

        internship = db.internships.find_one({"_id": iid})
        if not internship:
            return error_response("Internship not found", 404)

        title = internship.get("title", "Software Engineering")
        company = internship.get("company", "the company")
        domain = internship.get("domain", "")
        skills = internship.get("required_skills", [])
        skills_str = ", ".join(skills[:10]) if skills else "general skills"

        # Try LLM first ───────────────────────────────────────────────────────
        questions = None
        llm_used = False

        try:
            from engines import llm_engine  # noqa: PLC0415
            prompt = (
                f"Generate exactly 7 interview questions for a {title} internship role at {company}. "
                f"Required skills: {skills_str}. Domain: {domain}. "
                "Mix technical, behavioral, and situational question types. "
                "For each question also write a short coaching tip (1-2 sentences) that helps the candidate answer well. "
                "Return ONLY a JSON array with objects having keys: question (string), type (one of: technical, behavioral, situational), tip (string). "
                "No markdown, no extra text."
            )
            raw = llm_engine.call_llm_raw(prompt) if hasattr(llm_engine, "call_llm_raw") else None
            if raw:
                import json  # noqa: PLC0415
                questions = json.loads(raw)
                if isinstance(questions, list) and len(questions) >= 5:
                    llm_used = True
                else:
                    questions = None
        except Exception:
            pass  # Fall through to question bank

        # Fallback to local bank
        if not questions:
            questions = _get_question_bank_for_domain(domain)

        return success_response(
            data={
                "questions": questions,
                "llm_used": llm_used,
                "internship": {
                    "id": internship_id,
                    "title": title,
                    "company": company,
                    "domain": domain,
                    "required_skills": skills,
                },
            },
            message="Interview questions generated",
        )
    except Exception:
        logger.exception("Failed to generate interview prep")
        return error_response("Failed to generate interview prep", 500)
