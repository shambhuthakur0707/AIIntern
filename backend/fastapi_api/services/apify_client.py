import logging
import httpx
from typing import Any

logger = logging.getLogger(__name__)


class ApifyClient:
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.apify.com/v2"

    async def run_actor_and_fetch_items(
        self,
        actor_id: str,
        actor_input: dict[str, Any],
        max_items: int = 100,
    ) -> list[dict[str, Any]]:
        if not self.token or not actor_id:
            logger.warning("Apify token or actor id missing; skipping fetch for actor=%s", actor_id)
            return []

        run_url = f"{self.base_url}/acts/{actor_id}/runs"
        params = {
            "token": self.token,
            "waitForFinish": 120,
            "memory": 1024,
        }

        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                run_resp = await client.post(run_url, params=params, json=actor_input)
                run_resp.raise_for_status()
                run_data = run_resp.json().get("data", {})

                dataset_id = run_data.get("defaultDatasetId")
                if not dataset_id:
                    logger.warning("Apify actor run returned no dataset id for actor=%s", actor_id)
                    return []

                dataset_url = f"{self.base_url}/datasets/{dataset_id}/items"
                ds_params = {
                    "token": self.token,
                    "clean": "true",
                    "format": "json",
                    "limit": max_items,
                }
                items_resp = await client.get(dataset_url, params=ds_params)
                items_resp.raise_for_status()
                items = items_resp.json()
                return items if isinstance(items, list) else []
        except httpx.HTTPError as exc:
            logger.error("Apify request failed for actor=%s: %s", actor_id, exc)
            return []
