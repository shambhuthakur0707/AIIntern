import re
from typing import Dict, List, Set


BASE_SKILLS = {
    "python",
    "java",
    "javascript",
    "typescript",
    "react",
    "node.js",
    "nodejs",
    "sql",
    "mongodb",
    "postgresql",
    "tensorflow",
    "pytorch",
    "machine learning",
    "deep learning",
    "nlp",
    "data analysis",
    "scikit-learn",
    "pandas",
    "numpy",
    "docker",
    "kubernetes",
    "aws",
    "linux",
    "git",
    "rest api",
    "flask",
    "django",
    "opencv",
    "computer vision",
    "airflow",
    "kafka",
    "spark",
    "terraform",
}


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def _canonicalize(skill: str) -> str:
    cleaned = re.sub(r"\s+", " ", skill.strip())
    if not cleaned:
        return ""
    if cleaned.lower() == "nodejs":
        return "Node.js"
    return " ".join(part.capitalize() for part in cleaned.split(" "))


def build_skill_catalog(db) -> Set[str]:
    catalog = set(BASE_SKILLS)
    for doc in db.internships.find({}, {"required_skills": 1}):
        for skill in doc.get("required_skills", []):
            s = _normalize_text(skill)
            if s:
                catalog.add(s)
    return catalog


def extract_skills_from_text(text: str, skill_catalog: Set[str], limit: int = 20) -> List[str]:
    normalized = f" {_normalize_text(text)} "
    if not normalized.strip():
        return []

    matched: List[str] = []
    for skill in sorted(skill_catalog, key=len, reverse=True):
        pattern = rf"(?<![a-z0-9]){re.escape(skill)}(?![a-z0-9])"
        if re.search(pattern, normalized):
            canonical = _canonicalize(skill)
            if canonical and canonical not in matched:
                matched.append(canonical)
        if len(matched) >= limit:
            break
    return matched


def extract_profile_from_sources(db, cv_text: str, linkedin_url: str, github_url: str) -> Dict[str, List[str]]:
    source_blob = " ".join([cv_text or "", linkedin_url or "", github_url or ""])
    catalog = build_skill_catalog(db)
    skills = extract_skills_from_text(source_blob, catalog)
    interests = skills[:5]
    return {"skills": skills, "interests": interests}

