import os
import asyncio
import logging
from datetime import datetime
from typing import Optional
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .models import MediaFile
from .nexus import nexus_bus

# Import the new Rust hasher
import kintsugi_rs

logger = logging.getLogger(__name__)

class FileScanner:
    """
    High-performance Ingestion Engine.
    Leverages Rust blake3 streaming for minimal RAM footprint.
    """

    async def process_file(self, file_path: Path, db_session: AsyncSession):
        """
        Hashes a file, compares it to the database, and updates its state.
        """
        path_str = str(file_path)

        # 1. Check if file exists on disk
        if not file_path.exists():
            logger.warning(f"File missing during scan: {path_str}")
            return

        try:
            stat = file_path.stat()
            mtime = stat.st_mtime
            size = stat.st_size
        except OSError as e:
            logger.error(f"Cannot stat file {path_str}: {e}")
            return

        # 2. Hash the file via Rust (async/non-blocking)
        try:
            new_hash = await asyncio.to_thread(kintsugi_rs.calculate_blake3, path_str)
        except Exception as e:
            logger.error(f"Failed to hash {path_str}: {e}")
            return

        # 3. Query the DB
        result = await db_session.execute(select(MediaFile).where(MediaFile.filepath == path_str))
        record = result.scalars().first()

        now = datetime.now()

        if not record:
            # New file
            new_record = MediaFile(
                filepath=path_str,
                mtime=mtime,
                size=size,
                sha256_hash=new_hash,
                last_scanned_at=now,
                state="healthy"
            )
            db_session.add(new_record)
            logger.debug(f"Inserted new healthy file: {path_str}")
        else:
            # Existing file: Compare hashes
            if record.sha256_hash == new_hash:
                # Hash matches, update last_scanned_at
                record.last_scanned_at = now
                if record.state == "corrupted":
                    # In case it was previously marked corrupted but is now fine (e.g. replaced)
                    record.state = "healthy"
            else:
                # Hash mismatch -> Corrupted
                record.sha256_hash = new_hash
                record.last_scanned_at = now
                record.state = "corrupted"
                logger.warning(f"CORRUPTION DETECTED: {path_str}")
                await nexus_bus.broadcast("file_corrupted", {"path": path_str})

        # Commit the transaction
        await db_session.commit()
