import os
import time
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.models import SystemSettings

logger = logging.getLogger(__name__)

async def prune_triage_bin(db_session: AsyncSession) -> None:
    """
    Crawls the data/triage directory and deletes any files older than
    the retention_days defined in SystemSettings.
    """
    logger.info("Starting Triage Bin pruning job.")

    # 1. Fetch settings inside the transaction
    result = await db_session.execute(select(SystemSettings).where(SystemSettings.id == 1))
    settings = result.scalars().first()

    if not settings:
        logger.error("Could not load SystemSettings. Aborting prune job.")
        return

    retention_days = settings.retention_days
    if retention_days <= 0:
        logger.info("Retention days is 0 or less. Pruning disabled.")
        return

    cutoff_time = time.time() - (retention_days * 86400) # 86400 seconds in a day

    triage_dirs = [
        os.path.abspath("/app/data/triage/corrupted"),
        os.path.abspath("/app/data/triage/restored")
    ]

    files_deleted = 0

    for directory in triage_dirs:
        if not os.path.exists(directory):
            continue

        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    if entry.is_file(follow_symlinks=False):
                        try:
                            stat = entry.stat()
                            # Use ctime (creation time on windows/mac, metadata change on linux)
                            # or mtime as fallback. Usually mtime is sufficient.
                            if stat.st_mtime < cutoff_time:
                                try:
                                    os.remove(entry.path)
                                    files_deleted += 1
                                    logger.debug(f"Pruned old triage file: {entry.path}")
                                except OSError as e:
                                    logger.warning(f"Failed to delete triage file {entry.path}: {e}")
                        except OSError:
                            continue
        except OSError as e:
            logger.error(f"Failed to scan directory {directory}: {e}")

    logger.info(f"Triage Bin pruning complete. Deleted {files_deleted} old files.")

    # Ensure transaction finishes cleanly
    await db_session.commit()
