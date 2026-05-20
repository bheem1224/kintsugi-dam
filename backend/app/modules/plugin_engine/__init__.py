from sqlalchemy.ext.asyncio import AsyncSession
from .loader import PluginLoader
import logging

logger = logging.getLogger(__name__)

async def initialize(db_session: AsyncSession):
    """
    Bootstraps the plugin engine.
    """
    logger.info("Initializing Plugin Engine...")
    loader = PluginLoader(db_session)
    await loader.initialize_plugins()
    logger.info("Plugin Engine initialization complete.")
    return loader
