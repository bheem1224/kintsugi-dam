import asyncio
import os
import logging
from PIL import Image, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True

logger = logging.getLogger(__name__)


async def attempt_header_graft(
    corrupted_path: str, reference_path: str, output_path: str
) -> bool:
    """
    Test if the corrupted image opens with PIL.Image.open(). If it fails, read a healthy
    reference image, find the JPEG Start of Scan (SOS) marker b'\xff\xda', slice off the
    healthy header, and graft it onto the corrupted file's payload. Test if the new file
    opens, and return a boolean.
    """

    def _graft_sync() -> bool:
        try:
            with Image.open(corrupted_path) as img:
                img.load()
            return True
        except Exception:
            pass

        try:
            with open(reference_path, "rb") as f:
                ref_data = f.read()
            with open(corrupted_path, "rb") as f:
                corr_data = f.read()

            sos_marker = b"\xff\xda"

            ref_sos_idx = ref_data.find(sos_marker)
            if ref_sos_idx == -1:
                return False

            corr_sos_idx = corr_data.find(sos_marker)
            if corr_sos_idx == -1:
                return False

            grafted_data = ref_data[:ref_sos_idx] + corr_data[corr_sos_idx:]

            with open(output_path, "wb") as f:
                f.write(grafted_data)

            with Image.open(output_path) as img:
                img.load()
            return True
        except Exception as e:
            logger.error(f"Grafting failed: {e}")
            return False

    return await asyncio.to_thread(_graft_sync)


async def extract_exif_thumbnail(file_path: str, output_dir: str) -> str | None:
    """
    Safely open the image, check if it contains EXIF data and an embedded thumbnail.
    Extract the binary data, save it to output_dir as {original_filename}_thumb.jpg,
    and return the path. Wrap in a broad try/except block.
    """

    def _extract_sync() -> str | None:
        try:
            with Image.open(file_path) as img:
                exif_dict = img.info.get("exif")
                if not exif_dict:
                    return None

                # We need to manually parse the EXIF data to find the thumbnail
                # EXIF thumbnail is typically stored as JPEGInterchangeFormat (0x0201 or 513)
                # and JPEGInterchangeFormatLength (0x0202 or 514)
                # Pillow's Exif object exposes a way to get the IFD dicts, but it's internal.

                # A simple binary scan for the thumbnail SOI marker (FF D8) after the EXIF header
                # EXIF header is "Exif\x00\x00"
                # This is a lightweight fallback approach if Pillow doesn't provide get_thumbnail.

                # However, many EXIF chunks contain an embedded thumbnail starting with FF D8 FF E0
                # Let's search the raw EXIF bytes for the JPEG start marker.
                # A proper EXIF thumbnail is a full JPEG file embedded within the EXIF.

                # Search for start of image marker inside EXIF data
                # Since the first FFD8 is the main image (but we are in the EXIF APP1 segment),
                # the EXIF segment itself contains a thumbnail JPEG starting with FFD8.
                thumb_start = exif_dict.find(b"\xff\xd8")
                if thumb_start != -1:
                    # To be safer, we should also find the end marker. But write to EOF of EXIF is usually fine.
                    thumb_data = exif_dict[thumb_start:]

                    filename = os.path.basename(file_path)
                    name, _ = os.path.splitext(filename)
                    output_path = os.path.join(output_dir, f"{name}_thumb.jpg")

                    with open(output_path, "wb") as f:
                        f.write(thumb_data)
                    return output_path
                return None
        except Exception as e:
            logger.error(f"Failed to extract thumbnail: {e}")
            return None

    return await asyncio.to_thread(_extract_sync)


async def salvage_ghost_data(file_path: str, output_path: str) -> bool:
    """
    Force-render truncated data and save it.
    """

    def _salvage_sync() -> bool:
        try:
            with Image.open(file_path) as img:
                img.load()
                img.save(output_path)
            return True
        except Exception as e:
            logger.error(f"Salvage failed: {e}")
            return False

    return await asyncio.to_thread(_salvage_sync)


async def scan_for_rst_markers(file_path: str) -> list[int]:
    """
    Reads the file in binary mode and returns byte offsets for JPEG Restart Markers
    (b'\xff\xd0' through b'\xff\xd7').
    """

    def _scan_sync() -> list[int]:
        offsets = []
        try:
            with open(file_path, "rb") as f:
                data = f.read()

            for i in range(len(data) - 1):
                if data[i] == 0xFF and 0xD0 <= data[i + 1] <= 0xD7:
                    offsets.append(i)
        except Exception as e:
            logger.error(f"Scan failed: {e}")
        return offsets

    return await asyncio.to_thread(_scan_sync)
