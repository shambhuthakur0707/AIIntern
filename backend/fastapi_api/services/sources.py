import logging
from .apify_client import ApifyClient
from ..config import settings
from .normalizer import normalize_record

logger = logging.getLogger(__name__)


async def fetch_linkedin_jobs(apify_client: ApifyClient, location: str = "India") -> list[dict]:
    actor_input = {
        "keywords": "internship OR intern",
        "location": location,
        "maxItems": settings.apify_max_items,
        "country": "IN",
    }
    rows = await apify_client.run_actor_and_fetch_items(
        settings.apify_linkedin_actor_id,
        actor_input,
        max_items=settings.apify_max_items,
    )
    return [normalize_record(row, "LinkedIn") for row in rows]


async def fetch_ats_jobs(apify_client: ApifyClient, location: str = "India") -> list[dict]:
    actor_input = {
        "query": "internship OR intern",
        "location": location,
        "maxItems": settings.apify_max_items,
        "country": "IN",
    }
    rows = await apify_client.run_actor_and_fetch_items(
        settings.apify_ats_actor_id,
        actor_input,
        max_items=settings.apify_max_items,
    )
    return [normalize_record(row, "ATS") for row in rows]
