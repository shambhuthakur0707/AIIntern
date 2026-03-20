import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routes.internships import router as internships_router
from .services.aggregator import refresh_internships
from .services.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("FastAPI internship aggregator starting")
    try:
        await refresh_internships(location="India")
    except Exception as exc:
        logger.warning("Initial refresh failed: %s", exc)
    start_scheduler()
    yield
    stop_scheduler()
    logger.info("FastAPI internship aggregator stopped")


app = FastAPI(title="Internship Aggregator API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def health_check():
    return {"status": "ok", "service": "internship-aggregator"}


app.include_router(internships_router)
