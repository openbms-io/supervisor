"""Configuration paths management using centralized settings."""

import os
from pathlib import Path
from typing import Dict, Any
from src.config.settings import settings


def is_container_environment() -> bool:
    """
    Detect if running in a container environment.

    Returns:
        bool: True if running in container, False for native environment
    """
    # Check for explicit container flag (most reliable for our use case)
    if os.getenv("DOCKER_CONTAINER") == "true":
        return True

    # Check if /data directory exists and is writable (secondary check)
    data_path = Path("/data")
    if data_path.exists() and data_path.is_dir():
        try:
            # Test write access
            test_file = data_path / ".write_test"
            test_file.touch()
            test_file.unlink()
            return True
        except (PermissionError, OSError):
            pass

    return False


def get_database_file() -> str:
    """Get database file path from centralized settings."""
    return settings.DATABASE_PATH


def get_mqtt_config_file() -> str:
    """Get MQTT config file path from centralized settings."""
    return settings.MQTT_CONFIG_PATH


def get_cert_file() -> str:
    """Get certificate file path from centralized settings."""
    return settings.CERT_PATH


def get_config() -> Dict[str, Any]:
    """Get all configuration paths."""
    return {
        "database_file": settings.DATABASE_PATH,
        "mqtt_config_file": settings.MQTT_CONFIG_PATH,
        "cert_file": settings.CERT_PATH,
    }


def get_database_url() -> str:
    """Get the database connection URL for current environment."""
    return settings.DATABASE_URL
