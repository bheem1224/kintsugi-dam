import logging
import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel

from ..core.database import get_db
from ..core.models import MediaFile, SystemSettings, PluginConfig, User
from ..core.security import get_current_user
from .schemas import MediaFileResponse, AIRepairRequest, AIRepairResponse, SettingsUpdateRequest, PluginPatchRequest, PluginResponse
from ..core.models import User, Plugin
from ..core.config import settings as app_settings
from ..core.security import get_current_user


logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/files/corrupted", response_model=List[MediaFileResponse])
async def get_corrupted_files(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(MediaFile).where(MediaFile.state == "corrupted"))
    return result.scalars().all()


@router.post("/files/{file_id}/repair/ai", response_model=AIRepairResponse)
async def repair_file_ai(
    file_id: int, request: AIRepairRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    if request.provider == "cloud":
        result = await db.execute(select(SystemSettings))
        settings = result.scalars().first()

        if not settings or settings.cloud_credits < 1:
            raise HTTPException(status_code=402, detail="Insufficient cloud credits.")

        settings.cloud_credits -= 1
        await db.commit()
        logger.info(
            f"Deducted 1 cloud credit for file {file_id}. Remaining: {settings.cloud_credits}"
        )

        # Simulate AI repair
        return AIRepairResponse(status="success", message="Cloud AI repair initiated.")

    return AIRepairResponse(status="success", message="Local AI repair initiated.")


@router.get("/stats")
async def get_stats(request: Request, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    total_files_result = await db.execute(select(func.count(MediaFile.id)))
    total_files = total_files_result.scalar_one()

    corrupted_files_result = await db.execute(select(func.count(MediaFile.id)).where(MediaFile.state == "corrupted"))
    corrupted_files = corrupted_files_result.scalar_one()

    quarantined_files_result = await db.execute(select(func.count(MediaFile.id)).where(MediaFile.state == "pending_approval"))
    quarantined_files = quarantined_files_result.scalar_one()

    last_scan_result = await db.execute(select(func.max(MediaFile.last_hashed_date)))
    last_scan = last_scan_result.scalar_one()
    last_scan_time = last_scan.isoformat() if last_scan else None

    settings_result = await db.execute(select(SystemSettings).where(SystemSettings.id == 1))
    settings = settings_result.scalars().first()
    cloud_credits = settings.cloud_credits if settings else 0

    scheduler = request.app.state.scheduler
    current_scanner_state = "Sleeping"

    try:
        if getattr(scheduler, "_executors", None) and "default" in scheduler._executors:
            executor = scheduler._executors["default"]
            if hasattr(executor, "_instances") and executor._instances:
                current_scanner_state = "Scanning"
    except Exception:
        pass

    if current_scanner_state == "Sleeping":
        import os, json
        STATE_FILE = "data/scanner_state.json"
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r") as f:
                    state = json.load(f)
                    if state.get("stack", []):
                        current_scanner_state = "Scanning"
            except:
                pass

    watcher = request.app.state.watcher
    watcher_active = watcher.is_active() if watcher else False

    return {
        "total_files": total_files,
        "corrupted_files": corrupted_files,
        "total_quarantined": quarantined_files,
        "last_scan_time": last_scan_time,
        "cloud_credits": cloud_credits,
        "current_scanner_state": current_scanner_state,
        "watcher_active": watcher_active
    }

@router.post("/settings")
async def update_settings(request: Request, settings_req: SettingsUpdateRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    settings_result = await db.execute(select(SystemSettings).where(SystemSettings.id == 1))
    settings = settings_result.scalars().first()

    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")

    if settings_req.maintenance_start is not None:
        settings.maintenance_start = settings_req.maintenance_start
    if settings_req.maintenance_end is not None:
        settings.maintenance_end = settings_req.maintenance_end

    if settings_req.monitored_directory is not None and settings_req.monitored_directory != settings.monitored_directory:
        settings.monitored_directory = settings_req.monitored_directory
        # Restart the watcher with the new path
        watcher = request.app.state.watcher
        if watcher:
            watcher.restart(settings_req.monitored_directory)

    if settings_req.discord_webhook_url is not None:
        settings.discord_webhook_url = settings_req.discord_webhook_url
    if settings_req.ntfy_topic_url is not None:
        settings.ntfy_topic_url = settings_req.ntfy_topic_url
    if settings_req.auto_restore is not None:
        settings.auto_restore = settings_req.auto_restore
    if settings_req.auto_restore_cloud is not None:
        settings.auto_restore_cloud = settings_req.auto_restore_cloud
    if settings_req.auto_restore_ai is not None:
        settings.auto_restore_ai = settings_req.auto_restore_ai
    if settings_req.ai_use_kintsugi_cloud is not None:
        settings.ai_use_kintsugi_cloud = settings_req.ai_use_kintsugi_cloud
    if settings_req.retention_days is not None:
        settings.retention_days = settings_req.retention_days
    if settings_req.snapshot_mount_path is not None:
        settings.snapshot_mount_path = settings_req.snapshot_mount_path
    if settings_req.triage_directory is not None:
        settings.triage_directory = settings_req.triage_directory
    if settings_req.scan_intensity is not None:
        settings.scan_intensity = settings_req.scan_intensity
    if settings_req.is_setup_complete is not None:
        settings.is_setup_complete = settings_req.is_setup_complete

    if settings_req.plugins is not None:
        for plugin_name, is_active in settings_req.plugins.items():
            plugin_result = await db.execute(select(PluginConfig).where(PluginConfig.name == plugin_name))
            plugin = plugin_result.scalars().first()
            if plugin:
                plugin.is_active = is_active

    await db.commit()
    return {"status": "success"}

@router.get("/settings")
async def get_settings(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    settings_result = await db.execute(select(SystemSettings).where(SystemSettings.id == 1))
    settings = settings_result.scalars().first()

    plugins_result = await db.execute(select(PluginConfig))
    plugins = plugins_result.scalars().all()

    return {
        "settings": settings,
        "plugins": {p.name: p.is_active for p in plugins}
    }


class PathTestRequest(BaseModel):
    media_path: str
    triage_path: str

@router.post("/settings/test-paths")
async def test_paths(req: PathTestRequest, current_user: User = Depends(get_current_user)):
    results = {}
    
    # Test Media Path (Read Access)
    if os.path.exists(req.media_path):
        if os.access(req.media_path, os.R_OK):
            results["media"] = {"status": "ok", "message": "Read access verified."}
        else:
            results["media"] = {"status": "error", "message": "No read access."}
    else:
        results["media"] = {"status": "error", "message": "Path does not exist."}
        
    # Test Triage Path (Write Access)
    if not os.path.exists(req.triage_path):
        try:
            os.makedirs(req.triage_path, exist_ok=True)
        except Exception as e:
            results["triage"] = {"status": "error", "message": f"Cannot create directory: {str(e)}"}
            return results

    if os.access(req.triage_path, os.W_OK):
        results["triage"] = {"status": "ok", "message": "Write access verified."}
    else:
        results["triage"] = {"status": "error", "message": "No write access."}
        
    return results


class FSBrowseResponse(BaseModel):
    name: str
    type: str
    path: str

class FSScanRequest(BaseModel):
    path: str

@router.get("/fs/browse", response_model=List[FSBrowseResponse])
async def browse_fs(path: str = "/media", current_user: User = Depends(get_current_user)):
    # Security: Ensure absolute path boundary
    # In a real scenario, use actual mounts. For this prompt, /media is the hard boundary.
    base_dir = os.path.abspath("/media")
    target_dir = os.path.abspath(path)

    if os.path.commonpath([base_dir, target_dir]) != base_dir:
        raise HTTPException(status_code=403, detail="Directory traversal attempt blocked.")

    if not os.path.exists(target_dir) or not os.path.isdir(target_dir):
        # If /media doesn't exist locally during dev, fake it or raise 404
        if path == "/media" and not os.path.exists("/media"):
            return [] # Failsafe for dev environment without actual /media
        raise HTTPException(status_code=404, detail="Directory not found.")

    results = []
    try:
        with os.scandir(target_dir) as entries:
            for entry in entries:
                if entry.is_dir(follow_symlinks=False):
                    results.append({"name": entry.name, "type": "directory", "path": entry.path})
                elif entry.is_file(follow_symlinks=False):
                    ext = os.path.splitext(entry.name)[1].lower()
                    if ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"]:
                        results.append({"name": entry.name, "type": "file", "path": entry.path})
    except OSError:
        raise HTTPException(status_code=500, detail="Cannot read directory.")

    # Sort directories first, then files alphabetically
    results.sort(key=lambda x: (0 if x["type"] == "directory" else 1, x["name"].lower()))
    return results

from ..core.scanner import FileScanner
from ..core.remediation import remediate_from_snapshot


@router.post("/fs/scan")
async def scan_fs(
    req: FSScanRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    base_dir = os.path.abspath("/media")
    target_dir = os.path.abspath(req.path)

    if os.path.commonpath([base_dir, target_dir]) != base_dir:
        raise HTTPException(status_code=403, detail="Directory traversal attempt blocked.")

    if not os.path.exists(target_dir) or not os.path.isdir(target_dir):
        if req.path == "/media" and not os.path.exists("/media"):
            return {"status": "success", "message": "Dev fallback: no /media exists."}
        raise HTTPException(status_code=404, detail="Directory not found.")

    scheduler = request.app.state.scheduler
    is_running = False
    try:
        if getattr(scheduler, "_executors", None) and "default" in scheduler._executors:
            executor = scheduler._executors["default"]
            if hasattr(executor, "_instances") and executor._instances:
                is_running = True
    except Exception:
        pass

    if not is_running:
        STATE_FILE = "data/scanner_state.json"
        if os.path.exists(STATE_FILE):
            try:
                import json
                with open(STATE_FILE, "r") as f:
                    state = json.load(f)
                    if state.get("stack", []):
                        is_running = True
            except:
                pass

    if is_running:
        raise HTTPException(status_code=409, detail="A scan is already running.")

    # We need to run this as a background task.
    # run_scan requires an active db session. BackgroundTasks doesn't inherently manage async db sessions well if closed,
    # so we'll wrap it.

    from ..core.database import async_session_maker
    async def run_scan_bg(path_to_scan: str):
        async with async_session_maker() as session:
            await run_scan(path_to_scan, session)

    background_tasks.add_task(run_scan_bg, target_dir)
    return {"status": "success", "message": f"Scan initiated for {target_dir}"}

@router.post("/files/{file_id}/remediate/snapshot", response_model=AIRepairResponse)
async def remediate_file_snapshot(
    file_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get the file
    result = await db.execute(select(MediaFile).where(MediaFile.id == file_id))
    media_file = result.scalars().first()

    if not media_file:
        raise HTTPException(status_code=404, detail="File not found")

    # Get settings
    settings_result = await db.execute(select(SystemSettings).where(SystemSettings.id == 1))
    settings = settings_result.scalars().first()

    if not settings:
        raise HTTPException(status_code=500, detail="System settings not found")

    success, message = await remediate_from_snapshot(
        media_file.filepath,
        settings.snapshot_mount_path,
        settings.auto_restore
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    # Update DB state based on policy
    if settings.auto_restore:
        media_file.state = "clean"
    else:
        media_file.state = "pending_approval"

    await db.commit()

    return AIRepairResponse(status="success", message=message)

@router.patch("/plugins/{plugin_id}", response_model=PluginResponse)
async def update_plugin(
    plugin_id: str,
    request: PluginPatchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Plugin).where(Plugin.id == plugin_id))
    plugin = result.scalars().first()

    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")

    if request.channel is not None:
        if request.channel == "beta" and not app_settings.KINTSUGI_ENABLE_BETA_PLUGINS:
            raise HTTPException(status_code=403, detail="Beta plugins are currently disabled.")
        plugin.channel = request.channel

    if request.is_active is not None:
        plugin.is_active = request.is_active

    await db.commit()
    await db.refresh(plugin)
    return plugin
