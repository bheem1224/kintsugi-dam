import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.database import get_db
from ..core.models import SystemSettings, User
from ..core.security import get_current_user
from .schemas import LicenseActivationRequest, LicenseActivationResponse

logger = logging.getLogger(__name__)

router = APIRouter()

DEV_BYPASS_KEY = "DEV_BYPASS_LICENSE"


@router.post("/activate", response_model=LicenseActivationResponse)
async def activate_license(
    request: LicenseActivationRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    if request.license_key == DEV_BYPASS_KEY:
        logger.info("DEV_BYPASS_KEY used. Provisioning 100 cloud credits.")

        result = await db.execute(select(SystemSettings).where(SystemSettings.key == "cloud_credits"))
        setting = result.scalars().first()

        if setting:
            try:
                credits = int(setting.value)
            except ValueError:
                credits = 0
            setting.value = str(credits + 100)
        else:
            db.add(SystemSettings(key="cloud_credits", value="100"))

        await db.commit()
        return LicenseActivationResponse(
            status="success",
            credits_added=100,
            message="Development bypass activated. 100 credits provisioned.",
        )

    # Placeholder for real LemonSqueezy validation
    raise HTTPException(status_code=400, detail="Invalid license key.")
