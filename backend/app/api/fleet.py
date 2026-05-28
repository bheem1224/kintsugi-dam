import os
import uuid
import hashlib
from typing import Optional, Dict
from datetime import datetime, timedelta
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.database import get_db, async_session_maker
from app.core.models import FleetNode, FleetAuthority
from app.core.settings_manager import SettingsManager

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

# In-memory rate limiting and banning for Fleet Registration & Auth
# Tracks failures per IP address: IP -> [timestamp, ...]
RATE_LIMIT_STORE: Dict[str, list[datetime]] = defaultdict(list)
BANNED_IPS: Dict[str, datetime] = {}
MAX_FAILURES = 5
BAN_DURATION = timedelta(hours=24)

router = APIRouter()

def check_rate_limit(request: Request):
    client_ip = request.client.host
    now = datetime.now()

    # Fast path: check ban
    if client_ip in BANNED_IPS:
        ban_expires = BANNED_IPS[client_ip]
        if now < ban_expires:
            raise HTTPException(status_code=403, detail="Forbidden: IP address is temporarily banned.")
        else:
            del BANNED_IPS[client_ip]

def record_failure(request: Request):
    client_ip = request.client.host
    now = datetime.now()

    # Filter failures to the last 15 minutes to allow recovery from honest mistakes before a ban
    window_start = now - timedelta(minutes=15)
    RATE_LIMIT_STORE[client_ip] = [ts for ts in RATE_LIMIT_STORE[client_ip] if ts > window_start]

    RATE_LIMIT_STORE[client_ip].append(now)

    if len(RATE_LIMIT_STORE[client_ip]) >= MAX_FAILURES:
        BANNED_IPS[client_ip] = now + BAN_DURATION
        del RATE_LIMIT_STORE[client_ip]

"""
NGINX mTLS PROXY CONFIGURATION EXAMPLE:

To pass client certificates securely through Nginx Proxy Manager or any Nginx setup:

server {
    listen 443 ssl;
    server_name core.yourdomain.com;

    ssl_certificate /path/to/server/cert.pem;
    ssl_certificate_key /path/to/server/key.pem;

    # Require client certificate verification against the Kintsugi Core CA
    ssl_client_certificate /path/to/kintsugi/core/ca.crt;
    ssl_verify_client optional; # Or 'on'

    location / {
        proxy_pass http://kintsugi-backend:8000;

        # Forward certificate details to the FastAPI backend
        proxy_set_header X-SSL-Client-Cert $ssl_client_escaped_cert;
        proxy_set_header X-SSL-Client-SHA1 $ssl_client_fingerprint;
        proxy_set_header X-SSL-Client-Verify $ssl_client_verify;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}

CADDY mTLS PROXY CONFIGURATION EXAMPLE:

core.yourdomain.com {
    tls {
        client_auth {
            mode request
            trusted_ca_certs /path/to/kintsugi/core/ca.crt
        }
    }

    reverse_proxy kintsugi-backend:8000 {
        header_up X-SSL-Client-SHA1 {tls_client_fingerprint}
        header_up X-SSL-Client-Verify {tls_client_auth_status}
    }
}
"""

async def get_or_create_ca(db: AsyncSession) -> FleetAuthority:
    result = await db.execute(select(FleetAuthority).limit(1))
    ca = result.scalars().first()

    if not ca:
        # Generate new Root CA
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
        )

        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Kintsugi-DAM"),
            x509.NameAttribute(NameOID.COMMON_NAME, u"Kintsugi Core CA"),
        ])

        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=3650) # 10 years
        ).add_extension(
            x509.BasicConstraints(ca=True, path_length=None), critical=True,
        ).sign(private_key, hashes.SHA256())

        ca = FleetAuthority(
            private_key_pem=private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ).decode('utf-8'),
            public_cert_pem=cert.public_bytes(serialization.Encoding.PEM).decode('utf-8')
        )

        db.add(ca)
        await db.commit()
        await db.refresh(ca)

    return ca


