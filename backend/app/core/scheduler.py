import asyncio
import logging
from datetime import time
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select, nulls_first, asc

from .database import async_session_maker
from .models import MediaFile
from .scanner import FileScanner
from .qos import QoSManager
from app.tasks.prune import prune_triage_bin

logger = logging.getLogger(__name__)

async def run_lru_daemon(db_session_maker):
    """
    Continuous background daemon that scans the massive media library
    using an LRU (Least Recently Used) approach based on last_scanned_at.
    """
    logger.info("Starting LRU Scanner Daemon...")
    scanner = FileScanner()

    while True:
        try:
            # 1. QoS Check before fetching and processing a batch
            if await QoSManager.should_yield():
                logger.debug("QoS Manager: Yielding CPU/Disk to host system...")
                await asyncio.sleep(5)
                continue

            async with db_session_maker() as session:
                # 2. Query batch of 100 oldest unverified files
                result = await session.execute(
                    select(MediaFile)
                    .order_by(nulls_first(asc(MediaFile.last_scanned_at)))
                    .limit(100)
                )
                files_to_scan = result.scalars().all()

                if not files_to_scan:
                    # No files to scan, sleep for a while to avoid CPU loop
                    await asyncio.sleep(60)
                    continue

                # 3. Process the batch
                for record in files_to_scan:
                    # Respect QoS inside the batch loop too
                    if await QoSManager.should_yield():
                        logger.debug("QoS Manager: Yielding inside batch...")
                        await asyncio.sleep(5)

                    file_path = Path(record.filepath)
                    await scanner.process_file(file_path, session)

            # Briefly yield control to the event loop between batches
            await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Error in LRU daemon loop: {e}")
            await asyncio.sleep(60)


def start_scheduler() -> AsyncIOScheduler:
    """
    Initializes and starts the APScheduler for discrete cron tasks like pruning.
    (Scanning has moved to the run_lru_daemon).
    """
    scheduler = AsyncIOScheduler()

    async def _run_prune_job():
        async with async_session_maker() as session:
            await prune_triage_bin(session)

    # Run at 3:00 AM daily
    scheduler.add_job(
        _run_prune_job, "cron", hour=3, minute=0
    )

    scheduler.start()
    return scheduler
