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

    KINTSUGI_DB_TYPE: str = "sqlite"
    KINTSUGI_DB_HOST: str = ""
    KINTSUGI_DB_NAME: str = "/app/data/kintsugi.db"
    KINTSUGI_DB_USER: str = ""
    KINTSUGI_DB_PASSWORD: str = ""

    @property
    def DATABASE_URL(self) -> str:
        if self.KINTSUGI_DB_TYPE == "postgres":
            return f"postgresql+asyncpg://{self.KINTSUGI_DB_USER}:{self.KINTSUGI_DB_PASSWORD}@{self.KINTSUGI_DB_HOST}/{self.KINTSUGI_DB_NAME}"
        elif self.KINTSUGI_DB_TYPE == "mysql":
            return f"mysql+aiomysql://{self.KINTSUGI_DB_USER}:{self.KINTSUGI_DB_PASSWORD}@{self.KINTSUGI_DB_HOST}/{self.KINTSUGI_DB_NAME}"
        else:
            return f"sqlite+aiosqlite:///{self.KINTSUGI_DB_NAME}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
