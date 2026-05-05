from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PUBLIC_URL: str = "http://localhost:3000"
    OIDC_CLIENT_ID: Optional[str] = None
    OIDC_CLIENT_SECRET: Optional[str] = None
    OIDC_DISCOVERY_URL: Optional[str] = None

    PADDLE_API_KEY: Optional[str] = None
    PADDLE_WEBHOOK_SECRET: Optional[str] = None
    PADDLE_ENVIRONMENT: str = "sandbox"
    KINTSUGI_ENABLE_BETA_PLUGINS: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
