"""
fallback_engine.py — Rule-Based Fallback when LLM Fails

Generates deterministic reasoning, skill gap analysis, and a 4-week
learning roadmap using a curated resource map — ensuring the system
always returns complete, structured results.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# ── Curated learning resources ───────────────────────────────────────
RESOURCE_MAP: Dict[str, Dict[str, Any]] = {
    "python":           {"focus": "Python Fundamentals", "tasks": ["Complete Python.org tutorial", "Build a CLI project"]},
    "tensorflow":       {"focus": "TensorFlow & Keras", "tasks": ["Follow TensorFlow official tutorials", "Train a simple CNN"]},
    "pytorch":          {"focus": "PyTorch Basics", "tasks": ["Complete PyTorch 60-min blitz", "Implement a basic model"]},
    "deep learning":    {"focus": "Deep Learning Theory", "tasks": ["fast.ai Practical DL course", "Implement backprop from scratch"]},
    "machine learning": {"focus": "ML Fundamentals", "tasks": ["Andrew Ng ML Specialization", "Kaggle Getting Started competition"]},
    "sql":              {"focus": "SQL & Databases", "tasks": ["Mode SQL Tutorial", "Solve 20 LeetCode SQL problems"]},
    "pandas":           {"focus": "Data Wrangling", "tasks": ["Pandas official 10-min guide", "Clean a real-world dataset"]},
    "data analysis":    {"focus": "Data Analysis", "tasks": ["Kaggle Learn Data Analysis", "EDA on a public dataset"]},
    "react":            {"focus": "React Development", "tasks": ["React official tutorial", "Build a todo app with hooks"]},
    "node.js":          {"focus": "Node.js Backend", "tasks": ["Node.js official guide", "Build a REST API with Express"]},
    "javascript":       {"focus": "JavaScript Core", "tasks": ["MDN JavaScript Guide", "Build interactive web components"]},
    "docker":           {"focus": "Docker & Containers", "tasks": ["Docker Getting Started tutorial", "Containerize a Flask app"]},
    "kubernetes":       {"focus": "Kubernetes Basics", "tasks": ["Kubernetes.io tutorials", "Deploy app on Minikube"]},
    "aws":              {"focus": "AWS Cloud", "tasks": ["AWS Skill Builder free tier", "Deploy an app on EC2/S3"]},
    "git":              {"focus": "Git & Version Control", "tasks": ["Pro Git book chapters 1-3", "Contribute to an open-source repo"]},
    "nlp":              {"focus": "NLP Fundamentals", "tasks": ["Hugging Face NLP course", "Fine-tune a text classifier"]},
    "computer vision":  {"focus": "Computer Vision", "tasks": ["PyImageSearch tutorials", "Build an image classifier"]},
    "opencv":           {"focus": "OpenCV Basics", "tasks": ["OpenCV-Python tutorials", "Build a real-time face detector"]},
    "cybersecurity":    {"focus": "Cybersecurity Basics", "tasks": ["TryHackMe beginner path", "Complete a CTF challenge"]},
    "linux":            {"focus": "Linux Essentials", "tasks": ["Linux Journey tutorials", "Set up a Linux server"]},
    "rest api":         {"focus": "REST API Design", "tasks": ["Postman Learning Center", "Build and document an API"]},
    "flutter":          {"focus": "Flutter Mobile Dev", "tasks": ["Flutter official codelabs", "Build a weather app"]},
    "java":             {"focus": "Java Programming", "tasks": ["Oracle Java Tutorials", "Build a Spring Boot API"]},
    "kotlin":           {"focus": "Kotlin for Android", "tasks": ["Kotlin official docs", "Build an Android feature"]},
    "scikit-learn":     {"focus": "Scikit-learn ML", "tasks": ["Scikit-learn tutorials", "Build a classification pipeline"]},
    "numpy":            {"focus": "NumPy for Data", "tasks": ["NumPy quickstart tutorial", "Implement matrix operations"]},
    "transformers":     {"focus": "Transformer Models", "tasks": ["Hugging Face Transformers course", "Fine-tune BERT on a task"]},
    "hugging face":     {"focus": "HuggingFace Ecosystem", "tasks": ["HF course", "Deploy a model on HF Spaces"]},
    "bert":             {"focus": "BERT & Embeddings", "tasks": ["Read BERT paper", "Fine-tune BERT for text classification"]},
}


def _get_resource(skill: str) -> Dict[str, Any]:
    """Look up a learning resource for a skill."""
    skill_lower = skill.lower().strip()
    for key, val in RESOURCE_MAP.items():
        if key in skill_lower or skill_lower in key:
            return val
    return {
        "focus": f"Learn {skill}",
        "tasks": [f"Search '{skill} tutorial' on YouTube", f"Build a small {skill} project"],
    }


def generate_fallback(
    user_profile: Dict[str, Any],
    internship: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Generate a complete analysis result using deterministic logic.
    Same structure as the LLM output so the formatter doesn't care
    which engine produced it.

    Parameters
    ----------
    user_profile : dict with skills, experience_level, etc.
    internship   : dict from ranking_engine (has weighted_score,
                   matched_skills, missing_skills, etc.)

    Returns
    -------
    dict matching the LLM JSON schema + fallback_used=True
    """
    matched = internship.get("matched_skills", [])
    missing = internship.get("missing_skills", [])
    required = internship.get("required_skills", [])
    title = internship.get("title", "Untitled")
    score = internship.get("weighted_score", 0)

    # ── Confidence score ─────────────────────────────────────────
    confidence = round(score, 1)

    # ── Reasoning ────────────────────────────────────────────────
    if matched:
        reasoning = (
            f"You match {len(matched)} out of {len(required)} required skills "
            f"for {title}: {', '.join(matched)}. "
        )
    else:
        reasoning = f"You have limited skill overlap with {title}. "

    if missing:
        reasoning += (
            f"You are missing {len(missing)} skills: {', '.join(missing)}. "
            "Acquiring these would significantly improve your candidacy."
        )
    else:
        reasoning += "You meet all the required skills for this role."

    # ── Skill gap analysis ───────────────────────────────────────
    if missing:
        gap_analysis = (
            f"You are {len(missing)} skills away from the ideal candidate profile. "
            f"Key gaps: {', '.join(missing[:3])}. "
            f"Focus on these to move from {score:.0f}% to a stronger match."
        )
    else:
        gap_analysis = (
            "You have all the required skills. Focus on deepening your "
            "expertise and building portfolio projects to stand out."
        )

    # ── 4-week learning roadmap ──────────────────────────────────
    roadmap: List[Dict[str, Any]] = []
    skills_to_learn = missing[:4] if missing else matched[:4]

    for week_num, skill in enumerate(skills_to_learn, start=1):
        resource = _get_resource(skill)
        roadmap.append({
            "week": week_num,
            "focus": resource["focus"],
            "tasks": resource["tasks"],
        })

    # Pad to 4 weeks if fewer skills
    while len(roadmap) < 4:
        week_num = len(roadmap) + 1
        roadmap.append({
            "week": week_num,
            "focus": "Portfolio & Practice",
            "tasks": [
                "Build a project combining learned skills",
                "Write documentation and push to GitHub",
            ],
        })

    # ── Improvement priority ─────────────────────────────────────
    if missing:
        first_skill = missing[0]
        improvement_priority = (
            f"Start with {first_skill} — it is the most critical missing skill "
            f"for {title}. Learning this first will unlock the most value."
        )
    else:
        improvement_priority = (
            "Deepen your existing skills through real-world projects and "
            "open-source contributions to differentiate yourself."
        )

    logger.info("Generated fallback for '%s'", title)

    return {
        "confidence_score": confidence,
        "reasoning": reasoning,
        "strengths": matched,
        "missing_skills": missing,
        "skill_gap_analysis": gap_analysis,
        "learning_roadmap": roadmap,
        "improvement_priority": improvement_priority,
        "fallback_used": True,
    }
