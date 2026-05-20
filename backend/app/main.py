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

from .core.module_loader import module_loader
from .core.nexus import nexus_bus
from .core.models import User

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database tables exist via Alembic auto-migration
    import asyncio
    from alembic.config import Config
    from alembic import command

    alembic_cfg = Config("alembic.ini")
    await asyncio.to_thread(command.upgrade, alembic_cfg, "head")

    # Fetch initial settings from the database
    async with async_session_maker() as session:
        result = await session.execute(select(SystemSettings).where(SystemSettings.id == 1))
        settings = result.scalars().first()
        
        if not settings:
            settings = SystemSettings(id=1)
            session.add(settings)
            await session.commit()
            await session.refresh(settings)
            
        monitored_directory = settings.monitored_directory

    booting_flag = "/app/data/plugin_boot.lock"

    async with async_session_maker() as session:
        admin_result = await session.execute(select(User).where(User.role == "admin"))
        admin_user = admin_result.scalars().first()
        is_pro = admin_user.is_pro if admin_user else False

        if not is_pro:
            logger.info("Free Tier Active: Nexus Event Bus Disabled. Skipping plugin loader.")
        else:
            if os.path.exists(booting_flag):
                logger.error("CRASH DETECTED: SAFE MODE ENGAGED. PREVIOUS BOOT FAILED. All plugins disabled.")
            else:
                os.makedirs(os.path.dirname(booting_flag), exist_ok=True)
                with open(booting_flag, "w") as f:
                    f.write("booting")

                nexus_bus.initialize()
                await module_loader.boot_plugins(session)

                try:
                    os.remove(booting_flag)
                except OSError as e:
                    logger.warning(f"Could not remove booting flag: {e}")

        app.state.scheduler = start_scheduler()

    # Launch the continuous background LRU scanning daemon
    from .core.scheduler import run_lru_daemon
    import asyncio
    app.state.lru_daemon_task = asyncio.create_task(run_lru_daemon(async_session_maker))

    app.state.watcher = WatcherService()
    app.state.watcher.start(monitored_directory)

    yield
    app.state.watcher.stop()
    app.state.scheduler.shutdown()
    if hasattr(app.state, 'lru_daemon_task'):
        app.state.lru_daemon_task.cancel()

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
