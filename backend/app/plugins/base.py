from abc import ABC, abstractmethod
from typing import Tuple, Optional


class DetectorProvider(ABC):
    @abstractmethod
    def get_name(self) -> str:
        """Returns the name of the detector (e.g., 'ImageMagick')."""
        pass

    @abstractmethod
    async def analyze(self, file_path: str) -> Tuple[bool, str]:
        """
        Analyzes the file for structural integrity.
        Returns a tuple: (Is_Healthy: bool, Message: str)
        """
        pass


class RemediationProvider(ABC):
    @abstractmethod
    def get_name(self) -> str:
        """Returns the name of the provider (e.g., 'ZFS_Local')."""
        pass

    @abstractmethod
    async def find_clean_version(
        self, file_path: str, known_good_hash: str
    ) -> Optional[str]:
        """
        Searches the backup source for a clean version of the file.
        Returns the URI/Path to the clean file if found, otherwise None.
        """
        pass

    @abstractmethod
    async def restore_file(self, backup_uri: str, live_destination: str) -> bool:
        """
        Executes the actual restoration (copying, downloading) from the backup source
        to the live/quarantine destination. Returns True if successful.
        """
        pass
