"""
Test fixtures validation.

User Story: As a developer, I want test fixtures to work reliably
"""

import pytest


def test_mock_bacnet_wrapper_fixture(mock_bacnet_wrapper):
    """Test: All fixtures load without errors - BACnet wrapper"""
    assert mock_bacnet_wrapper is not None
    assert hasattr(mock_bacnet_wrapper, "connect")
    assert hasattr(mock_bacnet_wrapper, "read_points")
    assert mock_bacnet_wrapper.is_connected is True


def test_mock_mqtt_client_fixture(mock_mqtt_client):
    """Test: All fixtures load without errors - MQTT client"""
    assert mock_mqtt_client is not None
    assert hasattr(mock_mqtt_client, "connect")
    assert hasattr(mock_mqtt_client, "publish")
    assert mock_mqtt_client.is_connected is True


def test_sample_actor_messages_fixture(sample_actor_messages):
    """Test: Sample actor messages fixture works"""
    assert "config_upload" in sample_actor_messages
    assert "point_publish" in sample_actor_messages
    assert "heartbeat" in sample_actor_messages

    config_msg = sample_actor_messages["config_upload"]
    assert config_msg["sender"] == "MQTT"
    assert config_msg["receiver"] == "BACNET"
    assert config_msg["message_type"] == "CONFIG_UPLOAD_REQUEST"


def test_sample_bacnet_data_fixture(sample_bacnet_data):
    """Test: Sample BACnet data fixture works"""
    assert "device_123" in sample_bacnet_data
    assert "device_456" in sample_bacnet_data
    assert sample_bacnet_data["device_123"]["temp1"] == 25.0


@pytest.mark.asyncio
async def test_async_fixture_functionality(mock_bacnet_wrapper):
    """Test: Fixture cleanup works correctly - async operations"""
    # Test async mock functionality
    await mock_bacnet_wrapper.connect()
    result = await mock_bacnet_wrapper.read_points(["temp1", "temp2"])

    assert result == {"temp1": 25.0, "temp2": 26.0}
    mock_bacnet_wrapper.connect.assert_called_once()


def test_mock_objects_have_expected_methods(mock_rest_client):
    """Test: Mock objects have expected methods and properties"""
    assert hasattr(mock_rest_client, "post")
    assert hasattr(mock_rest_client, "get")
    assert hasattr(mock_rest_client, "uploaded_data")
    assert isinstance(mock_rest_client.uploaded_data, list)
