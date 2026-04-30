import os
import json
import logging
import wasmtime
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

class PluginManager:
    def __init__(self, db_session):
        self.db_session = db_session
        self.plugins_dir = "/app/data/plugins"
        self.engine = wasmtime.Engine()
        self.store = wasmtime.Store(self.engine)
        self.linker = wasmtime.Linker(self.engine)
        self.loaded_modules: dict[str, Tuple[str, str]] = {} # id -> (name, version)

        self._setup_directories()
        self._register_host_functions()

    def _setup_directories(self):
        os.makedirs(self.plugins_dir, exist_ok=True)
        os.makedirs("/app/data", exist_ok=True)

    def _register_host_functions(self):
        def host_log(caller, level: int, ptr: int, length: int):
            mem = caller.get("memory")
            if not mem:
                logger.error("host_log failed: no memory exported")
                return
            try:
                # `read` method args: store, start, stop
                msg_bytes = mem.read(caller, ptr, ptr + length)
                msg = msg_bytes.decode("utf-8", errors="replace")

                if level == 0:
                    logger.debug(f"[WASM] {msg}")
                elif level == 1:
                    logger.info(f"[WASM] {msg}")
                elif level == 2:
                    logger.warning(f"[WASM] {msg}")
                else:
                    logger.error(f"[WASM] {msg}")
            except Exception as e:
                logger.error(f"host_log exception: {e}")

        def host_read_media_chunk(caller, file_path_ptr: int, file_path_len: int, offset: int, length: int) -> int:
            mem = caller.get("memory")
            if not mem:
                logger.error("host_read_media_chunk failed: no memory exported")
                return 0

            try:
                # `read` method args: store, start, stop
                path_bytes = mem.read(caller, file_path_ptr, file_path_ptr + file_path_len)
                file_path = path_bytes.decode("utf-8", errors="replace")

                # Security check: strict resolution to /media/
                resolved_path = os.path.abspath(file_path)
                if not resolved_path.startswith("/media/"):
                    logger.error(f"Path traversal attempt blocked: {file_path}")
                    return 0

                if not os.path.exists(resolved_path):
                    logger.error(f"File not found: {resolved_path}")
                    return 0

                with open(resolved_path, "rb") as f:
                    f.seek(offset)
                    chunk_data = f.read(length)

                alloc_func = caller.get("alloc")
                if not alloc_func:
                    logger.error("host_read_media_chunk failed: no 'alloc' exported from WASM")
                    return 0

                # Allocate space in WASM memory
                # We need to call the WASM function
                dest_ptr = alloc_func(caller, len(chunk_data))

                # Write chunk to WASM memory
                # write args: store, value, start
                mem.write(caller, chunk_data, dest_ptr)
                return dest_ptr

            except Exception as e:
                logger.error(f"host_read_media_chunk exception: {e}")
                return 0

        self.linker.define_func("env", "host_log",
            wasmtime.FuncType([wasmtime.ValType.i32(), wasmtime.ValType.i32(), wasmtime.ValType.i32()], []),
            host_log)

        self.linker.define_func("env", "host_read_media_chunk",
            wasmtime.FuncType([wasmtime.ValType.i32(), wasmtime.ValType.i32(), wasmtime.ValType.i32(), wasmtime.ValType.i32()], [wasmtime.ValType.i32()]),
            host_read_media_chunk)

    async def initialize_plugins(self):
        from .models import Plugin
        from sqlalchemy import select

        for item in os.listdir(self.plugins_dir):
            plugin_path = os.path.join(self.plugins_dir, item)
            if not os.path.isdir(plugin_path):
                continue

            manifest_path = os.path.join(plugin_path, "manifest.json")
            if not os.path.exists(manifest_path):
                logger.warning(f"Plugin {item} lacks a manifest.json. Skipping.")
                continue

            try:
                with open(manifest_path, "r") as f:
                    manifest = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to parse manifest in {item}: {e}")
                continue

            # Validate required keys
            required_keys = ["id", "name", "version", "entrypoint", "min_kintsugi_version", "permissions"]
            missing_keys = [k for k in required_keys if k not in manifest]
            if missing_keys:
                logger.warning(f"Plugin {item} manifest missing keys: {missing_keys}. Skipping.")
                continue

            plugin_id = manifest["id"]

            # Check if enabled in DB
            result = await self.db_session.execute(select(Plugin).where(Plugin.plugin_id == plugin_id))
            db_plugin = result.scalars().first()

            if not db_plugin or not db_plugin.is_enabled:
                logger.debug(f"Plugin {plugin_id} is not enabled in database. Skipping.")
                continue

            entrypoint_path = os.path.join(plugin_path, manifest["entrypoint"])
            if not os.path.exists(entrypoint_path):
                logger.error(f"Entrypoint {manifest['entrypoint']} for plugin {plugin_id} not found. Skipping.")
                continue

            try:
                module = wasmtime.Module.from_file(self.engine, entrypoint_path)
                instance = self.linker.instantiate(self.store, module)
                self.loaded_modules[plugin_id] = (manifest["name"], manifest["version"])
            except Exception as e:
                logger.error(f"Failed to instantiate plugin {plugin_id}: {e}")

        if self.loaded_modules:
            loaded_str = ", ".join([f"{name} (v{ver})" for _, (name, ver) in self.loaded_modules.items()])
            logger.info(f"Successfully loaded WASM plugins: {loaded_str}")
        else:
            logger.info("No WASM plugins loaded.")
