import logging
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .models import SystemSettings

logger = logging.getLogger(__name__)

async def send_notification(message: str, db_session: AsyncSession):
    try:
        result = await db_session.execute(
            select(SystemSettings).where(SystemSettings.id == 1)
        )
        settings = result.scalar_one_or_none()

        if not settings:
            logger.warning("SystemSettings not found (id=1). Notifications will not be sent.")
            return

        async with httpx.AsyncClient() as client:
            if settings.discord_webhook_url:
                try:
                    payload = {"content": message}
                    response = await client.post(settings.discord_webhook_url, json=payload)
                    response.raise_for_status()
                except Exception as e:
                    logger.error(f"Failed to send Discord notification: {e}")

            if settings.ntfy_topic_url:
                try:
                    headers = {"Title": "Kintsugi-DAM Alert"}
                    data = message.encode("utf-8")
                    response = await client.post(settings.ntfy_topic_url, data=data, headers=headers)
                    response.raise_for_status()
                except Exception as e:
                    logger.error(f"Failed to send Ntfy notification: {e}")

    except Exception as e:
        logger.error(f"An unexpected error occurred in send_notification: {e}")
