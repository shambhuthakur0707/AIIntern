import asyncio
import logging
from datetime import datetime
from pymongo import UpdateOne
from ..config import settings
from ..db import get_collection
from .apify_client import ApifyClient
from .normalizer import dedupe_records
from .sources import fetch_ats_jobs, fetch_linkedin_jobs

logger = logging.getLogger(__name__)


async def refresh_internships(location: str = "India") -> dict:
    collection = get_collection()
    collection.create_index("dedupe_key", unique=True)
    collection.create_index("state")
    collection.create_index("title")

    apify_client = ApifyClient(settings.apify_token)

    linkedin_task = fetch_linkedin_jobs(apify_client, location=location)
    ats_task = fetch_ats_jobs(apify_client, location=location)

    linkedin_rows, ats_rows = await asyncio.gather(linkedin_task, ats_task, return_exceptions=True)

    rows = []
    for result in (linkedin_rows, ats_rows):
        if isinstance(result, Exception):
            logger.exception("Source fetch failed: %s", result)
            continue
        rows.extend(result)

    rows = [r for r in rows if r.get("title") and r.get("company") and r.get("location")]
    deduped = dedupe_records(rows)

    ops = []
    now = datetime.utcnow()
    for item in deduped:
        doc = dict(item)
        doc["updated_at"] = now
        ops.append(
            UpdateOne(
                {"dedupe_key": item["dedupe_key"]},
                {"$set": doc, "$setOnInsert": {"created_at": now}},
                upsert=True,
            )
        )

    stored = 0
    if ops:
        result = collection.bulk_write(ops, ordered=False)
        stored = (result.upserted_count or 0) + (result.modified_count or 0)

    logger.info(
        "Internship refresh complete fetched=%d deduped=%d stored=%d",
        len(rows), len(deduped), stored,
    )
    return {
        "fetched": len(rows),
        "deduped": len(deduped),
        "stored": stored,
        "run_at": now,
    }
