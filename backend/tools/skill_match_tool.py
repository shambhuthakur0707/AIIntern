"""
skill_match_tool.py — SkillMatchTool

Computes a match score (0–100) between user skills and internship required skills
using TF-IDF cosine similarity as a fast, interpretable baseline.
"""

import json
from typing import Type, List, Dict, Any
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class SkillMatchInput(BaseModel):
    user_skills: List[str] = Field(
        description="List of user's skills, e.g. ['Python', 'SQL', 'TensorFlow']"
    )
    internship: Dict[str, Any] = Field(
        description="Internship object containing at least 'required_skills' and optionally 'title'"
    )


class SkillMatchTool(BaseTool):
    name: str = "SkillMatchTool"
    description: str = (
        "Computes a numerical match score (0–100) between the user's skills and "
        "the internship's required skills using TF-IDF cosine similarity. "
        "Call this for EACH internship to get its match score."
    )
    args_schema: Type[BaseModel] = SkillMatchInput

    def _run(self, user_skills: List[str], internship: Dict[str, Any]) -> str:
        internship_skills = internship.get("required_skills", [])
        internship_title = internship.get("title", "")

        # Convert lists into normalized text
        user_text = " ".join([s.strip().lower() for s in user_skills])
        intern_text = " ".join([s.strip().lower() for s in internship_skills])

        if not user_text.strip() or not intern_text.strip():
            return json.dumps({
                "internship_title": internship_title,
                "match_score": 0
            })

        try:
            vectorizer = TfidfVectorizer(analyzer="word", ngram_range=(1, 2))
            tfidf_matrix = vectorizer.fit_transform([user_text, intern_text])
            score = cosine_similarity(
                tfidf_matrix[0:1], tfidf_matrix[1:2]
            )[0][0]
            match_score = round(float(score) * 100, 2)
        except Exception:
            match_score = 0.0

        return json.dumps({
            "internship_title": internship_title,
            "match_score": match_score
        })

    async def _arun(self, user_skills: List[str], internship: Dict[str, Any]) -> str:
        return self._run(user_skills, internship)