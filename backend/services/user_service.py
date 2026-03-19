from flask import current_app
from bson import ObjectId
from datetime import datetime

try:
    from ..engines.matching_engine import compute_skill_overlap
except ImportError:
    from engines.matching_engine import compute_skill_overlap


def _recommendation_required_skills(recommendation: dict):
    required_skills = recommendation.get("required_skills", [])
    if isinstance(required_skills, list) and required_skills:
        return [skill.strip() for skill in required_skills if isinstance(skill, str) and skill.strip()]

    combined = []
    seen = set()
    for field in ("matched_skills", "missing_skills"):
        for skill in recommendation.get(field, []) or []:
            cleaned = (skill or "").strip()
            if not cleaned:
                continue
            lowered = cleaned.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            combined.append(cleaned)
    return combined


def _refresh_last_match_result(user_doc: dict):
    match_result = user_doc.get("last_match_result")
    if not isinstance(match_result, dict):
        return user_doc

    recommendations = match_result.get("recommendations")
    if not isinstance(recommendations, list):
        return user_doc

    user_skills = user_doc.get("skills", [])
    refreshed = []
    changed = False

    for recommendation in recommendations:
        if not isinstance(recommendation, dict):
            refreshed.append(recommendation)
            continue

        required_skills = _recommendation_required_skills(recommendation)
        overlap = compute_skill_overlap(user_skills, required_skills)

        updated_recommendation = dict(recommendation)
        updated_recommendation["required_skills"] = required_skills
        updated_recommendation["matched_skills"] = overlap["matched_skills"]
        updated_recommendation["missing_skills"] = overlap["missing_skills"]

        score_breakdown = dict(updated_recommendation.get("score_breakdown") or {})
        score_breakdown["skill_overlap"] = overlap["overlap_pct"]
        updated_recommendation["score_breakdown"] = score_breakdown

        if (
            updated_recommendation["matched_skills"] != recommendation.get("matched_skills", [])
            or updated_recommendation["missing_skills"] != recommendation.get("missing_skills", [])
            or updated_recommendation.get("required_skills", []) != recommendation.get("required_skills", [])
        ):
            changed = True

        refreshed.append(updated_recommendation)

    if not changed:
        return user_doc

    refreshed_result = dict(match_result)
    refreshed_result["recommendations"] = refreshed

    db = current_app.config["DB"]
    db.users.update_one(
        {"_id": user_doc["_id"]},
        {
            "$set": {
                "last_match_result": refreshed_result,
                "updated_at": datetime.utcnow(),
            }
        },
    )
    user_doc["last_match_result"] = refreshed_result
    return user_doc


def refresh_user_match_result(user_doc: dict):
    if not user_doc:
        return None
    return _refresh_last_match_result(user_doc)


def get_user_by_id(user_id: str):
    """Fetch a user document by string ID."""
    db = current_app.config["DB"]

    try:
        return db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        return None


def update_user_match_result(user_id: str, match_result: dict):
    """Persist the agent's last match result on the user document."""
    db = current_app.config["DB"]

    db.users.update_one(
        {"_id": ObjectId(user_id)},
        {
            "$set": {
                "last_match_result": match_result,
                "updated_at": datetime.utcnow(),
            }
        },
    )


def get_all_internships():
    """Return all internship documents from MongoDB."""
    db = current_app.config["DB"]
    return list(db.internships.find())


def add_user_skill(user_id: str, skill: str):
    db = current_app.config["DB"]
    cleaned = (skill or "").strip()
    if not cleaned:
        return None

    db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$addToSet": {"skills": cleaned}, "$set": {"updated_at": datetime.utcnow()}},
    )
    user_doc = db.users.find_one({"_id": ObjectId(user_id)})
    return _refresh_last_match_result(user_doc) if user_doc else None


def remove_user_skill(user_id: str, skill: str):
    db = current_app.config["DB"]
    cleaned = (skill or "").strip()
    if not cleaned:
        return None

    db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$pull": {"skills": cleaned}, "$set": {"updated_at": datetime.utcnow()}},
    )
    user_doc = db.users.find_one({"_id": ObjectId(user_id)})
    return _refresh_last_match_result(user_doc) if user_doc else None


def update_user_profile_sources(
    user_id: str,
    linkedin_url: str = "",
    github_url: str = "",
    resume_filename: str = "",
    resume_text: str = "",
    imported_skills=None,
    imported_interests=None,
):
    db = current_app.config["DB"]
    imported_skills = imported_skills or []
    imported_interests = imported_interests or []

    set_fields = {"updated_at": datetime.utcnow()}
    if linkedin_url is not None:
        set_fields["linkedin_url"] = linkedin_url.strip()
    if github_url is not None:
        set_fields["github_url"] = github_url.strip()
    if resume_filename:
        set_fields["resume_filename"] = resume_filename.strip()
    if resume_text:
        set_fields["resume_text"] = resume_text[:20000]

    update_doc = {"$set": set_fields}
    if imported_skills:
        update_doc["$addToSet"] = {"skills": {"$each": imported_skills}}
    if imported_interests:
        update_doc.setdefault("$addToSet", {})
        update_doc["$addToSet"]["interests"] = {"$each": imported_interests}

    db.users.update_one({"_id": ObjectId(user_id)}, update_doc)
    user_doc = db.users.find_one({"_id": ObjectId(user_id)})
    return _refresh_last_match_result(user_doc) if user_doc else None
