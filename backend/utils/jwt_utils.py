from flask import current_app
from flask_jwt_extended import get_jwt_identity
from bson import ObjectId


def get_current_user():
    """
    Returns the full user document for the JWT-authenticated caller.
    """
    user_id = get_jwt_identity()

    if not user_id:
        return None

    try:
        db = current_app.config["DB"]
        user = db.users.find_one({"_id": ObjectId(user_id)})
        return user
    except Exception:
        return None