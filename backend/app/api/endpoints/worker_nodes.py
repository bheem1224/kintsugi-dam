from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.core.models import SystemSettings

router = APIRouter(prefix="/api/fleet/worker-config", tags=["fleet_worker"])

class RedisConfig(BaseModel):
    url: str
    port: str
    auth: Optional[str] = None

class PathMapping(BaseModel):
    local_path: str
    remote_path: str

class WorkerConfig(BaseModel):
    redis_url: str
    redis_port: str
    redis_auth: Optional[str] = None
    path_mappings: str # Storing as JSON string in settings

@router.get("")
async def get_worker_config(db: AsyncSession = Depends(get_db)):
    keys = ["redis_url", "redis_port", "redis_auth", "path_mappings"]
    result = await db.execute(select(SystemSettings).where(SystemSettings.key.in_(keys)))

    config = {row.key: row.value for row in result.scalars().all()}

    return {
        "redis_url": config.get("redis_url", ""),
        "redis_port": config.get("redis_port", ""),
        "redis_auth": config.get("redis_auth", ""),
        "path_mappings": config.get("path_mappings", "[]")
    }

@router.put("")
async def update_worker_config(config: WorkerConfig, db: AsyncSession = Depends(get_db)):
    settings_to_update = {
        "redis_url": config.redis_url,
        "redis_port": config.redis_port,
        "redis_auth": config.redis_auth or "",
        "path_mappings": config.path_mappings
    }

    for key, value in settings_to_update.items():
        result = await db.execute(select(SystemSettings).where(SystemSettings.key == key))
        existing_setting = result.scalars().first()
        if existing_setting:
            existing_setting.value = value
        else:
            db.add(SystemSettings(key=key, value=value))

    await db.commit()
    return {"status": "success"}
