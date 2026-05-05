import os
import json
import hashlib
import shutil
import ast
import httpx
import logging
import wasmtime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .models import Plugin, User

logger = logging.getLogger(__name__)

PLUGINS_DIR = "/app/data/plugins"
STAGING_DIR = os.path.join(PLUGINS_DIR, ".staging")
BACKUPS_DIR = os.path.join(PLUGINS_DIR, "backups")

os.makedirs(PLUGINS_DIR, exist_ok=True)
os.makedirs(STAGING_DIR, exist_ok=True)
os.makedirs(BACKUPS_DIR, exist_ok=True)


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


async def install_plugin(
    plugin_id: str,
    manifest_url: str,
    db: AsyncSession
) -> bool:
    # 1. Verify Pro status
    admin_result = await db.execute(select(User).where(User.role == "admin", User.is_pro == True))
    if not admin_result.scalars().first():
        raise Exception("403: Pro license required for plugins")

    # 2. Download manifest
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(manifest_url)
            resp.raise_for_status()
            manifest = resp.json()
        except Exception as e:
            raise Exception(f"Failed to fetch manifest: {e}")

    download_url = manifest.get("url")
    expected_hash = manifest.get("sha256")
    plugin_type = manifest.get("type", "wasm")
    is_privileged = manifest.get("privileged_mode", False)

    if not download_url or not expected_hash:
        raise Exception("Invalid manifest: missing url or sha256")

    ext = ".py" if plugin_type == "python" else ".wasm"
    staging_file = os.path.join(STAGING_DIR, f"{plugin_id}{ext}")

    # 3. Download plugin binary/script
    async with httpx.AsyncClient() as client:
        try:
            with open(staging_file, "wb") as f:
                async with client.stream("GET", download_url) as r:
                    r.raise_for_status()
                    for chunk in r.iter_bytes():
                        f.write(chunk)
        except Exception as e:
            if os.path.exists(staging_file):
                os.remove(staging_file)
            raise Exception(f"Failed to download plugin: {e}")

    # 4. Validate SHA256
    hasher = hashlib.sha256()
    with open(staging_file, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)

    if hasher.hexdigest() != expected_hash:
        os.remove(staging_file)
        raise Exception("SHA256 validation failed")

    # 5. Staging test / validation
    try:
        if plugin_type == "wasm":
            engine = wasmtime.Engine()
            wasmtime.Module.validate(engine, open(staging_file, "rb").read())
        elif plugin_type == "python":
            with open(staging_file, "r") as f:
                source = f.read()
            tree = ast.parse(source)
            if not is_privileged:
                validator = StrictASTValidator()
                validator.visit(tree)
    except Exception as e:
        os.remove(staging_file)
        raise Exception(f"Validation failed: {e}")

    # 6. Blue/Green swap
    active_file = os.path.join(PLUGINS_DIR, f"{plugin_id}{ext}")
    backup_file = os.path.join(BACKUPS_DIR, f"{plugin_id}{ext}")

    if os.path.exists(active_file):
        shutil.move(active_file, backup_file)

    shutil.move(staging_file, active_file)

    # 7. Save manifest copy
    manifest_file = os.path.join(PLUGINS_DIR, f"{plugin_id}.json")
    with open(manifest_file, "w") as f:
        json.dump(manifest, f)

    # 8. Update DB
    result = await db.execute(select(Plugin).where(Plugin.id == plugin_id))
    plugin = result.scalars().first()

    if not plugin:
        plugin = Plugin(
            id=plugin_id,
            name=manifest.get("name", plugin_id),
            installed_version=manifest.get("version", "1.0.0"),
            channel="stable",
            is_active=True,
            source_url=manifest_url,
            is_official=manifest.get("is_official", False),
            type=plugin_type,
            is_privileged=is_privileged
        )
        db.add(plugin)
    else:
        plugin.installed_version = manifest.get("version", "1.0.0")
        plugin.type = plugin_type
        plugin.is_privileged = is_privileged
        plugin.source_url = manifest_url
        plugin.is_official = manifest.get("is_official", False)
        plugin.name = manifest.get("name", plugin.name)

    await db.commit()
    return True
