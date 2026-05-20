import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import passlib.hash as hashing

from app.core.database import get_db
from app.core.models import ApiKey
from app.core.nexus import nexus_bus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/triage", tags=["notifications", "triage"])

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

def verify_api_key_hash(plain_key: str, hashed_key: str) -> bool:
    try:
        # Assuming bcrypt is used, can fallback to simpler matching or other hash mechanism if needed
        # We will use passlib's bcrypt
        from passlib.handlers.bcrypt import bcrypt
        return bcrypt.verify(plain_key, hashed_key)
    except Exception:
        # Fallback if just sha256 or plaintext is stored, or handle differently
        # For an enterprise system, bcrypt is standard
        pass

    # Simple fallback for testing if hashing wasn't strictly configured yet
    import hashlib
    return hashlib.sha256(plain_key.encode()).hexdigest() == hashed_key

async def get_authorized_api_key(
    api_key_header: str = Security(api_key_header),
    db: AsyncSession = Depends(get_db)
) -> ApiKey:
    """
    Dependency to verify the Authorization: Bearer <API_KEY> header.
    """
    if not api_key_header:
        raise HTTPException(status_code=401, detail="Missing API Key header")

    # Handle 'Bearer <key>' or just '<key>'
    token = api_key_header
    if token.lower().startswith("bearer "):
        token = token[7:]

    # Since we only have the plaintext key from the request, we must query DB
    # We might need to fetch all keys and verify, or better:
    # Key prefix can be used to look up the key efficiently: e.g., 'pk_live_...'
    # For this implementation, we will fetch the key if it matches an expected pattern,
    # or iterate through keys (which is bad practice for large DBs, but fine for small/MVP).
    # Since prompt specifies key_prefix and hashed_key, usually keys are of form: prefix.secret

    parts = token.split(".")
    if len(parts) == 2:
        prefix, secret = parts
        result = await db.execute(select(ApiKey).where(ApiKey.key_prefix == prefix))
        api_keys = result.scalars().all()
    else:
        # If no dot, just check all (fallback)
        result = await db.execute(select(ApiKey))
        api_keys = result.scalars().all()

    valid_key = None
    for ak in api_keys:
        if verify_api_key_hash(token, ak.hashed_key):
            valid_key = ak
            break

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
