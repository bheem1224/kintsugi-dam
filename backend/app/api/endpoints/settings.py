from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.core.database import get_db
from app.core.models import SystemSettings

router = APIRouter(prefix="/api/settings", tags=["settings"])

class SettingUpdate(BaseModel):
    key: str
    value: str

class SettingsUpdateRequest(BaseModel):
    settings: List[SettingUpdate]

@router.put("")
async def update_settings(request: SettingsUpdateRequest, db: AsyncSession = Depends(get_db)):
    # Update settings or create them if they don't exist
    for setting in request.settings:
        result = await db.execute(select(SystemSettings).where(SystemSettings.key == setting.key))
        existing_setting = result.scalars().first()
        if existing_setting:
            existing_setting.value = setting.value
        else:
            db.add(SystemSettings(key=setting.key, value=setting.value))

    await db.commit()
    return {"status": "success"}

@router.get("")
async def get_settings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SystemSettings))
    rows = result.scalars().all()

    settings_dict = {row.key: row.value for row in rows}

    return {"settings": settings_dict}
