from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import os
import logging
from logging.handlers import RotatingFileHandler
import asyncio

from app.core.database import get_db
from app.core.models import FleetNode

router = APIRouter(prefix="/api/fleet", tags=["fleet_logs"])

LOG_DIR = "/app/data/logs"
os.makedirs(LOG_DIR, exist_ok=True)

class LogEntry(BaseModel):
    node_id: str
    message: str
    level: str = "INFO"

# Dict to hold rotating file handlers
_handlers = {}

def get_node_logger(node_id: str) -> logging.Logger:
    if node_id in _handlers:
        return logging.getLogger(f"fleet_{node_id}")

    logger = logging.getLogger(f"fleet_{node_id}")
    logger.setLevel(logging.INFO)

    log_file = os.path.join(LOG_DIR, f"fleet_{node_id}.log")

    # 100MB max size, 1 backup
    handler = RotatingFileHandler(log_file, maxBytes=100*1024*1024, backupCount=1)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    _handlers[node_id] = handler
    return logger

@router.post("/logs/stream")
async def ingest_logs(entry: LogEntry, db: AsyncSession = Depends(get_db)):
    # Verify node exists (assuming node_id is the public_key_thumbprint)
    result = await db.execute(select(FleetNode).where(FleetNode.public_key_thumbprint == entry.node_id))
    node = result.scalars().first()

    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    logger = get_node_logger(entry.node_id)

    level = getattr(logging, entry.level.upper(), logging.INFO)
    logger.log(level, entry.message)

    return {"status": "success"}

@router.get("/logs/{node_id}")
async def stream_logs(node_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FleetNode).where(FleetNode.public_key_thumbprint == node_id))
    node = result.scalars().first()

    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    log_file = os.path.join(LOG_DIR, f"fleet_{node_id}.log")
    if not os.path.exists(log_file):
        return StreamingResponse(iter([]), media_type="text/plain")

    async def log_generator():
        # Open the file
        try:
            with open(log_file, "r") as f:
                # Seek to end minus a bit or just read all for simplicity in this example
                # A robust tail -f equivalent
                f.seek(0, 2) # Seek to end

                while True:
                    if await request.is_disconnected():
                        break

                    line = f.readline()
                    if not line:
                        await asyncio.sleep(0.5)
                        continue

                    yield f"data: {line}\n\n"
        except FileNotFoundError:
            pass

    return StreamingResponse(log_generator(), media_type="text/event-stream")
