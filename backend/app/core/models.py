from datetime import datetime
from typing import Optional

from sqlalchemy import String, Float, Integer, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base

class MediaFile(Base):
    __tablename__ = 'media_files'

    id: Mapped[int] = mapped_column(primary_key=True)
    filepath: Mapped[str] = mapped_column(String, unique=True, index=True)
    mtime: Mapped[float] = mapped_column(Float)
    size: Mapped[int] = mapped_column(Integer)
    sha256_hash: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    last_hashed_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    state: Mapped[str] = mapped_column(String, default='clean')

class PluginConfig(Base):
    __tablename__ = 'plugin_configs'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    type: Mapped[str] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    priority: Mapped[int] = mapped_column(Integer)

class ScanHistory(Base):
    __tablename__ = 'scan_history'

    id: Mapped[int] = mapped_column(primary_key=True)
    scan_date: Mapped[datetime] = mapped_column(DateTime)
    files_scanned: Mapped[int] = mapped_column(Integer)
    bytes_processed: Mapped[int] = mapped_column(Integer)
    duration_seconds: Mapped[float] = mapped_column(Float)


class SystemSettings(Base):
    __tablename__ = 'system_settings'

    id: Mapped[int] = mapped_column(primary_key=True)
    discord_webhook_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    ntfy_topic_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    consensus_threshold: Mapped[int] = mapped_column(Integer, default=2)
