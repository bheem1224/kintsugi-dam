import os
import logging
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .models import MediaFile

FEATURE_FLAG_AUTO_HEAL = False

logger = logging.getLogger(__name__)

async def prune_recycle_bin(db_session: AsyncSession):
    try:
        # 90-day threshold
        threshold_date = datetime.now() - timedelta(days=90)

        result = await db_session.execute(
            select(MediaFile).where(MediaFile.state == 'quarantined')
        )
        quarantined_files = result.scalars().all()

        for file in quarantined_files:
            # We use last_hashed_date as the proxy for when it was quarantined
            if file.last_hashed_date and file.last_hashed_date < threshold_date:
                try:
                    os.remove(file.filepath)
                    logger.info(f"Successfully pruned physical file: {file.filepath}")

                    # Delete the record if physical deletion succeeded
                    await db_session.delete(file)
                    logger.info(f"Removed database record for pruned file: {file.filepath}")

                except FileNotFoundError:
                    # File is already gone, proceed with deleting the database record
                    logger.warning(f"File {file.filepath} not found on disk, deleting DB record anyway.")
                    await db_session.delete(file)
                    logger.info(f"Removed database record for missing file: {file.filepath}")

                except (PermissionError, OSError) as e:
                    # Cannot delete due to permissions or other OS issues. DO NOT delete DB record.
                    logger.error(f"Failed to remove physical file {file.filepath} due to OS error: {e}. Skipping DB record deletion.")

        await db_session.commit()

    except Exception as e:
        logger.error(f"An unexpected error occurred during recycle bin pruning: {e}")
        await db_session.rollback()

async def execute_auto_heal(db_session: AsyncSession):
    if not FEATURE_FLAG_AUTO_HEAL:
        return
    logger.info("Auto-heal triggered but feature is hard-locked for Beta")
