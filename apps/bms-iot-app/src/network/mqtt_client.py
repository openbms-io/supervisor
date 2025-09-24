import json
import time
import logging
import os
from typing import Any, Dict, Callable

import paho.mqtt.client as mqtt

from .mqtt_config import MQTTConfig, default_config, CERT_FILE_PATH
from src.utils.performance_monitor import payload_monitor

logger = logging.getLogger(__name__)


class MQTTClient:
    """MQTT Client for connecting to EMQX broker and publishing monitoring data."""

    def __init__(self, config: MQTTConfig = default_config):
        self.config = config
        # Use standard MQTT client with default protocol version
        self.client = mqtt.Client(client_id=config.client_id)
        self.connected = False

        # Log warning if TLS is disabled
        if not config.use_tls:
            logger.warning(
                "TLS is disabled. It is strongly recommended to enable TLS for secure communication"
            )

        self._setup_client()

    def _setup_client(self):
        """Configure the MQTT client with callbacks and credentials."""
        # Set up credentials if provided
        if self.config.username and self.config.password:
            self.client.username_pw_set(self.config.username, self.config.password)

        # Configure TLS if enabled
        if self.config.use_tls:
            logger.info(
                f"Configuring TLS with CA certificate: {self.config.tls_ca_cert}"
            )
            if self.config.tls_ca_cert and os.path.exists(self.config.tls_ca_cert):
                # For EMQXSL, we need to verify the certificate
                self.client.tls_set(
                    ca_certs=self.config.tls_ca_cert,
                    certfile=None,
                    keyfile=None,
                    cert_reqs=mqtt.ssl.CERT_REQUIRED,
                    tls_version=mqtt.ssl.PROTOCOL_TLS,
                    ciphers=None,
                )
                # Do not verify hostname in certificate - for custom domains
                self.client.tls_insecure_set(False)
            elif os.path.exists(CERT_FILE_PATH):
                # If no specific CA cert is provided but the default one exists, use it
                logger.info(f"Using default CA certificate: {CERT_FILE_PATH}")
                self.client.tls_set(
                    ca_certs=CERT_FILE_PATH,
                    certfile=None,
                    keyfile=None,
                    cert_reqs=mqtt.ssl.CERT_REQUIRED,
                    tls_version=mqtt.ssl.PROTOCOL_TLS,
                    ciphers=None,
                )
                self.client.tls_insecure_set(False)
            else:
                logger.warning(
                    "CA certificate file not found. Using system CA certificates"
                )
                self.client.tls_set()
        else:
            logger.warning(
                "TLS is disabled. It is strongly recommended to enable TLS for secure communication"
            )

        # Set up callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_publish = self._on_publish

    def _on_connect(self, client, userdata, flags, rc):
        """Callback for when the client receives a CONNACK response from the server."""
        if rc == 0:
            self.connected = True
            if self.config.use_tls:
                logger.info(
                    f"Connected securely (TLS) to MQTT broker {self.config.broker_host}:{self.config.broker_port}"
                )
            else:
                logger.info(
                    f"Connected to MQTT broker {self.config.broker_host}:{self.config.broker_port} (UNENCRYPTED)"
                )
        else:
            error_messages = {
                1: "Incorrect protocol version",
                2: "Invalid client identifier",
                3: "Server unavailable",
                4: "Bad username or password",
                5: "Not authorized",
            }
            error_message = error_messages.get(rc, f"Unknown error code: {rc}")
            logger.error(f"Failed to connect to MQTT broker: {error_message}")

    def _on_disconnect(self, client, userdata, rc):
        """Callback for when the client disconnects from the server."""
        self.connected = False
        logger.warning(f"Disconnected from MQTT broker with code: {rc}")
        # Implement reconnection logic
        if rc != 0:
            self._reconnect()

    def _on_publish(self, client, userdata, mid):
        """Callback for when a message has been published."""
        logger.debug(f"Message published with ID: {mid}")

    def connect(self):
        """Connect to the MQTT broker."""
        try:
            if self.config.use_tls:
                logger.info(
                    f"Connecting securely (TLS) to MQTT broker {self.config.broker_host}:{self.config.broker_port}"
                )
            else:
                logger.info(
                    f"Connecting to MQTT broker {self.config.broker_host}:{self.config.broker_port} (UNENCRYPTED)"
                )

            self.client.connect(
                self.config.broker_host, self.config.broker_port, self.config.keep_alive
            )
            self.client.loop_start()
            # Give it a moment to connect
            time.sleep(0.5)
            return self.connected
        except Exception as e:
            logger.error(f"Error connecting to MQTT broker: {e}")
            return False

    def disconnect(self):
        """Disconnect from the MQTT broker."""
        if self.connected:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("Disconnected from MQTT broker")

    def _reconnect(self):
        """Attempt to reconnect to the MQTT broker."""
        if not self.connected:
            logger.info(
                f"Attempting to reconnect in {self.config.reconnect_delay} seconds..."
            )
            time.sleep(self.config.reconnect_delay)
            try:
                self.connect()
            except Exception as e:
                logger.error(f"Reconnection failed: {e}")

    def subscribe(self, topic: str, qos: int = 1) -> bool:
        """Subscribe to a topic."""
        if not self.connected:
            logger.warning("Cannot subscribe: Not connected to MQTT broker")
            return False
        status = self.client.subscribe(topic, qos)
        if status[0] != mqtt.MQTT_ERR_SUCCESS:
            logger.error(
                f"Failed to subscribe to topic: {mqtt.error_string(status[0])}"
            )
            return False
        return True

    def set_on_message(
        self, callback: Callable[[mqtt.Client, Any, mqtt.MQTTMessage], None]
    ):
        """Set the callback for when a message is received."""
        self.client.on_message = callback

    def publish(
        self, topic: str, payload: Dict[str, Any], retain: bool = False
    ) -> bool:
        """
        Publish a message to the MQTT broker.

        Args:
            topic: The topic to publish to (will be prefixed with config.topic_prefix)
            payload: The message payload (will be converted to JSON)
            retain: Whether the message should be retained by the broker

        Returns:
            bool: True if successfully published, False otherwise
        """
        if not self.connected:
            logger.warning("Cannot publish: Not connected to MQTT broker")
            return False

        full_topic = topic
        if self.config.topic_prefix is not None and self.config.topic_prefix != "":
            full_topic = f"{self.config.topic_prefix}/{topic}"

        logger.info(f"Publishing message to topic: {full_topic}")
        try:
            # Convert payload to JSON string
            def ensure_json_serializable(payload):
                if hasattr(payload, "model_dump"):
                    return payload.model_dump()
                elif hasattr(payload, "dict"):
                    return payload.dict()
                return payload

            message = json.dumps(ensure_json_serializable(payload))

            # Monitor payload size
            self._record_payload_metrics(payload, message)

            logger.info(f"Publishing message to topic: {full_topic}")
            result = self.client.publish(
                full_topic, message, qos=self.config.qos, retain=retain
            )

            logger.info(
                f"Published message to topic: {full_topic} with result: {result.rc}"
            )
            # result.wait_for_publish() # This is blocking and will wait for the message to be published.
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                logger.error(
                    f"Failed to publish message: {mqtt.error_string(result.rc)}"
                )
                return False

            return True
        except Exception as e:
            logger.error(f"Error publishing message: {str(e)}")
            return False

    def _record_payload_metrics(self, payload: Dict[str, Any], message: str) -> None:
        """
        Record payload metrics for monitoring MQTT message sizes.

        Args:
            payload: Original payload dictionary before JSON serialization
            message: JSON serialized message string
        """
        try:
            has_optional_properties = self._check_for_optional_properties(payload)
            property_count = self._count_properties(payload)
            payload_monitor.record_payload_size(
                payload=message,
                property_count=property_count,
                has_optional_properties=has_optional_properties,
            )
        except Exception as e:
            # Don't let monitoring errors break publishing
            logger.debug(f"Failed to record payload metrics: {e}")

    def _check_for_optional_properties(self, payload: Dict[str, Any]) -> bool:
        """
        Check if the payload contains optional BACnet properties.

        Returns True if any optional properties are detected in the payload.
        """
        # Optional property indicators - JSON strings or complex objects
        optional_property_keys = [
            "priority_array",
            "limit_enable",
            "event_enable",
            "acked_transitions",
            "event_time_stamps",
            "event_message_texts",
            "event_message_texts_config",
            "event_algorithm_inhibit_ref",
            "min_pres_value",
            "max_pres_value",
            "cov_increment",
            "time_delay",
            "time_delay_normal",
            "deadband",
            "notification_class",
            "notify_type",
            "high_limit",
            "low_limit",
        ]

        def search_dict(obj, keys_to_find):
            """Recursively search for keys in nested dictionaries."""
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key in keys_to_find:
                        return True
                    if isinstance(value, (dict, list)):
                        if search_dict(value, keys_to_find):
                            return True
            elif isinstance(obj, list):
                for item in obj:
                    if search_dict(item, keys_to_find):
                        return True
            return False

        return search_dict(payload, optional_property_keys)

    def _count_properties(self, payload: Dict[str, Any]) -> int:
        """
        Count the number of properties in the payload.

        For nested objects, counts top-level keys and nested keys in 'points' arrays.
        """
        count = 0

        def count_keys(obj):
            nonlocal count
            if isinstance(obj, dict):
                count += len(obj)
                # If this is a point with properties, count its nested properties too
                if "properties" in obj and isinstance(obj["properties"], dict):
                    count += len(obj["properties"])
                # Recursively count in nested objects/lists
                for value in obj.values():
                    if isinstance(value, (dict, list)):
                        count_keys(value)
            elif isinstance(obj, list):
                for item in obj:
                    count_keys(item)

        count_keys(payload)
        return count
