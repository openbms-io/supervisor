"""
Dynamic path configuration for BMS IoT App.

Provides container-aware path selection:
- Container environment: Uses /data/* paths for persistence
- Native environment: Uses existing local paths
"""

import os
from pathlib import Path
from typing import Dict, Any


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


def get_config_paths() -> Dict[str, Any]:
    """
    Get configuration file paths based on runtime environment.

    Returns:
        Dict containing all configuration paths:
        - database_url: SQLite database connection string
        - mqtt_config_file: MQTT configuration file path
        - credentials_file: API credentials file path
        - cert_file: TLS certificate file path
        - data_dir: Base directory for data storage
    """
    if is_container_environment():
        # Container paths - persistent storage in /data
        data_dir = Path("/data")

        # Ensure data directory exists (only if we have permission)
        try:
            data_dir.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError):
            # If we can't create /data, we're probably in a test environment
            # Fall back to native paths
            pass

        return {
            "database_url": f"sqlite+aiosqlite:///{data_dir}/bms_bacnet.db",
            "mqtt_config_file": str(data_dir / "mqtt-config.json"),
            "credentials_file": str(data_dir / "credentials.json"),
            "cert_file": str(data_dir / "emqxsl-ca.crt"),
            "data_dir": str(data_dir),
            "is_container": True,
        }
    else:
        # Native paths - simplified with mirror structure support
        # Certificate is always in the app root directory
        app_root = Path(
            __file__
        ).parent.parent.parent  # Go from src/config/paths.py → src/config → src → app root
        cert_file = app_root / "emqxsl-ca.crt"

        return {
            "database_url": "sqlite+aiosqlite:///./bms_bacnet.db",
            "mqtt_config_file": os.path.expanduser("~/.bms-iot-mqtt-config.json"),
            "credentials_file": str(Path.home() / ".bms" / "credentials.json"),
            "cert_file": str(cert_file.resolve()),
            "data_dir": str(Path.cwd()),
            "is_container": False,
        }


def get_database_url() -> str:
    """Get the database connection URL for current environment."""
    return get_config_paths()["database_url"]


def get_mqtt_config_file() -> str:
    """Get the MQTT configuration file path for current environment."""
    return get_config_paths()["mqtt_config_file"]


def get_credentials_file() -> str:
    """Get the credentials file path for current environment."""
    return get_config_paths()["credentials_file"]


def get_cert_file() -> str:
    """Get the TLS certificate file path for current environment."""
    return get_config_paths()["cert_file"]
