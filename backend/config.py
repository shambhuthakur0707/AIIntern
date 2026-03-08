import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "aiintern_db")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback-secret-key")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "True").lower() == "true"

    # ── Job scraper API keys ──────────────────────────────────────────────
    # JSearch (RapidAPI) — covers LinkedIn, Indeed, Glassdoor, ZipRecruiter
    # Free tier: 200 req/month  →  https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
    JSEARCH_API_KEY = os.getenv("JSEARCH_API_KEY", "")

    # Adzuna — global job board aggregator
    # Free tier: 250 req/month  →  https://developer.adzuna.com/
    ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID", "")
    ADZUNA_API_KEY = os.getenv("ADZUNA_API_KEY", "")

    # How often the background scraper runs (hours). Default: every 6 hours.
    SCRAPER_INTERVAL_HOURS = int(os.getenv("SCRAPER_INTERVAL_HOURS", 6))