class FleetRegisterRequest(BaseModel):
    registration_token: str
    node_name: str
    csr_pem: str

class FleetRegisterResponse(BaseModel):
    client_cert_pem: str
    ca_cert_pem: str


@router.post("/register", response_model=FleetRegisterResponse)
async def register_node(request: Request, payload: FleetRegisterRequest, db: AsyncSession = Depends(get_db)):
    check_rate_limit(request)

    expected_token = await SettingsManager.get("fleet_registration_token")
    if not expected_token or payload.registration_token != expected_token:
        record_failure(request)
        raise HTTPException(status_code=401, detail="Invalid registration token")

    # Lazy initialize CA
    ca = await get_or_create_ca(db)

    # Parse CSR
    try:
        csr = x509.load_pem_x509_csr(payload.csr_pem.encode('utf-8'))
        if not csr.is_signature_valid:
            raise ValueError("Invalid CSR signature")
    except Exception as e:
        record_failure(request)
        raise HTTPException(status_code=400, detail=f"Invalid CSR format: {e}")

    # Calculate Thumbprint from CSR public key (what the final cert will have)
    public_key = csr.public_key()

    # To calculate the cert fingerprint we actually need to create the cert first
    ca_private_key = serialization.load_pem_private_key(
        ca.private_key_pem.encode('utf-8'),
        password=None,
    )

    # Generate Client Certificate
    client_cert = x509.CertificateBuilder().subject_name(
        csr.subject
    ).issuer_name(
        x509.load_pem_x509_certificate(ca.public_cert_pem.encode('utf-8')).subject
    ).public_key(
        csr.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.utcnow()
    ).not_valid_after(
        datetime.utcnow() + timedelta(days=365) # 1 year validity
    ).sign(ca_private_key, hashes.SHA256())

    # Get SHA1 Thumbprint (commonly used by proxies)
    thumbprint_bytes = client_cert.fingerprint(hashes.SHA1())
    thumbprint = thumbprint_bytes.hex().lower()

    # Check if node already exists
    result = await db.execute(select(FleetNode).where(FleetNode.name == payload.node_name))
    node = result.scalars().first()

    if node:
        node.public_key_thumbprint = thumbprint
        node.status = "active"
        node.last_seen_at = datetime.now()
    else:
        node = FleetNode(
            name=payload.node_name,
            public_key_thumbprint=thumbprint,
            status="active"
        )
        db.add(node)

    await db.commit()

    return FleetRegisterResponse(
        client_cert_pem=client_cert.public_bytes(serialization.Encoding.PEM).decode('utf-8'),
        ca_cert_pem=ca.public_cert_pem
    )

