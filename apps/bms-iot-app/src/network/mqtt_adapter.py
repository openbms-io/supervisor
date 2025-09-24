"""
MQTT Adapter for BMS IoT Application.
Provides functionality for MQTT operations and configuration.
"""

import json
import logging
import os
import time
from typing import Dict, Any, Optional

from .mqtt_client import MQTTClient
from .mqtt_config import (
    MQTTConfig,
    save_config,
    load_config,
    emqx_cloud_config_template,
    CERT_FILE_PATH,
)

# Get module-level logger
logger = logging.getLogger(__name__)

# Load saved MQTT configuration
mqtt_config = load_config()


def configure_mqtt(
    broker_host: str,
    broker_port: int,
    client_id: str,
    username: Optional[str],
    password: Optional[str],
    use_tls: bool,
    tls_ca_cert: Optional[str],
    topic_prefix: str,
) -> MQTTConfig:
    """Configure MQTT client with the specified parameters."""
    global mqtt_config

    # Update global configuration
    mqtt_config = MQTTConfig(
        broker_host=broker_host,
        broker_port=broker_port,
        client_id=client_id,
        username=username,
        password=password,
        use_tls=use_tls,
        tls_ca_cert=tls_ca_cert,
        topic_prefix=topic_prefix,
    )

    # If TLS is enabled but no certificate is specified, try to use the default EMQX certificate
    if use_tls and not tls_ca_cert and os.path.exists(CERT_FILE_PATH):
        mqtt_config.tls_ca_cert = CERT_FILE_PATH
        logger.info(f"Using default CA certificate: {CERT_FILE_PATH}")

    # Save configuration to file
    save_config(mqtt_config)

    # Log configuration details
    logger.info("MQTT configuration updated:")
    logger.info(f"  Broker: {broker_host}:{broker_port}")
    logger.info(f"  Client ID: {client_id}")
    logger.info(f"  Topic prefix: {topic_prefix}")
    logger.info(f"  TLS enabled: {use_tls}")
    if mqtt_config.tls_ca_cert:
        logger.info(f"  CA Certificate: {mqtt_config.tls_ca_cert}")
    if username:
        logger.info(f"  Username: {username}")

    return mqtt_config


def configure_emqx(
    username: str,
    password: str,
    client_id: str,
    topic_prefix: str,
) -> MQTTConfig:
    """Configure MQTT client for EMQX with TLS."""
    global mqtt_config

    # Check if certificate file exists
    if not os.path.exists(CERT_FILE_PATH):
        logger.error(f"CA certificate file not found at {CERT_FILE_PATH}")
        raise FileNotFoundError(f"CA certificate file not found at {CERT_FILE_PATH}")

    # Update global configuration using EMQX template
    mqtt_config = MQTTConfig(
        broker_host=emqx_cloud_config_template.broker_host,
        broker_port=emqx_cloud_config_template.broker_port,
        client_id=client_id,
        username=username,
        password=password,
        use_tls=True,
        tls_ca_cert=CERT_FILE_PATH,
        topic_prefix=topic_prefix,
    )

    # Save configuration to file
    save_config(mqtt_config)

    # Log configuration details
    logger.info("EMQX MQTT configuration updated:")
    logger.info(
        f"  Broker: {emqx_cloud_config_template.broker_host}:{emqx_cloud_config_template.broker_port} (TLS enabled)"
    )
    logger.info(f"  Client ID: {client_id}")
    logger.info(f"  Topic prefix: {topic_prefix}")
    logger.info(f"  CA Certificate: {CERT_FILE_PATH}")
    logger.info(f"  Username: {username}")

    return mqtt_config


def test_connection() -> bool:
    """Test MQTT connection with current configuration."""
    logger.info(
        f"Testing MQTT connection to {mqtt_config.broker_host}:{mqtt_config.broker_port}"
    )

    client = MQTTClient(mqtt_config)
    if client.connect():
        logger.info("Successfully connected to MQTT broker!")

        # Publish a test message
        success = client.publish(
            "test",
            {"message": "Test message from BMS IoT app", "timestamp": time.time()},
        )

        if success:
            logger.info("Test message published successfully!")
        else:
            logger.error("Failed to publish test message")

        # Disconnect
        time.sleep(1)  # Give time for the message to be sent
        client.disconnect()
        return True
    else:
        logger.error(f"Failed to connect to MQTT broker {mqtt_config.broker_host}")
        return False


def get_current_config() -> Dict[str, Any]:
    """Get current MQTT configuration as a dictionary."""
    config_dict = {
        "broker": f"{mqtt_config.broker_host}:{mqtt_config.broker_port}",
        "client_id": mqtt_config.client_id,
        "topic_prefix": mqtt_config.topic_prefix,
        "tls_enabled": mqtt_config.use_tls,
    }

    if mqtt_config.tls_ca_cert:
        config_dict["ca_certificate"] = mqtt_config.tls_ca_cert

    if mqtt_config.username:
        config_dict["username"] = mqtt_config.username

    logger.debug(f"Retrieved configuration for broker {mqtt_config.broker_host}")
    return config_dict


def publish_message(
    topic: str,
    message: Optional[str] = None,
    temperature: Optional[float] = None,
    humidity: Optional[float] = None,
    retain: bool = False,
) -> bool:
    """Publish a message to the MQTT broker."""
    # Create payload
    payload = {
        "timestamp": time.time(),
        "source": "bms-iot-app",
        "type": "test-message",
    }

    # Add custom message if provided
    if message:
        payload["message"] = message

    # Add sensor data if provided
    if temperature is not None:
        payload["temperature"] = temperature

    if humidity is not None:
        payload["humidity"] = humidity

    # If no data was provided, add some default values
    if not message and temperature is None and humidity is None:
        payload["temperature"] = 22.5
        payload["humidity"] = 45.0
        payload["message"] = "Test message from BMS IoT application"

    full_topic = topic
    if mqtt_config.topic_prefix is not None and mqtt_config.topic_prefix != "":
        full_topic = f"{mqtt_config.topic_prefix}/{topic}"

    logger.info(f"Publishing to topic {full_topic}:")
    logger.info(json.dumps(payload, indent=2))

    # Connect and publish
    client = MQTTClient(mqtt_config)
    if client.connect():
        logger.info(
            f"Connected to MQTT broker {mqtt_config.broker_host}:{mqtt_config.broker_port}"
        )

        # Publish message
        success = client.publish(topic, payload, retain)

        if success:
            logger.info("Message published successfully!")
        else:
            logger.error("Failed to publish message")

        # Disconnect
        time.sleep(0.5)  # Give time for the message to be sent
        client.disconnect()
        return success
    else:
        logger.error(f"Failed to connect to MQTT broker {mqtt_config.broker_host}")
        return False


def get_mqtt_config() -> MQTTConfig:
    """Get the current MQTT configuration."""
    return mqtt_config
