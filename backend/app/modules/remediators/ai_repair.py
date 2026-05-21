from PIL import ImageFile
import os
import base64
import logging
from io import BytesIO
from typing import List, Optional, Dict
from PIL import Image, ExifTags
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.models import MediaFile
from app.core.nexus import nexus_bus

logger = logging.getLogger(__name__)

class AIRepairContext(BaseModel):
    corrupted_file_path: str
    extracted_thumbnail_b64: str
    adjacent_context_paths: List[str]
    camera_profile: Dict[str, str]

def extract_exif_thumbnail_manual(filepath: str) -> Optional[bytes]:
    """
    Fallback method to extract thumbnail via raw binary search of the EXIF segment
    if Pillow's native extraction fails on corrupted images.
    """
    try:
        with open(filepath, 'rb') as f:
            data = f.read(1024 * 512) # Read first 512KB to find EXIF and thumbnail

        # Very basic search for JPEG SOI (Start of Image) inside EXIF
        # This is a naive search as requested by memory/guidelines to manually find b'\xff\xd8'
        # skipping the first SOI which is the main image.

        # Find first SOI
        first_soi = data.find(b'\xff\xd8')
        if first_soi == -1:
            return None

        # Find second SOI (often the thumbnail in EXIF)
        second_soi = data.find(b'\xff\xd8', first_soi + 2)
        if second_soi == -1:
            return None

        # Find EOI (End of Image) for the thumbnail
        eoi = data.find(b'\xff\xd9', second_soi)
        if eoi == -1:
            return None

        thumbnail_bytes = data[second_soi:eoi+2]
        return thumbnail_bytes
    except Exception as e:
        logger.error(f"Manual thumbnail extraction failed: {e}")
        return None

def extract_metadata_and_thumbnail(filepath: str) -> tuple[str, Dict[str, str]]:
    """
    Extracts thumbnail and camera profile from a file.
    Returns (thumbnail_b64, camera_profile)
    """
    camera_profile = {}
    thumbnail_b64 = ""

    try:
        ImageFile.LOAD_TRUNCATED_IMAGES = True

        # Try Pillow native first
        with Image.open(filepath) as img:
            # Parse EXIF for Camera Profile
            exif = img.getexif()
            if exif:
                for tag_id in exif:
                    tag = ExifTags.TAGS.get(tag_id, tag_id)
                    val = exif.get(tag_id)
                    if isinstance(val, bytes):
                        try:
                            val = val.decode('utf-8', 'ignore')
                        except:
                            val = str(val)

                    if tag in ["ISOSpeedRatings", "FNumber", "FocalLength", "Model", "Make", "ExposureTime"]:
                        camera_profile[str(tag)] = str(val)

            # Try to get EXIF thumbnail
            thumb_bytes = img.info.get('exif')
            if hasattr(img, 'get_thumbnail') and img.get_thumbnail(): # Or similar depending on PIL version
                 # Actually, Pillow doesn't have a reliable get_thumbnail() for raw EXIF bytes directly exposed easily
                 # but we can check exif data. Let's rely on the manual binary extraction if needed.
                 pass

        # Fallback to manual extraction for thumbnail
        raw_thumb = extract_exif_thumbnail_manual(filepath)
        if raw_thumb:
            thumbnail_b64 = base64.b64encode(raw_thumb).decode('utf-8')

    except Exception as e:
        logger.error(f"Failed to parse metadata/thumbnail from {filepath}: {e}")

    return thumbnail_b64, camera_profile

async def gather_ai_repair_context(db: AsyncSession, corrupted_file_id: int) -> Optional[AIRepairContext]:
    """
    Gather context surrounding a corrupted file to feed into an AI Remediation Provider.
    """
    result = await db.execute(select(MediaFile).where(MediaFile.id == corrupted_file_id))
    corrupted_file = result.scalars().first()

    if not corrupted_file:
        logger.error(f"Corrupted file ID {corrupted_file_id} not found in DB.")
        return None

    filepath = corrupted_file.filepath

    # 1 & 3: Extract thumbnail and profile
    from PIL import ImageFile
    ImageFile.LOAD_TRUNCATED_IMAGES = True
    thumbnail_b64, camera_profile = extract_metadata_and_thumbnail(filepath)

    # 2: Find adjacent context paths
    # We sort by filename (filepath) or mtime since capture_time isn't reliably parsed into DB columns yet
    adjacent_paths = []

    # File before
    before_res = await db.execute(
        select(MediaFile.filepath)
        .where(MediaFile.filepath < corrupted_file.filepath)
        .order_by(MediaFile.filepath.desc())
        .limit(1)
    )
    before_path = before_res.scalars().first()
    if before_path:
        adjacent_paths.append(before_path)

    # File after
    after_res = await db.execute(
        select(MediaFile.filepath)
        .where(MediaFile.filepath > corrupted_file.filepath)
        .order_by(MediaFile.filepath.asc())
        .limit(1)
    )
    after_path = after_res.scalars().first()
    if after_path:
        adjacent_paths.append(after_path)

    context = AIRepairContext(
        corrupted_file_path=filepath,
        extracted_thumbnail_b64=thumbnail_b64,
        adjacent_context_paths=adjacent_paths,
        camera_profile=camera_profile
    )

    # Broadcast to Connection Layer
    await nexus_bus.broadcast("event:remediator:ai_context_ready", context.model_dump())

    return context
