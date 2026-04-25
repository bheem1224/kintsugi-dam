import os
import shutil
import asyncio
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

async def remediate_from_snapshot(
    file_path: str,
    snapshot_mount_path: str,
    auto_restore: bool
) -> Tuple[bool, str]:
    """
    Attempts to restore a file from a snapshot.
    Copies the corrupted file to the triage bin, then searches for a clean snapshot.
    If auto_restore is True, overwrites the live file.
    """

    # 1. Standardize paths
    base_media = os.path.abspath("/media")
    abs_file_path = os.path.abspath(file_path)

    corrupted_dir = os.path.abspath("/app/data/triage/corrupted")
    restored_dir = os.path.abspath("/app/data/triage/restored")

    os.makedirs(corrupted_dir, exist_ok=True)
    os.makedirs(restored_dir, exist_ok=True)

    # Verify the file is actually within the managed media directory
    if not abs_file_path.startswith(base_media):
        return False, "File is not within the managed /media directory."

    filename = os.path.basename(abs_file_path)

    # 2. Copy the corrupted file to the triage bin (Safety first)
    if os.path.exists(abs_file_path):
        corrupted_dest = os.path.join(corrupted_dir, filename)
        # Add timestamp if file already exists in triage to prevent overwriting evidence
        if os.path.exists(corrupted_dest):
            import time
            corrupted_dest = os.path.join(corrupted_dir, f"{int(time.time())}_{filename}")

        try:
            await asyncio.to_thread(shutil.copy2, abs_file_path, corrupted_dest)
        except OSError as e:
            logger.error(f"Failed to copy corrupted file to triage: {e}")
            return False, "Failed to isolate corrupted file."

    # 3. Resolve the snapshot path
    # Remove /media/ from the start to get the relative path
    rel_path = os.path.relpath(abs_file_path, base_media)
    snapshot_file_path = os.path.join(os.path.abspath(snapshot_mount_path), rel_path)

    if not os.path.exists(snapshot_file_path):
        return False, "No clean snapshot found for this file."

    # 4. Copy the snapshot to the triage restored folder
    restored_dest = os.path.join(restored_dir, filename)
    try:
        await asyncio.to_thread(shutil.copy2, snapshot_file_path, restored_dest)
    except OSError as e:
        logger.error(f"Failed to retrieve snapshot: {e}")
        return False, "Failed to retrieve snapshot from mount."

    # 5. Apply State Machine Policy
    if auto_restore:
        try:
            await asyncio.to_thread(shutil.copy2, restored_dest, abs_file_path)
            logger.info(f"Auto-restored {filename} from snapshot.")
            return True, "File auto-restored successfully."
        except OSError as e:
            logger.error(f"Failed to overwrite live file: {e}")
            return False, "Failed to auto-restore into live directory."
    else:
        logger.info(f"Snapshot retrieved to {restored_dest}, pending manual approval.")
        return True, "Snapshot retrieved to Triage. Pending manual approval."
