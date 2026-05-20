import os
import shutil
import logging
from typing import Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.models import SystemSettings, MediaFile, TriageEntry

logger = logging.getLogger(__name__)

async def quarantine_file(db_session: AsyncSession, media_file_id: int) -> Tuple[bool, str]:
    """
    Moves a corrupted file to the quarantine directory, leaves a placeholder,
    and creates a TriageEntry in QUARANTINED state.
    """

    # 1. Get the media file
    result = await db_session.execute(select(MediaFile).where(MediaFile.id == media_file_id))
    media_file = result.scalars().first()

    if not media_file:
        return False, "Media file not found."

    original_path = media_file.filepath

    if not os.path.exists(original_path):
         return False, f"Original file missing: {original_path}"

    # 2. Get system settings for quarantine directory
    settings_result = await db_session.execute(
        select(SystemSettings.value).where(SystemSettings.key == "triage_directory")
    )
    triage_dir = settings_result.scalars().first()

    if not triage_dir:
        return False, "System settings 'triage_directory' not found."
    quarantine_dir = os.path.join(triage_dir, "quarantine")
    os.makedirs(quarantine_dir, exist_ok=True)

    filename = os.path.basename(original_path)
    quarantine_path = os.path.join(quarantine_dir, filename)

    # Add timestamp if file already exists in triage to prevent overwriting evidence
    if os.path.exists(quarantine_path):
        import time
        quarantine_path = os.path.join(quarantine_dir, f"{int(time.time())}_{filename}")

    # 3. Move the file
    try:
        shutil.move(original_path, quarantine_path)
    except OSError as e:
        logger.error(f"Failed to move file {original_path} to {quarantine_path}: {e}")
        return False, f"Failed to move file to quarantine: {e}"

    # 4. Leave a placeholder
    placeholder_path = f"{original_path}.kintsugi-quarantined.txt"
    try:
        with open(placeholder_path, "w") as f:
            f.write("This file was quarantined by Kintsugi-DAM due to detected corruption.")
    except OSError as e:
        logger.error(f"Failed to create placeholder {placeholder_path}: {e}")
        # Try to rollback move
        try:
             shutil.move(quarantine_path, original_path)
        except:
             pass
        return False, f"Failed to create placeholder: {e}"

    # 5. Create DB entry
    # Check if entry already exists to prevent duplicates
    triage_result = await db_session.execute(select(TriageEntry).where(TriageEntry.media_file_id == media_file_id))
    triage_entry = triage_result.scalars().first()

    if triage_entry:
        triage_entry.status = "QUARANTINED"
        triage_entry.quarantine_path = quarantine_path
        triage_entry.expires_at = None
    else:
        triage_entry = TriageEntry(
            media_file_id=media_file_id,
            original_path=original_path,
            quarantine_path=quarantine_path,
            status="QUARANTINED"
        )
        db_session.add(triage_entry)

    # Mark media file state as corrupted
    media_file.state = "corrupted"

    await db_session.commit()
    logger.info(f"Successfully quarantined {original_path} to {quarantine_path}")
    return True, "File quarantined successfully."
