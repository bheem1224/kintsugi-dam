import logging
import os
import traceback
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from datetime import time

from .api.routers import router as api_router
from .api.license import router as license_router
from .api.auth import router as auth_router
from .core.scheduler import start_scheduler
from .core.watcher import WatcherService
from .core.database import async_session_maker, engine, Base
from .core.models import SystemSettings
from sqlalchemy import select

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Fetch initial settings from the database
    async with async_session_maker() as session:
        result = await session.execute(select(SystemSettings).where(SystemSettings.id == 1))
        settings = result.scalars().first()
        monitored_directory = settings.monitored_directory if settings else "/media"

    app.state.scheduler = start_scheduler(monitored_directory, time(1, 0), time(5, 0))

    app.state.watcher = WatcherService()
    app.state.watcher.start(monitored_directory)

    yield
    app.state.watcher.stop()
    app.state.scheduler.shutdown()

app = FastAPI(title="Kintsugi-DAM API", lifespan=lifespan)

logger = logging.getLogger(__name__)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception handler caught: {exc}\n{traceback.format_exc()}")
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

allowed_origins_env = os.environ.get("ALLOWED_ORIGINS")
if allowed_origins_env:
    allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]
else:
    allowed_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
app.include_router(license_router, prefix="/api/license")
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])

@app.get("/")
async def root():
    return {"message": "Kintsugi-DAM API is running"}
