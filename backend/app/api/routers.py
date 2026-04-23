import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.database import get_db
from ..core.models import MediaFile, SystemSettings
from .schemas import MediaFileResponse, AIRepairRequest, AIRepairResponse

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/files/corrupted", response_model=List[MediaFileResponse])
async def get_corrupted_files(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MediaFile).where(MediaFile.state == 'corrupted'))
    return result.scalars().all()

@router.post("/files/{file_id}/repair/ai", response_model=AIRepairResponse)
async def repair_file_ai(
    file_id: int,
    request: AIRepairRequest,
    db: AsyncSession = Depends(get_db)
):
    if request.provider == "cloud":
        result = await db.execute(select(SystemSettings))
        settings = result.scalars().first()

        if not settings or settings.cloud_credits < 1:
            raise HTTPException(status_code=402, detail="Insufficient cloud credits.")

        settings.cloud_credits -= 1
        await db.commit()
        logger.info(f"Deducted 1 cloud credit for file {file_id}. Remaining: {settings.cloud_credits}")

        # Simulate AI repair
        return AIRepairResponse(status="success", message="Cloud AI repair initiated.")

    return AIRepairResponse(status="success", message="Local AI repair initiated.")

@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    # Placeholder for stats
    return {"total_files": 0, "corrupted_files": 0}
