import importlib
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .models import SystemSettings

logger = logging.getLogger(__name__)

class ModuleLoader:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModuleLoader, cls).__new__(cls)
            cls._instance.engine_instance = None
        return cls._instance

    async def boot_plugins(self, db_session: AsyncSession):
        """
        Dynamically imports the plugin_engine module if enabled in SystemSettings.
        Avoids memory overhead if plugins are disabled.
        """
        result = await db_session.execute(
            select(SystemSettings.value).where(SystemSettings.key == "enable_3rd_party_plugins")
        )
        val = result.scalars().first()
        enable_3rd_party_plugins = val.lower() == "true" if val else False

        if enable_3rd_party_plugins:
            logger.info("3rd-party plugins are enabled. Loading plugin_engine module...")
            try:
                plugin_engine = importlib.import_module("app.modules.plugin_engine")
                self.engine_instance = await plugin_engine.initialize(db_session)
            except Exception as e:
                logger.error(f"Failed to load or initialize plugin_engine module: {e}")
        else:
            logger.info("3rd-party plugins are disabled. Skipping plugin_engine load.")

module_loader = ModuleLoader()
