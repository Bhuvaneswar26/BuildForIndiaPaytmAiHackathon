from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings
from app.ingestion import run_all

scheduler = AsyncIOScheduler()


def start_scheduler() -> None:
    scheduler.add_job(
        run_all,
        CronTrigger(hour=settings.cron_hour, minute=settings.cron_minute),
        id="nightly_passbook_ingest",
        replace_existing=True,
    )
    scheduler.start()
