"""
skill_gap_tool.py — SkillGapAnalysisTool

Identifies skills the user lacks for a given internship and generates
a structured week-by-week learning roadmap.
"""

import json
from abc import ABC, abstractmethod
from typing import Type, List, Dict, Any
from pydantic import BaseModel, Field


class BaseTool(ABC):
    name: str = ""
    description: str = ""
    args_schema: Type[BaseModel] = None

    @abstractmethod
    def _run(self, *args, **kwargs): ...

    async def _arun(self, *args, **kwargs):
        return self._run(*args, **kwargs)


# Curated learning resource map
RESOURCE_MAP = {
    "python": {"resource": "Python.org docs + Automate the Boring Stuff", "weeks": 1},
    "machine learning": {"resource": "Coursera Andrew Ng ML Specialization", "weeks": 2},
    "deep learning": {"resource": "fast.ai Practical Deep Learning", "weeks": 2},
    "tensorflow": {"resource": "TensorFlow official tutorials + Keras docs", "weeks": 1},
    "pytorch": {"resource": "PyTorch 60-minute blitz tutorial", "weeks": 1},
    "sql": {"resource": "Mode SQL Tutorial + LeetCode SQL problems", "weeks": 1},
    "data analysis": {"resource": "Pandas docs + Kaggle Learn Data Analysis", "weeks": 1},
    "react": {"resource": "React official docs + Scrimba React course", "weeks": 2},
    "node.js": {"resource": "Node.js official guide + The Odin Project", "weeks": 2},
    "docker": {"resource": "Docker Getting Started + Play with Docker labs", "weeks": 1},
    "kubernetes": {"resource": "Kubernetes.io tutorials + Kodekloud", "weeks": 2},
    "aws": {"resource": "AWS Skill Builder free tier + A Cloud Guru", "weeks": 2},
    "cybersecurity": {"resource": "TryHackMe beginner paths + CompTIA Security+", "weeks": 3},
    "nlp": {"resource": "Hugging Face NLP course (free)", "weeks": 2},
    "computer vision": {"resource": "PyImageSearch + CS231n lecture notes", "weeks": 2},
    "flutter": {"resource": "Flutter official codelabs + Angela Yu Udemy", "weeks": 2},
    "java": {"resource": "Java Tutorials Oracle + Effective Java book", "weeks": 2},
    "devops": {"resource": "Linux Foundation LFS258 + GitHub Actions docs", "weeks": 2},
    "rest api": {"resource": "Postman Learning Center + Flask-RESTful docs", "weeks": 1},
    "git": {"resource": "Pro Git book (free) + GitHub Learning Lab", "weeks": 0.5},
}


def _get_resource(skill: str) -> dict:
    skill_lower = skill.lower()
    for key, val in RESOURCE_MAP.items():
        if key in skill_lower or skill_lower in key:
            return val
    return {
        "resource": f"Search '{skill} tutorial' on YouTube or Coursera",
        "weeks": 1
    }


def _unique_case_insensitive(items: List[str]) -> List[str]:
    """De-duplicate while preserving order, case-insensitive."""
    seen = set()
    unique = []
    for item in items:
        key = item.lower().strip()
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(item.strip())
    return unique


class SkillGapInput(BaseModel):
    user_skills: List[str] = Field(
        description="List of user's current skills"
    )
    internship: Dict[str, Any] = Field(
        description="Internship object containing at least 'required_skills' and optionally 'title'"
    )


class SkillGapAnalysisTool(BaseTool):
    name: str = "SkillGapAnalysisTool"
    description: str = (
        "Identifies the exact skills the user is missing for a given internship "
        "and returns a structured learning roadmap."
    )
    args_schema: Type[BaseModel] = SkillGapInput

    def _run(self, user_skills: List[str], internship: Dict[str, Any]) -> str:
        internship_title = internship.get("title", "")
        required_skills = internship.get("required_skills", [])

        user_set = {s.strip().lower() for s in user_skills if s.strip()}
        required_list = _unique_case_insensitive([s for s in required_skills if s and s.strip()])

        missing_skills = [
            skill for skill in required_list
            if skill.lower() not in user_set
        ]

        roadmap = []
        week_counter = 1

        for skill in missing_skills:
            resource_info = _get_resource(skill)
            duration = resource_info["weeks"]

            # Handle fractional weeks safely
            duration_int = int(duration) if duration >= 1 else 1
            end_week = week_counter + duration_int - 1

            roadmap.append({
                "skill": skill,
                "resource": resource_info["resource"],
                "estimated_weeks": duration,
                "week_start": week_counter,
                "week_end": end_week,
            })

            week_counter = end_week + 1

        return json.dumps({
            "internship_title": internship_title,
            "missing_skills": missing_skills,
            "gap_count": len(missing_skills),
            "total_learning_weeks": week_counter - 1,
            "roadmap": roadmap,
        })

    async def _arun(self, user_skills: List[str], internship: Dict[str, Any]) -> str:
        return self._run(user_skills, internship)
