import hashlib
from concurrent.futures import ProcessPoolExecutor

# Global ProcessPoolExecutor to avoid blocking the asyncio event loop on teardown
hash_pool = ProcessPoolExecutor()

def calculate_sha256(file_path: str) -> str:
    """
    Synchronously calculates the SHA-256 hash of a file.
    Reads the file in 64KB chunks to maintain a low memory footprint
    for large files (e.g., massive video files).
    """
    sha256_hash = hashlib.sha256()

    with open(file_path, "rb") as f:
        # Read and update hash string value in blocks of 64K
        for byte_block in iter(lambda: f.read(65536), b""):
            sha256_hash.update(byte_block)

    return sha256_hash.hexdigest()