async def verify_mtls(request: Request, db: AsyncSession) -> FleetNode:
    check_rate_limit(request)

    thumbprint = None

    # 1. Cloudflare Tunnel Authenticated Origin Pull (Inbound-Free Outbound-Only)
    if "cf-client-cert-der-base64" in request.headers:
        import base64
        try:
            der_cert_b64 = request.headers.get("cf-client-cert-der-base64")
            cert_bytes = base64.b64decode(der_cert_b64)
            cert = x509.load_der_x509_certificate(cert_bytes)
            # Match the same hashing algorithm used in the register endpoint (SHA1 is common for proxy thumbprints)
            thumbprint = cert.fingerprint(hashes.SHA1()).hex().lower()
        except Exception as e:
            record_failure(request)
            raise HTTPException(status_code=400, detail=f"Invalid Cloudflare Client Cert: {e}")

    # 2. Try to get thumbprint from other proxy headers
    elif "x-ssl-client-sha1" in request.headers:
        thumbprint = request.headers.get("x-ssl-client-sha1", "").lower()
    elif "x-ssl-client-cert" in request.headers:
        pass

    # 3. Try to get it from direct ASGI connection
    elif hasattr(request.scope, 'get') and request.scope.get('client_cert'):
        cert_bytes = request.scope['client_cert']
        cert = x509.load_der_x509_certificate(cert_bytes)
        thumbprint = cert.fingerprint(hashes.SHA1()).hex().lower()

    if not thumbprint:
        record_failure(request)
        raise HTTPException(status_code=401, detail="mTLS Client Certificate required")

    # Remove colons if proxy formats it as AA:BB:CC
    thumbprint = thumbprint.replace(":", "")

    result = await db.execute(select(FleetNode).where(FleetNode.public_key_thumbprint == thumbprint))
    node = result.scalars().first()

    if not node:
        record_failure(request)
        raise HTTPException(status_code=403, detail="Unrecognized Fleet Node")

    if node.status != "active":
        record_failure(request)
        raise HTTPException(status_code=403, detail=f"Node status is {node.status}")

    # Node Location Locks
    if node.is_local_only:
        client_ip = request.client.host
        from app.core.security import ip_in_cidr
        # RFC 1918 Private IP Ranges
        private_ranges = ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "127.0.0.0/8", "::1/128", "fc00::/7"]
        is_private = any(ip_in_cidr(client_ip, cidr) for cidr in private_ranges)

        if not is_private:
            record_failure(request)
            raise HTTPException(
                status_code=403,
                detail={"error": "ip_restricted", "detail": "Node is restricted to local network only"}
            )

    # Update last seen
    node.last_seen_at = datetime.now()
    await db.commit()

    return node


@router.post("/upload-chunk")
async def upload_chunk(
    request: Request,
    x_upload_id: str = Header(...),
    x_chunk_index: int = Header(...),
    x_is_final: str = Header(...),
    db: AsyncSession = Depends(get_db)
):
    node = await verify_mtls(request, db)

    is_final = x_is_final.lower() == 'true'

    cache_dir = os.path.join(".kintsugi", "import_cache", x_upload_id)
    os.makedirs(cache_dir, exist_ok=True)

    chunk_path = os.path.join(cache_dir, f"chunk_{x_chunk_index}")

    # Stream request body to file
    with open(chunk_path, "wb") as f:
        async for chunk in request.stream():
            f.write(chunk)

    if is_final:
        # Reassemble
        # For simplicity, we assume we know the total chunks, or we just read all chunks sequentially until missing
        final_file_path = os.path.join(cache_dir, "reassembled_file")
        with open(final_file_path, "wb") as out_f:
            idx = 0
            while True:
                c_path = os.path.join(cache_dir, f"chunk_{idx}")
                if not os.path.exists(c_path):
                    break
                with open(c_path, "rb") as in_f:
                    out_f.write(in_f.read())
                os.remove(c_path) # Cleanup chunk
                idx += 1

        # Move to primary watch directory
        watch_dir = await SettingsManager.get("monitored_directory", "/media")

        # In a real scenario we need the original filename, but for now we generate a UUID
        final_dest = os.path.join(watch_dir, f"fleet_{node.id}_{x_upload_id}")
        os.makedirs(os.path.dirname(final_dest), exist_ok=True)

        os.rename(final_file_path, final_dest)

        # Cleanup cache dir
        try:
            os.rmdir(cache_dir)
        except OSError:
            pass # Directory not empty if chunks arrived out of order or failed

        return {"status": "success", "message": "File reassembled and passed to ingest router"}

    return {"status": "success", "message": f"Chunk {x_chunk_index} received"}


class FleetNodeResponse(BaseModel):
    id: int
    name: str
    node_type: str
    public_key_thumbprint: str
    status: str
    quota_bytes: Optional[int]
    registered_at: datetime
    last_seen_at: datetime
    is_local_only: bool

    class Config:
        from_attributes = True

@router.get("/nodes", response_model=list[FleetNodeResponse])
async def list_fleet_nodes(
    db: AsyncSession = Depends(get_db),
    # Assuming standard admin auth needed here.
    # from app.api.auth import get_current_user
    # current_user = Depends(get_current_user)
):
    result = await db.execute(select(FleetNode))
    return result.scalars().all()
