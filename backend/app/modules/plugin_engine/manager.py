import os
import json
import hashlib
import shutil
import httpx
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.models import Plugin, User
from .schemas import PluginManifest

logger = logging.getLogger(__name__)

PLUGINS_DIR = "/app/data/plugins"
STAGING_DIR = os.path.join(PLUGINS_DIR, ".staging")
BACKUPS_DIR = os.path.join(PLUGINS_DIR, "backups")

os.makedirs(PLUGINS_DIR, exist_ok=True)
os.makedirs(STAGING_DIR, exist_ok=True)
os.makedirs(BACKUPS_DIR, exist_ok=True)

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
            manifest_data = resp.json()
            manifest = PluginManifest(**manifest_data)
        except Exception as e:
            raise Exception(f"Failed to fetch or validate manifest: {e}")

    download_url = manifest.url
    expected_hash = manifest.sha256
    plugin_type = manifest.type
    permissions = manifest.permissions

    if not download_url or not expected_hash:
        raise Exception("Invalid manifest: missing url or sha256")

    ext = ".py" if plugin_type in ["python", "python_native"] else (".so" if plugin_type == "pyo3" else ".wasm")
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

    # 5. Blue/Green swap
    active_file = os.path.join(PLUGINS_DIR, f"{plugin_id}{ext}")
    backup_file = os.path.join(BACKUPS_DIR, f"{plugin_id}{ext}")

    if os.path.exists(active_file):
        shutil.move(active_file, backup_file)

    shutil.move(staging_file, active_file)

    # 6. Save manifest copy
    manifest_file = os.path.join(PLUGINS_DIR, f"{plugin_id}.json")
    with open(manifest_file, "w") as f:
        json.dump(manifest_data, f)

    # 7. Update DB
    result = await db.execute(select(Plugin).where(Plugin.id == plugin_id))
    plugin = result.scalars().first()

    if not plugin:
        plugin = Plugin(
            id=plugin_id,
            name=manifest.name,
            installed_version=manifest.version,
            channel="stable",
            is_active=True,
            source_url=manifest_url,
            is_official=manifest.is_official,
            type=plugin_type,
            permissions=permissions
        )
        db.add(plugin)
    else:
        plugin.installed_version = manifest.version
        plugin.type = plugin_type
        plugin.permissions = permissions
        plugin.source_url = manifest_url
        plugin.is_official = manifest.is_official
        plugin.name = manifest.name

    await db.commit()
    return True
