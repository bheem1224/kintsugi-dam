from datetime import time
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .scanner import run_scan
from .database import async_session_maker


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

    scheduler.start()
    return scheduler
