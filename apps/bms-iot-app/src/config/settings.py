"""Centralized configuration management with environment variable support."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv


def get_env_file() -> str:
    """Determine which .env file to use based on environment."""
    if "pytest" in sys.modules or "PYTEST_CURRENT_TEST" in os.environ:
        return ".env.test"
    return os.getenv("ENV_FILE", ".env")


def load_environment(app_root: Path = None):
    """Load environment variables from appropriate .env file.

    Args:
        app_root: Optional path to app root. If not provided, uses default relative path.
    """
    env_file = get_env_file()

    if app_root is None:
        # TODO: Need to find a better way to do this
        app_root = Path(__file__).parent.parent.parent

    env_path = app_root / env_file
    if env_path.exists():
        load_dotenv(env_path, override=True)


# Load environment variables when module is imported
load_environment()


class Settings:
    """Application settings loaded from environment variables."""

    DATABASE_PATH = os.path.expanduser(
        os.getenv("BMS_IOT_DATABASE_PATH", "~/.bms/bms-iot.db")
    )
    DATABASE_URL = f"sqlite+aiosqlite:///{DATABASE_PATH}"

    MQTT_CONFIG_PATH = os.path.expanduser(
        os.getenv("BMS_IOT_MQTT_CONFIG_PATH", "~/.bms-iot-mqtt-config.json")
    )

    CERT_PATH = os.path.expanduser(os.getenv("BMS_IOT_CERT_PATH", "./emqxsl-ca.crt"))


settings = Settings()
