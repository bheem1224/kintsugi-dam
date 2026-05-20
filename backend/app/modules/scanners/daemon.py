import asyncio
import logging
from typing import List, AsyncGenerator
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import async_session_maker as SessionLocal
from app.core.models import SystemSettings, MediaFile
from app.core.scanner import FileScanner

logger = logging.getLogger(__name__)

async def is_pro_tier(db_session: AsyncSession) -> bool:
    result = await db_session.execute(select(SystemSettings).limit(1))
    settings = result.scalar_one_or_none()
    if settings and settings.license_tier in ['pro', 'studio']:
        return True
    return False

async def get_max_workers(db_session: AsyncSession) -> int:
    result = await db_session.execute(select(SystemSettings).limit(1))
    settings = result.scalar_one_or_none()
    if settings:
        return settings.max_workers
    return 1

async def scanner_worker(queue: asyncio.Queue, scanner: FileScanner):
    while True:
        file_path_str = await queue.get()
        if file_path_str is None:
            queue.task_done()
            break

        # Inject a fresh DB session per file to avoid contention and
        # safely handle transactions across async boundaries.
        try:
            async with SessionLocal() as db_session:
                await scanner.process_file(Path(file_path_str), db_session)
        except Exception as e:
            logger.error(f"Error scanning {file_path_str}: {e}")
        finally:
            queue.task_done()

async def run_scanner_daemon(file_paths_generator: AsyncGenerator[str, None]):
    """
    Background scanner daemon that consumes an async generator of file paths.
    """
    async with SessionLocal() as db_session:
        pro_tier = await is_pro_tier(db_session)
        configured_workers = await get_max_workers(db_session)

    # Determine actual workers
    num_workers = configured_workers if pro_tier else 1

    # Ensure at least 1 worker and not unbounded
    num_workers = max(1, min(num_workers, 32))

    logger.info(f"Starting scanner daemon with {num_workers} workers (Pro tier: {pro_tier})")

    queue = asyncio.Queue(maxsize=num_workers * 2) # bounded queue to prevent memory blowup
    scanner = FileScanner()

    # Start workers
    workers = []
    for _ in range(num_workers):
        worker_task = asyncio.create_task(scanner_worker(queue, scanner))
        workers.append(worker_task)

    # Producer loop
    async for path in file_paths_generator:
        await queue.put(path)

    # Stop workers
    for _ in range(num_workers):
        await queue.put(None)

    await queue.join()
    await asyncio.gather(*workers)
    logger.info("Scanner daemon finished.")
