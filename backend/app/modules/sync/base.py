import abc

class ISyncProvider(abc.ABC):
    """
    Base interface for external state sync providers.
    """

    @abc.abstractmethod
    async def handle_deletion(self, payload: dict):
        """
        Handle a deletion webhook payload from the provider.
        """
        pass
