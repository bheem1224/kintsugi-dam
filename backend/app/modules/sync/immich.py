import logging
from sqlalchemy import select
from app.core.database import async_session_maker
from app.core.models import MediaFile
from .base import ISyncProvider

logger = logging.getLogger(__name__)

class ImmichSyncProvider(ISyncProvider):
    async def handle_deletion(self, payload: dict):
        """
        Parses Immich webhook payload and performs a "Ghost Deletion"
        (removes the file from Kintsugi database/scanner queue without triggering corruption alert).
        """
        try:
            # Immich webhook payload structure logic goes here
            # Assuming payload contains the asset path
            # Typical Immich webhook for asset deletion:
            # { "event": "asset.deleted", "asset": { "originalPath": "/path/to/file.jpg" } }

            asset = payload.get("asset", {})
            file_path = asset.get("originalPath")

            if not file_path:
                logger.warning(f"ImmichSyncProvider: No file path found in payload: {payload}")
                return

            logger.info(f"ImmichSyncProvider: Processing deletion for {file_path}")

            async with async_session_maker() as session:
                result = await session.execute(
                    select(MediaFile).where(MediaFile.filepath == file_path)
                )
                record = result.scalars().first()

                if record:
                    await session.delete(record)
                    await session.commit()
                    logger.info(f"ImmichSyncProvider: Ghost deleted record for {file_path}")
                else:
                    logger.debug(f"ImmichSyncProvider: Record not found for {file_path}, nothing to delete")

        except Exception as e:
            logger.error(f"ImmichSyncProvider error handling deletion: {e}")
