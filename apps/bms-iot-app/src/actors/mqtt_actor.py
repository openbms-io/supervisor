import asyncio
from typing import Optional
from src.network.mqtt_config import MQTTConfig
from src.actors.messages.actor_queue_registry import ActorQueueRegistry
from src.actors.messages.message_type import (
    ActorName,
    ActorMessage,
    ActorMessageType,
)
from src.controllers.mqtt.mqtt_controller import MQTTHandler
from packages.mqtt_topics.topics_loader import CommandNameEnum
from src.models.iot_device_status import upsert_iot_device_status
from src.models.device_status_enums import ConnectionStatusEnum

from src.utils.logger import logger

logging = logger


class MQTTActor:
    def __init__(
        self,
        mqtt_config: MQTTConfig,
        actor_queue_registry: ActorQueueRegistry,
        organization_id: str,
        site_id: str,
        iot_device_id: str,
        controller_device_id: Optional[str] = None,
        iot_device_point_id: Optional[str] = None,
    ):
        self.mqtt_config = mqtt_config
        self.organization_id = organization_id
        self.site_id = site_id
        self.iot_device_id = iot_device_id
        self.controller_device_id = controller_device_id
        self.iot_device_point_id = iot_device_point_id
        self.actor_queue_registry = actor_queue_registry
        self.actor_name = ActorName.MQTT
        self.mqtt_handler = MQTTHandler(
            mqtt_config=mqtt_config,
            organization_id=organization_id,
            site_id=site_id,
            iot_device_id=iot_device_id,
            controller_device_id=controller_device_id,
            iot_device_point_id=iot_device_point_id,
        )

    async def start(self):
        self.mqtt_handler.setup(self.actor_queue_registry, self.actor_name)

        # Initialize connection status
        await self._update_connection_status(ConnectionStatusEnum.CONNECTED)

        async def handle_messages_loop():
            while True:
                await self._handle_messages()
                await asyncio.sleep(0)  # Yield control to event loop

        handle_messages_task = asyncio.create_task(handle_messages_loop())

        try:
            while True:
                if not self.mqtt_handler.mqtt_client.client.is_connected():
                    await self._update_connection_status(
                        ConnectionStatusEnum.DISCONNECTED
                    )
                    await self.stop()
                    handle_messages_task.cancel()
                    raise RuntimeError("MQTT client disconnected")
                await asyncio.sleep(5)
        except Exception:
            await self._update_connection_status(ConnectionStatusEnum.ERROR)
            handle_messages_task.cancel()
            raise

    async def _handle_messages(self):
        queue = self.actor_queue_registry.get_queue(self.actor_name)

        while not queue.empty():
            message: ActorMessage = await queue.get()
            if message.message_type == ActorMessageType.CONFIG_UPLOAD_RESPONSE:
                self.mqtt_handler.publish_response(
                    CommandNameEnum.get_config, message.payload
                )
            elif message.message_type == ActorMessageType.POINT_PUBLISH_REQUEST:
                await self.mqtt_handler.publish_point_bulk(message.payload.points)
            elif message.message_type == ActorMessageType.SET_VALUE_TO_POINT_RESPONSE:
                self.mqtt_handler.publish_response(
                    CommandNameEnum.set_value_to_point, message.payload
                )
            elif message.message_type == ActorMessageType.HEARTBEAT_STATUS:
                await self.mqtt_handler.publish_heartbeat_status(message.payload)
            elif message.message_type == ActorMessageType.START_MONITORING_RESPONSE:
                self.mqtt_handler.publish_response(
                    CommandNameEnum.start_monitoring, message.payload
                )
            elif message.message_type == ActorMessageType.STOP_MONITORING_RESPONSE:
                self.mqtt_handler.publish_response(
                    CommandNameEnum.stop_monitoring, message.payload
                )
            else:
                logger.error(
                    f"Unknown message type: {message.message_type}. Please implement the handler for this message type."
                )

    async def stop(self):
        logger.info("Stopping MQTTActor...")
        await self._update_connection_status(ConnectionStatusEnum.DISCONNECTED)
        self.mqtt_handler.stop()
        logger.info("MQTTActor stopped.")

    async def _update_connection_status(self, status: ConnectionStatusEnum):
        """Update MQTT connection status in local database."""
        try:
            status_data = {
                "organization_id": self.organization_id,
                "site_id": self.site_id,
                "mqtt_connection_status": status,
            }
            await upsert_iot_device_status(self.iot_device_id, status_data)
            logger.debug(f"[MQTTActor] Updated MQTT connection status to: {status}")
        except Exception as e:
            logger.error(f"[MQTTActor] Failed to update connection status: {e}")
