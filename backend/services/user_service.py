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