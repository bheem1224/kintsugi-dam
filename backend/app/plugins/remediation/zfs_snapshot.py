import os
import asyncio
import shutil
from typing import Optional
from pathlib import Path
from app.plugins.base import RemediationProvider


class ZFSRemediation(RemediationProvider):
    def get_name(self) -> str:
        return "ZFS_Snapshot"

    async def find_clean_version(
        self, file_path: str, known_good_hash: str
    ) -> Optional[str]:
        """
        Searches the backup source for a clean version of the file using mtime.
        The known_good_hash argument from base class is treated as known_good_mtime here based on instructions.
        """
        # Convert known_good_hash argument to float since the request mentioned mtime
        try:
            target_mtime = float(known_good_hash)
        except ValueError:
            return None

        def _sync_find() -> Optional[str]:
            # This is a naive heuristic to find the mount point.
            # Real-world use might require configuration for the exact ZFS dataset mount.
            # Assuming the library is mounted at some base directory that contains .zfs

            p = Path(file_path).resolve()

            # Walk up to find .zfs directory
            mount_point = None
            current = p
            while current != current.parent:
                if (current / ".zfs").is_dir():
                    mount_point = current
                    break
                current = current.parent

            if not mount_point:
                return None

            snapshots_dir = mount_point / ".zfs" / "snapshot"
            if not snapshots_dir.is_dir():
                return None

            # Get relative path from mount point
            rel_path = p.relative_to(mount_point)

            # Find all snapshot directories
            best_match = None
            best_match_time_diff = float("inf")

            try:
                snapshots = [d for d in snapshots_dir.iterdir() if d.is_dir()]
            except OSError:
                return None

            # Iterate through snapshots to find the file
            for snap in snapshots:
                snap_file_path = snap / rel_path
                if snap_file_path.is_file():
                    try:
                        stat = snap_file_path.stat()
                        mtime = stat.st_mtime

                        # We want the most recent version that matches or is older than the known good mtime
                        # (allowing a small tolerance for filesystem precision issues)
                        if mtime <= target_mtime + 1.0:
                            diff = target_mtime - mtime
                            # Keep the snapshot with mtime closest to our target
                            if diff < best_match_time_diff:
                                best_match_time_diff = diff
                                best_match = str(snap_file_path)
                    except OSError:
                        continue

            return best_match

        return await asyncio.to_thread(_sync_find)

    async def restore_file(self, backup_uri: str, live_destination: str) -> bool:
        def _sync_restore() -> bool:
            try:
                # Ensure destination directory exists
                os.makedirs(os.path.dirname(live_destination), exist_ok=True)
                # Copy file from snapshot to live destination
                shutil.copy2(backup_uri, live_destination)
                return True
            except OSError:
                return False

        return await asyncio.to_thread(_sync_restore)
