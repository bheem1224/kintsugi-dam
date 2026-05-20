import logging
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .models import SystemSettings

logger = logging.getLogger(__name__)


async def send_notification(message: str, db_session: AsyncSession):
    try:
        discord_res = await db_session.execute(
            select(SystemSettings.value).where(SystemSettings.key == "discord_webhook_url")
        )
        discord_webhook_url = discord_res.scalars().first()

        ntfy_res = await db_session.execute(
            select(SystemSettings.value).where(SystemSettings.key == "ntfy_topic_url")
        )
        ntfy_topic_url = ntfy_res.scalars().first()

        async with httpx.AsyncClient() as client:
            if discord_webhook_url:
                try:
                    payload = {"content": message}
                    response = await client.post(
                        discord_webhook_url, json=payload
                    )
                    response.raise_for_status()
                except Exception as e:
                    logger.error(f"Failed to send Discord notification: {e}")

            if ntfy_topic_url:
                try:
                    headers = {"Title": "Kintsugi-DAM Alert"}
                    data = message.encode("utf-8")
                    response = await client.post(
                        ntfy_topic_url, data=data, headers=headers
                    )
                    response.raise_for_status()
                except Exception as e:
                    logger.error(f"Failed to send Ntfy notification: {e}")

    except Exception as e:
        logger.error(f"An unexpected error occurred in send_notification: {e}")
