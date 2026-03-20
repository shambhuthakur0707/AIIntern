import logging
import re
from fastapi import APIRouter, HTTPException, Query
from ..db import get_collection
from ..models.internship import InternshipOut, RefreshResult
from ..services.aggregator import refresh_internships

logger = logging.getLogger(__name__)
router = APIRouter(prefix="", tags=["internships"])


@router.get("/internships", response_model=list[InternshipOut])
async def get_internships(
    state: str | None = Query(default=None),
    role: str | None = Query(default=None),
):
    try:
        query = {}
        if state:
            query["state"] = {"$regex": f"^{re.escape(state)}$", "$options": "i"}
        if role:
            query["title"] = {"$regex": re.escape(role), "$options": "i"}

        rows = list(
            get_collection()
            .find(query, {"_id": 0, "dedupe_key": 0, "created_at": 0, "updated_at": 0})
            .sort("posted_at", -1)
        )
        return rows
    except Exception as exc:
        logger.exception("Failed to fetch internships: %s", exc)
        raise HTTPException(status_code=500, detail="Could not fetch internships")


@router.post("/internships/refresh", response_model=RefreshResult)
async def refresh_internship_data():
    try:
        result = await refresh_internships(location="India")
        return result
    except Exception as exc:
        logger.exception("Failed to refresh internships: %s", exc)
        raise HTTPException(status_code=500, detail="Refresh failed")
