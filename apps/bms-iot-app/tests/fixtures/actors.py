"""
Actor-related test fixtures.
"""

import pytest
from unittest.mock import Mock, AsyncMock


@pytest.fixture
def mock_actor_system():
    """Mock actor system for testing"""
    system = Mock()
    system.actors = {}
    system.message_log = []
    return system


@pytest.fixture
def mock_mqtt_actor():
    """Mock MQTT actor for testing"""
    actor = AsyncMock()
    actor.name = "MQTT"
    actor.connect = AsyncMock()
    actor.publish = AsyncMock()
    actor.subscribe = AsyncMock()
    actor.disconnect = AsyncMock()
    actor.received_messages = []
    return actor


@pytest.fixture
def mock_bacnet_actor():
    """Mock BACnet monitoring actor for testing"""
    actor = AsyncMock()
    actor.name = "BACNET"
    actor.start_monitoring = AsyncMock()
    actor.stop_monitoring = AsyncMock()
    actor.read_points = AsyncMock(return_value={"temp1": 25.0, "temp2": 26.0})
    actor.received_messages = []
    return actor


@pytest.fixture
def mock_uploader_actor():
    """Mock uploader actor for testing"""
    actor = AsyncMock()
    actor.name = "UPLOADER"
    actor.upload_data = AsyncMock()
    actor.queue_data = AsyncMock()
    actor.received_messages = []
    actor.upload_queue = []
    return actor


@pytest.fixture
def mock_heartbeat_actor():
    """Mock heartbeat actor for testing"""
    actor = AsyncMock()
    actor.name = "HEARTBEAT"
    actor.generate_heartbeat = AsyncMock()
    actor.collect_status = AsyncMock()
    actor.received_messages = []
    return actor


@pytest.fixture
def all_mock_actors(
    mock_mqtt_actor, mock_bacnet_actor, mock_uploader_actor, mock_heartbeat_actor
):
    """All mock actors for comprehensive testing"""
    return {
        "MQTT": mock_mqtt_actor,
        "BACNET": mock_bacnet_actor,
        "UPLOADER": mock_uploader_actor,
        "HEARTBEAT": mock_heartbeat_actor,
    }
