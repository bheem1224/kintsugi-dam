import os
import shutil
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.database import get_db
from app.core.models import User, TriageEntry, MediaFile, SystemSettings
from app.api.auth import get_current_user
from app.core.security import require_permission
from app.core.nexus import nexus_bus
from app.modules.triage.core import quarantine_file

router = APIRouter(tags=["triage"])

class TriageEntryResponse(BaseModel):
    id: int
    media_file_id: int
    original_path: str
    quarantine_path: str
    status: str
    created_at: datetime
    expires_at: Optional[datetime]

    class Config:
        orm_mode = True

class ActionRequest(BaseModel):
    action: str # "APPROVE"

@router.get("/", response_model=List[TriageEntryResponse])
async def list_triage_entries(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(TriageEntry))
    return result.scalars().all()


@router.post("/{id}/action")
async def perform_triage_action(
    id: int,
    action_req: ActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _ = Depends(require_permission("triage:approve"))
):
    result = await db.execute(select(TriageEntry).where(TriageEntry.id == id))
    entry = result.scalars().first()

    if not entry:
        raise HTTPException(status_code=404, detail="Triage entry not found")

    if action_req.action == "APPROVE":
        if entry.status == "APPROVED":
            return {"status": "success", "message": "Already approved."}

        settings_result = await db.execute(
            select(SystemSettings.value).where(SystemSettings.key == "approved_retention_days")
        )
        val = settings_result.scalars().first()
        approved_retention_days = int(val) if val else 30

        entry.status = "APPROVED"
        entry.expires_at = datetime.now() + timedelta(days=approved_retention_days)

        await db.commit()
        return {"status": "success", "message": "Triage entry approved."}
    else:
        raise HTTPException(status_code=400, detail="Invalid action")


@router.post("/{id}/upload-replacement")
async def upload_replacement(
    id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _ = Depends(require_permission("triage:approve"))
):
    result = await db.execute(select(TriageEntry).where(TriageEntry.id == id))
    entry = result.scalars().first()

    if not entry:
        raise HTTPException(status_code=404, detail="Triage entry not found")

    original_path = entry.original_path
    placeholder_path = f"{original_path}.kintsugi-quarantined.txt"

    # 1. Ensure target directory exists
    os.makedirs(os.path.dirname(original_path), exist_ok=True)

    # 2. Save the replacement file
    try:
        with open(original_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {e}")

    # 3. Delete placeholder
    if os.path.exists(placeholder_path):
        try:
            os.remove(placeholder_path)
        except OSError:
            pass # ignore if placeholder doesn't exist

    # 4. Get settings for TTL
    settings_result = await db.execute(
        select(SystemSettings.value).where(SystemSettings.key == "approved_retention_days")
    )
    val = settings_result.scalars().first()
    approved_retention_days = int(val) if val else 30

    # 5. Update DB State
    entry.status = "APPROVED"
    entry.expires_at = datetime.now() + timedelta(days=approved_retention_days)

    # Update MediaFile state to healthy
    media_result = await db.execute(select(MediaFile).where(MediaFile.id == entry.media_file_id))
    media_file = media_result.scalars().first()
    if media_file:
        media_file.state = "healthy"
        # We might also want to trigger a rescan or update hash, but for now just mark healthy

    await db.commit()

    # 6. Fire event
    await nexus_bus.broadcast("event:triage:manual_resolved", {"media_file_id": entry.media_file_id, "path": original_path})

    return {"status": "success", "message": "Replacement uploaded successfully"}
