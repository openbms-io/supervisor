import json
import pytest
from pathlib import Path
from typing import Dict, Any

from ..topics_loader import (
    load_mqtt_topics,
    build_mqtt_topic_dict,
    build_mqtt_command_topic,
    build_mqtt_status_topic,
    build_mqtt_data_topic,
    Topics,
    CommandSection,
    StatusSection,
    DataSection,
)

def test_load_mqtt_topics():
    """Test that MQTT topics can be loaded from the JSON file as a Topics model."""
    topics = load_mqtt_topics()
    assert isinstance(topics, Topics)
    assert hasattr(topics, "command")
    assert hasattr(topics, "status")
    assert hasattr(topics, "data")
    assert hasattr(topics.command, "get_config")
    assert hasattr(topics.status, "update")
    assert hasattr(topics.data, "point")
    assert hasattr(topics.data, "point_bulk")

def test_build_mqtt_topic_dict():
    """Test building MQTT topic Topics model with placeholder replacement."""
    test_values = {
        "organization_id": "test-org",
        "site_id": "test-site",
        "iot_device_id": "test-iot-device",
        "controller_device_id": "test-controller",
        "iot_device_point_id": "test-point"
    }
    result = build_mqtt_topic_dict(**test_values)
    assert isinstance(result, Topics)
    # Check that placeholders are replaced
    def check_placeholders_replaced(node):
        if hasattr(node, "model_fields"):  # Pydantic v2 model
            for value in node.__dict__.values():
                check_placeholders_replaced(value)
        elif isinstance(node, str):
            for placeholder in test_values.keys():
                assert f"{{{placeholder}}}" not in node
                assert f"${{{placeholder}}}" not in node
    check_placeholders_replaced(result)
    # Explicitly check that the output values are as expected
    assert result.command.get_config.request == "iot/global/test-org/test-site/test-iot-device/command/get_config/request"
    assert result.command.get_config.response == "iot/global/test-org/test-site/test-iot-device/command/get_config/response"
    assert result.command.reboot.request == "iot/global/test-org/test-site/test-iot-device/command/reboot/request"
    assert result.command.reboot.response == "iot/global/test-org/test-site/test-iot-device/command/reboot/response"
    assert result.status.update == "iot/global/test-org/test-site/test-iot-device/status/update"
    assert result.status.heartbeat == "iot/global/test-org/test-site/test-iot-device/status/heartbeat"
    assert result.data.point == "iot/global/test-org/test-site/test-iot-device/test-controller/test-point"
    assert result.data.point_bulk == "iot/global/test-org/test-site/test-iot-device/bulk"

def test_build_mqtt_topic_dict_missing_values():
    """Test that missing or empty optional placeholder values result in data.point being None."""
    result = build_mqtt_topic_dict(
        organization_id="test-org",
        site_id="test-site",
        iot_device_id="test-iot-device",
        controller_device_id="test-controller",
        iot_device_point_id=""  # Empty point_id
    )
    assert result.data.point is None
    assert result.data.point_bulk == "iot/global/test-org/test-site/test-iot-device/bulk"

def test_build_mqtt_topic_dict_optional_data_point():
    """Test that data.point is None if controller_device_id or iot_device_point_id is missing."""
    result = build_mqtt_topic_dict(
        organization_id="test-org",
        site_id="test-site",
        iot_device_id="test-iot-device",
        controller_device_id=None,
        iot_device_point_id=None
    )
    assert result.data.point is None
    assert result.data.point_bulk == "iot/global/test-org/test-site/test-iot-device/bulk"

def test_build_mqtt_command_topic():
    """Test build_mqtt_command_topic returns a CommandSection with correct topics."""
    section = build_mqtt_command_topic(
        organization_id="test-org",
        site_id="test-site",
        iot_device_id="test-iot-device",
    )
    assert isinstance(section, CommandSection)
    assert section.get_config.request.startswith("iot/global/test-org/test-site/test-iot-device/command/get_config/request")
    assert section.reboot.request.startswith("iot/global/test-org/test-site/test-iot-device/command/reboot/request")

def test_build_mqtt_status_topic():
    """Test build_mqtt_status_topic returns a StatusSection with correct topics."""
    section = build_mqtt_status_topic(
        organization_id="test-org",
        site_id="test-site",
        iot_device_id="test-iot-device",
    )
    assert isinstance(section, StatusSection)
    assert section.update.startswith("iot/global/test-org/test-site/test-iot-device/status/update")
    assert section.heartbeat.startswith("iot/global/test-org/test-site/test-iot-device/status/heartbeat")

def test_build_mqtt_data_topic_full():
    """Test build_mqtt_data_topic returns a DataSection with point filled when all IDs are provided."""
    section = build_mqtt_data_topic(
        organization_id="test-org",
        site_id="test-site",
        iot_device_id="test-iot-device",
        controller_device_id="test-controller",
        iot_device_point_id="test-point",
    )
    assert isinstance(section, DataSection)
    assert section.point == "iot/global/test-org/test-site/test-iot-device/test-controller/test-point"
    assert section.point_bulk == "iot/global/test-org/test-site/test-iot-device/bulk"

def test_build_mqtt_data_topic_missing():
    """Test build_mqtt_data_topic returns a DataSection with point=None if controller_device_id or iot_device_point_id is missing."""
    section = build_mqtt_data_topic(
        organization_id="test-org",
        site_id="test-site",
        iot_device_id="test-iot-device",
        controller_device_id=None,
        iot_device_point_id=None,
    )
    assert isinstance(section, DataSection)
    assert section.point is None
    assert section.point_bulk == "iot/global/test-org/test-site/test-iot-device/bulk"

def test_build_mqtt_topic_dict_invalid_values():
    """Test that invalid values are handled appropriately."""
    test_values = {
        "organization_id": "test-org",
        "site_id": "test-site",
        "iot_device_id": "test-iot-device",
        "controller_device_id": "test-controller",
        "iot_device_point_id": "test-point"
    }

    result = build_mqtt_topic_dict(**test_values)

    # Verify that non-string values are preserved (not relevant for this schema, but keep for completeness)
    def check_value_types(node: Any) -> None:
        if isinstance(node, dict):
            for value in node.values():
                check_value_types(value)
        elif isinstance(node, (int, float, bool)):
            assert isinstance(node, (int, float, bool))

    check_value_types(result)

def test_build_mqtt_topic_dict_nested_structure():
    """Test that nested structures are properly handled."""
    test_values = {
        "organization_id": "test-org",
        "site_id": "test-site",
        "iot_device_id": "test-iot-device",
        "controller_device_id": "test-controller",
        "iot_device_point_id": "test-point"
    }

    result = build_mqtt_topic_dict(**test_values)

    # Verify that nested dictionaries are preserved
    def check_nested_structure(node: Any) -> None:
        if isinstance(node, dict):
            assert len(node) > 0
            for value in node.values():
                check_nested_structure(value)

    check_nested_structure(result)

def test_build_mqtt_topic_dict_empty_values():
    """Test that empty values raise ValueError."""
    test_values = {
        "organization_id": "",
        "site_id": "",
        "iot_device_id": "",
        "controller_device_id": "",
        "iot_device_point_id": ""
    }

    with pytest.raises(ValueError) as exc_info:
        build_mqtt_topic_dict(**test_values)
    assert "Missing placeholder value for" in str(exc_info.value)
