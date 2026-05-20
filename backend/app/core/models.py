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
    last_scanned_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
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
    discord_webhook_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    ntfy_topic_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    consensus_threshold: Mapped[int] = mapped_column(Integer, default=2)
    cloud_credits: Mapped[int] = mapped_column(Integer, default=0)
    maintenance_start: Mapped[str] = mapped_column(String, default="01:00")
    maintenance_end: Mapped[str] = mapped_column(String, default="05:00")
    monitored_directory: Mapped[str] = mapped_column(String, default="/media")
    triage_directory: Mapped[str] = mapped_column(String, default="/app/data/triage")
    scan_intensity: Mapped[str] = mapped_column(String, default="eco") # eco, balanced, turbo
    is_setup_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    max_workers: Mapped[int] = mapped_column(Integer, default=1)
    auto_restore: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_restore_cloud: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_restore_ai: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_use_kintsugi_cloud: Mapped[bool] = mapped_column(Boolean, default=True)
    retention_days: Mapped[int] = mapped_column(Integer, default=90)
    approved_retention_days: Mapped[int] = mapped_column(Integer, default=30)
    snapshot_mount_path: Mapped[str] = mapped_column(String, default="/snapshots")
    enable_3rd_party_plugins: Mapped[bool] = mapped_column(Boolean, default=False)

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String, default="user")
    license_key: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_pro: Mapped[bool] = mapped_column(Boolean, default=False)
    paddle_customer_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    paddle_subscription_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)


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


class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    key_prefix: Mapped[str] = mapped_column(String)
    hashed_key: Mapped[str] = mapped_column(String)
    permissions: Mapped[List[str]] = mapped_column(JSON, default=list)
class TriageEntry(Base):
    __tablename__ = "triage_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    media_file_id: Mapped[int] = mapped_column(Integer, index=True)
    original_path: Mapped[str] = mapped_column(String)
    quarantine_path: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="QUARANTINED") # QUARANTINED, PENDING_APPROVAL, APPROVED
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
