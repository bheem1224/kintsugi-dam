import logging
from datetime import datetime
from typing import Optional, Any

from fastapi import APIRouter, Depends, HTTPException, Request, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.models import ApiKey, User
from app.core.security import verify_password
from app.modules.sync.base import ISyncProvider

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sync", tags=["sync"])

async def get_webhook_api_key(
    request: Request,
    api_key_query: Optional[str] = Query(None, alias="api_key"),
    x_api_key_header: Optional[str] = Header(None, alias="X-API-Key"),
    api_key_header: Optional[str] = Header(None, alias="api_key"),
    api_key_header_hyphen: Optional[str] = Header(None, alias="api-key"),
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
) -> ApiKey:

    token = api_key_query or x_api_key_header or api_key_header or api_key_header_hyphen

    if not token and authorization:
        if authorization.lower().startswith("bearer "):
            token = authorization[7:]

    if not token:
        raise HTTPException(status_code=401, detail="Missing API Key")

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

    # Check if we have candidate keys to verify
    if not api_keys:
        # Run a dummy bcrypt verification to consume constant time
        # and prevent timing attacks from revealing if a prefix exists.
        dummy_hash = "$2b$12$LqyV5wE1J7/a.4kQ4O79Ue8eR6Vqg9/u3DkHjJjP4/12345678901"
        try:
            verify_password("dummy_secret", dummy_hash)
        except Exception:
            pass
        raise HTTPException(status_code=401, detail="Invalid API Key")

    valid_key = None
    matched = False
    for ak in api_keys:
        try:
            # Evaluate all candidate keys in the list to prevent timing leakage of matching index
            is_match = verify_password(plain_to_verify, ak.hashed_key)
            if is_match and not matched:
                valid_key = ak
                matched = True
        except Exception:
            continue

    if not valid_key:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    if valid_key.expires_at and valid_key.expires_at < datetime.now():
        raise HTTPException(status_code=401, detail="API Key has expired")

    user_res = await db.execute(select(User).where(User.id == valid_key.user_id))
    user = user_res.scalars().first()
    allowed_ips = user.allowed_ips if user else []

    if allowed_ips:
        from app.core.security import ip_in_cidr
        client_ip = request.client.host
        ip_allowed = False
        for cidr in allowed_ips:
            if ip_in_cidr(client_ip, cidr):
                ip_allowed = True
                break
        if not ip_allowed:
            raise HTTPException(status_code=403, detail="Forbidden: IP address not allowed")

    return valid_key

@router.post("/{provider_name}/webhook")
async def sync_webhook(
    provider_name: str,
    payload: dict,
    api_key: ApiKey = Depends(get_webhook_api_key)
):
    # Dynamically find the provider class
    provider_class = None

    # Iterate through all subclasses of ISyncProvider
    for subclass in ISyncProvider.__subclasses__():
        if subclass.__name__.lower() == f"{provider_name.lower()}syncprovider":
            provider_class = subclass
            break

    if not provider_class:
        raise HTTPException(status_code=404, detail=f"Sync provider '{provider_name}' not found")

    provider_instance = provider_class()

    # We only care about deletion webhooks for now
    await provider_instance.handle_deletion(payload)

    return {"status": "success"}
