import os
import secrets
import json
import ipaddress
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .database import get_db
from .models import User, ApiKey, SystemSettings

# JWT Config
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
SECRET_FILE = "/app/data/jwt_secret.json"

if not JWT_SECRET_KEY:
    if os.path.exists(SECRET_FILE):
        try:
            with open(SECRET_FILE, "r") as f:
                data = json.load(f)
                JWT_SECRET_KEY = data.get("secret")
        except Exception:
            pass

    if not JWT_SECRET_KEY:
        JWT_SECRET_KEY = secrets.token_urlsafe(32)
        os.makedirs(os.path.dirname(SECRET_FILE), exist_ok=True)
        with open(SECRET_FILE, "w") as f:
            json.dump({"secret": JWT_SECRET_KEY}, f)

JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 7 days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    to_encode.update({"type": "refresh"})
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=30)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def ip_in_cidr(ip_str: str, cidr_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
        if "/" not in cidr_str:
            return ip == ipaddress.ip_address(cidr_str)
        network = ipaddress.ip_network(cidr_str, strict=False)
        return ip in network
    except ValueError:
        return False

async def get_request_allowed_ips(request: Request, db: AsyncSession = Depends(get_db)) -> list:
    if hasattr(request.state, "allowed_ips"):
        return request.state.allowed_ips

    token = request.headers.get("Authorization")
    if token and token.startswith("Bearer "):
        token = token.split(" ")[1]
    else:
        token = request.cookies.get("kintsugi_token")

    if token:
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            email = payload.get("sub")
            if email and payload.get("type") != "refresh":
                res = await db.execute(select(User).where(User.email == email))
                user = res.scalars().first()
                if user:
                    request.state.user = user
                    request.state.allowed_ips = user.allowed_ips
                    return user.allowed_ips
        except Exception:
            pass

    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        api_token = auth_header.split(" ")[1]
        parts = api_token.split(".")
        if len(parts) == 2 or len(parts) == 1:
            try:
                from app.api.notifications import get_authorized_api_key
                from fastapi.security import HTTPAuthorizationCredentials
                creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=api_token)
                api_key = await get_authorized_api_key(creds, db)
                if api_key:
                    res = await db.execute(select(User).where(User.id == api_key.user_id))
                    user = res.scalars().first()
                    if user:
                        request.state.api_key = api_key
                        request.state.allowed_ips = user.allowed_ips
                        return user.allowed_ips
            except Exception:
                pass

    return []

async def verify_ip_allowlist(request: Request, allowed_ips: list = Depends(get_request_allowed_ips)):
    if allowed_ips:
        client_ip = request.client.host
        ip_allowed = False
        for cidr in allowed_ips:
            if ip_in_cidr(client_ip, cidr):
                ip_allowed = True
                break
        if not ip_allowed:
            raise HTTPException(status_code=403, detail="Forbidden: IP address not allowed")

async def get_current_user(
    request: Request, db: AsyncSession = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = request.headers.get("Authorization")
    if token and token.startswith("Bearer "):
        token = token.split(" ")[1]
    else:
        token = request.cookies.get("kintsugi_token")

    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        if payload.get("type") == "refresh":
            raise credentials_exception
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()

    if user is None:
        raise credentials_exception

    if user.allowed_ips:
        client_ip = request.client.host
        ip_allowed = False
        for cidr in user.allowed_ips:
            if ip_in_cidr(client_ip, cidr):
                ip_allowed = True
                break
        if not ip_allowed:
            raise HTTPException(status_code=403, detail="Forbidden: IP address not allowed")

    request.state.user = user
    request.state.allowed_ips = user.allowed_ips
    return user

def require_permission(permission: str):
    async def dependency(
        request: Request,
        db: AsyncSession = Depends(get_db)
    ):
        res_tier = await db.execute(
            select(SystemSettings.value).where(SystemSettings.key == "license_tier")
        )
        tier = res_tier.scalars().first()
        
        if tier != "studio":
            return True

        user = getattr(request.state, "user", None)
        api_key = getattr(request.state, "api_key", None)

        if not user and not api_key:
            await get_request_allowed_ips(request, db)
            user = getattr(request.state, "user", None)
            api_key = getattr(request.state, "api_key", None)

        if not user and not api_key:
            raise HTTPException(status_code=401, detail="Not authenticated")

        permissions = []
        if user:
            permissions = user.permissions or []
        elif api_key:
            permissions = api_key.permissions or []

        if permission not in permissions:
            raise HTTPException(
                status_code=403,
                detail=f"Forbidden: Lacks required permission '{permission}'"
            )
        return True

    return dependency
