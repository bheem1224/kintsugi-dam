import json
import logging
import asyncio
from typing import Dict, Any

from app.core.nexus import nexus_bus
from app.core.database import async_session_maker
from app.core.models import NotificationLogs, SystemSettings
from app.core.http_client import RequestManager

logger = logging.getLogger(__name__)

# We instantiate a unified HTTP client instance. The prompt mentioned "GlobalRequestManager",
# but there is no such class in app.core.http_client. We will use RequestManager as it's the class defined in the module.
# To satisfy the "GlobalRequestManager" singleton pattern, we instantiate it here globally.
webhook_client = RequestManager(provider="webhook_dispatcher")

async def handle_consensus_finalized(payload: Dict[str, Any]):
    """
    Handles event:consensus_finalized.
    Extracts details and saves a formatted string to NotificationLogs.
    Payload expected: {"file_path": str, "scanners": [{"name": str, "status": str}], "final_verdict": str}
    """
    try:
        file_path = payload.get("file_path", "Unknown file")
        scanners = payload.get("scanners", [])
        final_verdict = payload.get("final_verdict", "Unknown")

        scanners_str = ", ".join([f"{s.get('name', 'Unknown')}: {s.get('status', 'Unknown')}" for s in scanners])
        summary = f"File: {file_path} | Verdict: {final_verdict} | Scanners: {scanners_str}"

        async with async_session_maker() as db_session:
            log_entry = NotificationLogs(
                file_path=file_path,
                summary=summary
            )
            db_session.add(log_entry)
            await db_session.commit()
            logger.info(f"Notification log saved for {file_path}")
    except Exception as e:
        logger.error(f"Failed to handle consensus_finalized event: {e}", exc_info=True)

async def handle_remediation_completed(payload: Dict[str, Any]):
    """
    Handles event:remediation_completed.
    """
    try:
        file_path = payload.get("file_path", "Unknown file")
        method = payload.get("method", "Unknown")
        status = payload.get("status", "Unknown")

        summary = f"File: {file_path} | Remediation Method: {method} | Status: {status}"

        async with async_session_maker() as db_session:
            log_entry = NotificationLogs(
                file_path=file_path,
                summary=summary
            )
            db_session.add(log_entry)
            await db_session.commit()
            logger.info(f"Notification log saved for {file_path}")
    except Exception as e:
        logger.error(f"Failed to handle remediation_completed event: {e}", exc_info=True)

async def handle_auth_required(payload: Dict[str, Any]):
    """
    Handles event:auth_required.
    Dispatches a webhook (Discord/Slack) requesting authorization.
    """
    try:
        triage_id = payload.get("triage_id")
        file_path = payload.get("file_path", "Unknown file")
        reason = payload.get("reason", "Authorization required")

        async with async_session_maker() as db_session:
            from sqlalchemy.future import select
            res_discord = await db_session.execute(
                select(SystemSettings.value).where(SystemSettings.key == "discord_webhook_url")
            )
            discord_url = res_discord.scalars().first()

            res_slack = await db_session.execute(
                select(SystemSettings.value).where(SystemSettings.key == "slack_webhook_url")
            )
            slack_url = res_slack.scalars().first()

            if not (discord_url or slack_url):
                logger.info("No Discord/Slack webhook URLs configured in SystemSettings.")
                return

        embed_payload = {
            "content": f"**Authorization Required**\nFile: `{file_path}`\nReason: {reason}\nAction required: Send a POST request to `/api/triage/{triage_id}/authorize` with a valid API Key to resume processing."
        }

        if discord_url:
            try:
                await webhook_client.post(discord_url, json=embed_payload)
                logger.info(f"Discord webhook sent for {file_path}")
            except Exception as e:
                logger.error(f"Failed to send Discord webhook: {e}")

        if slack_url:
            try:
                await webhook_client.post(slack_url, json={"text": embed_payload["content"]})
                logger.info(f"Slack webhook sent for {file_path}")
            except Exception as e:
                logger.error(f"Failed to send Slack webhook: {e}")
    except Exception as e:
        logger.error(f"Failed to handle auth_required event: {e}", exc_info=True)

async def async_init_notification_engine():
    """
    Async implementation to initialize subscriptions
    """
    await nexus_bus.subscribe("event:consensus_finalized", handle_consensus_finalized)
    await nexus_bus.subscribe("event:remediation_completed", handle_remediation_completed)
    await nexus_bus.subscribe("event:auth_required", handle_auth_required)
    logger.info("Notification engine initialized and subscribed to events.")

def init_notification_engine():
    """
    Initialize the notification module by scheduling the async subscriptions.
    Since we are running inside the FastAPI lifespan context, there's an event loop.
    However, if we are in an async def context we should await it, but main.py calls this synchronously.
    Let's use asyncio.create_task to run the subscription process safely since subscribe itself is an async def.
    """
    asyncio.create_task(async_init_notification_engine())
