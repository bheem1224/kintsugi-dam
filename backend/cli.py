import argparse
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select

# We connect directly to the SQLite database.
# Using the same database url logic as core/database.py or just a hardcoded default for rescue
# Since memory says it uses config.py with KINTSUGI_DB_TYPE, we'll try to import config

def main():
    parser = argparse.ArgumentParser(description="Kintsugi-DAM Admin Rescue CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    rescue_parser = subparsers.add_parser("emergency-rescue", help="Forcefully re-enable local admin login")
    rescue_parser.add_argument("--email", required=True, help="Email of the admin user to rescue")

    args = parser.parse_args()

    if args.command == "emergency-rescue":
        asyncio.run(emergency_rescue(args.email))
    else:
        parser.print_help()

async def emergency_rescue(email: str):
    try:
        from app.core.config import settings
        from app.core.models import User

        # We need to construct the URL based on config, just like database.py
        if settings.KINTSUGI_DB_TYPE == "sqlite":
            db_url = f"sqlite+aiosqlite:///{settings.KINTSUGI_DB_NAME}"
        elif settings.KINTSUGI_DB_TYPE == "postgresql":
            db_url = f"postgresql+asyncpg://{settings.KINTSUGI_DB_USER}:{settings.KINTSUGI_DB_PASSWORD}@{settings.KINTSUGI_DB_HOST}/{settings.KINTSUGI_DB_NAME}"
        else:
            db_url = f"mysql+aiomysql://{settings.KINTSUGI_DB_USER}:{settings.KINTSUGI_DB_PASSWORD}@{settings.KINTSUGI_DB_HOST}/{settings.KINTSUGI_DB_NAME}"

        engine = create_async_engine(db_url)
        SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)

        async with SessionLocal() as session:
            result = await session.execute(select(User).where(User.email == email))
            user = result.scalars().first()

            if not user:
                print(f"Error: User with email {email} not found.")
                return

            user.is_local_disabled = False
            await session.commit()
            print(f"Success: Local login has been forcefully re-enabled for {email}.")

    except Exception as e:
        print(f"Error during emergency rescue: {e}")

if __name__ == "__main__":
    main()
