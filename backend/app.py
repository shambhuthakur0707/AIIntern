from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import Config
from pymongo import MongoClient


def create_app():
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = Config.JWT_SECRET_KEY

    # Extensions
    JWTManager(app)
    CORS(app, origins="*", supports_credentials=True)

    # MongoDB connection
    mongo_client = MongoClient(Config.MONGO_URI)
    db = mongo_client[Config.MONGO_DB_NAME]

    # ✅ Store DB inside app config (IMPORTANT)
    app.config["DB"] = db

    # Register blueprints
    from routes.auth_routes import auth_bp
    from routes.agent_routes import agent_bp
    from routes.dashboard_routes import dashboard_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(agent_bp, url_prefix="/api/agent")
    app.register_blueprint(dashboard_bp, url_prefix="/api")

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