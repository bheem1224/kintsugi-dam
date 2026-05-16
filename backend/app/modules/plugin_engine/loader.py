import os
import importlib.util
import wasmtime
import logging
import ast
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.models import Plugin
from .proxy_bus import SandboxProxyBus

logger = logging.getLogger(__name__)

PLUGINS_DIR = "/app/data/plugins"

class StrictASTValidator(ast.NodeVisitor):
    def __init__(self):
        self.banned_modules = {"os", "sys", "subprocess", "socket", "builtins"}

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name.split(".")[0] in self.banned_modules:
                raise ValueError(f"Banned import detected: {alias.name}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module and node.module.split(".")[0] in self.banned_modules:
            raise ValueError(f"Banned import detected: {node.module}")
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            if node.func.id in {"eval", "exec", "__import__", "getattr", "setattr", "delattr"}:
                raise ValueError(f"Banned function call detected: {node.func.id}")
        self.generic_visit(node)


class PluginLoader:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.engine = wasmtime.Engine()
        self.loaded_modules = {}

    async def initialize_plugins(self):
        result = await self.db.execute(select(Plugin).where(Plugin.is_active == True))
        plugins = result.scalars().all()

        for plugin in plugins:
            try:
                await self._load_plugin(plugin)
            except Exception as e:
                logger.error(f"Failed to load plugin {plugin.id}: {e}.")

    async def _load_plugin(self, plugin: Plugin):
        permissions = plugin.permissions or []
        proxy_bus = SandboxProxyBus(plugin_id=plugin.id, permissions=permissions)

        if plugin.type == "wasm":
            await self._load_wasm(plugin, proxy_bus)
        elif plugin.type == "python":
            await self._load_python_restricted(plugin, proxy_bus)
        elif plugin.type == "python_native":
            await self._load_python_native(plugin, proxy_bus)
        elif plugin.type == "pyo3":
            await self._load_pyo3(plugin, proxy_bus)
        else:
            logger.error(f"Unknown plugin type: {plugin.type} for plugin {plugin.id}")

    async def _load_wasm(self, plugin: Plugin, proxy_bus: SandboxProxyBus):
        file_path = os.path.join(PLUGINS_DIR, f"{plugin.id}.wasm")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"WASM plugin file not found: {file_path}")

        # Basic validation
        with open(file_path, "rb") as f:
            wasm_bytes = f.read()
        wasmtime.Module.validate(self.engine, wasm_bytes)
        module = wasmtime.Module(self.engine, wasm_bytes)

        # Storing for reference, advanced execution via proxy_bus bindings can be expanded
        self.loaded_modules[plugin.id] = module
        logger.info(f"Loaded WASM plugin: {plugin.id}")

    async def _load_python_restricted(self, plugin: Plugin, proxy_bus: SandboxProxyBus):
        file_path = os.path.join(PLUGINS_DIR, f"{plugin.id}.py")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Python plugin file not found: {file_path}")

        # AST Validation
        with open(file_path, "r") as f:
            source = f.read()
        tree = ast.parse(source)
        validator = StrictASTValidator()
        validator.visit(tree)

        await self._import_and_register(plugin.id, file_path, proxy_bus)

    async def _load_python_native(self, plugin: Plugin, proxy_bus: SandboxProxyBus):
        if "system:native_execution" not in proxy_bus.permissions:
             raise ValueError(f"Plugin {plugin.id} requires 'system:native_execution' permission.")

        file_path = os.path.join(PLUGINS_DIR, f"{plugin.id}.py")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Python native plugin file not found: {file_path}")

        await self._import_and_register(plugin.id, file_path, proxy_bus)

    async def _load_pyo3(self, plugin: Plugin, proxy_bus: SandboxProxyBus):
        if "system:native_execution" not in proxy_bus.permissions:
             raise ValueError(f"Plugin {plugin.id} requires 'system:native_execution' permission.")

        # Look for .so or .pyd (Windows)
        so_path = os.path.join(PLUGINS_DIR, f"{plugin.id}.so")
        pyd_path = os.path.join(PLUGINS_DIR, f"{plugin.id}.pyd")

        file_path = so_path if os.path.exists(so_path) else pyd_path

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PyO3 plugin file not found: {file_path}")

        await self._import_and_register(plugin.id, file_path, proxy_bus)

    async def _import_and_register(self, plugin_id: str, file_path: str, proxy_bus: SandboxProxyBus):
        spec = importlib.util.spec_from_file_location(plugin_id, file_path)
        if not spec or not spec.loader:
            raise ImportError(f"Could not load spec for {plugin_id}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Register to Nexus Event Bus using the SandboxProxyBus
        if hasattr(module, "register"):
            await module.register(proxy_bus)

        self.loaded_modules[plugin_id] = module
        logger.info(f"Loaded native/python plugin: {plugin_id}")
