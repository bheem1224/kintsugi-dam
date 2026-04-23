import asyncio
import os
import sys
import shutil

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from app.core.scanner import run_scan
from app.core.database import async_session_maker, engine, Base


async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def test_path_traversal():
    await setup_db()

    os.makedirs("test_scan_dir", exist_ok=True)

    malicious_filename = "test_scan_dir/..%2f..%2f..%2fetc%2fpasswd"
    with open(malicious_filename, "w") as f:
        f.write("fake content")

    async with async_session_maker() as session:
        result = await run_scan("test_scan_dir", session)
        print(f"Scan result: {result}")

    async with async_session_maker() as session:
        from app.core.models import MediaFile
        from sqlalchemy import select

        records = await session.execute(select(MediaFile))
        for r in records.scalars().all():
            print(f"Stored filepath: {r.filepath}")


if __name__ == "__main__":
    try:
        asyncio.run(test_path_traversal())
    finally:
        if os.path.exists("test_scan_dir"):
            shutil.rmtree("test_scan_dir")
        if os.path.exists("data/kintsugi.db"):
            os.remove("data/kintsugi.db")
        if os.path.exists("data/kintsugi.db-shm"):
            os.remove("data/kintsugi.db-shm")
        if os.path.exists("data/kintsugi.db-wal"):
            os.remove("data/kintsugi.db-wal")
