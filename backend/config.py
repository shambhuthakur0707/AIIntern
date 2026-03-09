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
    JSEARCH_API_KEY = os.getenv("JSEARCH_API_KEY", "")
    ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID", "")
    ADZUNA_API_KEY = os.getenv("ADZUNA_API_KEY", "")
    SCRAPER_INTERVAL_HOURS = int(os.getenv("SCRAPER_INTERVAL_HOURS", 6))

    # ── Google OAuth ──────────────────────────────────────────────────────
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")

    # ── Email / SMTP for OTP ──────────────────────────────────────────────
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True").lower() == "true"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "")

    # ── Security ──────────────────────────────────────────────────────────
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 5 * 1024 * 1024))  # 5MB
