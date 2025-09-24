from typing import Any, Dict, Callable, Optional, List, Coroutine
from packages.mqtt_topics.topics_loader import (
    build_mqtt_topic_dict,
    Topics,
    CommandSection,
    CommandNameEnum,
)
from src.network.mqtt_client import MQTTClient
import asyncio
import paho.mqtt.client as mqtt
from src.models.controller_points import ControllerPointsModel
from datetime import datetime
import json

from src.utils.logger import logger

MessageHandler = Callable[
    [mqtt.Client, Any, mqtt.MQTTMessage], Coroutine[Any, Any, None]
]


def _serialize_point(point: ControllerPointsModel):
    """
    Serialize ControllerPointsModel for MQTT transmission.

    Converts SQLite storage format to structured MQTT payload format,
    including parsing JSON strings for complex BACnet properties.
    """
    data = point.model_dump()
    for k, v in data.items():
        if isinstance(v, datetime):
            data[k] = v.isoformat()

    # Decode health data from semicolon-separated strings to arrays for MQTT
    if data.get("status_flags"):
        try:
            # Convert "fault;overridden" to ["fault", "overridden"]
            data["status_flags"] = [
                flag.strip() for flag in data["status_flags"].split(";") if flag.strip()
            ]
        except Exception as e:
            logger.warning(
                f"Failed to decode status_flags '{data['status_flags']}': {e}"
            )
            data["status_flags"] = None

    # Parse JSON strings for complex BACnet optional properties
    json_properties = [
        "priority_array",
        "limit_enable",
        "event_enable",
        "acked_transitions",
        "event_time_stamps",
        "event_message_texts",
        "event_message_texts_config",
        "event_algorithm_inhibit_ref",
    ]

    for prop in json_properties:
        if data.get(prop):
            try:
                data[prop] = json.loads(data[prop])
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"Failed to parse JSON for {prop} '{data[prop]}': {e}")
                data[prop] = None

    # Add unix milli timestamp to the payload for influxDB.
    data["created_at_unix_milli_timestamp"] = point.created_at_unix_milli_timestamp
    return data


class MqttCommandDispatcher:
    """
    Encapsulates MQTT topic extraction, handler registration, subscription, and dispatch logic.
    Only one instance should be used per process.
    """

    def __init__(
        self,
        mqtt_client: MQTTClient,
        organization_id: str,
        site_id: str,
        iot_device_id: str,
        controller_device_id: Optional[str] = None,
        iot_device_point_id: Optional[str] = None,
    ):
        self.mqtt_client = mqtt_client
        self.organization_id = organization_id
        self.site_id = site_id
        self.iot_device_id = iot_device_id
        self.controller_device_id = controller_device_id
        self.iot_device_point_id = iot_device_point_id
        self.handlers: dict[CommandNameEnum, MessageHandler] = {}
        self.update_mqtt_topics(controller_device_id, iot_device_point_id)

    def update_mqtt_topics(
        self,
        controller_device_id: Optional[str] = None,
        iot_device_point_id: Optional[str] = None,
    ):
        self.controller_device_id = controller_device_id
        self.iot_device_point_id = iot_device_point_id

        self.mqtt_topics: Topics = build_mqtt_topic_dict(
            organization_id=self.organization_id,
            site_id=self.site_id,
            iot_device_id=self.iot_device_id,
            controller_device_id=self.controller_device_id,
            iot_device_point_id=self.iot_device_point_id,
        )
        self.command_section: CommandSection = self.mqtt_topics.command
        self.command_names = list(CommandNameEnum)
        self.request_topics: List[str] = [
            self.command_section.get_config.request,
            self.command_section.reboot.request,
            self.command_section.set_value_to_point.request,
            self.command_section.start_monitoring.request,
            self.command_section.stop_monitoring.request,
        ]
        self.response_topics: List[str] = [
            self.command_section.get_config.response,
            self.command_section.reboot.response,
            self.command_section.set_value_to_point.response,
            self.command_section.start_monitoring.response,
            self.command_section.stop_monitoring.response,
        ]
        self.status_update_topic = self.mqtt_topics.status.update
        self.status_heartbeat_topic = self.mqtt_topics.status.heartbeat
        self.point_topic = self.mqtt_topics.data.point

    def register_handler(self, command: CommandNameEnum, handler: MessageHandler):
        if command in self.command_names:
            self.handlers[command] = handler
        else:
            raise AttributeError(f"No handler slot for command: {command}")

    def subscribe_all(self):
        for topic in self.request_topics:
            logger.info(f"Subscribing to {topic}")
            self.mqtt_client.subscribe(topic=topic, qos=1)

    def attach_to_client(self):
        def _on_message(client, userdata, message: mqtt.MQTTMessage):
            logger.info(f"Received message: {message}")
            topic = message.topic
            if topic == self.command_section.get_config.request:
                handler = self.handlers.get(CommandNameEnum.get_config)
            elif topic == self.command_section.reboot.request:
                handler = self.handlers.get(CommandNameEnum.reboot)
            elif topic == self.command_section.set_value_to_point.request:
                handler = self.handlers.get(CommandNameEnum.set_value_to_point)
            elif topic == self.command_section.start_monitoring.request:
                handler = self.handlers.get(CommandNameEnum.start_monitoring)
            elif topic == self.command_section.stop_monitoring.request:
                handler = self.handlers.get(CommandNameEnum.stop_monitoring)
            else:
                handler = None

            if handler:
                logger.info(f"Handling message: {message}, userdata: {userdata}")
                asyncio.run(handler(client, userdata, message))
            else:
                logger.warning(f"No handler for topic: {topic}")

        self.mqtt_client.set_on_message(_on_message)

    # --- Publish helpers ---
    def publish_response(self, command: CommandNameEnum, payload: Dict[str, Any]):
        if command == CommandNameEnum.get_config:
            self.mqtt_client.publish(self.command_section.get_config.response, payload)
        elif command == CommandNameEnum.reboot:
            self.mqtt_client.publish(self.command_section.reboot.response, payload)
        elif command == CommandNameEnum.set_value_to_point:
            self.mqtt_client.publish(
                self.command_section.set_value_to_point.response, payload
            )
        elif command == CommandNameEnum.start_monitoring:
            self.mqtt_client.publish(
                self.command_section.start_monitoring.response, payload
            )
        elif command == CommandNameEnum.stop_monitoring:
            self.mqtt_client.publish(
                self.command_section.stop_monitoring.response, payload
            )
        else:
            raise ValueError(f"No response topic for command: {command}")

    def publish_update(self, payload: Dict[str, Any]):
        if self.status_update_topic:
            self.mqtt_client.publish(self.status_update_topic, payload)

    def publish_heartbeat(self, payload: Dict[str, Any]):
        if self.status_heartbeat_topic:
            self.mqtt_client.publish(self.status_heartbeat_topic, payload)

    def publish_point_bulk(self, payload: list[ControllerPointsModel]):
        logger.info(f"Publishing point bulk count: {len(payload)}")
        point_bulk_topic = self.mqtt_topics.data.point_bulk
        if not point_bulk_topic:
            raise ValueError(
                f"Bulk topic is not set. Please update the mqtt topics. Check mqtt_topics: {self.mqtt_topics}"
            )

        payload_dict = [_serialize_point(point) for point in payload]
        logger.info(
            f"Publishing point bulk count: {len(payload_dict)} to topic: {point_bulk_topic}"
        )
        has_published = self.mqtt_client.publish(
            point_bulk_topic, {"points": payload_dict}
        )

        return has_published
