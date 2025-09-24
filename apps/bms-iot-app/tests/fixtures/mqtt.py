"""
MQTT-related test fixtures.
"""

import pytest
from unittest.mock import Mock, AsyncMock


@pytest.fixture
def mock_mqtt_adapter():
    """Mock MQTT adapter for testing"""
    adapter = AsyncMock()
    adapter.connect = AsyncMock()
    adapter.disconnect = AsyncMock()
    adapter.publish = AsyncMock()
    adapter.subscribe = AsyncMock()
    adapter.is_connected = True
    adapter.published_messages = []
    adapter.subscriptions = []
    return adapter


@pytest.fixture
def mock_mqtt_config():
    """Mock MQTT configuration"""
    return {
        "broker_host": "test.mosquitto.org",
        "broker_port": 1883,
        "keepalive": 60,
        "username": None,
        "password": None,
        "client_id": "test_client_123",
    }


@pytest.fixture
def mock_mqtt_message():
    """Mock MQTT message"""
    message = Mock()
    message.topic = "iot/global/test_org/test_site/test_device/command/start"
    message.payload = b'{"command": "start_monitoring", "device_id": "123"}'
    message.qos = 1
    message.retain = False
    return message


@pytest.fixture
def sample_mqtt_topics():
    """Sample MQTT topics for testing"""
    return {
        "command_start": "iot/global/test_org/test_site/test_device/command/start_monitoring/request",
        "command_stop": "iot/global/test_org/test_site/test_device/command/stop_monitoring/request",
        "status": "iot/global/test_org/test_site/test_device/status/update",
        "heartbeat": "iot/global/test_org/test_site/test_device/status/heartbeat",
        "data": "iot/global/test_org/test_site/test_device/data/bulk",
    }


@pytest.fixture
def mock_mqtt_command_dispatcher():
    """Mock MQTT command dispatcher"""
    dispatcher = AsyncMock()
    dispatcher.dispatch_command = AsyncMock()
    dispatcher.register_handler = AsyncMock()
    dispatcher.command_handlers = {}
    return dispatcher
