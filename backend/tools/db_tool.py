"""
db_tool.py — FetchInternshipsTool
LangChain BaseTool that retrieves all internship documents from MongoDB.
"""
import json
from abc import ABC, abstractmethod
from typing import Type
from pydantic import BaseModel, Field


class BaseTool(ABC):
    name: str = ""
    description: str = ""
    args_schema: Type[BaseModel] = None

    @abstractmethod
    def _run(self, *args, **kwargs): ...

    async def _arun(self, *args, **kwargs):
        return self._run(*args, **kwargs)
from flask import current_app
from bson import ObjectId


class FetchInternshipsInput(BaseModel):
    query: str = Field(default="all", description="Use 'all' to fetch every internship.")


class FetchInternshipsTool(BaseTool):
    name: str = "FetchInternshipsTool"
    description: str = (
        "Fetches all available internship listings from the database. "
        "Always call this first before scoring or gap analysis. "
        "Returns a JSON array of internship objects."
    )
    args_schema: Type[BaseModel] = FetchInternshipsInput

    def _run(self, query: str = "all") -> str:
        # ✅ Get DB safely from Flask app context
        db = current_app.config["DB"]

        internships = list(db.internships.find())

        result = []
        for intern in internships:
            intern["_id"] = str(intern["_id"])
            result.append(intern)

        return json.dumps(result, default=str)

    async def _arun(self, query: str = "all") -> str:
        return self._run(query)