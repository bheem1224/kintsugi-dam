import os
from pathlib import Path
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/fs", tags=["filesystem"])

# Internal directories to hide
HIDDEN_DIRS = {"/app", "/bin", "/usr", "/sys", "/proc", "/lib", "/etc", "/dev", "/run", "/var", "/tmp", "/boot", "/home", "/root", "/sbin", "/srv", "/lib64", "/opt"}

@router.get("/explore")
async def explore_fs(path: str = Query("/", description="Path to explore")):
    # Ensure path is absolute and within container
    try:
        target_path = Path(path).resolve()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid path")

    if not target_path.is_absolute():
        raise HTTPException(status_code=400, detail="Path must be absolute")

    if not target_path.exists():
        raise HTTPException(status_code=404, detail="Directory not found")

    if not target_path.is_dir():
        raise HTTPException(status_code=400, detail="Path is not a directory")

    items = []
    try:
        for entry in os.scandir(target_path):
            entry_path_str = entry.path

            # Hide internal system folders if we are exploring root or their direct parents
            # More strictly: if the entry starts with any HIDDEN_DIRS (as an exact directory match), we skip it.
            # e.g. entry_path_str == "/app" -> skip
            should_hide = False
            for hidden in HIDDEN_DIRS:
                if entry_path_str == hidden or entry_path_str.startswith(hidden + "/"):
                    should_hide = True
                    break

            if should_hide:
                continue

            try:
                stat = entry.stat()
                items.append({
                    "name": entry.name,
                    "path": entry_path_str,
                    "is_dir": entry.is_dir(),
                    "size": stat.st_size if not entry.is_dir() else 0,
                    "mtime": stat.st_mtime
                })
            except (OSError, PermissionError):
                # Skip files/dirs we can't stat
                pass

    except (OSError, PermissionError) as e:
         raise HTTPException(status_code=403, detail=f"Permission denied accessing directory: {str(e)}")

    # Sort: directories first, then alphabetically
    items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))

    return {
        "current_path": str(target_path),
        "parent_path": str(target_path.parent) if str(target_path) != "/" else None,
        "items": items
    }
