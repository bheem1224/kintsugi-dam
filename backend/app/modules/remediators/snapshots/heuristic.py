import os
import re
from pathlib import Path
from typing import Optional, Tuple, List
import logging

logger = logging.getLogger(__name__)

class SnapshotHeuristicResolver:
    """
    Dynamically figures out how live file paths map to snapshot mount directories.
    Identifies the path transformation pattern once and caches a compiled regex
    to instantly resolve subsequent lookups without recursion or brute-force scanning.
    """
    def __init__(self):
        # Format: (compiled_regex, snapshot_base_directory)
        self._cached_pattern: Optional[Tuple[re.Pattern, Path]] = None

    def get_snapshot_versions(self, snapshot_mount_path: Path, corrupted_path: Path) -> List[Path]:
        """
        Returns a list of EXACT paths to the snapshot versions of the corrupted file,
        sorted from NEWEST to OLDEST.
        """
        if not snapshot_mount_path.exists():
            return []

        resolved = self._resolve_via_pattern(snapshot_mount_path, corrupted_path)
        if not resolved:
            return []

        dataset_base, rel_path = resolved

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
            snap_file = snap / rel_path
            if snap_file.exists():
                exact_paths.append(snap_file)

        return exact_paths

    def _resolve_via_pattern(self, snapshot_mount_path: Path, corrupted_path: Path) -> Optional[Tuple[Path, Path]]:
        # 1. Check if we have a compiled regex cache
        corrupted_posix = corrupted_path.as_posix()
        if self._cached_pattern:
            pattern, dataset_base = self._cached_pattern
            match = pattern.match(corrupted_posix)
            if match:
                rel_path = Path(match.group("rel_path"))
                return dataset_base, rel_path

        # 2. Cache miss: perform structural discovery
        discovery = self._discover_structure(snapshot_mount_path, corrupted_path)
        if not discovery:
            return None

        live_prefix, dataset_base, rel_path = discovery

        # 3. Compile and cache a regex pattern matching the live prefix and capturing the relative path
        escaped_prefix = re.escape(live_prefix.as_posix())
        pattern_str = f"^{escaped_prefix}/?(?P<rel_path>.+)$"
        
        self._cached_pattern = (re.compile(pattern_str, re.IGNORECASE), dataset_base)
        
        return dataset_base, rel_path

    def _discover_structure(self, base_dir: Path, target_file: Path, max_depth: int = 3) -> Optional[Tuple[Path, Path, Path]]:
        """
        Performs a single-pass recursive discovery to find a snapshot containing the target file.
        Returns: (live_prefix_path, dataset_base_path, relative_path_from_snapshot_to_file)
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
                test_snap = Path(snapshot_dirs[0].path)

                parts = target_file.parts
                for i in range(len(parts)):
                    rel_suffix = Path(*parts[i:])
                    if rel_suffix.is_absolute():
                        try:
                            rel_suffix = rel_suffix.relative_to(rel_suffix.anchor)
                        except ValueError:
                            pass

                    test_file = test_snap / rel_suffix
                    if test_file.exists():
                        live_prefix = Path(*parts[:i])
                        return (live_prefix, current_dir, rel_suffix)

            # Recurse deeper into directories
            for entry in snapshot_dirs:
                res = search_recursive(Path(entry.path), current_depth + 1)
                if res:
                    return res

            return None

        return search_recursive(base_dir, 0)

# Global singleton instance
heuristic_resolver = SnapshotHeuristicResolver()
