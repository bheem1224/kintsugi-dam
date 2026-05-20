import os
from pathlib import Path
from typing import Optional, Dict, Tuple, List
import logging

logger = logging.getLogger(__name__)

class SnapshotHeuristicResolver:
    """
    Dynamically figures out how live file paths map to snapshot mount directories.
    Caches the exact relative path offset so future lookups are instant.
    """
    def __init__(self):
        # Maps a live file's parent directory (str) to a tuple of:
        # (snapshot_dataset_base_path, relative_path_offset)
        self._pattern_cache: Dict[str, Tuple[Path, Path]] = {}

    def get_snapshot_versions(self, snapshot_mount_path: Path, corrupted_path: Path) -> List[Path]:
        """
        Returns a list of EXACT paths to the snapshot versions of the corrupted file,
        sorted from NEWEST to OLDEST.
        """
        if not snapshot_mount_path.exists():
            return []

        mapping = self._resolve_dataset_mapping(snapshot_mount_path, corrupted_path)
        if not mapping:
            return []

        dataset_base, relative_offset = mapping

        # Find all snapshot folders inside the dataset_base
        snapshots = []
        try:
            for entry in os.scandir(dataset_base):
                if entry.is_dir():
                    snapshots.append(Path(entry.path))
        except OSError:
            pass

        # Sort newest to oldest based on modification time
        snapshots.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        # Construct the exact file paths in each snapshot
        exact_paths = []
        for snap in snapshots:
            snap_file = snap / relative_offset
            if snap_file.exists():
                exact_paths.append(snap_file)

        return exact_paths

    def _resolve_dataset_mapping(self, snapshot_mount_path: Path, corrupted_path: Path) -> Optional[Tuple[Path, Path]]:
        live_dir = str(corrupted_path.parent)

        if live_dir in self._pattern_cache:
            return self._pattern_cache[live_dir]

        # Cache miss. Shallow heuristic search.
        result = self._shallow_search(snapshot_mount_path, corrupted_path)
        if result:
            # Cache the pattern for this specific parent directory
            dataset_base, test_snap, rel_suffix = result

            # rel_suffix is the path from the snapshot root to the file.
            # We want to cache the offset from the snapshot root to the parent directory.
            dir_offset = rel_suffix.parent

            self._pattern_cache[live_dir] = (dataset_base, rel_suffix)
            return (dataset_base, rel_suffix)

        return None

    def _shallow_search(self, base_dir: Path, target_file: Path, max_depth: int = 3) -> Optional[Tuple[Path, Path, Path]]:
        """
        Searches for a snapshot containing the target file.
        Returns (dataset_base, a_snapshot_dir, relative_path_from_snapshot_to_file)
        """
        def search_recursive(current_dir: Path, current_depth: int) -> Optional[Tuple[Path, Path, Path]]:
            if current_depth > max_depth:
                return None

            try:
                entries = list(os.scandir(current_dir))
            except OSError:
                return None

            snapshot_dirs = [e for e in entries if e.is_dir()]
            if snapshot_dirs:
                # Test the first snapshot directory
                test_snap = Path(snapshot_dirs[0].path)

                parts = target_file.parts
                # Try all possible relative suffixes by stripping prefixes
                for i in range(len(parts)):
                    rel_suffix = Path(*parts[i:])
                    if rel_suffix.is_absolute():
                        # Remove the leading anchor (e.g. /)
                        try:
                            rel_suffix = rel_suffix.relative_to(rel_suffix.anchor)
                        except ValueError:
                            pass

                    test_file = test_snap / rel_suffix
                    if test_file.exists():
                        return (current_dir, test_snap, rel_suffix)

            # Recurse deeper into directories
            for entry in snapshot_dirs:
                res = search_recursive(Path(entry.path), current_depth + 1)
                if res:
                    return res

            return None

        return search_recursive(base_dir, 0)

# Global singleton instance
heuristic_resolver = SnapshotHeuristicResolver()
