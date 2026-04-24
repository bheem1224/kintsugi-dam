import os
import json
import asyncio
import logging
from datetime import datetime, time
from typing import List, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .models import MediaFile
from .hashing import calculate_sha256, hash_pool
from app.plugins.detectors.jpeginfo import JpegInfoDetector
from app.plugins.detectors.pillow_deep_scan import PillowDeepScanDetector

logger = logging.getLogger(__name__)

STATE_FILE = "data/scanner_state.json"

# Toaster Philosophy: Limit concurrent subprocesses to avoid crashing low-end servers
CONCURRENCY_LIMIT = 4
detector_semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)


def is_within_timebox(current_time: time, start_time: time, end_time: time) -> bool:
    """
    Checks if the current time is within the allowed window.
    Handles maintenance windows that cross midnight.
    """
    if start_time < end_time:
        return start_time <= current_time <= end_time
    else:
        # Crosses midnight (e.g., 23:00 to 04:00)
        return current_time >= start_time or current_time <= end_time


async def run_scan(
    target_dir: str,
    db_session: AsyncSession,
    start_time: Optional[time] = None,
    end_time: Optional[time] = None,
) -> Dict[str, str]:
    """
    Walks the target directory, compares file metadata against the database,
    and calculates SHA-256 hashes concurrently for new or modified files.
    Respects the provided timebox and pauses if the window is exceeded.
    """
    batch = []
    stack = []

    root_dir_abs = os.path.abspath(target_dir)

    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                state = json.load(f)
                stack = state.get("stack", [])
            os.remove(STATE_FILE)
        except Exception:
            stack = [target_dir]
    else:
        stack = [target_dir]

    # 1. Walk the directory statelessly using os.scandir and a stack
    while stack:
        current_dir = stack.pop()
        try:
            # Use os.scandir for cached stats
            with os.scandir(current_dir) as entries:
                for entry in entries:
                    entry_abs_path = os.path.abspath(entry.path)

                    # Directory Jail Enforcement
                    if (
                        os.path.commonpath([root_dir_abs, entry_abs_path])
                        != root_dir_abs
                    ):
                        logger.critical(
                            f"Security Alert: Path traversal attempt blocked: {entry.path} escaped root {target_dir}"
                        )
                        continue

                    if entry.is_dir(follow_symlinks=False):
                        stack.append(entry.path)
                    elif entry.is_file(follow_symlinks=False):
                        filepath = entry.path

                        try:
                            stat = entry.stat()
                        except OSError:
                            continue  # Skip if file cannot be accessed

                        mtime = stat.st_mtime
                        size = stat.st_size

                        # Check DB for existing record
                        result = await db_session.execute(
                            select(MediaFile).where(MediaFile.filepath == filepath)
                        )
                        record = result.scalars().first()

                        if record and record.mtime == mtime and record.size == size:
                            continue  # Up-to-date, skip

                        # New or modified, queue for hashing
                        batch.append((filepath, mtime, size, record))

                        # The Trigger: Process batch of 100
                        if len(batch) >= 100:
                            await _process_batch(batch, db_session)
                            batch.clear()  # Empty the batch list

                            # Check timebox
                            if start_time and end_time:
                                now = datetime.now().time()
                                if not is_within_timebox(now, start_time, end_time):
                                    await db_session.close()
                                    # Save state before pausing
                                    os.makedirs("data", exist_ok=True)
                                    with open(STATE_FILE, "w") as f:
                                        json.dump({"stack": stack}, f)
                                    return {"status": "paused"}
        except OSError:
            continue  # Skip directory if cannot be accessed

    # Process any remaining files in the batch
    if batch:
        await _process_batch(batch, db_session)

    # Even if timebox expired after the last batch, we finished the whole scan.
    # Therefore, return completed.
    return {"status": "completed"}


async def _process_single_file(
    filepath: str,
    mtime: float,
    size: int,
    record: Optional[MediaFile],
    loop: asyncio.AbstractEventLoop,
) -> tuple:
    # Hash the file
    file_hash = await loop.run_in_executor(hash_pool, calculate_sha256, filepath)

    # Only run detectors on image files for now
    ext = os.path.splitext(filepath)[1].lower()
    is_image = ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"]

    file_state = "clean"
    error_msg = ""

    if is_image:
        async with detector_semaphore:
            # First line of defense: JpegInfo
            jpeg_detector = JpegInfoDetector()
            is_clean, msg = await jpeg_detector.analyze(filepath)

            if not is_clean:
                file_state = "corrupted"
                error_msg = msg
            else:
                # Fallback consensus check: Pillow Deep Scan
                pillow_detector = PillowDeepScanDetector()
                is_clean_pillow, msg_pillow = await pillow_detector.analyze(filepath)
                if not is_clean_pillow:
                    file_state = "corrupted"
                    error_msg = msg_pillow

    return filepath, mtime, size, record, file_hash, file_state, error_msg


async def _process_batch(batch: List[tuple], db_session: AsyncSession) -> None:
    """Helper function to hash a batch of files, run detections, and update the database."""
    if not batch:
        return

    loop = asyncio.get_running_loop()

    # Map the CPU-bound hashing and scanning functions concurrently
    tasks = [
        _process_single_file(filepath, mtime, size, record, loop)
        for filepath, mtime, size, record in batch
    ]
    results = await asyncio.gather(*tasks)

    # Update the database
    for filepath, mtime, size, record, file_hash, file_state, error_msg in results:
        if record:
            # Update existing record
            record.mtime = mtime
            record.size = size
            record.sha256_hash = file_hash
            record.last_hashed_date = datetime.utcnow()
            record.state = file_state
        else:
            # Create new record
            new_record = MediaFile(
                filepath=filepath,
                mtime=mtime,
                size=size,
                sha256_hash=file_hash,
                last_hashed_date=datetime.utcnow(),
                state=file_state,
            )
            db_session.add(new_record)

    # Commit changes
    await db_session.commit()
