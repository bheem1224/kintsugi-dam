from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.core.models import MediaFile, TriageEntry, ScanHistory

router = APIRouter(prefix="/api/stats", tags=["stats"])

class StatsResponse(BaseModel):
    total_scanned: int
    bit_rot_alerts: int
    remediation_deltas: int
    ttl_expirations: int

@router.get("", response_model=StatsResponse)
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    # Total Scanned (Integrity Pool)
    # Using MediaFile count for total files tracked/scanned
    total_scanned_res = await db.execute(select(func.count(MediaFile.id)))
    total_scanned = total_scanned_res.scalar() or 0

    # Bit-Rot Alerts
    # Quarantined or Pending Approval items in Triage
    bit_rot_res = await db.execute(
        select(func.count(TriageEntry.id)).where(TriageEntry.status.in_(["QUARANTINED", "PENDING_APPROVAL"]))
    )
    bit_rot_alerts = bit_rot_res.scalar() or 0

    # Remediation Deltas (Fixed files)
    # Approved/Remediated items
    remediation_res = await db.execute(
        select(func.count(TriageEntry.id)).where(TriageEntry.status == "APPROVED")
    )
    remediation_deltas = remediation_res.scalar() or 0

    # TTL Expirations
    # Items that expired and were processed
    ttl_res = await db.execute(
        select(func.count(TriageEntry.id)).where(TriageEntry.status == "EXPIRED")
    )
    ttl_expirations = ttl_res.scalar() or 0

    return StatsResponse(
        total_scanned=total_scanned,
        bit_rot_alerts=bit_rot_alerts,
        remediation_deltas=remediation_deltas,
        ttl_expirations=ttl_expirations
    )
