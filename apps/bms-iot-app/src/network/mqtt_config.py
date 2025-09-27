from pydantic import BaseModel
from typing import Optional
import json
import os
from src.utils.logger import logger

from ..config.paths import get_mqtt_config_file, get_cert_file

# Path to store persistent MQTT configuration
CONFIG_FILE_PATH = get_mqtt_config_file()


class MQTTConfig(BaseModel):
    """Configuration for MQTT client."""

    broker_host: str = "localhost"
    broker_port: int = 1883
    client_id: str = "bms-iot-client"
    username: Optional[str] = None
    password: Optional[str] = None
    use_tls: bool = True  # Enable TLS by default
    tls_ca_cert: Optional[str] = None
    topic_prefix: str = "bms/monitoring"
    qos: int = 1  # QoS level (0, 1, or 2)
    keep_alive: int = 60  # Keep alive interval in seconds
    reconnect_delay: int = 5  # Reconnect delay in seconds
    clean_session: bool = True  # Clean session flag for MQTT


def save_config(config: MQTTConfig) -> bool:
    """Save MQTT configuration to a file."""
    try:
        # Convert to dict, but exclude password from serialization if not needed
        config_dict = config.model_dump(
            exclude={"password"} if config.password is None else {}
        )

        with open(CONFIG_FILE_PATH, "w") as f:
            json.dump(config_dict, f, indent=2)

        logger.info(f"MQTT configuration saved to {CONFIG_FILE_PATH}")
        return True
    except Exception as e:
        logger.error(f"Failed to save MQTT configuration: {e}")
        return False


def load_config() -> MQTTConfig:
    """Load MQTT configuration from file, or return default if not found."""
    if not os.path.exists(CONFIG_FILE_PATH):
        logger.info("No saved MQTT configuration found, using default")
        return MQTTConfig()

    try:
        with open(CONFIG_FILE_PATH, "r") as f:
            config_dict = json.load(f)

        # Create new MQTTConfig instance
        config = MQTTConfig(**config_dict)
        logger.info(f"MQTT configuration loaded from {CONFIG_FILE_PATH}")
        logger.info(f"MQTT configuration: {config}")
        return config
    except Exception as e:
        logger.warning(f"Failed to load MQTT configuration: {e}. Using default.")
        return MQTTConfig()


# Default configuration for development
default_config = load_config()

# Path to the certificate file
CERT_FILE_PATH = get_cert_file()

# Example EMQX Cloud configuration template (DO NOT USE IN PRODUCTION)
# To configure MQTT, use the CLI: python -m src.cli mqtt config
# Or set environment variables for auto-provisioning
emqx_cloud_config_template = MQTTConfig(
    broker_host="t78ae18a.ala.us-east-1.emqxsl.com",
    broker_port=8883,  # TLS port
    client_id="bms-iot-client",
    username="",  # Configure via CLI or environment
    password="",  # Configure via CLI or environment
    use_tls=True,  # Enable TLS
    tls_ca_cert=CERT_FILE_PATH,  # Path to the CA certificate
    topic_prefix="",
)
