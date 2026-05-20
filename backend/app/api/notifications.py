import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.models import ApiKey
from app.core.nexus import nexus_bus
from app.core.security import verify_password

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/triage", tags=["notifications", "triage"])

security = HTTPBearer(auto_error=False)

async def get_authorized_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> ApiKey:
    """
    Dependency to verify the Authorization: Bearer <API_KEY> header.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Missing API Key header")

    token = credentials.credentials
    parts = token.split(".")
    
    if len(parts) == 2:
        prefix, secret = parts
        result = await db.execute(select(ApiKey).where(ApiKey.key_prefix == prefix))
        api_keys = result.scalars().all()
        plain_to_verify = secret
    else:
        result = await db.execute(select(ApiKey))
        api_keys = result.scalars().all()
        plain_to_verify = token

    valid_key = None
    for ak in api_keys:
        try:
            if verify_password(plain_to_verify, ak.hashed_key):
                valid_key = ak
                break
        except Exception:
            continue

    if not valid_key:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    # Check expiration
    if valid_key.expires_at and valid_key.expires_at < datetime.now():
        raise HTTPException(status_code=401, detail="API Key has expired")

    # Check permissions
    if "triage:authorize" not in valid_key.permissions:
        raise HTTPException(status_code=403, detail="API Key lacks 'triage:authorize' permission")

    return valid_key


@router.post("/{triage_id}/authorize")
async def authorize_triage(
    triage_id: str,
    api_key: ApiKey = Depends(get_authorized_api_key),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint to unfreeze the pipeline.
    """
    # 1. We mock the update of the TriageEntry since we can't touch triage directories or models
    logger.info(f"Triage {triage_id} authorized by API Key {api_key.id}")

    # 2. Broadcast nexus event to unfreeze pipeline
    await nexus_bus.broadcast("event:triage:auth_approved", {"triage_id": triage_id})

    return {"status": "success", "message": f"Triage {triage_id} authorized and pipeline resumed."}
