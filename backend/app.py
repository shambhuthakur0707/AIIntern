from datetime import timedelta
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail
from pymongo import MongoClient

try:
    from .config import Config
except ImportError:
    from config import Config

mail = Mail()
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per hour"])


def create_app():
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = Config.JWT_SECRET_KEY
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=2)
    app.config["MAX_CONTENT_LENGTH"] = Config.MAX_CONTENT_LENGTH

    # Mail config
    app.config["MAIL_SERVER"] = Config.MAIL_SERVER
    app.config["MAIL_PORT"] = Config.MAIL_PORT
    app.config["MAIL_USE_TLS"] = Config.MAIL_USE_TLS
    app.config["MAIL_USERNAME"] = Config.MAIL_USERNAME
    app.config["MAIL_PASSWORD"] = Config.MAIL_PASSWORD
    app.config["MAIL_DEFAULT_SENDER"] = Config.MAIL_DEFAULT_SENDER

    # Extensions
    JWTManager(app)
    CORS(app, origins=Config.CORS_ORIGINS, supports_credentials=True)
    limiter.init_app(app)
    mail.init_app(app)

    # Security headers
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

    # MongoDB connection
    mongo_client = MongoClient(Config.MONGO_URI)
    db = mongo_client[Config.MONGO_DB_NAME]

    # ✅ Store DB inside app config (IMPORTANT)
    app.config["DB"] = db

    # Ensure indexes for fast queries
    db.internships.create_index([("domain", 1)])
    db.internships.create_index([("location", 1)])
    db.internships.create_index([("required_skills", 1)])
    db.internship_analyses.create_index("cache_key", unique=True)
    db.internship_analyses.create_index("expires_at")
    db.users.create_index([("email", 1)], unique=True)
    db.otp_codes.create_index("expires_at", expireAfterSeconds=0)

    # Register blueprints
    try:
        from .routes.auth_routes import auth_bp
        from .routes.agent_routes import agent_bp
        from .routes.dashboard_routes import dashboard_bp
        from .routes.internships_routes import internships_bp
        from .routes.scraper_routes import scraper_bp
    except ImportError:
        from routes.auth_routes import auth_bp
        from routes.agent_routes import agent_bp
        from routes.dashboard_routes import dashboard_bp
        from routes.internships_routes import internships_bp
        from routes.scraper_routes import scraper_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(agent_bp, url_prefix="/api/agent")
    app.register_blueprint(dashboard_bp, url_prefix="/api")
    app.register_blueprint(internships_bp, url_prefix="/api/internships")
    app.register_blueprint(scraper_bp, url_prefix="/api/scraper")

    # Start the background internship scraper scheduler
    try:
        from .scrapers.scheduler import init_scheduler
    except ImportError:
        from scrapers.scheduler import init_scheduler
    init_scheduler(app, interval_hours=Config.SCRAPER_INTERVAL_HOURS)

    @app.route("/api/health")
    def health():
        return {
            "status": "ok",
            "message": "AI Internship Matcher API running"
        }

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(
        debug=Config.FLASK_DEBUG,
        port=Config.FLASK_PORT,
        host="0.0.0.0"
    )
