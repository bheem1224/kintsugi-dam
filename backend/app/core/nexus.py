import asyncio
from typing import Callable, Dict, List
import logging

logger = logging.getLogger(__name__)

class NexusEventBus:
    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NexusEventBus, cls).__new__(cls)
            cls._instance.subscribers: Dict[str, List[Callable]] = {}
            cls._instance.is_active = False
        return cls._instance

    def initialize(self):
        self.is_active = True
        logger.info("Nexus Event Bus initialized.")

    def disable(self):
        self.is_active = False
        self.subscribers.clear()
        logger.info("Nexus Event Bus disabled.")

    async def subscribe(self, event_name: str, callback: Callable):
        if not self.is_active:
            return
        async with self._lock:
            if event_name not in self.subscribers:
                self.subscribers[event_name] = []
            self.subscribers[event_name].append(callback)
            logger.debug(f"Subscribed to {event_name}")

    async def broadcast(self, event_name: str, payload: dict):
        if not self.is_active:
            return
        logger.debug(f"Broadcasting event {event_name}")
        callbacks = []
        async with self._lock:
            if event_name in self.subscribers:
                callbacks = self.subscribers[event_name].copy()

        for callback in callbacks:
            try:
                await callback(payload)
            except Exception as e:
                logger.error(f"Error executing callback for event {event_name}: {e}")

nexus_bus = NexusEventBus()
