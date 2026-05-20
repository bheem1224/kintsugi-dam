import asyncio
import logging
import os
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.models import TriageEntry

logger = logging.getLogger(__name__)

async def run_triage_daemon(db_session_maker):
    """
    Background worker that monitors triage entries.
    Deletes expired quarantined files and their DB rows.
    """
    logger.info("Starting Triage Scheduler Daemon...")

    while True:
        try:
            async with db_session_maker() as session:
                # Find all expired entries
                now = datetime.now()
                result = await session.execute(
                    select(TriageEntry)
                    .where(TriageEntry.expires_at != None)
                    .where(TriageEntry.expires_at < now)
                )
                expired_entries = result.scalars().all()

                for entry in expired_entries:
                    quarantine_path = entry.quarantine_path

                    if os.path.exists(quarantine_path):
                        try:
                            os.remove(quarantine_path)
                            logger.info(f"Purged expired quarantined file: {quarantine_path}")
                        except OSError as e:
                            logger.warning(f"Failed to delete quarantined file {quarantine_path}: {e}")
                            # Continue to delete DB row to avoid infinite loops if file is missing/locked

                    await session.delete(entry)

                if expired_entries:
                    await session.commit()
                    logger.info(f"Purged {len(expired_entries)} expired triage entries.")

        except Exception as e:
            logger.error(f"Error in triage daemon loop: {e}")

        # Poll every 1 hour
        await asyncio.sleep(3600)
