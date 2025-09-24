from src.utils.logger import logger
from src.actors.messages.actor_queue_registry import ActorQueueRegistry
from src.actors.messages.message_type import (
    ActorMessageType,
    ActorName,
    ConfigUploadPayload,
    ActorMessage,
    PointPublishPayload,
    ConfigUploadResponsePayload,
    ImmediateUploadTriggerPayload,
)
from src.controllers.uploader.upload import upload_config, get_points_to_publish
import asyncio
from src.controllers.uploader.upload import mark_points_as_uploaded_in_db

logging = logger


class UploaderActor:
    def __init__(self, actor_queue_registry: ActorQueueRegistry):
        self.actor_queue_registry = actor_queue_registry
        self.actor_name = ActorName.UPLOADER
        self.keep_running = True

    async def start(self):
        await self._run_monitor_loop()

    async def _run_monitor_loop(self):
        logger.info("UploaderActor started")
        queue = self.actor_queue_registry.get_queue(self.actor_name)

        while self.keep_running:
            await self.publish_points()

            while not queue.empty():
                message: ActorMessage = await queue.get()
                logger.info(f"UploaderActor received message: {message.message_type}")
                if message.message_type == ActorMessageType.CONFIG_UPLOAD_RESPONSE:
                    await self.on_upload_request(message.payload)
                elif message.message_type == ActorMessageType.POINT_PUBLISH_RESPONSE:
                    await self.on_point_publish_response(message.payload)
                elif message.message_type == ActorMessageType.IMMEDIATE_UPLOAD_TRIGGER:
                    await self.on_immediate_upload_trigger(message.payload)
            await asyncio.sleep(2)  # Yield control to event loop

    async def on_upload_request(self, payload: ConfigUploadPayload):
        urlToUploadConfig: str = payload.urlToUploadConfig
        jwtToken: str = payload.jwtToken

        logger.info(f"Uploading config to {urlToUploadConfig} with jwtToken {jwtToken}")
        await upload_config(urlToUploadConfig, jwtToken)
        await self.actor_queue_registry.send_from(
            sender=self.actor_name,
            receiver=ActorName.MQTT,
            type=ActorMessageType.CONFIG_UPLOAD_RESPONSE,
            payload=ConfigUploadResponsePayload(success=True),
        )

    async def publish_points(self):
        points = await get_points_to_publish()
        if not points:
            logging.warning("No points found to publish.")
            return None

        payload = PointPublishPayload(points=points)

        await self.actor_queue_registry.send_from(
            sender=self.actor_name,
            receiver=ActorName.MQTT,
            type=ActorMessageType.POINT_PUBLISH_REQUEST,
            payload=payload,
        )

    async def on_point_publish_response(self, payload: PointPublishPayload):
        logger.info(
            f"UploaderActor received point publish response: {len(payload.points)}"
        )
        await mark_points_as_uploaded_in_db(payload.points)
        logger.info(f"UploaderActor marked points as uploaded: {len(payload.points)}")

    async def on_immediate_upload_trigger(self, payload: ImmediateUploadTriggerPayload):
        """
        Handle immediate upload trigger by performing an immediate upload cycle.
        This ensures manual writes are uploaded to TimescaleDB immediately.
        """
        try:
            logger.info(
                f"UploaderActor received immediate upload trigger: reason={payload.reason}"
            )

            # Perform immediate upload cycle (same logic as regular publish_points)
            await self.publish_points()

            logger.info(
                f"UploaderActor completed immediate upload cycle for reason: {payload.reason}"
            )

        except Exception as e:
            logger.error(f"UploaderActor failed to perform immediate upload: {e}")
            # We don't re-raise because this is fire-and-forget
