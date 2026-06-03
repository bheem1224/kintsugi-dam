from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.core.models import SystemSettings

router = APIRouter(prefix="/api/sso", tags=["sso"])

class SSOConfig(BaseModel):
    sso_type: str  # "oidc" or "saml" or "none"
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    issuer_url: Optional[str] = None
    metadata_url: Optional[str] = None

@router.get("")
async def get_sso_config(db: AsyncSession = Depends(get_db)):
    keys = ["sso_type", "sso_client_id", "sso_client_secret", "sso_issuer_url", "sso_metadata_url"]
    result = await db.execute(select(SystemSettings).where(SystemSettings.key.in_(keys)))

    config = {row.key: row.value for row in result.scalars().all()}

    return {
        "sso_type": config.get("sso_type", "none"),
        "client_id": config.get("sso_client_id", ""),
        "client_secret": config.get("sso_client_secret", ""),
        "issuer_url": config.get("sso_issuer_url", ""),
        "metadata_url": config.get("sso_metadata_url", "")
    }

@router.put("")
async def update_sso_config(config: SSOConfig, db: AsyncSession = Depends(get_db)):
    if config.sso_type not in ["oidc", "saml", "none"]:
        raise HTTPException(status_code=400, detail="Invalid SSO type. Must be 'oidc', 'saml', or 'none'.")

    settings_to_update = {
        "sso_type": config.sso_type,
        "sso_client_id": config.client_id or "",
        "sso_client_secret": config.client_secret or "",
        "sso_issuer_url": config.issuer_url or "",
        "sso_metadata_url": config.metadata_url or ""
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
