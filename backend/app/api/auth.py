import secrets
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from authlib.integrations.starlette_client import OAuth, OAuthError
from typing import List, Optional

from ..core.database import get_db
from ..core.models import User, SystemSettings
from ..core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, get_current_user
from ..core.config import settings
from ..core.saml_auth import init_saml_auth

router = APIRouter()

async def get_oidc_client(db: AsyncSession):
    res = await db.execute(
        select(SystemSettings).where(
            SystemSettings.key.in_([
                "oidc_client_id", 
                "oidc_client_secret", 
                "oidc_discovery_url",
                "oidc_auth_url"
            ])
        )
    )
    rows = res.scalars().all()
    kvs = {row.key: row.value for row in rows}

    client_id = kvs.get("oidc_client_id") or settings.OIDC_CLIENT_ID
    client_secret = kvs.get("oidc_client_secret") or settings.OIDC_CLIENT_SECRET
    discovery_url = kvs.get("oidc_discovery_url") or kvs.get("oidc_auth_url") or settings.OIDC_DISCOVERY_URL

    if not (client_id and client_secret and discovery_url):
        return None

    oauth = OAuth()
    oauth.register(
        name='oidc',
        client_id=client_id,
        client_secret=client_secret,
        server_metadata_url=discovery_url,
        client_kwargs={
            'scope': 'openid email profile'
        }
    )
    return oauth.oidc

class UserCreate(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class UserProfile(BaseModel):
    email: str
    permissions: List[str]

class RefreshTokenRequest(BaseModel):
    refresh_token: Optional[str] = None

@router.get("/status")
async def get_system_status(db: AsyncSession = Depends(get_db)):
    user_result = await db.execute(select(User).limit(1))
    user_exists = user_result.scalars().first() is not None
    
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
    refresh_token = create_refresh_token(data={"sub": new_user.email})
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/token", response_model=Token)
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
    refresh_token = create_refresh_token(data={"sub": user.email})
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/refresh")
async def refresh_token(
    request: Request,
    body: Optional[RefreshTokenRequest] = None,
    db: AsyncSession = Depends(get_db)
):
    token = None
    if body and body.refresh_token:
        token = body.refresh_token
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    if not token:
        token = request.cookies.get("kintsugi_refresh_token")

    if not token:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    try:
        from ..core.security import JWT_SECRET_KEY, JWT_ALGORITHM, ip_in_cidr
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if user.allowed_ips:
        client_ip = request.client.host
        ip_allowed = False
        for cidr in user.allowed_ips:
            if ip_in_cidr(client_ip, cidr):
                ip_allowed = True
                break
        if not ip_allowed:
            raise HTTPException(status_code=403, detail="Forbidden: IP address not allowed")

    new_access_token = create_access_token(data={"sub": user.email})
    new_refresh_token = create_refresh_token(data={"sub": user.email})

    response_data = {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }

    from fastapi.responses import JSONResponse
    response = JSONResponse(content=response_data)
    is_secure = settings.PUBLIC_URL.startswith("https://")
    response.set_cookie(
        key="kintsugi_token",
        value=new_access_token,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        max_age=60*60
    )
    response.set_cookie(
        key="kintsugi_refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        max_age=60*24*7*60
    )
    return response

@router.get("/me", response_model=UserProfile)
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "email": current_user.email,
        "permissions": current_user.permissions
    }

@router.get("/oidc/login")
async def oidc_login(request: Request, db: AsyncSession = Depends(get_db)):
    oidc_client = await get_oidc_client(db)
    if not oidc_client:
        raise HTTPException(status_code=400, detail="OIDC is not configured")
    redirect_uri = f"{settings.PUBLIC_URL.rstrip('/')}/api/auth/oidc/callback"
    return await oidc_client.authorize_redirect(request, redirect_uri)

