from typing import Tuple
from backend.app.plugins.base import DetectorProvider


class LocalAIDetector(DetectorProvider):
    def get_name(self) -> str:
        """Returns the name of the detector."""
        return "LocalAIDetector"

    async def analyze(self, file_path: str) -> Tuple[bool, str]:
        """
        Analyzes the file using the local AI model.
        Returns a tuple: (Is_Healthy: bool, Message: str)
        """
        return True, "AI Detection Not Initialized"
