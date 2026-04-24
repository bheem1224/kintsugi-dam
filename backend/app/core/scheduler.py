from datetime import time
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .scanner import run_scan
from .database import async_session_maker
from app.tasks.prune import prune_triage_bin


def start_scheduler(
    target_dir: str, start_time: time, end_time: time
) -> AsyncIOScheduler:
    """
    Initializes and starts the APScheduler to run the scanner job daily.
    """
    scheduler = AsyncIOScheduler()

    async def _run_scan_job():
        """
        Wrapper function to inject the async database session and run the scan.
        """
        async with async_session_maker() as session:
            await run_scan(target_dir, session, start_time, end_time)

    # Schedule the job to run daily at the specified start_time
    scheduler.add_job(
        _run_scan_job, "cron", hour=start_time.hour, minute=start_time.minute
    )

    async def _run_prune_job():
        async with async_session_maker() as session:
            await prune_triage_bin(session)

    # Run at 3:00 AM daily
    scheduler.add_job(
        _run_prune_job, "cron", hour=3, minute=0
    )

    scheduler.start()
    return scheduler
