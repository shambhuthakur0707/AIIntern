import os
from dataclasses import dataclass
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(BASE_DIR)
load_dotenv(os.path.join(BACKEND_DIR, ".env"))


@dataclass(frozen=True)
class Settings:
    mongo_uri: str = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    mongo_db_name: str = os.getenv("MONGO_DB_NAME", "aiintern_db")
    mongo_collection: str = os.getenv("FASTAPI_MONGO_COLLECTION", "internships")

    apify_token: str = os.getenv("APIFY_TOKEN", "")
    apify_linkedin_actor_id: str = os.getenv("APIFY_LINKEDIN_ACTOR_ID", "")
    apify_ats_actor_id: str = os.getenv("APIFY_ATS_ACTOR_ID", "")

    apify_max_items: int = int(os.getenv("APIFY_MAX_ITEMS", "100"))
    refresh_interval_hours: int = int(os.getenv("REFRESH_INTERVAL_HOURS", "6"))


settings = Settings()
