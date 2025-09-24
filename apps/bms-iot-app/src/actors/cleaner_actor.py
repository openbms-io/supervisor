from src.utils.logger import logger
import asyncio
from src.actors.messages.actor_queue_registry import ActorQueueRegistry
from src.actors.messages.message_type import ActorName
from src.models.controller_points import delete_uploaded_points


class CleanerActor:
    def __init__(self, actor_queue_registry: ActorQueueRegistry):
        self.actor_queue_registry = actor_queue_registry
        self.actor_name = ActorName.CLEANER
        self.keep_running = True

    async def start(self):
        await self._run_monitor_loop()

    async def _run_monitor_loop(self):
        logger.info("CleanerActor started")

        while self.keep_running:
            await self.delete_uploaded_points()
            await asyncio.sleep(10)  # Run every 10 seconds

    async def delete_uploaded_points(self):
        deleted_count = await delete_uploaded_points()
        if deleted_count:
            logger.info(
                f"CleanerActor deleted {deleted_count} uploaded points from DB."
            )
        else:
            logger.info("CleanerActor found no uploaded points to delete.")
