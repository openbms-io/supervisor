import logging
import json
import time
from typing import Optional, Any
import paho.mqtt.client as mqtt

from src.network.mqtt_config import MQTTConfig
from src.network.mqtt_command_dispatcher import MqttCommandDispatcher
from src.network.mqtt_client import MQTTClient
from src.actors.messages.message_type import (
    ActorName,
    ActorMessageType,
    ConfigUploadPayload,
    PointPublishPayload,
    AllowedPayloadTypes,
    SetValueToPointRequestPayload,
    HeartbeatStatusPayload,
    MonitoringControlPayload,
)
from packages.mqtt_topics.topics_loader import CommandNameEnum
from src.models.controller_points import ControllerPointsModel
from src.actors.messages.actor_queue_registry import ActorQueueRegistry

logger = logging.getLogger(__name__)


class MQTTHandler:
    def __init__(
        self,
        mqtt_config: MQTTConfig,
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
        self.mqtt_client: Optional[MQTTClient] = None
        self.dispatcher: Optional[MqttCommandDispatcher] = None
        self.actor_queue_registry: Optional[ActorQueueRegistry] = None
        self.actor_name: Optional[ActorName] = None

    def setup(self, actor_queue_registry: ActorQueueRegistry, actor_name: ActorName):
        self.actor_queue_registry = actor_queue_registry
        self.actor_name = actor_name
        self.mqtt_client = MQTTClient(self.mqtt_config)
        self.dispatcher = MqttCommandDispatcher(
            mqtt_client=self.mqtt_client,
            organization_id=self.organization_id,
            site_id=self.site_id,
            iot_device_id=self.iot_device_id,
        )

        self.dispatcher.update_mqtt_topics(
            controller_device_id=self.controller_device_id,
            iot_device_point_id=self.iot_device_point_id,
        )

        assert self.actor_name is not None
        assert self.actor_queue_registry is not None
        # Register handlers here
        self.dispatcher.register_handler(
            CommandNameEnum.set_value_to_point,
            lambda client, userdata, message: self.on_set_value_to_point_request(
                self.actor_queue_registry, self.actor_name, client, userdata, message
            ),
        )

        self.dispatcher.register_handler(
            CommandNameEnum.get_config,
            lambda client, userdata, message: self.on_get_config_request(
                self.actor_queue_registry, self.actor_name, client, userdata, message
            ),
        )
        self.dispatcher.register_handler(
            CommandNameEnum.reboot,
            lambda client, userdata, message: self.on_reboot_request(
                self.actor_queue_registry, self.actor_name, client, userdata, message
            ),
        )

        self.dispatcher.register_handler(
            CommandNameEnum.start_monitoring,
            lambda client, userdata, message: self.on_start_monitoring_request(
                self.actor_queue_registry, self.actor_name, client, userdata, message
            ),
        )

        self.dispatcher.register_handler(
            CommandNameEnum.stop_monitoring,
            lambda client, userdata, message: self.on_stop_monitoring_request(
                self.actor_queue_registry, self.actor_name, client, userdata, message
            ),
        )
        self.dispatcher.attach_to_client()
        logger.info("Connecting to MQTT broker...")
        if not self.mqtt_client.connect():
            raise RuntimeError("Failed to connect to MQTT broker")
        self.dispatcher.subscribe_all()
        logger.info("Subscribed to all request topics.")
        return self.mqtt_client, self.dispatcher

    # def update_mqtt_topics(self, controller_device_id: str, iot_device_point_id: str):
    #     self.controller_device_id = controller_device_id
    #     self.iot_device_point_id = iot_device_point_id
    #     if self.dispatcher:
    #         self.dispatcher.update_mqtt_topics(controller_device_id, iot_device_point_id)

    # def register_handler(self, command: CommandNameEnum, handler):
    #     if self.dispatcher:
    #         self.dispatcher.register_handler(command, handler)

    # def attach_to_client(self):
    #     if self.dispatcher:
    #         self.dispatcher.attach_to_client()

    def publish_response(self, command: CommandNameEnum, payload: AllowedPayloadTypes):
        payload_dict = payload.model_dump()
        if self.dispatcher:
            self.dispatcher.publish_response(command=command, payload=payload_dict)

    async def publish_point_bulk(self, points: list[ControllerPointsModel]):
        assert self.actor_queue_registry is not None
        assert self.actor_name is not None

        if self.dispatcher:
            has_published = self.dispatcher.publish_point_bulk(points)
            await self.actor_queue_registry.send_from(
                sender=self.actor_name,
                receiver=ActorName.UPLOADER,
                type=ActorMessageType.POINT_PUBLISH_RESPONSE,
                payload=PointPublishPayload(points=points),
            )
            return has_published
        return False

    async def publish_heartbeat_status(self, payload: HeartbeatStatusPayload):
        """Publish heartbeat status to MQTT heartbeat topic."""
        if self.dispatcher:
            payload_dict = payload.model_dump()
            # Add metadata
            payload_dict.update(
                {
                    "timestamp": time.time(),
                    "organization_id": self.organization_id,
                    "site_id": self.site_id,
                    "iot_device_id": self.iot_device_id,
                }
            )
            self.dispatcher.publish_heartbeat(payload_dict)
            return True
        return False

    def stop(self):
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            logger.info("MQTTHandler stopped.")

    # Example handler methods (to be registered with dispatcher)
    async def on_get_config_request(
        self,
        actor_queue_registry: Optional[ActorQueueRegistry],
        actor_name: Optional[ActorName],
        client: mqtt.Client,
        userdata: Any,
        message: mqtt.MQTTMessage,
    ):
        if not actor_queue_registry or not actor_name:
            raise ValueError("actor_queue_registry and actor_name cannot be None")

        payload_dict = json.loads(message.payload.decode())
        urlToUploadConfig: str = payload_dict.get("urlToUploadConfig")
        jwtToken: str = payload_dict.get("jwtToken")
        iotDeviceControllers: list[dict] = (
            payload_dict.get("iotDeviceControllers") or []
        )
        bacnetReaders: list[dict] = payload_dict.get("bacnetReaders") or []
        logger.info(f"on_get_config_request: Full payload: {payload_dict}")

        # Parse BACnet readers data
        bacnet_readers_config = []
        for reader_data in bacnetReaders:
            try:
                from src.actors.messages.message_type import BacnetReaderConfig

                reader_config = BacnetReaderConfig(**reader_data)
                bacnet_readers_config.append(reader_config)
            except Exception as e:
                logger.warning(
                    f"Failed to parse BACnet reader config: {reader_data}, error: {e}"
                )
                continue

        payload = ConfigUploadPayload(
            urlToUploadConfig=urlToUploadConfig,
            jwtToken=jwtToken,
            iotDeviceControllers=iotDeviceControllers,
            bacnetReaders=bacnet_readers_config,
        )
        logger.info(
            f"Received get_config request with {len(iotDeviceControllers)} controllers and {len(bacnet_readers_config)} BACnet readers"
        )
        logger.info(f"Full payload: {payload}")
        await actor_queue_registry.send_from(
            sender=actor_name,
            receiver=ActorName.BACNET,  # will be overwritten in broadcast
            type=ActorMessageType.CONFIG_UPLOAD_REQUEST,
            payload=payload,
        )

    async def on_set_value_to_point_request(
        self,
        actor_queue_registry: Optional[ActorQueueRegistry],
        actor_name: Optional[ActorName],
        client: mqtt.Client,
        userdata: Any,
        message: mqtt.MQTTMessage,
    ):
        logger.info(f"Received set_value_to_point request: {message}")
        if not actor_queue_registry or not actor_name:
            raise ValueError("actor_queue_registry and actor_name cannot be None")

        payload_dict: dict = json.loads(message.payload.decode())
        logger.info(f"Received set_value_to_point request: {payload_dict}")
        payload = SetValueToPointRequestPayload.model_validate(payload_dict)

        logger.info(f"Received set_value_to_point request: {payload}")

        # Send message to BACNET_WRITER actor
        await actor_queue_registry.send_from(
            sender=actor_name,
            receiver=ActorName.BACNET_WRITER,
            type=ActorMessageType.SET_VALUE_TO_POINT_REQUEST,
            payload=payload,
        )

    async def on_reboot_request(
        self,
        actor_queue_registry: Optional[ActorQueueRegistry],
        actor_name: Optional[ActorName],
        client: mqtt.Client,
        userdata: Any,
        message: mqtt.MQTTMessage,
    ):
        if not actor_queue_registry or not actor_name:
            raise ValueError("actor_queue_registry and actor_name cannot be None")

        payload = json.loads(message.payload.decode())
        logger.info(f"Received reboot request: {payload}")
        # Implement reboot logic here

    async def on_start_monitoring_request(
        self,
        actor_queue_registry: Optional[ActorQueueRegistry],
        actor_name: Optional[ActorName],
        client: mqtt.Client,
        userdata: Any,
        message: mqtt.MQTTMessage,
    ):
        if not actor_queue_registry or not actor_name:
            raise ValueError("actor_queue_registry and actor_name cannot be None")

        payload_dict = json.loads(message.payload.decode())
        payload = MonitoringControlPayload.model_validate(payload_dict)
        logger.info(f"Received start_monitoring request: {payload}")

        # Send message to BACNET actor
        await actor_queue_registry.send_from(
            sender=actor_name,
            receiver=ActorName.BACNET,
            type=ActorMessageType.START_MONITORING_REQUEST,
            payload=payload,
        )

    async def on_stop_monitoring_request(
        self,
        actor_queue_registry: Optional[ActorQueueRegistry],
        actor_name: Optional[ActorName],
        client: mqtt.Client,
        userdata: Any,
        message: mqtt.MQTTMessage,
    ):
        if not actor_queue_registry or not actor_name:
            raise ValueError("actor_queue_registry and actor_name cannot be None")

        payload_dict = json.loads(message.payload.decode())
        payload = MonitoringControlPayload.model_validate(payload_dict)
        logger.info(f"Received stop_monitoring request: {payload}")

        # Send message to BACNET actor
        await actor_queue_registry.send_from(
            sender=actor_name,
            receiver=ActorName.BACNET,
            type=ActorMessageType.STOP_MONITORING_REQUEST,
            payload=payload,
        )
