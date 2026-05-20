import os
import time
import asyncio
import logging
from typing import Dict, Optional

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent, FileMovedEvent

from .database import async_session_maker
from .models import MediaFile
from .scanner import FileScanner
from pathlib import Path
from sqlalchemy import select

logger = logging.getLogger(__name__)

class SettlingQueue:
    def __init__(self, settle_time: float = 10.0):
        self.settle_time = settle_time
        self._queue: Dict[str, dict] = {}
        self._lock = asyncio.Lock()
        self._running = True

    async def add_or_update(self, filepath: str):
        if not os.path.isfile(filepath):
            return

        try:
            stat = os.stat(filepath)
            size = stat.st_size
            mtime = stat.st_mtime
        except OSError:
            return

        async with self._lock:
            self._queue[filepath] = {
                "size": size,
                "mtime": mtime,
                "timestamp": time.time()
            }

    async def process_queue(self):
        while self._running:
            await asyncio.sleep(2)

            now = time.time()
            ready_files = []

            async with self._lock:
                for filepath, data in list(self._queue.items()):
                    if now - data["timestamp"] >= self.settle_time:
                        # Verify it's truly stable by checking size again
                        try:
                            stat = os.stat(filepath)
                            if stat.st_size == data["size"]:
                                ready_files.append((filepath, stat.st_mtime, stat.st_size))
                                del self._queue[filepath]
                            else:
                                # Size changed, reset timer
                                self._queue[filepath] = {
                                    "size": stat.st_size,
                                    "mtime": stat.st_mtime,
                                    "timestamp": now
                                }
                        except OSError:
                            # File deleted or inaccessible, remove from queue
                            del self._queue[filepath]

            for filepath, mtime, size in ready_files:
                asyncio.create_task(self._scan_stable_file(filepath, mtime, size))

    async def _scan_stable_file(self, filepath: str, mtime: float, size: int):
        logger.info(f"File stable. Initiating hot-scan: {filepath}")

        loop = asyncio.get_running_loop()

        async with async_session_maker() as session:
            # Check DB record
            result = await session.execute(
                select(MediaFile).where(MediaFile.filepath == filepath)
            )
            record = result.scalars().first()

            # Use the existing _process_single_file which uses the semaphore
            _, new_mtime, new_size, _, file_hash, file_state, _ = await _process_single_file(
                filepath, mtime, size, record, loop
            )

            from datetime import datetime
            if record:
                record.mtime = new_mtime
                record.size = new_size
                record.sha256_hash = file_hash
                record.last_hashed_date = datetime.utcnow()
                record.state = file_state
            else:
                new_record = MediaFile(
                    filepath=filepath,
                    mtime=new_mtime,
                    size=new_size,
                    sha256_hash=file_hash,
                    last_hashed_date=datetime.utcnow(),
                    state=file_state,
                )
                session.add(new_record)

            await session.commit()

    def stop(self):
        self._running = False

class HotFolderHandler(FileSystemEventHandler):
    def __init__(self, settling_queue: SettlingQueue):
        self.settling_queue = settling_queue
        self.loop = asyncio.get_running_loop()

    def _trigger(self, event):
        if event.is_directory:
            return

        ext = os.path.splitext(event.src_path)[1].lower()
        if ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"]:
            # Schedule the update in the asyncio loop thread safely
            asyncio.run_coroutine_threadsafe(
                self.settling_queue.add_or_update(event.src_path),
                self.loop
            )

    def on_created(self, event):
        if isinstance(event, FileCreatedEvent):
            self._trigger(event)

    def on_modified(self, event):
        if isinstance(event, FileModifiedEvent):
            self._trigger(event)

    def on_moved(self, event):
        if isinstance(event, FileMovedEvent) and not event.is_directory:
            ext = os.path.splitext(event.dest_path)[1].lower()
            if ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"]:
                asyncio.run_coroutine_threadsafe(
                    self.settling_queue.add_or_update(event.dest_path),
                    self.loop
                )

class WatcherService:
    def __init__(self):
        self.observer: Optional[Observer] = None
        self.settling_queue: Optional[SettlingQueue] = None
        self.queue_task: Optional[asyncio.Task] = None
        self.current_path: Optional[str] = None

    def is_active(self) -> bool:
        if self.observer and self.observer.is_alive():
            return True
        return False

    def start(self, path: str):
        if not os.path.exists(path):
            logger.error(f"Cannot start watcher. Path does not exist: {path}")
            # If path doesn't exist, we just gracefully handle it and stay inactive
            return

        self.current_path = path

        self.settling_queue = SettlingQueue(settle_time=10.0)
        self.queue_task = asyncio.create_task(self.settling_queue.process_queue())

        handler = HotFolderHandler(self.settling_queue)
        self.observer = Observer()
        self.observer.schedule(handler, path, recursive=True)
        self.observer.start()
        logger.info(f"Watcher started on directory: {path}")

    def stop(self):
        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=2.0)
            self.observer = None
            logger.info("Watcher observer stopped.")

        if self.settling_queue:
            self.settling_queue.stop()

        if self.queue_task:
            self.queue_task.cancel()

    def restart(self, new_path: str):
        logger.info(f"Restarting watcher on new path: {new_path}")
        self.stop()
        self.start(new_path)
