import os
import shutil
import importlib.util
import wasmtime
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .models import Plugin
from .nexus import nexus_bus
from .plugin_manager import PLUGINS_DIR, BACKUPS_DIR

logger = logging.getLogger(__name__)

class PluginManager:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.engine = wasmtime.Engine()
        self.wasm_modules = {}

    async def initialize_plugins(self):
        result = await self.db.execute(select(Plugin).where(Plugin.is_active == True))
        plugins = result.scalars().all()

        for plugin in plugins:
            try:
                await self._load_plugin(plugin)
            except Exception as e:
                logger.error(f"Failed to load plugin {plugin.id}: {e}. Rolling back.")
                await self._rollback_plugin(plugin)

    async def _load_plugin(self, plugin: Plugin):
        ext = ".py" if plugin.type == "python" else ".wasm"
        file_path = os.path.join(PLUGINS_DIR, f"{plugin.id}{ext}")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Plugin file not found: {file_path}")

        if plugin.type == "wasm":
            with open(file_path, "rb") as f:
                wasm_bytes = f.read()
            module = wasmtime.Module(self.engine, wasm_bytes)
            # Basic loading, advanced instantiating can be expanded
            self.wasm_modules[plugin.id] = module
            logger.info(f"Loaded WASM plugin: {plugin.id}")

        elif plugin.type == "python":
            spec = importlib.util.spec_from_file_location(plugin.id, file_path)
            if not spec or not spec.loader:
                raise ImportError(f"Could not load spec for {plugin.id}")

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Register to Nexus Event Bus if method exists
            if hasattr(module, "register"):
                await module.register(nexus_bus)
            logger.info(f"Loaded Python plugin: {plugin.id}")

    async def _rollback_plugin(self, plugin: Plugin):
        ext = ".py" if plugin.type == "python" else ".wasm"
        active_file = os.path.join(PLUGINS_DIR, f"{plugin.id}{ext}")
        backup_file = os.path.join(BACKUPS_DIR, f"{plugin.id}{ext}")

        if os.path.exists(backup_file):
            logger.info(f"Restoring backup for {plugin.id}")
            if os.path.exists(active_file):
                os.remove(active_file)
            shutil.copy(backup_file, active_file)

            try:
                await self._load_plugin(plugin)
                logger.info(f"Successfully rolled back {plugin.id}")
                return
            except Exception as e:
                logger.error(f"Backup failed to load for {plugin.id}: {e}")

        logger.error(f"Disabling plugin {plugin.id}")
        plugin.is_active = False
        await self.db.commit()

