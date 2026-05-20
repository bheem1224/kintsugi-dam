import logging
from typing import List, Callable
from app.core.nexus import nexus_bus

logger = logging.getLogger(__name__)

class SandboxViolationError(Exception):
    pass

class SandboxProxyBus:
    def __init__(self, plugin_id: str, permissions: List[str]):
        self.plugin_id = plugin_id
        self.permissions = permissions

    async def subscribe(self, event_name: str, callback: Callable):
        required_permission = f"event:{event_name}:subscribe"
        if required_permission not in self.permissions:
            logger.critical(
                f"SECURITY WARNING: Plugin '{self.plugin_id}' attempted to subscribe to "
                f"'{event_name}' without the '{required_permission}' permission."
            )
            raise SandboxViolationError(f"Missing permission: {required_permission}")

        await nexus_bus.subscribe(event_name, callback)

    async def broadcast(self, event_name: str, payload: dict):
        required_permission = f"event:{event_name}:publish"
        if required_permission not in self.permissions:
            logger.critical(
                f"SECURITY WARNING: Plugin '{self.plugin_id}' attempted to broadcast "
                f"'{event_name}' without the '{required_permission}' permission."
            )
            raise SandboxViolationError(f"Missing permission: {required_permission}")

        await nexus_bus.broadcast(event_name, payload)
