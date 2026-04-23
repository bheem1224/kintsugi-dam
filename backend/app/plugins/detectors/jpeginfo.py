import asyncio
from typing import Tuple
from app.plugins.base import DetectorProvider


class JpegInfoDetector(DetectorProvider):
    def get_name(self) -> str:
        return "JpegInfo"

    async def analyze(self, file_path: str) -> Tuple[bool, str]:
        try:
            process = await asyncio.create_subprocess_exec(
                "jpeginfo",
                "-c",
                file_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            output = stdout.decode("utf-8", errors="ignore")

            if "[OK]" in output:
                return True, "Clean"
            elif "[WARNING]" in output or "[ERROR]" in output:
                # Extract the error message, usually after the file name
                parts = output.split(file_path, 1)
                error_msg = parts[1].strip() if len(parts) > 1 else output.strip()
                return False, f"Corrupted: {error_msg}"
            else:
                return False, f"Corrupted: Unknown error output: {output.strip()}"
        except FileNotFoundError:
            return False, "Corrupted: jpeginfo command not found. Is it installed?"
        except Exception as e:
            return False, f"Corrupted: JpegInfo execution failed: {str(e)}"
