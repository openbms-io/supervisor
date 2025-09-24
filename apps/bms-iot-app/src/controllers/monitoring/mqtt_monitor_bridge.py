"""Bridge module to connect BACnet monitoring with MQTT publishing."""

import logging
import time
from typing import Dict, Any, Optional

from ...network.mqtt_client import MQTTClient
from ...network.mqtt_config import MQTTConfig
from ...network.mqtt_adapter import get_mqtt_config

logger = logging.getLogger(__name__)


class MQTTMonitorBridge:
    """Bridge class to connect BACnet monitoring with MQTT publishing."""

    def __init__(self, mqtt_config: Optional[MQTTConfig] = None):
        """Initialize the MQTT-Monitor bridge."""
        # Use provided config or default to saved configuration
        self.mqtt_config = mqtt_config or get_mqtt_config()
        self.mqtt_client = MQTTClient(self.mqtt_config)
        self.connected = False

    async def start(self):
        """Start the MQTT client connection."""
        if self.mqtt_client.connect():
            self.connected = True
            logger.info(
                f"MQTT Monitor Bridge connected to {self.mqtt_config.broker_host}"
            )
            return True
        return False

    async def stop(self):
        """Stop the MQTT client connection."""
        if self.connected:
            self.mqtt_client.disconnect()
            self.connected = False
            logger.info("MQTT Monitor Bridge disconnected")

    async def publish_device_data(self, device_id: int, data: Dict[str, Any]):
        """
        Publish device data to MQTT.

        Args:
            device_id: The BACnet device ID
            data: The device data to publish
        """
        if not self.connected:
            logger.warning("Cannot publish: MQTT Bridge not connected")
            return False

        # Add timestamp if not present
        if "timestamp" not in data:
            data["timestamp"] = time.time()

        # Publish to device-specific topic
        topic = f"device/{device_id}"
        return self.mqtt_client.publish(topic, data)

    async def publish_object_data(
        self, device_id: int, object_type: str, object_id: int, data: Dict[str, Any]
    ):
        """
        Publish object data to MQTT.

        Args:
            device_id: The BACnet device ID
            object_type: The BACnet object type (e.g., 'analogValue')
            object_id: The BACnet object ID
            data: The object data to publish
        """
        if not self.connected:
            logger.warning("Cannot publish: MQTT Bridge not connected")
            return False

        # Add timestamp if not present
        if "timestamp" not in data:
            data["timestamp"] = time.time()

        # Publish to object-specific topic
        topic = f"device/{device_id}/{object_type}/{object_id}"
        return self.mqtt_client.publish(topic, data)

    async def publish_monitoring_data(self, topic: str, data: Dict[str, Any]):
        """
        Publish generic monitoring data to MQTT.

        Args:
            topic: The specific topic (will be appended to topic_prefix)
            data: The data to publish
        """
        if not self.connected:
            logger.warning("Cannot publish: MQTT Bridge not connected")
            return False

        # Add timestamp if not present
        if "timestamp" not in data:
            data["timestamp"] = time.time()

        return self.mqtt_client.publish(topic, data)
