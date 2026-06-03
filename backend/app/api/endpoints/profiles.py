from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.core.database import get_db
from app.core.models import Profile

router = APIRouter(prefix="/api/profiles", tags=["profiles"])

class ProfileCreate(BaseModel):
    name: str
    payload_json: Dict[str, Any]

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    payload_json: Optional[Dict[str, Any]] = None

class ProfileResponse(BaseModel):
    id: int
    name: str
    payload_json: Dict[str, Any]

@router.get("", response_model=List[ProfileResponse])
async def list_profiles(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Profile))
    return result.scalars().all()

@router.post("", response_model=ProfileResponse)
async def create_profile(profile: ProfileCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Profile).where(Profile.name == profile.name))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Profile with this name already exists")

    new_profile = Profile(name=profile.name, payload_json=profile.payload_json)
    db.add(new_profile)
    await db.commit()
    await db.refresh(new_profile)
    return new_profile

@router.get("/{profile_id}", response_model=ProfileResponse)
async def get_profile(profile_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Profile).where(Profile.id == profile_id))
    profile = result.scalars().first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@router.put("/{profile_id}", response_model=ProfileResponse)
async def update_profile(profile_id: int, profile_update: ProfileUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Profile).where(Profile.id == profile_id))
    profile = result.scalars().first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    if profile_update.name is not None:
        profile.name = profile_update.name
    if profile_update.payload_json is not None:
        profile.payload_json = profile_update.payload_json

    await db.commit()
    await db.refresh(profile)
    return profile

@router.delete("/{profile_id}")
async def delete_profile(profile_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Profile).where(Profile.id == profile_id))
    profile = result.scalars().first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    await db.delete(profile)
    await db.commit()
    return {"status": "success"}
