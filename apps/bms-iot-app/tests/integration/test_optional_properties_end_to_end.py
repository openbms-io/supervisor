"""
Integration Test for BACnet Optional Properties End-to-End Flow.

This test suite validates the complete Phase 3 implementation from BACnet
property reading through SQLite storage to MQTT publishing.
"""

import json
from unittest.mock import Mock
from src.models.controller_points import ControllerPointsModel
from src.network.mqtt_command_dispatcher import _serialize_point
from src.utils.bacnet_health_processor import BACnetHealthProcessor


class TestOptionalPropertiesEndToEnd:
    """Test complete optional properties data flow."""

    def test_bacnet_health_processor_to_controller_points_model(self):
        """Test: BACnet processor output fits ControllerPointsModel."""
        # Mock raw BACnet properties (what we'd get from BAC0)
        raw_properties = {
            # Basic properties
            "presentValue": 22.5,
            "units": "degreesCelsius",
            # Health properties
            "statusFlags": [0, 1, 0, 1],
            "eventState": "normal",
            "outOfService": False,
            "reliability": "noFaultDetected",
            # Optional properties
            "minPresValue": 10.0,
            "maxPresValue": 100.0,
            "highLimit": 85.0,
            "lowLimit": 15.0,
            "resolution": 0.1,
            "priorityArray": Mock(__class__=Mock(__name__="PriorityArray")),
            "relinquishDefault": 20.0,
            "covIncrement": 0.5,
            "timeDelay": 300,
            "limitEnable": Mock(__class__=Mock(__name__="LimitEnable")),
            "eventEnable": Mock(__class__=Mock(__name__="EventTransitionBits")),
            "eventDetectionEnable": True,
        }

        # Mock priority array access with self parameter
        def mock_priority_getitem(self, index):
            if index == 7:
                return 25.0
            elif index == 15:
                return 18.5
            return None

        raw_properties["priorityArray"].__getitem__ = mock_priority_getitem

        # Mock limit enable
        raw_properties["limitEnable"].value = [1, 1]

        # Mock event enable
        raw_properties["eventEnable"].value = [1, 1, 0]

        # Process health properties
        health_data = BACnetHealthProcessor.process_all_health_properties(
            raw_properties
        )

        # Process optional properties
        optional_data = BACnetHealthProcessor.process_all_optional_properties(
            raw_properties
        )

        # Merge data (as done in monitor.py)
        combined_data = {**health_data, **optional_data}

        # Create ControllerPointsModel with processed data
        point = ControllerPointsModel(
            controller_ip_address="192.168.1.100",
            bacnet_object_type="analogValue",
            point_id=1,
            iot_device_point_id="test-point-id",
            controller_id="test-controller",
            controller_device_id="test-device",
            present_value=str(raw_properties["presentValue"]),
            units=raw_properties["units"],
            **combined_data,
        )

        # Verify health properties are correctly processed
        assert point.status_flags == "fault;out-of-service"
        assert point.event_state == "normal"
        assert point.out_of_service is False
        assert point.reliability == "noFaultDetected"

        # Verify optional properties are correctly processed
        assert point.min_pres_value == 10.0
        assert point.max_pres_value == 100.0
        assert point.high_limit == 85.0
        assert point.low_limit == 15.0
        assert point.resolution == 0.1
        assert point.relinquish_default == 20.0
        assert point.cov_increment == 0.5
        assert point.time_delay == 300
        assert point.event_detection_enable is True

        # Verify JSON properties
        assert point.priority_array is not None
        priority_parsed = json.loads(point.priority_array)
        assert priority_parsed[7] == 25.0
        assert priority_parsed[15] == 18.5

        assert point.limit_enable is not None
        limit_parsed = json.loads(point.limit_enable)
        assert limit_parsed["lowLimitEnable"] is True
        assert limit_parsed["highLimitEnable"] is True

        assert point.event_enable is not None
        event_parsed = json.loads(point.event_enable)
        assert event_parsed["toFault"] is True
        assert event_parsed["toNormal"] is True
        assert event_parsed["toOffnormal"] is False

    def test_controller_points_model_to_mqtt_serialization(self):
        """Test: ControllerPointsModel to MQTT payload serialization."""
        # Create a point with optional properties (as stored in SQLite)
        point = ControllerPointsModel(
            controller_ip_address="192.168.1.100",
            bacnet_object_type="analogValue",
            point_id=1,
            iot_device_point_id="test-point-id",
            controller_id="test-controller",
            controller_device_id="test-device",
            present_value="22.5",
            units="degreesCelsius",
            # Health properties
            status_flags="fault;overridden",
            event_state="normal",
            out_of_service=False,
            reliability="noFaultDetected",
            # Optional properties (stored as JSON strings in SQLite)
            high_limit=85.0,
            low_limit=15.0,
            priority_array=json.dumps(
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
            ),
            limit_enable=json.dumps({"lowLimitEnable": True, "highLimitEnable": True}),
            event_enable=json.dumps(
                {"toFault": True, "toNormal": True, "toOffnormal": False}
            ),
            event_detection_enable=True,
        )

        # Serialize for MQTT
        mqtt_payload = _serialize_point(point)

        # Verify basic properties
        assert mqtt_payload["present_value"] == "22.5"
        assert mqtt_payload["units"] == "degreesCelsius"

        # Verify health properties are properly formatted
        assert mqtt_payload["status_flags"] == ["fault", "overridden"]
        assert mqtt_payload["event_state"] == "normal"
        assert mqtt_payload["out_of_service"] is False
        assert mqtt_payload["reliability"] == "noFaultDetected"

        # Verify optional scalar properties
        assert mqtt_payload["high_limit"] == 85.0
        assert mqtt_payload["low_limit"] == 15.0
        assert mqtt_payload["event_detection_enable"] is True

        # Verify JSON properties are parsed to structured data for MQTT
        assert isinstance(mqtt_payload["priority_array"], list)
        assert len(mqtt_payload["priority_array"]) == 16
        assert mqtt_payload["priority_array"][2] == 25.0
        assert mqtt_payload["priority_array"][8] == 50.0
        assert mqtt_payload["priority_array"][15] == 20.0

        assert isinstance(mqtt_payload["limit_enable"], dict)
        assert mqtt_payload["limit_enable"]["lowLimitEnable"] is True
        assert mqtt_payload["limit_enable"]["highLimitEnable"] is True

        assert isinstance(mqtt_payload["event_enable"], dict)
        assert mqtt_payload["event_enable"]["toFault"] is True
        assert mqtt_payload["event_enable"]["toNormal"] is True
        assert mqtt_payload["event_enable"]["toOffnormal"] is False

        # Verify unix timestamp is included
        assert "created_at_unix_milli_timestamp" in mqtt_payload
        # The computed field might be None without database, so check if present or None
        timestamp_value = mqtt_payload["created_at_unix_milli_timestamp"]
        assert timestamp_value is None or isinstance(timestamp_value, int)

    def test_complete_data_flow_simulation(self):
        """Test: Simulate complete data flow from BACnet reading to MQTT publishing."""

        # Step 1: Simulate BACnet reading (what BAC0 would return)
        raw_bacnet_data = {
            "presentValue": 23.4,
            "units": "degreesCelsius",
            "statusFlags": [0, 0, 1, 0],  # overridden flag set
            "eventState": "normal",
            "outOfService": False,
            "reliability": "noFaultDetected",
            "highLimit": 30.0,
            "lowLimit": 10.0,
            "resolution": 0.1,
            "covIncrement": 0.5,
            "timeDelay": 300,
            "notificationClass": 1,
            "eventDetectionEnable": True,
            "eventAlgorithmInhibit": False,
        }

        # Step 2: Process properties (as done in monitor.py)
        health_data = BACnetHealthProcessor.process_all_health_properties(
            raw_bacnet_data
        )
        optional_data = BACnetHealthProcessor.process_all_optional_properties(
            raw_bacnet_data
        )
        combined_data = {**health_data, **optional_data}

        # Step 3: Store in SQLite (ControllerPointsModel)
        point = ControllerPointsModel(
            controller_ip_address="192.168.1.100",
            bacnet_object_type="analogValue",
            point_id=5,
            iot_device_point_id="floor2-temp-sensor",
            controller_id="hvac-controller-01",
            controller_device_id="bacnet-device-123",
            present_value=str(raw_bacnet_data["presentValue"]),
            units=raw_bacnet_data["units"],
            **combined_data,
        )

        # Step 4: Publish to MQTT (serialization)
        mqtt_payload = _serialize_point(point)

        # Step 5: Verify end-to-end data integrity

        # Original BACnet data should be preserved
        assert float(mqtt_payload["present_value"]) == raw_bacnet_data["presentValue"]
        assert mqtt_payload["units"] == raw_bacnet_data["units"]

        # Health data should be properly formatted
        assert mqtt_payload["status_flags"] == ["overridden"]  # Only the set flag
        assert mqtt_payload["event_state"] == raw_bacnet_data["eventState"]
        assert mqtt_payload["out_of_service"] == raw_bacnet_data["outOfService"]
        assert mqtt_payload["reliability"] == raw_bacnet_data["reliability"]

        # Optional properties should be preserved
        assert mqtt_payload["high_limit"] == raw_bacnet_data["highLimit"]
        assert mqtt_payload["low_limit"] == raw_bacnet_data["lowLimit"]
        assert mqtt_payload["resolution"] == raw_bacnet_data["resolution"]
        assert mqtt_payload["cov_increment"] == raw_bacnet_data["covIncrement"]
        assert mqtt_payload["time_delay"] == raw_bacnet_data["timeDelay"]
        assert (
            mqtt_payload["notification_class"] == raw_bacnet_data["notificationClass"]
        )
        assert (
            mqtt_payload["event_detection_enable"]
            == raw_bacnet_data["eventDetectionEnable"]
        )
        assert (
            mqtt_payload["event_algorithm_inhibit"]
            == raw_bacnet_data["eventAlgorithmInhibit"]
        )

        # Metadata should be preserved
        assert mqtt_payload["point_id"] == 5
        assert mqtt_payload["iot_device_point_id"] == "floor2-temp-sensor"
        assert mqtt_payload["controller_id"] == "hvac-controller-01"
        assert mqtt_payload["controller_device_id"] == "bacnet-device-123"

    def test_backwards_compatibility_with_existing_health_only(self):
        """Test: System still works with devices that only have basic health properties."""

        # Simulate legacy device with only basic health properties
        legacy_bacnet_data = {
            "presentValue": 21.2,
            "units": "degreesCelsius",
            "statusFlags": [0, 0, 0, 0],  # All normal
            "eventState": "normal",
            "outOfService": False,
            "reliability": "noFaultDetected",
            # No optional properties
        }

        # Process as usual
        health_data = BACnetHealthProcessor.process_all_health_properties(
            legacy_bacnet_data
        )
        optional_data = BACnetHealthProcessor.process_all_optional_properties(
            legacy_bacnet_data
        )
        combined_data = {**health_data, **optional_data}

        # Create point (optional properties should be None)
        point = ControllerPointsModel(
            controller_ip_address="192.168.1.200",
            bacnet_object_type="analogInput",
            point_id=10,
            iot_device_point_id="legacy-sensor",
            controller_id="legacy-controller",
            controller_device_id="legacy-device",
            present_value=str(legacy_bacnet_data["presentValue"]),
            units=legacy_bacnet_data["units"],
            **combined_data,
        )

        # Serialize for MQTT
        mqtt_payload = _serialize_point(point)

        # Basic functionality should work perfectly
        assert (
            float(mqtt_payload["present_value"]) == legacy_bacnet_data["presentValue"]
        )
        assert mqtt_payload["units"] == legacy_bacnet_data["units"]
        assert mqtt_payload["status_flags"] is None  # No flags set, so None
        assert mqtt_payload["event_state"] == "normal"
        assert mqtt_payload["out_of_service"] is False
        assert mqtt_payload["reliability"] == "noFaultDetected"

        # Optional properties should be None (not causing errors)
        assert mqtt_payload["high_limit"] is None
        assert mqtt_payload["low_limit"] is None
        assert mqtt_payload["priority_array"] is None
        assert mqtt_payload["event_enable"] is None
        assert mqtt_payload["limit_enable"] is None
        assert mqtt_payload["event_detection_enable"] is None

        # Should still have required metadata
        assert mqtt_payload["point_id"] == 10
        assert mqtt_payload["iot_device_point_id"] == "legacy-sensor"

    def test_complex_properties_round_trip_integrity(self):
        """Test: Complex BACnet properties maintain integrity through full pipeline."""

        # Create complex BACnet properties
        mock_priority_array = Mock(__class__=Mock(__name__="PriorityArray"))

        def priority_getitem(self, index):
            # Realistic priority array with manual override and relinquish default
            if index == 7:
                return 25.5  # Manual override at priority 8
            elif index == 15:
                return 18.0  # Relinquish default at priority 16
            return None

        mock_priority_array.__getitem__ = priority_getitem

        mock_limit_enable = Mock(__class__=Mock(__name__="LimitEnable"))
        mock_limit_enable.value = [1, 0]  # Low limit enabled, high limit disabled

        mock_event_enable = Mock(__class__=Mock(__name__="EventTransitionBits"))
        mock_event_enable.value = [
            1,
            1,
            0,
        ]  # Fault and normal enabled, offnormal disabled

        # Simulate complex BACnet reading
        complex_bacnet_data = {
            "presentValue": 22.75,
            "units": "degreesCelsius",
            "statusFlags": [0, 0, 1, 0],  # Overridden
            "eventState": "normal",
            "outOfService": False,
            "reliability": "noFaultDetected",
            "priorityArray": mock_priority_array,
            "relinquishDefault": 18.0,
            "limitEnable": mock_limit_enable,
            "eventEnable": mock_event_enable,
            "eventTimeStamps": [
                Mock(isoformat=lambda: "2024-01-01T10:30:00Z"),
                None,
                Mock(isoformat=lambda: "2024-01-01T12:15:00Z"),
            ],
            "eventMessageTexts": [
                "Temperature high",
                "Normal operation",
                "Temperature warning",
            ],
        }

        # Process through pipeline
        health_data = BACnetHealthProcessor.process_all_health_properties(
            complex_bacnet_data
        )
        optional_data = BACnetHealthProcessor.process_all_optional_properties(
            complex_bacnet_data
        )
        combined_data = {**health_data, **optional_data}

        # Store and serialize
        point = ControllerPointsModel(
            controller_ip_address="192.168.1.100",
            bacnet_object_type="analogValue",
            point_id=1,
            iot_device_point_id="complex-sensor",
            controller_id="test-controller",
            controller_device_id="test-device",
            present_value=str(complex_bacnet_data["presentValue"]),
            units=complex_bacnet_data["units"],
            **combined_data,
        )

        mqtt_payload = _serialize_point(point)

        # Verify complex properties maintain exact values

        # Priority array should preserve exact values and positions
        priority_result = mqtt_payload["priority_array"]
        assert isinstance(priority_result, list)
        assert len(priority_result) == 16
        assert priority_result[7] == 25.5  # Manual override preserved
        assert priority_result[15] == 18.0  # Relinquish default preserved
        assert priority_result[0] is None  # Null values preserved
        assert priority_result[5] is None  # Null values preserved

        # Limit enable should preserve specific bit settings
        limit_result = mqtt_payload["limit_enable"]
        assert isinstance(limit_result, dict)
        assert limit_result["lowLimitEnable"] is True  # Bit 0 was 1
        assert limit_result["highLimitEnable"] is False  # Bit 1 was 0

        # Event enable should preserve specific bit settings
        event_result = mqtt_payload["event_enable"]
        assert isinstance(event_result, dict)
        assert event_result["toFault"] is True  # Bit 0 was 1
        assert event_result["toNormal"] is True  # Bit 1 was 1
        assert event_result["toOffnormal"] is False  # Bit 2 was 0

        # Timestamps should preserve exact values and nulls
        timestamps_result = mqtt_payload["event_time_stamps"]
        assert isinstance(timestamps_result, list)
        assert len(timestamps_result) == 3
        assert timestamps_result[0] == "2024-01-01T10:30:00Z"
        assert timestamps_result[1] is None
        assert timestamps_result[2] == "2024-01-01T12:15:00Z"

        # Messages should preserve exact strings
        messages_result = mqtt_payload["event_message_texts"]
        assert isinstance(messages_result, list)
        assert len(messages_result) == 3
        assert messages_result[0] == "Temperature high"
        assert messages_result[1] == "Normal operation"
        assert messages_result[2] == "Temperature warning"
