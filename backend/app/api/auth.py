import secrets
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from authlib.integrations.starlette_client import OAuth, OAuthError

from ..core.database import get_db
from ..core.models import User
from ..core.security import verify_password, get_password_hash, create_access_token, get_current_user
from ..core.config import settings

router = APIRouter()

oauth = OAuth()
if settings.OIDC_CLIENT_ID and settings.OIDC_CLIENT_SECRET and settings.OIDC_DISCOVERY_URL:
    oauth.register(
        name='oidc',
        client_id=settings.OIDC_CLIENT_ID,
        client_secret=settings.OIDC_CLIENT_SECRET,
        server_metadata_url=settings.OIDC_DISCOVERY_URL,
        client_kwargs={
            'scope': 'openid email profile'
        }
    )

from typing import List

class UserCreate(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserProfile(BaseModel):
    email: str
    permissions: List[str]

@router.get("/status")
async def get_system_status(db: AsyncSession = Depends(get_db)):
    # Check if ANY user exists
    user_result = await db.execute(select(User).limit(1))
    user_exists = user_result.scalars().first() is not None
    
    # Check if setup is complete
    from ..core.models import SystemSettings
    settings_result = await db.execute(
        select(SystemSettings.value).where(SystemSettings.key == "is_setup_complete")
    )
    val = settings_result.scalars().first()
    setup_complete = val.lower() == "true" if val else False
    
    return {
        "setup_required": not (user_exists and setup_complete),
        "admin_exists": user_exists
    }

@router.post("/register", response_model=Token)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    check_users = await db.execute(select(User).limit(1))
    if check_users.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Initial setup is already complete. Self-registration is disabled."
        )

    hashed_password = get_password_hash(user.password)
    new_user = User(
        email=user.email,
        hashed_password=hashed_password,
        is_local_disabled=False,
        permissions=["system:write", "triage:approve"],
        allowed_ips=[]
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    access_token = create_access_token(data={"sub": new_user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalars().first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.is_local_disabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Local login is disabled for this account."
        )

    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserProfile)
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "email": current_user.email,
        "permissions": current_user.permissions
    }

@router.get("/oidc/login")
async def oidc_login(request: Request):
    if not oauth.oidc:
        raise HTTPException(status_code=400, detail="OIDC is not configured")
    redirect_uri = f"{settings.PUBLIC_URL.rstrip('/')}/api/auth/oidc/callback"
    return await oauth.oidc.authorize_redirect(request, redirect_uri)

@router.get("/oidc/callback")
async def oidc_callback(request: Request, db: AsyncSession = Depends(get_db)):
    if not oauth.oidc:
        raise HTTPException(status_code=400, detail="OIDC is not configured")

    try:
        token = await oauth.oidc.authorize_access_token(request)
        userinfo = token.get('userinfo')
        if not userinfo or not userinfo.get('email'):
            raise HTTPException(status_code=400, detail="OIDC provider did not return an email")
    except OAuthError as e:
        raise HTTPException(status_code=400, detail=f"OAuth error: {e.error}")

    email = userinfo.get('email')

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()

    if not user:
        check_users = await db.execute(select(User).limit(1))
        any_user = check_users.scalars().first()

        if not any_user:
            # First user, auto-provision
            hashed_password = get_password_hash(secrets.token_urlsafe(32))
            user = User(
                email=email,
                hashed_password=hashed_password,
                is_local_disabled=False,
                permissions=["system:write", "triage:approve"],
                allowed_ips=[]
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        else:
            # Not first user, reject
            raise HTTPException(status_code=403, detail="User not found and self-registration via OIDC is not enabled.")

    access_token = create_access_token(data={"sub": user.email})

    response = RedirectResponse(url="/")
    is_secure = settings.PUBLIC_URL.startswith("https://")
    response.set_cookie(
        key="kintsugi_token",
        value=access_token,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        max_age=60*24*7*60 # 7 days in seconds
    )
    return response
