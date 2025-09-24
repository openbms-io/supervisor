from src.utils.logger import logger
import asyncio
import time
from src.actors.messages.actor_queue_registry import ActorQueueRegistry
from src.actors.messages.message_type import (
    ActorName,
    ActorMessage,
    ActorMessageType,
    ForceHeartbeatPayload,
)
from src.controllers.heartbeat_controller.heartbeat import HeartbeatController

logging = logger


class HeartbeatActor:
    def __init__(
        self,
        actor_queue_registry: ActorQueueRegistry,
        organization_id: str,
        site_id: str,
        iot_device_id: str,
    ):
        self.actor_queue_registry = actor_queue_registry
        self.actor_name = ActorName.HEARTBEAT
        self.keep_running = True
        self.heartbeat_interval = 30  # 30 seconds

        # Store device identifiers
        self.organization_id = organization_id
        self.site_id = site_id
        self.iot_device_id = iot_device_id

        # Use the HeartbeatController for business logic
        self.heartbeat_controller = HeartbeatController(
            organization_id, site_id, iot_device_id
        )

    async def start(self):
        await self.heartbeat_controller.start()
        await self._run_heartbeat_loop()

    async def _run_heartbeat_loop(self):
        queue = self.actor_queue_registry.get_queue(self.actor_name)
        last_heartbeat = 0

        while self.keep_running:
            try:
                current_time = time.time()

                # Check for incoming messages (non-blocking)
                while not queue.empty():
                    msg: ActorMessage = await queue.get()
                    await self._handle_message(msg)

                # Send heartbeat every interval
                if current_time - last_heartbeat >= self.heartbeat_interval:
                    await self._send_heartbeat()
                    last_heartbeat = current_time

                await asyncio.sleep(1)  # Check messages every second

            except Exception as e:
                logger.error(f"HeartbeatActor error: {e}")
                await asyncio.sleep(5)

    def on_stop(self):
        self.keep_running = False

    async def _handle_message(self, msg: ActorMessage):
        logger.info(f"[HeartbeatActor] Received message: {msg}")

        if msg.message_type == ActorMessageType.FORCE_HEARTBEAT_REQUEST:
            if isinstance(msg.payload, ForceHeartbeatPayload):
                logger.info(
                    f"[HeartbeatActor] Force heartbeat requested - Reason: {msg.payload.reason}"
                )
                await self._force_heartbeat(msg.payload.reason)
            else:
                logger.warning(
                    "[HeartbeatActor] Received FORCE_HEARTBEAT_REQUEST with unexpected payload type"
                )
        else:
            logger.warning(
                f"[HeartbeatActor] Unhandled message type: {msg.message_type}"
            )

    async def _send_heartbeat(self):
        """Collect heartbeat data via controller and send to MQTT actor."""
        try:
            # Delegate to the heartbeat controller for data collection
            heartbeat_payload = await self.heartbeat_controller.collect_heartbeat_data()

            # Send to MQTT actor for publishing
            await self.actor_queue_registry.send_from(
                sender=self.actor_name,
                receiver=ActorName.MQTT,
                type=ActorMessageType.HEARTBEAT_STATUS,
                payload=heartbeat_payload,
            )

            logger.info(
                f"[HeartbeatActor] Sent heartbeat for device {self.iot_device_id}"
            )

        except Exception as e:
            logger.error(f"[HeartbeatActor] Failed to send heartbeat: {e}")

    async def _force_heartbeat(self, reason: str):
        """Immediately send heartbeat regardless of timing interval."""
        try:
            logger.info(
                f"[HeartbeatActor] Executing force heartbeat - Reason: {reason}"
            )

            # Delegate to the heartbeat controller for force heartbeat
            heartbeat_payload = await self.heartbeat_controller.force_heartbeat(reason)

            # Send to MQTT actor for publishing
            await self.actor_queue_registry.send_from(
                sender=self.actor_name,
                receiver=ActorName.MQTT,
                type=ActorMessageType.HEARTBEAT_STATUS,
                payload=heartbeat_payload,
            )

            logger.info(
                f"[HeartbeatActor] Force heartbeat completed successfully for reason: {reason}"
            )
        except Exception as e:
            logger.error(
                f"[HeartbeatActor] Failed to execute force heartbeat for reason '{reason}': {e}"
            )
