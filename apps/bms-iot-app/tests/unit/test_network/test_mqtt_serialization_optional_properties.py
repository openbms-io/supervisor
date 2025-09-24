"""
Test MQTT Serialization with BACnet Optional Properties.

This test suite validates the Phase 3 enhancements to the _serialize_point
function that added support for parsing JSON properties and structured
MQTT payload transmission.
"""

import json
from datetime import datetime, timezone
from unittest.mock import patch
from src.network.mqtt_command_dispatcher import _serialize_point
from src.models.controller_points import ControllerPointsModel


class TestMQTTSerializationOptionalProperties:
    """Test MQTT serialization with optional BACnet properties."""

    def test_serialize_point_with_basic_properties_only(self):
        """Test: Serialization with only basic required properties."""
        point = ControllerPointsModel(
            controller_ip_address="192.168.1.100",
            bacnet_object_type="analogValue",
            point_id=1,
            iot_device_point_id="test-point-id",
            controller_id="test-controller",
            controller_device_id="test-device",
            present_value="22.5",
            units="degreesCelsius",
        )

        serialized = _serialize_point(point)

        assert serialized["controller_ip_address"] == "192.168.1.100"
        assert serialized["present_value"] == "22.5"
        assert serialized["units"] == "degreesCelsius"

        # Optional properties should be None
        assert serialized["high_limit"] is None
        assert serialized["priority_array"] is None
        assert serialized["event_enable"] is None

    def test_serialize_point_with_status_flags_parsing(self):
        """Test: Status flags semicolon-separated string to array conversion."""
        point = ControllerPointsModel(
            controller_ip_address="192.168.1.100",
            bacnet_object_type="analogValue",
            point_id=1,
            iot_device_point_id="test-point-id",
            controller_id="test-controller",
            controller_device_id="test-device",
            status_flags="fault;overridden;out-of-service",
        )

        serialized = _serialize_point(point)

        # Should convert semicolon-separated to array
        assert serialized["status_flags"] == ["fault", "overridden", "out-of-service"]

    def test_serialize_point_with_empty_status_flags(self):
        """Test: Empty or None status flags handling."""
        point = ControllerPointsModel(
            controller_ip_address="192.168.1.100",
            bacnet_object_type="analogValue",
            point_id=1,
            iot_device_point_id="test-point-id",
            controller_id="test-controller",
            controller_device_id="test-device",
            status_flags=None,
        )

        serialized = _serialize_point(point)
        assert serialized["status_flags"] is None

    def test_serialize_point_with_priority_array_json(self):
        """Test: Priority array JSON string parsing to structured data."""
        priority_array_json = json.dumps(
            [
                None,
                None,
                25.0,
                None,
                None,
                None,
                None,
                None,
                50.0,
                None,
                None,
                None,
                None,
                None,
                None,
                20.0,
            ]
        )

        point = ControllerPointsModel(
            controller_ip_address="192.168.1.100",
            bacnet_object_type="analogValue",
            point_id=1,
            iot_device_point_id="test-point-id",
            controller_id="test-controller",
            controller_device_id="test-device",
            priority_array=priority_array_json,
        )

        serialized = _serialize_point(point)

        # Should parse JSON string to structured data
        assert isinstance(serialized["priority_array"], list)
        assert len(serialized["priority_array"]) == 16
        assert serialized["priority_array"][2] == 25.0
        assert serialized["priority_array"][8] == 50.0
        assert serialized["priority_array"][15] == 20.0
        assert serialized["priority_array"][0] is None

    def test_serialize_point_with_limit_enable_json(self):
        """Test: Limit enable JSON string parsing to structured data."""
        limit_enable_json = json.dumps(
            {"lowLimitEnable": True, "highLimitEnable": False}
        )

        point = ControllerPointsModel(
            controller_ip_address="192.168.1.100",
            bacnet_object_type="analogValue",
            point_id=1,
            iot_device_point_id="test-point-id",
            controller_id="test-controller",
            controller_device_id="test-device",
            limit_enable=limit_enable_json,
        )

        serialized = _serialize_point(point)

        # Should parse JSON string to structured object
        assert isinstance(serialized["limit_enable"], dict)
        assert serialized["limit_enable"]["lowLimitEnable"] is True
        assert serialized["limit_enable"]["highLimitEnable"] is False

    def test_serialize_point_with_event_enable_json(self):
        """Test: Event enable JSON string parsing to structured data."""
        event_enable_json = json.dumps(
            {"toFault": True, "toNormal": True, "toOffnormal": False}
        )

        point = ControllerPointsModel(
            controller_ip_address="192.168.1.100",
            bacnet_object_type="analogValue",
            point_id=1,
            iot_device_point_id="test-point-id",
            controller_id="test-controller",
            controller_device_id="test-device",
            event_enable=event_enable_json,
        )

        serialized = _serialize_point(point)

        # Should parse JSON string to structured object
        assert isinstance(serialized["event_enable"], dict)
        assert serialized["event_enable"]["toFault"] is True
        assert serialized["event_enable"]["toNormal"] is True
        assert serialized["event_enable"]["toOffnormal"] is False

    def test_serialize_point_with_event_timestamps_json(self):
        """Test: Event timestamps JSON array parsing."""
        timestamps_json = json.dumps(
            ["2024-01-01T10:00:00Z", None, "2024-01-01T12:00:00Z"]
        )

        point = ControllerPointsModel(
            controller_ip_address="192.168.1.100",
            bacnet_object_type="analogValue",
            point_id=1,
            iot_device_point_id="test-point-id",
            controller_id="test-controller",
            controller_device_id="test-device",
            event_time_stamps=timestamps_json,
        )

        serialized = _serialize_point(point)

        # Should parse JSON string to array
        assert isinstance(serialized["event_time_stamps"], list)
        assert len(serialized["event_time_stamps"]) == 3
        assert serialized["event_time_stamps"][0] == "2024-01-01T10:00:00Z"
        assert serialized["event_time_stamps"][1] is None
        assert serialized["event_time_stamps"][2] == "2024-01-01T12:00:00Z"

    def test_serialize_point_with_event_messages_json(self):
        """Test: Event message texts JSON array parsing."""
        messages_json = json.dumps(
            ["High alarm condition", "Normal operation", "Warning threshold"]
        )

        point = ControllerPointsModel(
            controller_ip_address="192.168.1.100",
            bacnet_object_type="analogValue",
            point_id=1,
            iot_device_point_id="test-point-id",
            controller_id="test-controller",
            controller_device_id="test-device",
            event_message_texts=messages_json,
        )

        serialized = _serialize_point(point)

        # Should parse JSON string to array
        assert isinstance(serialized["event_message_texts"], list)
        assert len(serialized["event_message_texts"]) == 3
        assert serialized["event_message_texts"][0] == "High alarm condition"
        assert serialized["event_message_texts"][1] == "Normal operation"
        assert serialized["event_message_texts"][2] == "Warning threshold"

    def test_serialize_point_with_object_property_reference_json(self):
        """Test: Object property reference JSON parsing."""
        ref_json = json.dumps(
            {
                "objectIdentifier": "analogInput:1",
                "propertyIdentifier": "presentValue",
                "arrayIndex": None,
            }
        )

        point = ControllerPointsModel(
            controller_ip_address="192.168.1.100",
            bacnet_object_type="analogValue",
            point_id=1,
            iot_device_point_id="test-point-id",
            controller_id="test-controller",
            controller_device_id="test-device",
            event_algorithm_inhibit_ref=ref_json,
        )

        serialized = _serialize_point(point)

        # Should parse JSON string to structured object
        assert isinstance(serialized["event_algorithm_inhibit_ref"], dict)
        assert (
            serialized["event_algorithm_inhibit_ref"]["objectIdentifier"]
            == "analogInput:1"
        )
        assert (
            serialized["event_algorithm_inhibit_ref"]["propertyIdentifier"]
            == "presentValue"
        )
        assert serialized["event_algorithm_inhibit_ref"]["arrayIndex"] is None

    def test_serialize_point_with_all_json_properties(self):
        """Test: Serialization with all JSON properties populated."""
        point = ControllerPointsModel(
            controller_ip_address="192.168.1.100",
            bacnet_object_type="analogValue",
            point_id=1,
            iot_device_point_id="test-point-id",
            controller_id="test-controller",
            controller_device_id="test-device",
            priority_array=json.dumps([None] * 16),
            limit_enable=json.dumps({"lowLimitEnable": True, "highLimitEnable": True}),
            event_enable=json.dumps(
                {"toFault": True, "toNormal": True, "toOffnormal": True}
            ),
            acked_transitions=json.dumps(
                {"toFault": False, "toNormal": True, "toOffnormal": False}
            ),
            event_time_stamps=json.dumps([None, None, None]),
            event_message_texts=json.dumps(["", "", ""]),
            event_message_texts_config=json.dumps(["", "", ""]),
            event_algorithm_inhibit_ref=json.dumps(
                {"objectIdentifier": "test", "propertyIdentifier": "test"}
            ),
        )

        serialized = _serialize_point(point)

        # All JSON properties should be parsed to structured data
        assert isinstance(serialized["priority_array"], list)
        assert isinstance(serialized["limit_enable"], dict)
        assert isinstance(serialized["event_enable"], dict)
        assert isinstance(serialized["acked_transitions"], dict)
        assert isinstance(serialized["event_time_stamps"], list)
        assert isinstance(serialized["event_message_texts"], list)
        assert isinstance(serialized["event_message_texts_config"], list)
        assert isinstance(serialized["event_algorithm_inhibit_ref"], dict)

    def test_serialize_point_with_invalid_json_properties(self):
        """Test: Graceful handling of invalid JSON in properties."""
        point = ControllerPointsModel(
            controller_ip_address="192.168.1.100",
            bacnet_object_type="analogValue",
            point_id=1,
            iot_device_point_id="test-point-id",
            controller_id="test-controller",
            controller_device_id="test-device",
            priority_array="invalid json {{{",
            limit_enable="not json at all",
            event_enable=None,  # None should be handled gracefully
        )

        with patch("src.utils.logger.logger.warning") as mock_warning:
            serialized = _serialize_point(point)

            # Should log warnings for invalid JSON
            assert mock_warning.call_count >= 2  # At least 2 invalid JSON strings

            # Invalid JSON should result in None values
            assert serialized["priority_array"] is None
            assert serialized["limit_enable"] is None
            assert serialized["event_enable"] is None

    def test_serialize_point_with_datetime_fields(self):
        """Test: Datetime fields are properly converted to ISO format."""
        now = datetime.now(timezone.utc)
        point = ControllerPointsModel(
            controller_ip_address="192.168.1.100",
            bacnet_object_type="analogValue",
            point_id=1,
            iot_device_point_id="test-point-id",
            controller_id="test-controller",
            controller_device_id="test-device",
            created_at=now,
            updated_at=now,
        )

        serialized = _serialize_point(point)

        # Datetime fields should be ISO formatted strings
        assert isinstance(serialized["created_at"], str)
        assert isinstance(serialized["updated_at"], str)
        assert "T" in serialized["created_at"]  # ISO format marker
        assert "T" in serialized["updated_at"]  # ISO format marker

    def test_serialize_point_unix_timestamp_included(self):
        """Test: Unix millisecond timestamp is included in serialized data."""
        point = ControllerPointsModel(
            controller_ip_address="192.168.1.100",
            bacnet_object_type="analogValue",
            point_id=1,
            iot_device_point_id="test-point-id",
            controller_id="test-controller",
            controller_device_id="test-device",
        )

        serialized = _serialize_point(point)

        # Unix timestamp should be included for InfluxDB
        assert "created_at_unix_milli_timestamp" in serialized
        # The computed field might be None without database, so check if present or None
        timestamp_value = serialized["created_at_unix_milli_timestamp"]
        assert timestamp_value is None or isinstance(timestamp_value, int)

    def test_serialize_point_with_mixed_properties(self):
        """Test: Serialization with mix of basic, health, and optional properties."""
        point = ControllerPointsModel(
            controller_ip_address="192.168.1.100",
            bacnet_object_type="analogValue",
            point_id=1,
            iot_device_point_id="test-point-id",
            controller_id="test-controller",
            controller_device_id="test-device",
            # Basic properties
            present_value="22.5",
            units="degreesCelsius",
            # Health properties
            status_flags="fault;overridden",
            event_state="normal",
            out_of_service=False,
            reliability="noFaultDetected",
            # Optional properties
            high_limit=30.0,
            low_limit=10.0,
            priority_array=json.dumps([None, None, 25.0]),
            event_detection_enable=True,
        )

        serialized = _serialize_point(point)

        # All property types should be present and correctly formatted
        assert serialized["present_value"] == "22.5"
        assert serialized["units"] == "degreesCelsius"
        assert serialized["status_flags"] == ["fault", "overridden"]
        assert serialized["event_state"] == "normal"
        assert serialized["out_of_service"] is False
        assert serialized["reliability"] == "noFaultDetected"
        assert serialized["high_limit"] == 30.0
        assert serialized["low_limit"] == 10.0
        assert isinstance(serialized["priority_array"], list)
        assert serialized["event_detection_enable"] is True
