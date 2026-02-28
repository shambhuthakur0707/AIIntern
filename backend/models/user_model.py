from datetime import datetime


def create_user_document(name, email, password_hash, skills, interests, experience_level, education):
    """
    Returns a MongoDB-ready user document.
    """
    return {
        "name": name,
        "email": email.lower().strip(),
        "password_hash": password_hash,
        "skills": [s.strip() for s in skills],          # e.g. ["Python", "SQL", "TensorFlow"]
        "interests": [i.strip() for i in interests],    # e.g. ["ML", "Data Science"]
        "experience_level": experience_level,            # "beginner" | "intermediate" | "advanced"
        "education": education,                          # "B.Tech", "M.Tech", etc.
        "last_match_result": None,                       # Populated by agent after /match
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


def sanitize_user(user_doc):
    """
    Strips sensitive fields before sending to client.
    """
    if not user_doc:
        return None
    return {
        "id": str(user_doc["_id"]),
        "name": user_doc.get("name"),
        "email": user_doc.get("email"),
        "skills": user_doc.get("skills", []),
        "interests": user_doc.get("interests", []),
        "experience_level": user_doc.get("experience_level"),
        "education": user_doc.get("education"),
        "last_match_result": user_doc.get("last_match_result"),
    }
