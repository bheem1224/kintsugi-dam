import json
from typing import Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import async_session_maker
from app.core.models import SystemSettings

class SettingsManager:
    @staticmethod
    async def get(key: str, default: Any = None) -> Any:
        async with async_session_maker() as session:
            result = await session.execute(
                select(SystemSettings).where(SystemSettings.key == key)
            )
            setting = result.scalars().first()
            if setting:
                # Try to parse as JSON if it's a list or dict
                if setting.value.startswith("[") or setting.value.startswith("{"):
                    try:
                        return json.loads(setting.value)
                    except json.JSONDecodeError:
                        return setting.value
                return setting.value
            return default

    @staticmethod
    async def set(key: str, value: Any):
        async with async_session_maker() as session:
            result = await session.execute(
                select(SystemSettings).where(SystemSettings.key == key)
            )
            setting = result.scalars().first()

            str_val = value
            if isinstance(value, (dict, list)):
                str_val = json.dumps(value)
            elif not isinstance(value, str):
                str_val = str(value)

            if setting:
                setting.value = str_val
            else:
                new_setting = SystemSettings(key=key, value=str_val)
                session.add(new_setting)

            await session.commit()
