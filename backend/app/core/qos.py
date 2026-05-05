import psutil
import asyncio

class QoSManager:
    _last_disk_io = None

    @classmethod
    async def should_yield(cls) -> bool:
        """
        Checks if the CPU or Disk IO usage is too high, indicating Kintsugi should yield.
        """
        loop = asyncio.get_running_loop()

        def _check_metrics():
            # Check CPU
            cpu = psutil.cpu_percent(interval=0.1)
            if cpu > 75.0:
                return True

            # Check Disk
            current_io = psutil.disk_io_counters()
            if not current_io:
                return False

            if cls._last_disk_io is None:
                cls._last_disk_io = current_io
                return False

            # Calculate diff
            read_diff = current_io.read_bytes - cls._last_disk_io.read_bytes
            write_diff = current_io.write_bytes - cls._last_disk_io.write_bytes

            cls._last_disk_io = current_io

            # Massive external read/write activity (e.g. > 50MB/s) -> let's say 50 * 1024 * 1024
            # Since interval=0.1s, 50MB/s is 5MB in 0.1s
            if read_diff > 5 * 1024 * 1024 or write_diff > 5 * 1024 * 1024:
                return True

            return False

        return await loop.run_in_executor(None, _check_metrics)
