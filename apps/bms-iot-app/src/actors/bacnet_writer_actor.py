from src.utils.logger import logger
import asyncio
from src.actors.messages.actor_queue_registry import ActorQueueRegistry
from src.actors.messages.message_type import (
    ActorName,
    ActorMessage,
    ActorMessageType,
    SetValueToPointRequestPayload,
    ImmediateUploadTriggerPayload,
)
from src.controllers.bacnet_writer.writer import BACnetWriter

logging = logger


class BacnetWriterActor:
    def __init__(self, actor_queue_registry: ActorQueueRegistry):
        self.actor_queue_registry = actor_queue_registry
        self.actor_name = ActorName.BACNET_WRITER
        self.keep_running = True

        # Use the BACnet writer controller
        self.bacnet_writer = BACnetWriter()

    async def start(self):
        await self.bacnet_writer.start()
        await self._run_message_loop()

    async def _run_message_loop(self):
        queue = self.actor_queue_registry.get_queue(self.actor_name)

        while self.keep_running:
            try:
                # Check for incoming messages (non-blocking)
                while not queue.empty():
                    msg: ActorMessage = await queue.get()
                    await self._handle_message(msg)

                await asyncio.sleep(0.1)  # Small delay to prevent busy waiting

            except Exception as e:
                logger.error(f"BacnetWriterActor error: {e}")
                await asyncio.sleep(1)

    def on_stop(self):
        self.keep_running = False

    async def _handle_message(self, msg: ActorMessage):
        logger.info(f"[BacnetWriterActor] Received message: {msg}")

        if msg.message_type == ActorMessageType.SET_VALUE_TO_POINT_REQUEST:
            if isinstance(msg.payload, SetValueToPointRequestPayload):
                await self._handle_set_value_request(msg.payload, msg.sender)
            else:
                logger.warning(
                    "Received SET_VALUE_TO_POINT_REQUEST with unexpected payload type"
                )
        else:
            logger.warning(f"Unhandled message type: {msg.message_type}")

    async def _handle_set_value_request(
        self, payload: SetValueToPointRequestPayload, sender: ActorName
    ):
        """Handle the set value to point request by delegating to BACnet writer controller."""
        logger.info(
            f"[BacnetWriterActor] Handling set value request for point {payload.iotDevicePointId}"
        )

        # Delegate to the BACnet writer controller
        response_payload, db_record = await self.bacnet_writer.write_value_to_point(
            payload
        )

        # Send response back to sender
        await self.actor_queue_registry.send_from(
            sender=self.actor_name,
            receiver=sender,
            type=ActorMessageType.SET_VALUE_TO_POINT_RESPONSE,
            payload=response_payload,
        )

        # If write was successful and we have a database record, trigger immediate upload
        if response_payload.success and db_record is not None:
            await self.actor_queue_registry.send_from(
                sender=self.actor_name,
                receiver=ActorName.UPLOADER,
                type=ActorMessageType.IMMEDIATE_UPLOAD_TRIGGER,
                payload=ImmediateUploadTriggerPayload(reason="manual_write"),
            )
            logger.info(
                f"[BacnetWriterActor] Successfully handled request and triggered upload for point {payload.iotDevicePointId}"
            )
        else:
            logger.error(
                f"[BacnetWriterActor] Failed to handle request for point {payload.iotDevicePointId}"
            )
