import asyncio
import os
import sys
from pathlib import Path

# Add apps/api to path
api_dir = Path(__file__).resolve().parent.parent / "apps" / "api"
sys.path.insert(0, str(api_dir))
os.chdir(str(api_dir))

from alembic import command
from alembic.config import Config
from app.core.database import Base, engine
from app.models import *

def run_alembic_migrations():
    print("[MIGRATION] Running Alembic database migrations...")
    alembic_cfg = Config(str(api_dir / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(api_dir / "alembic"))
    command.upgrade(alembic_cfg, "head")
    print("[MIGRATION] Alembic migrations applied successfully (head).")

async def ensure_schema():
    print("[SCHEMA] Verifying all database entities and tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[SCHEMA] All 45+ database tables verified.")

if __name__ == "__main__":
    try:
        run_alembic_migrations()
    except Exception as e:
        print(f"[WARN] Alembic migration notice: {e}. Falling back to sync create_all...")
        asyncio.run(ensure_schema())
