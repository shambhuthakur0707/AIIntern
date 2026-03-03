from datetime import datetime


def create_internship_document(
    title, company, required_skills, description,
    domain, stipend, duration, location="Remote", openings=5, apply_url=""
):
    """
    Returns a MongoDB-ready internship document.
    """
    return {
        "title": title,
        "company": company,
        "required_skills": [s.strip() for s in required_skills],
        "description": description,
        "domain": domain,           # "ML", "Web Dev", "Data Science", etc.
        "stipend": stipend,         # e.g. "₹15,000/month"
        "duration": duration,       # e.g. "3 months"
        "location": location,
        "openings": openings,
        "apply_url": apply_url,
        "created_at": datetime.utcnow(),
    }


def sanitize_internship(doc):
    if not doc:
        return None
    return {
        "id": str(doc["_id"]),
        "title": doc.get("title"),
        "company": doc.get("company"),
        "required_skills": doc.get("required_skills", []),
        "description": doc.get("description"),
        "domain": doc.get("domain"),
        "stipend": doc.get("stipend"),
        "duration": doc.get("duration"),
        "location": doc.get("location"),
        "openings": doc.get("openings"),
        "apply_url": doc.get("apply_url"),
    }
