from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class WebhookConfig(BaseModel):
    discord_webhook_url: Optional[str] = None
    ntfy_topic_url: Optional[str] = None


class ContextPickerRequest(BaseModel):
    file_id: int
    context_file_ids: List[int]


class LicenseActivationRequest(BaseModel):
    license_key: str


class LicenseActivationResponse(BaseModel):
    status: str
    credits_added: int
    message: str


class MediaFileResponse(BaseModel):
    id: int
    filepath: str
    mtime: float
    size: int
    sha256_hash: Optional[str] = None
    last_hashed_date: Optional[datetime] = None
    state: str

    class Config:
        orm_mode = True


class AIRepairRequest(BaseModel):
    context_file_ids: List[int]
    provider: str


class AIRepairResponse(BaseModel):
    status: str
    message: str
