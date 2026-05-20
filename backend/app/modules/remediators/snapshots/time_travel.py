import os
import shutil
import asyncio
import logging
from pathlib import Path
from typing import Optional

from sqlalchemy import select

from app.core.nexus import nexus_bus
from app.core.database import async_session_maker as SessionLocal
from app.core.models import SystemSettings
from app.core.scanner import FileScanner
from .heuristic import heuristic_resolver

logger = logging.getLogger(__name__)

async def copy_file_async(src: str, dst: str):
    def _sync_copy():
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
    await asyncio.to_thread(_sync_copy)

async def remediate_via_snapshots(corrupted_file_path: str) -> bool:
    """
    Time-travel snapshot remediation logic.
    """
    corrupted_path = Path(corrupted_file_path)

    async with SessionLocal() as db_session:
        result = await db_session.execute(select(SystemSettings).limit(1))
        settings = result.scalar_one_or_none()

        if not settings:
            logger.error("System settings not found for snapshot remediation.")
            await nexus_bus.broadcast("remediator:failed", {"path": corrupted_file_path})
            return False

        snapshot_mount_path = Path(settings.snapshot_mount_path)

    # Use Heuristic Resolver to get EXACT file paths across all available snapshots (newest to oldest)
    snapshot_versions = await asyncio.to_thread(
        heuristic_resolver.get_snapshot_versions, snapshot_mount_path, corrupted_path
    )

    if not snapshot_versions:
        logger.warning(f"No snapshot versions found for {corrupted_file_path}")
        await nexus_bus.broadcast("remediator:failed", {"path": corrupted_file_path})
        return False

    scanner = FileScanner()

    for snap_file in snapshot_versions:
        logger.info(f"Testing snapshot version: {snap_file}")

        # Pass the snapshot file to Scanner.scan() (runs structural/hash checks)
        scan_result = await scanner.scan(snap_file)

        if scan_result == "HEALTHY":
            logger.info(f"Found healthy snapshot version at: {snap_file}")

            # Copy to replacements directory
            quarantine_dir = Path(".kintsugi/quarantine/replacements")
            # Preserve folder structure or just filename? Usually just filename in replacements
            # if we have a flat quarantine, or maintain structure. Let's do a simple flat copy or hash-based.
            # We'll use the original filename to keep it simple but safe.
            replacement_path = quarantine_dir / corrupted_path.name

            await copy_file_async(str(snap_file), str(replacement_path))

            # Broadcast success
            await nexus_bus.broadcast("remediator:version_isolated", {
                "original_path": corrupted_file_path,
                "replacement_path": str(replacement_path),
                "source_snapshot": str(snap_file)
            })

            return True

    # If we get here, all snapshots were exhausted
    logger.warning(f"All snapshots exhausted for {corrupted_file_path}, none were healthy.")
    await nexus_bus.broadcast("remediator:failed", {"path": corrupted_file_path})
    return False
