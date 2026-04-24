import asyncio
from typing import Tuple
from PIL import Image
from app.plugins.base import DetectorProvider


class PillowDeepScanDetector(DetectorProvider):
    def get_name(self) -> str:
        return "Pillow_Deep_Scan"

    def _sync_analyze(self, file_path: str) -> Tuple[bool, str]:
        # Enable loading of truncated images to catch more errors rather than just failing to open
        from PIL import ImageFile

        ImageFile.LOAD_TRUNCATED_IMAGES = True

        try:
            with Image.open(file_path) as img:
                img.verify()

            # verify() doesn't always catch everything, we must reopen to load()
            with Image.open(file_path) as img:
                img.load()

            return True, "Clean"
        except (OSError, SyntaxError):
            return False, "Corrupted: Render Failure"
        except Exception as e:
            return False, f"Corrupted: Unexpected render failure: {str(e)}"

    async def analyze(self, file_path: str) -> Tuple[bool, str]:
        return await asyncio.to_thread(self._sync_analyze, file_path)
