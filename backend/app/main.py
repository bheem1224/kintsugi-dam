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
from .api.billing import router as billing_router
from .core.scheduler import start_scheduler
from .core.watcher import WatcherService
from .core.database import async_session_maker, engine, Base
from .core.models import SystemSettings
from sqlalchemy import select

from .core.plugins import PluginManager

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

    booting_flag = "/app/data/booting.flag"
    if os.path.exists(booting_flag):
        logger.error("CRASH DETECTED: Booting in Safe Mode. All plugins disabled.")
    else:
        # Create booting flag
        os.makedirs(os.path.dirname(booting_flag), exist_ok=True)
        with open(booting_flag, "w") as f:
            f.write("booting")

        async with async_session_maker() as session:
            plugin_manager = PluginManager(session)
            await plugin_manager.initialize_plugins()
            app.state.plugin_manager = plugin_manager

        # Delete booting flag
        try:
            os.remove(booting_flag)
        except OSError as e:
            logger.warning(f"Could not remove booting flag: {e}")

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
from starlette.middleware.sessions import SessionMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
import secrets
app.add_middleware(SessionMiddleware, secret_key=os.environ.get("SESSION_SECRET", secrets.token_urlsafe(32)))

app.include_router(api_router, prefix="/api")
app.include_router(license_router, prefix="/api/license")
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(billing_router, prefix="/api/billing", tags=["billing"])

@app.get("/")
async def root():
    return {"message": "Kintsugi-DAM API is running"}