@router.get("/oidc/callback")
async def oidc_callback(request: Request, db: AsyncSession = Depends(get_db)):
    oidc_client = await get_oidc_client(db)
    if not oidc_client:
        raise HTTPException(status_code=400, detail="OIDC is not configured")

    try:
        token = await oidc_client.authorize_access_token(request)
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
            raise HTTPException(status_code=403, detail="User not found and self-registration via OIDC is not enabled.")

    from ..core.security import ip_in_cidr
    if user.allowed_ips:
        client_ip = request.client.host
        ip_allowed = False
        for cidr in user.allowed_ips:
            if ip_in_cidr(client_ip, cidr):
                ip_allowed = True
                break
        if not ip_allowed:
            raise HTTPException(status_code=403, detail="Forbidden: IP address not allowed")

    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})

    response = RedirectResponse(url="/")
    is_secure = settings.PUBLIC_URL.startswith("https://")
    response.set_cookie(
        key="kintsugi_token",
        value=access_token,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        max_age=60*60
    )
    response.set_cookie(
        key="kintsugi_refresh_token",
        value=refresh_token,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        max_age=60*24*7*60
    )
    return response

async def check_enterprise_tier(db: AsyncSession):
    res = await db.execute(select(SystemSettings).where(SystemSettings.key == "license_tier"))
    tier = res.scalars().first()
    if tier and tier.value == "free":
        raise HTTPException(status_code=403, detail="SAML SSO requires a Pro or Studio license.")
    return True

async def get_saml_kvs(db: AsyncSession):
    res = await db.execute(
        select(SystemSettings).where(
            SystemSettings.key.in_([
                "saml_idp_entity_id", 
                "saml_idp_sso_url", 
                "saml_idp_x509_cert",
                "saml_sp_entity_id"
            ])
        )
    )
    rows = res.scalars().all()
    kvs = {row.key: row.value for row in rows}
    return kvs

@router.get("/saml/login")
async def saml_login(request: Request, db: AsyncSession = Depends(get_db)):
    await check_enterprise_tier(db)
    kvs = await get_saml_kvs(db)
    auth = await init_saml_auth(request, kvs)
    sso_built_url = auth.login()
    return RedirectResponse(url=sso_built_url)

@router.post("/saml/acs")
async def saml_acs(request: Request, db: AsyncSession = Depends(get_db)):
    await check_enterprise_tier(db)
    kvs = await get_saml_kvs(db)
    auth = await init_saml_auth(request, kvs)
    
    await request.form()
    auth.process_response()
    errors = auth.get_errors()
    
    if errors:
        raise HTTPException(status_code=400, detail=f"SAML validation error: {', '.join(errors)}")
        
    if not auth.is_authenticated():
        raise HTTPException(status_code=401, detail="SAML authentication failed.")
        
    email = auth.get_nameid()
    if not email:
        attrs = auth.get_attributes()
        if attrs and 'email' in attrs and len(attrs['email']) > 0:
            email = attrs['email'][0]
        
    if not email:
        raise HTTPException(status_code=400, detail="Could not extract email from SAML assertion.")

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()

    if not user:
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

    from ..core.security import ip_in_cidr
    if user.allowed_ips:
        client_ip = request.client.host
        ip_allowed = False
        for cidr in user.allowed_ips:
            if ip_in_cidr(client_ip, cidr):
                ip_allowed = True
                break
        if not ip_allowed:
            raise HTTPException(status_code=403, detail="Forbidden: IP address not allowed")

    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})

    response = RedirectResponse(url="/")
    is_secure = settings.PUBLIC_URL.startswith("https://")
    response.set_cookie(
        key="kintsugi_token",
        value=access_token,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        max_age=60*60
    )
    response.set_cookie(
        key="kintsugi_refresh_token",
        value=refresh_token,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        max_age=60*24*7*60
    )
    return response

@router.get("/saml/metadata")
async def saml_metadata(request: Request, db: AsyncSession = Depends(get_db)):
    await check_enterprise_tier(db)
    kvs = await get_saml_kvs(db)
    auth = await init_saml_auth(request, kvs)
    settings_obj = auth.get_settings()
    metadata = settings_obj.get_sp_metadata()
    errors = settings_obj.validate_metadata(metadata)
    
    if len(errors) > 0:
        raise HTTPException(status_code=500, detail=f"Invalid SP metadata: {', '.join(errors)}")
        
    from fastapi.responses import Response
    return Response(content=metadata, media_type="text/xml")
