"""
Test ControllerPointsModel with BACnet Optional Properties.

This test suite validates the Phase 3 enhancements that added 23 optional
BACnet properties to the ControllerPointsModel for SQLite storage.
"""

import json
from src.models.controller_points import ControllerPointsModel


class TestControllerPointsModelOptionalProperties:
    """Test optional BACnet properties in ControllerPointsModel."""

    def test_create_model_with_basic_properties_only(self):
        """Test: Model creation with only required fields works."""
        point = ControllerPointsModel(
            controller_ip_address="192.168.1.100",
            bacnet_object_type="analogValue",
            point_id=1,
            iot_device_point_id="test-point-id",
            controller_id="test-controller",
            controller_device_id="test-device",
        )

        assert point.controller_ip_address == "192.168.1.100"
        assert point.bacnet_object_type == "analogValue"
        assert point.point_id == 1

        # All optional properties should default to None
        assert point.min_pres_value is None
        assert point.max_pres_value is None
        assert point.priority_array is None
        assert point.event_enable is None

    def test_create_model_with_value_limit_properties(self):
        """Test: Model creation with value limit properties."""
        point = ControllerPointsModel(
            controller_ip_address="192.168.1.100",
            bacnet_object_type="analogValue",
            point_id=1,
            iot_device_point_id="test-point-id",
            controller_id="test-controller",
            controller_device_id="test-device",
            min_pres_value=10.0,
            max_pres_value=100.0,
            high_limit=85.0,
            low_limit=15.0,
            resolution=0.1,
        )

        assert point.min_pres_value == 10.0
        assert point.max_pres_value == 100.0
        assert point.high_limit == 85.0
        assert point.low_limit == 15.0
        assert point.resolution == 0.1

    def test_create_model_with_control_properties(self):
        """Test: Model creation with control properties (JSON storage)."""
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
            relinquish_default=20.0,
        )

        assert point.priority_array == priority_array_json
        assert point.relinquish_default == 20.0

        # Verify we can parse the JSON back
        parsed_array = json.loads(point.priority_array)
        assert len(parsed_array) == 16
        assert parsed_array[2] == 25.0
        assert parsed_array[8] == 50.0
        assert parsed_array[15] == 20.0

    def test_create_model_with_notification_properties(self):
        """Test: Model creation with notification configuration properties."""
        limit_enable_json = json.dumps(
            {"lowLimitEnable": True, "highLimitEnable": True}
        )

        point = ControllerPointsModel(
            controller_ip_address="192.168.1.100",
            bacnet_object_type="analogValue",
            point_id=1,
            iot_device_point_id="test-point-id",
            controller_id="test-controller",
            controller_device_id="test-device",
            cov_increment=0.5,
            time_delay=300,
            time_delay_normal=600,
            notification_class=1,
            notify_type="EVENT",
            deadband=0.2,
            limit_enable=limit_enable_json,
        )

        assert point.cov_increment == 0.5
        assert point.time_delay == 300
        assert point.time_delay_normal == 600
        assert point.notification_class == 1
        assert point.notify_type == "EVENT"
        assert point.deadband == 0.2
        assert point.limit_enable == limit_enable_json

        # Verify JSON parsing
        parsed_limit = json.loads(point.limit_enable)
        assert parsed_limit["lowLimitEnable"] is True
        assert parsed_limit["highLimitEnable"] is True

    def test_create_model_with_event_properties(self):
        """Test: Model creation with event properties (complex JSON)."""
        event_enable_json = json.dumps(
            {"toFault": True, "toNormal": True, "toOffnormal": False}
        )
        acked_transitions_json = json.dumps(
            {"toFault": False, "toNormal": True, "toOffnormal": False}
        )
        event_timestamps_json = json.dumps(["2024-01-01T10:00:00Z", None, None])
        event_messages_json = json.dumps(["High alarm", "Normal condition", "Warning"])

        point = ControllerPointsModel(
            controller_ip_address="192.168.1.100",
            bacnet_object_type="analogValue",
            point_id=1,
            iot_device_point_id="test-point-id",
            controller_id="test-controller",
            controller_device_id="test-device",
            event_enable=event_enable_json,
            acked_transitions=acked_transitions_json,
            event_time_stamps=event_timestamps_json,
            event_message_texts=event_messages_json,
            event_message_texts_config=json.dumps(["", "", ""]),
        )

        assert point.event_enable == event_enable_json
        assert point.acked_transitions == acked_transitions_json
        assert point.event_time_stamps == event_timestamps_json
        assert point.event_message_texts == event_messages_json

        # Verify JSON parsing for complex structures
        parsed_enable = json.loads(point.event_enable)
        assert parsed_enable["toFault"] is True
        assert parsed_enable["toOffnormal"] is False

        parsed_timestamps = json.loads(point.event_time_stamps)
        assert parsed_timestamps[0] == "2024-01-01T10:00:00Z"
        assert parsed_timestamps[1] is None

    def test_create_model_with_algorithm_control_properties(self):
        """Test: Model creation with algorithm control properties."""
        inhibit_ref_json = json.dumps(
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
            event_detection_enable=True,
            event_algorithm_inhibit_ref=inhibit_ref_json,
            event_algorithm_inhibit=False,
            reliability_evaluation_inhibit=False,
        )

        assert point.event_detection_enable is True
        assert point.event_algorithm_inhibit is False
        assert point.reliability_evaluation_inhibit is False
        assert point.event_algorithm_inhibit_ref == inhibit_ref_json

        # Verify JSON parsing
        parsed_ref = json.loads(point.event_algorithm_inhibit_ref)
        assert parsed_ref["objectIdentifier"] == "analogInput:1"
        assert parsed_ref["propertyIdentifier"] == "presentValue"
        assert parsed_ref["arrayIndex"] is None

    def test_create_model_with_all_optional_properties(self):
        """Test: Model creation with all 23 optional properties."""
        point = ControllerPointsModel(
            # Required fields
            controller_ip_address="192.168.1.100",
            bacnet_object_type="analogValue",
            point_id=1,
            iot_device_point_id="test-point-id",
            controller_id="test-controller",
            controller_device_id="test-device",
            # Value limit properties
            min_pres_value=10.0,
            max_pres_value=100.0,
            high_limit=85.0,
            low_limit=15.0,
            resolution=0.1,
            # Control properties
            priority_array=json.dumps([None] * 16),
            relinquish_default=20.0,
            # Notification configuration
            cov_increment=0.5,
            time_delay=300,
            time_delay_normal=600,
            notification_class=1,
            notify_type="EVENT",
            deadband=0.2,
            limit_enable=json.dumps({"lowLimitEnable": True, "highLimitEnable": True}),
            # Event properties
            event_enable=json.dumps(
                {"toFault": True, "toNormal": True, "toOffnormal": True}
            ),
            acked_transitions=json.dumps(
                {"toFault": False, "toNormal": True, "toOffnormal": False}
            ),
            event_time_stamps=json.dumps([None, None, None]),
            event_message_texts=json.dumps(["", "", ""]),
            event_message_texts_config=json.dumps(["", "", ""]),
            # Algorithm control
            event_detection_enable=True,
            event_algorithm_inhibit_ref=None,
            event_algorithm_inhibit=False,
            reliability_evaluation_inhibit=False,
        )

        # Verify all properties are set
        assert point.min_pres_value == 10.0
        assert point.max_pres_value == 100.0
        assert point.high_limit == 85.0
        assert point.low_limit == 15.0
        assert point.resolution == 0.1
        assert point.relinquish_default == 20.0
        assert point.cov_increment == 0.5
        assert point.time_delay == 300
        assert point.time_delay_normal == 600
        assert point.notification_class == 1
        assert point.notify_type == "EVENT"
        assert point.deadband == 0.2
        assert point.event_detection_enable is True
        assert point.event_algorithm_inhibit is False
        assert point.reliability_evaluation_inhibit is False

        # Verify JSON properties can be parsed
        assert json.loads(point.priority_array) == [None] * 16
        assert json.loads(point.limit_enable)["lowLimitEnable"] is True
        assert json.loads(point.event_enable)["toFault"] is True

    def test_model_serialization_with_optional_properties(self):
        """Test: Model dict serialization includes optional properties."""
        point = ControllerPointsModel(
            controller_ip_address="192.168.1.100",
            bacnet_object_type="analogValue",
            point_id=1,
            iot_device_point_id="test-point-id",
            controller_id="test-controller",
            controller_device_id="test-device",
            high_limit=85.0,
            priority_array=json.dumps([None, None, 25.0]),
            event_detection_enable=True,
        )

        data = point.model_dump()

        # Verify optional properties are in serialized data
        assert "high_limit" in data
        assert "priority_array" in data
        assert "event_detection_enable" in data
        assert data["high_limit"] == 85.0
        assert data["event_detection_enable"] is True

        # Verify None properties are also included
        assert "low_limit" in data
        assert data["low_limit"] is None

    def test_model_backward_compatibility(self):
        """Test: Model maintains backward compatibility with existing health properties."""
        point = ControllerPointsModel(
            controller_ip_address="192.168.1.100",
            bacnet_object_type="analogValue",
            point_id=1,
            iot_device_point_id="test-point-id",
            controller_id="test-controller",
            controller_device_id="test-device",
            # Existing health properties
            status_flags="fault;overridden",
            event_state="normal",
            out_of_service=False,
            reliability="noFaultDetected",
            # New optional properties
            high_limit=85.0,
            low_limit=15.0,
        )

        # Verify existing properties still work
        assert point.status_flags == "fault;overridden"
        assert point.event_state == "normal"
        assert point.out_of_service is False
        assert point.reliability == "noFaultDetected"

        # Verify new properties work alongside existing ones
        assert point.high_limit == 85.0
        assert point.low_limit == 15.0

    def test_model_with_invalid_json_properties(self):
        """Test: Model handles invalid JSON in string properties gracefully."""
        # This tests that invalid JSON in string fields doesn't break model creation
        # The validation would happen during serialization/deserialization
        point = ControllerPointsModel(
            controller_ip_address="192.168.1.100",
            bacnet_object_type="analogValue",
            point_id=1,
            iot_device_point_id="test-point-id",
            controller_id="test-controller",
            controller_device_id="test-device",
            priority_array="invalid json string",
            limit_enable="not json either",
        )

        # Model creation should succeed
        assert point.priority_array == "invalid json string"
        assert point.limit_enable == "not json either"

        # JSON parsing would fail during MQTT serialization, which is tested separately
