from sqlalchemy import BigInteger
from datetime import datetime
from typing import Optional, List

from sqlalchemy import String, Float, Integer, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class MediaFile(Base):
    __tablename__ = "media_files"

    id: Mapped[int] = mapped_column(primary_key=True)
    filepath: Mapped[str] = mapped_column(String, unique=True, index=True)
    mtime: Mapped[float] = mapped_column(Float)
    size: Mapped[int] = mapped_column(Integer)
    sha256_hash: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    last_scanned_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    state: Mapped[str] = mapped_column(String, default="clean")


class PluginConfig(Base):
    __tablename__ = "plugin_configs"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    type: Mapped[str] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    priority: Mapped[int] = mapped_column(Integer)


class ScanHistory(Base):
    __tablename__ = "scan_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    scan_date: Mapped[datetime] = mapped_column(DateTime)
    files_scanned: Mapped[int] = mapped_column(Integer)
    bytes_processed: Mapped[int] = mapped_column(Integer)
    duration_seconds: Mapped[float] = mapped_column(Float)


class SystemSettings(Base):
    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String, unique=True, index=True)
    value: Mapped[str] = mapped_column(String)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    is_local_disabled: Mapped[bool] = mapped_column(Boolean, default=False)
    permissions: Mapped[List[str]] = mapped_column(JSON, default=list)
    allowed_ips: Mapped[List[str]] = mapped_column(JSON, default=list)


class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String, nullable=False)
    hashed_key: Mapped[str] = mapped_column(String, nullable=False)
    permissions: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class Plugin(Base):
    __tablename__ = "plugins"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    installed_version: Mapped[str] = mapped_column(String)
    channel: Mapped[str] = mapped_column(String, default="stable")
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    source_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_official: Mapped[bool] = mapped_column(Boolean, default=False)
    type: Mapped[str] = mapped_column(String)
    permissions: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)


class NotificationLogs(Base):
    __tablename__ = "notification_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    file_path: Mapped[str] = mapped_column(String)
    summary: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class TriageEntry(Base):
    __tablename__ = "triage_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    media_file_id: Mapped[int] = mapped_column(Integer, index=True)
    original_path: Mapped[str] = mapped_column(String)
    quarantine_path: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(
        String, default="QUARANTINED"
    )  # QUARANTINED, PENDING_APPROVAL, APPROVED
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class FleetNode(Base):
    __tablename__ = "fleet_nodes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    public_key_thumbprint: Mapped[str] = mapped_column(String, unique=True, index=True)
    status: Mapped[str] = mapped_column(String, default="active")
    quota_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    registered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    is_local_only: Mapped[bool] = mapped_column(Boolean, default=False)

class FleetAuthority(Base):
    __tablename__ = "fleet_authority"

    id: Mapped[int] = mapped_column(primary_key=True)
    private_key_pem: Mapped[str] = mapped_column(String)
    public_cert_pem: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
