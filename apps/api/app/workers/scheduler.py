import asyncio
import logging
from datetime import datetime, timezone
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.content import ContentSchedule
from app.services.publishing_service import PublishingService

logger = logging.getLogger("pravah.scheduler")

async def run_scheduled_publishing_job():
    """
    Background worker loop that discovers due content schedules
    and safely dispatches them via the publishing pipeline.
    """
    logger.info("Checking for scheduled content items to publish...")
    async with AsyncSessionLocal() as db:
        try:
            now = datetime.now(timezone.utc)
            query = (
                select(ContentSchedule)
                .where(
                    ContentSchedule.scheduled_for <= now,
                    ContentSchedule.is_published == False,
                    ContentSchedule.attempts < ContentSchedule.max_attempts,
                )
                .limit(20)
            )
            res = await db.execute(query)
            due_schedules = res.scalars().all()

            if not due_schedules:
                return

            logger.info(f"Found {len(due_schedules)} content items due for publishing.")
            pub_svc = PublishingService(db)

            for sched in due_schedules:
                try:
                    await pub_svc.publish_content_now(
                        org_id=sched.organisation_id,
                        content_id=sched.content_id,
                    )
                except Exception as ex:
                    logger.error(f"Error publishing scheduled content {sched.content_id}: {str(ex)}")

        except Exception as e:
            logger.error(f"Scheduler job error: {str(e)}")

async def start_scheduler_loop(interval_seconds: int = 30):
    logger.info("Starting PRAVAH Background Scheduler Loop...")
    while True:
        try:
            await run_scheduled_publishing_job()
        except Exception as ex:
            logger.error(f"Unhandled error in scheduler: {str(ex)}")
        await asyncio.sleep(interval_seconds)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(start_scheduler_loop())
