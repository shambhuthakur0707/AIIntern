from flask import current_app
from bson import ObjectId
from datetime import datetime


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
    return db.users.find_one({"_id": ObjectId(user_id)})


def remove_user_skill(user_id: str, skill: str):
    db = current_app.config["DB"]
    cleaned = (skill or "").strip()
    if not cleaned:
        return None

    db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$pull": {"skills": cleaned}, "$set": {"updated_at": datetime.utcnow()}},
    )
    return db.users.find_one({"_id": ObjectId(user_id)})


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
    return db.users.find_one({"_id": ObjectId(user_id)})
