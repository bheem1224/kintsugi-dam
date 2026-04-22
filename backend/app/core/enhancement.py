import asyncio
import logging
from PIL import Image, ImageFilter, ImageChops
import numpy as np

logger = logging.getLogger(__name__)


async def pre_enhance_thumbnail(thumb_path: str, output_path: str) -> None:
    """
    Uses Pillow's resize (LANCZOS) to double the resolution and applies ImageFilter.SHARPEN.
    """

    def _enhance_sync():
        try:
            with Image.open(thumb_path) as img:
                # Convert to RGB to ensure we can apply filters properly
                if img.mode != "RGB":
                    img = img.convert("RGB")

                new_size = (img.width * 2, img.height * 2)
                enhanced = img.resize(new_size, Image.Resampling.LANCZOS)
                enhanced = enhanced.filter(ImageFilter.SHARPEN)
                enhanced.save(output_path)
        except Exception as e:
            logger.error(f"Thumbnail enhancement failed: {e}")
            raise

    await asyncio.to_thread(_enhance_sync)


async def apply_synthetic_grain(
    repaired_image_path: str, original_exif_path: str
) -> None:
    """
    Extracts the ISO from original_exif_path (default 400).
    Uses numpy to generate a Gaussian noise matrix scaled by ISO (ISO 100 as baseline),
    converts it to a PIL Image, and blends it over the repaired image using ImageChops.overlay().
    Saves in-place.
    """

    def _apply_grain_sync():
        try:
            iso = 400
            # Try to extract ISO from original_exif_path
            try:
                with Image.open(original_exif_path) as orig:
                    exif = orig.getexif()
                    if exif:
                        # Standard EXIF tag for ISOSpeedRatings is 34855
                        if 34855 in exif:
                            val = exif[34855]
                            if isinstance(val, int):
                                iso = val
                            elif isinstance(val, tuple) and len(val) > 0:
                                iso = val[0]
            except Exception:
                pass  # Use default 400 if we can't read it

            # Scale variance/intensity linearly based on ISO 100 baseline
            # e.g. ISO 100 -> multiplier 1, ISO 800 -> multiplier 8
            iso = max(100, iso)  # avoid weird math if ISO is 0
            multiplier = iso / 100.0

            # Create noise matrix
            with Image.open(repaired_image_path) as repaired:
                if repaired.mode != "RGB":
                    repaired = repaired.convert("RGB")

                width, height = repaired.size

                # We want a mid-gray background with noise
                # Baseline std_dev for ISO 100 could be 4
                std_dev = 4.0 * multiplier

                # Generate gaussian noise
                noise = np.random.normal(128, std_dev, (height, width, 3))
                # Clip to 0-255 range and convert to uint8
                noise = np.clip(noise, 0, 255).astype(np.uint8)

                noise_img = Image.fromarray(noise, mode="RGB")

                # Blend with overlay
                blended = ImageChops.overlay(repaired, noise_img)

                blended.save(repaired_image_path)

        except Exception as e:
            logger.error(f"Applying synthetic grain failed: {e}")
            raise

    await asyncio.to_thread(_apply_grain_sync)
