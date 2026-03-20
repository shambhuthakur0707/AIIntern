import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from ..config import settings
from .aggregator import refresh_internships

logger = logging.getLogger(__name__)

scheduler: AsyncIOScheduler | None = None


def start_scheduler() -> None:
    global scheduler
    if scheduler and scheduler.running:
        return

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        refresh_internships,
        trigger=IntervalTrigger(hours=settings.refresh_interval_hours),
        kwargs={"location": "India"},
        id="refresh_internships_job",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    logger.info("Scheduler started with interval=%d hours", settings.refresh_interval_hours)


def stop_scheduler() -> None:
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
