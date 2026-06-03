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
from .api.notifications import router as notifications_router
from .api.triage import router as triage_router
from .api.fleet import router as fleet_router
from .api.endpoints.profiles import router as profiles_router
from .api.endpoints.fs import router as fs_router
from .api.endpoints.settings import router as settings_router
from .api.endpoints.sso import router as sso_router
from .api.endpoints.worker_nodes import router as worker_nodes_router
from .api.endpoints.stats import router as stats_router
from .api.endpoints.fleet_logs import router as fleet_logs_router
from .modules.triage.scheduler import run_triage_daemon
from .core.scheduler import start_scheduler
from .modules.ingest.watcher import TieredWatcherDaemon
from .core.database import async_session_maker, engine, Base
from .core.models import SystemSettings
from sqlalchemy import select

from .core.module_loader import module_loader
from .core.nexus import nexus_bus
from .modules.notifications.services import async_init_notification_engine
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
        defaults = {
            "discord_webhook_url": "",
            "ntfy_topic_url": "",
            "consensus_threshold": "2",
            "cloud_credits": "0",
            "maintenance_start": "01:00",
            "maintenance_end": "05:00",
            "monitored_directory": "/media",
            "triage_directory": "/app/data/triage",
            "scan_intensity": "eco",
            "is_setup_complete": "false",
            "max_workers": "1",
            "auto_restore": "false",
            "auto_restore_cloud": "false",
            "auto_restore_ai": "false",
            "ai_use_kintsugi_cloud": "true",
            "retention_days": "90",
            "approved_retention_days": "30",
            "snapshot_mount_path": "/snapshots",
            "enable_3rd_party_plugins": "false",
            "ai_api_endpoint": "https://api.openai.com/v1"
        }
        result = await session.execute(select(SystemSettings))
        existing_keys = {row.key for row in result.scalars().all()}
        
        added = False
        for k, v in defaults.items():
            if k not in existing_keys:
                session.add(SystemSettings(key=k, value=v))
                added = True
        if added:
            await session.commit()

        res_dir = await session.execute(select(SystemSettings.value).where(SystemSettings.key == "monitored_directory"))
        monitored_directory = res_dir.scalars().first() or "/media"

    booting_flag = "/app/data/plugin_boot.lock"

    async with async_session_maker() as session:
        admin_result = await session.execute(select(User).limit(1))
        admin_user = admin_result.scalars().first()
        is_pro = True if admin_user else False

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
                await async_init_notification_engine()
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
    app.state.triage_daemon_task = asyncio.create_task(run_triage_daemon(async_session_maker))

    app.state.watcher = TieredWatcherDaemon()
    await app.state.watcher.start()

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
app.include_router(notifications_router)
app.include_router(triage_router, prefix="/api/triage")
app.include_router(fleet_router, prefix="/api/fleet", tags=["fleet"])
app.include_router(profiles_router)
app.include_router(fs_router)
app.include_router(settings_router)
app.include_router(sso_router)
app.include_router(worker_nodes_router)
app.include_router(stats_router)
app.include_router(fleet_logs_router)

@app.get("/")
async def root():
    return {"message": "Kintsugi-DAM API is running"}

from .api.sync import router as sync_router
app.include_router(sync_router, prefix="/api")
