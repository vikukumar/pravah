import asyncio
import os
import sys
from pathlib import Path

# Add apps/api to path
api_dir = Path(__file__).resolve().parent.parent / "apps" / "api"
sys.path.insert(0, str(api_dir))
os.chdir(str(api_dir))

from app.core.database import Base, engine
from app.models import *

async def main():
    print("Resetting PRAVAH database for initial setup wizard...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("[SUCCESS] Database cleared! You can now open http://localhost:3000/setup to run the first-time setup wizard.")

if __name__ == "__main__":
    asyncio.run(main())
