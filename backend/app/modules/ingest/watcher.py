import os
import time
import asyncio
import logging
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent, FileMovedEvent

from app.core.database import async_session_maker
from app.core.models import MediaFile
from app.core.scanner import FileScanner
from app.core.settings_manager import SettingsManager
from app.core.image_utils import Image

logger = logging.getLogger(__name__)

def extract_exif_date_taken(filepath: str) -> Optional[datetime]:
    try:
        with Image.open(filepath) as img:
            exif = img.getexif()
            if exif:
                # 36867 is DateTimeOriginal
                date_str = exif.get(36867)
                if date_str:
                    # Format is usually YYYY:MM:DD HH:MM:SS
                    return datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
    except Exception as e:
        logger.debug(f"Could not extract EXIF date from {filepath}: {e}")
    return None

class TieredSettlingQueue:
    def __init__(self, settle_time: float = 10.0):
        self.settle_time = settle_time
        self._queue: Dict[str, dict] = {}
        self._lock = asyncio.Lock()
        self._running = True
        self.scanner = FileScanner()

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
                        try:
                            stat = os.stat(filepath)
                            if stat.st_size == data["size"]:
                                ready_files.append((filepath, stat.st_mtime, stat.st_size))
                                del self._queue[filepath]
                            else:
                                self._queue[filepath] = {
                                    "size": stat.st_size,
                                    "mtime": stat.st_mtime,
                                    "timestamp": now
                                }
                        except OSError:
                            del self._queue[filepath]

            for filepath, mtime, size in ready_files:
                asyncio.create_task(self._process_stable_file(filepath))

    async def _process_stable_file(self, filepath: str):
        logger.info(f"File stable for ingest: {filepath}")

        library_root = await SettingsManager.get("library_directory", "/media/library")
        date_taken = await asyncio.to_thread(extract_exif_date_taken, filepath)

        if date_taken:
            template = await SettingsManager.get("ingest_folder_template", "%Y/%m")
            try:
                folder_path = date_taken.strftime(template)
            except ValueError:
                folder_path = date_taken.strftime("%Y/%m")
        else:
            template = await SettingsManager.get("fallback_folder_template", "Fallback/%Y/%m")
            try:
                mtime = os.stat(filepath).st_mtime
                fallback_date = datetime.fromtimestamp(mtime)
                folder_path = fallback_date.strftime(template)
            except (OSError, ValueError):
                folder_path = "Fallback/Unknown"

        target_dir = os.path.join(library_root, folder_path)
        os.makedirs(target_dir, exist_ok=True)

        filename = os.path.basename(filepath)
        target_path = os.path.join(target_dir, filename)

        # Avoid overwriting if file exists, add timestamp
        if os.path.exists(target_path) and os.path.abspath(filepath) != os.path.abspath(target_path):
            base, ext = os.path.splitext(filename)
            timestamp = int(time.time())
            target_path = os.path.join(target_dir, f"{base}_{timestamp}{ext}")

        if os.path.abspath(filepath) != os.path.abspath(target_path):
            try:
                await asyncio.to_thread(shutil.move, filepath, target_path)
                logger.info(f"Moved {filepath} to {target_path}")
            except Exception as e:
                logger.error(f"Failed to move file {filepath}: {e}")
                return

        # Pass to scanner
        async with async_session_maker() as session:
            await self.scanner.process_file(Path(target_path), session)

    def stop(self):
        self._running = False

class TieredHotFolderHandler(FileSystemEventHandler):
    def __init__(self, settling_queue: TieredSettlingQueue):
        self.settling_queue = settling_queue
        self.loop = asyncio.get_running_loop()

    def _trigger(self, event):
        if event.is_directory:
            return

        ext = os.path.splitext(event.src_path)[1].lower()
        if ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"]:
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

class TieredWatcherDaemon:
    def __init__(self):
        self.observers: List[Observer] = []
        self.settling_queue: Optional[TieredSettlingQueue] = None
        self.queue_task: Optional[asyncio.Task] = None
        self.watched_paths: List[str] = []
        self._monitoring_task: Optional[asyncio.Task] = None

    async def _get_watch_directories(self) -> List[str]:
        tier = await SettingsManager.get("license_tier", "free")
        paths = []

        primary = await SettingsManager.get("watch_directory_primary")
        if primary:
            paths.append(primary)

        if tier in ["pro", "studio"]:
            extra = await SettingsManager.get("watch_directories_extra")
            if isinstance(extra, list):
                paths.extend(extra)
            elif isinstance(extra, str) and extra:
                try:
                    import json
                    parsed = json.loads(extra)
                    if isinstance(parsed, list):
                        paths.extend(parsed)
                except Exception:
                    pass

        return list(set(paths)) # Remove duplicates

    async def _monitor_settings(self):
        while True:
            await asyncio.sleep(60) # Check every minute
            try:
                new_paths = await self._get_watch_directories()
                if set(new_paths) != set(self.watched_paths):
                    logger.info("Watch directories changed. Reloading watcher daemon...")
                    await self.restart()
            except Exception as e:
                logger.error(f"Error checking watch directories: {e}")

    async def start(self):
        self.watched_paths = await self._get_watch_directories()

        if not self.watched_paths:
            logger.warning("No watch directories configured. Watcher daemon idle.")
            return

        self.settling_queue = TieredSettlingQueue(settle_time=10.0)
        self.queue_task = asyncio.create_task(self.settling_queue.process_queue())
        handler = TieredHotFolderHandler(self.settling_queue)

        for path in self.watched_paths:
            if os.path.exists(path):
                observer = Observer()
                observer.schedule(handler, path, recursive=True)
                observer.start()
                self.observers.append(observer)
                logger.info(f"Watcher started on directory: {path}")
            else:
                logger.warning(f"Watch directory does not exist: {path}")

        if not self._monitoring_task:
            self._monitoring_task = asyncio.create_task(self._monitor_settings())

    def stop(self):
        for observer in self.observers:
            if observer.is_alive():
                observer.stop()
                observer.join(timeout=2.0)
        self.observers.clear()

        if self.settling_queue:
            self.settling_queue.stop()

        if self.queue_task:
            self.queue_task.cancel()

        logger.info("Tiered watcher daemon stopped.")

    async def restart(self):
        self.stop()
        await self.start()
