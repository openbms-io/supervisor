"""
Test BACnet Monitor Optional Properties Integration.

This test suite validates the Phase 3 enhancements to monitor.py that added
support for reading and processing all 24 optional BACnet properties.
"""

from unittest.mock import patch
from src.controllers.monitoring.monitor import BACnetMonitor


class TestBACnetMonitorOptionalProperties:
    """Test BACnet monitor with optional property support."""

    def test_get_available_device_properties_basic_configuration(self):
        """Test: Available properties detection with basic configuration."""
        monitor = BACnetMonitor()

        # Mock object properties with basic health properties only
        object_properties = {
            "presentValue": 22.5,
            "statusFlags": [0, 1, 0, 1],
            "eventState": "normal",
            "reliability": "noFaultDetected",
        }

        available = monitor.get_available_device_properties(object_properties)

        # Should include presentValue (always) + available health properties
        assert "presentValue" in available
        assert "statusFlags" in available
        assert "eventState" in available
        assert "reliability" in available

        # Should not include properties that aren't in configuration
        assert "highLimit" not in available
        assert "priorityArray" not in available

    def test_get_available_device_properties_with_optional_properties(self):
        """Test: Available properties detection with optional BACnet properties."""
        monitor = BACnetMonitor()

        # Mock object properties with optional properties
        object_properties = {
            "presentValue": 22.5,
            "statusFlags": [0, 1, 0, 1],
            "eventState": "normal",
            "reliability": "noFaultDetected",
            "highLimit": 30.0,
            "lowLimit": 10.0,
            "priorityArray": [None] * 16,
            "eventEnable": [1, 1, 0],
            "limitEnable": [1, 1],
            "covIncrement": 0.5,
            "timeDelay": 300,
            "notificationClass": 1,
            "eventDetectionEnable": True,
        }

        available = monitor.get_available_device_properties(object_properties)

        # Should include basic properties
        assert "presentValue" in available
        assert "statusFlags" in available
        assert "eventState" in available
        assert "reliability" in available

        # Should include available optional properties
        assert "highLimit" in available
        assert "lowLimit" in available
        assert "priorityArray" in available
        assert "eventEnable" in available
        assert "limitEnable" in available
        assert "covIncrement" in available
        assert "timeDelay" in available
        assert "notificationClass" in available
        assert "eventDetectionEnable" in available

    def test_get_available_device_properties_with_null_values(self):
        """Test: Properties with null values are excluded."""
        monitor = BACnetMonitor()

        # Mock object properties with some null values
        object_properties = {
            "presentValue": 22.5,
            "statusFlags": None,  # Null value - should be excluded
            "eventState": "normal",
            "highLimit": None,  # Null value - should be excluded
            "lowLimit": 10.0,  # Valid value - should be included
            "priorityArray": [None] * 16,  # Valid array - should be included
        }

        available = monitor.get_available_device_properties(object_properties)

        # Should include non-null properties
        assert "presentValue" in available
        assert "eventState" in available
        assert "lowLimit" in available
        assert "priorityArray" in available

        # Should exclude null properties
        assert "statusFlags" not in available
        assert "highLimit" not in available

    def test_get_available_device_properties_empty_configuration(self):
        """Test: Empty or None configuration returns minimal set."""
        monitor = BACnetMonitor()

        # Test with None configuration
        available_none = monitor.get_available_device_properties(None)
        assert available_none == ["presentValue"]

        # Test with empty configuration
        available_empty = monitor.get_available_device_properties({})
        assert available_empty == ["presentValue"]

    def test_get_available_device_properties_all_optional_properties(self):
        """Test: All 24 optional properties are detected when present."""
        monitor = BACnetMonitor()

        # Mock object properties with all optional properties
        object_properties = {
            # Basic required
            "presentValue": 22.5,
            # Existing health properties
            "statusFlags": [0, 1, 0, 1],
            "eventState": "normal",
            "outOfService": False,
            "reliability": "noFaultDetected",
            # All 23 optional properties
            "minPresValue": 10.0,
            "maxPresValue": 100.0,
            "highLimit": 85.0,
            "lowLimit": 15.0,
            "resolution": 0.1,
            "priorityArray": [None] * 16,
            "relinquishDefault": 20.0,
            "covIncrement": 0.5,
            "timeDelay": 300,
            "timeDelayNormal": 600,
            "notificationClass": 1,
            "notifyType": "EVENT",
            "deadband": 0.2,
            "limitEnable": [1, 1],
            "eventEnable": [1, 1, 1],
            "ackedTransitions": [0, 1, 0],
            "eventTimeStamps": [None, None, None],
            "eventMessageTexts": ["", "", ""],
            "eventMessageTextsConfig": ["", "", ""],
            "eventDetectionEnable": True,
            "eventAlgorithmInhibitRef": None,
            "eventAlgorithmInhibit": False,
            "reliabilityEvaluationInhibit": False,
        }

        available = monitor.get_available_device_properties(object_properties)

        # Should include presentValue + all configured properties
        expected_properties = [
            "presentValue",
            # Health properties
            "statusFlags",
            "eventState",
            "outOfService",
            "reliability",
            # Optional properties
            "minPresValue",
            "maxPresValue",
            "highLimit",
            "lowLimit",
            "resolution",
            "priorityArray",
            "relinquishDefault",
            "covIncrement",
            "timeDelay",
            "timeDelayNormal",
            "notificationClass",
            "notifyType",
            "deadband",
            "limitEnable",
            "eventEnable",
            "ackedTransitions",
            "eventTimeStamps",
            "eventMessageTexts",
            "eventMessageTextsConfig",
            "eventDetectionEnable",
            "eventAlgorithmInhibit",
            "reliabilityEvaluationInhibit",
        ]

        for prop in expected_properties:
            assert prop in available, f"Property {prop} should be available"

        # Should not include eventAlgorithmInhibitRef (it's None in config)
        assert "eventAlgorithmInhibitRef" not in available

    def test_get_available_device_properties_analog_value_subset(self):
        """Test: AnalogValue object with typical property subset."""
        monitor = BACnetMonitor()

        # Mock AnalogValue properties (common subset)
        object_properties = {
            "presentValue": 22.5,
            "statusFlags": [0, 0, 0, 0],
            "eventState": "normal",
            "reliability": "noFaultDetected",
            "outOfService": False,
            "highLimit": 30.0,
            "lowLimit": 10.0,
            "priorityArray": [None] * 16,
            "relinquishDefault": 20.0,
            "covIncrement": 0.5,
            "limitEnable": [1, 1],
            "eventEnable": [1, 1, 0],
        }

        available = monitor.get_available_device_properties(object_properties)

        # Should include all present properties
        expected = [
            "presentValue",
            "statusFlags",
            "eventState",
            "reliability",
            "outOfService",
            "highLimit",
            "lowLimit",
            "priorityArray",
            "relinquishDefault",
            "covIncrement",
            "limitEnable",
            "eventEnable",
        ]

        for prop in expected:
            assert prop in available

        # Should not include properties not in configuration
        assert "timeDelay" not in available
        assert "notificationClass" not in available

    def test_get_available_device_properties_analog_input_subset(self):
        """Test: AnalogInput object without control properties."""
        monitor = BACnetMonitor()

        # Mock AnalogInput properties (no control properties)
        object_properties = {
            "presentValue": 550.0,
            "statusFlags": [0, 0, 0, 0],
            "eventState": "normal",
            "reliability": "noFaultDetected",
            "outOfService": False,
            "highLimit": 1000.0,
            "lowLimit": 400.0,
            "resolution": 1.0,
            "covIncrement": 10.0,
            "eventEnable": [1, 1, 0],
            "limitEnable": [1, 1],
            # Note: No priorityArray or relinquishDefault (input object)
        }

        available = monitor.get_available_device_properties(object_properties)

        # Should include present properties
        expected = [
            "presentValue",
            "statusFlags",
            "eventState",
            "reliability",
            "outOfService",
            "highLimit",
            "lowLimit",
            "resolution",
            "covIncrement",
            "eventEnable",
            "limitEnable",
        ]

        for prop in expected:
            assert prop in available

        # Should not include control properties not present
        assert "priorityArray" not in available
        assert "relinquishDefault" not in available

    def test_get_available_device_properties_binary_value_subset(self):
        """Test: BinaryValue object with binary-specific properties."""
        monitor = BACnetMonitor()

        # Mock BinaryValue properties
        object_properties = {
            "presentValue": 1,
            "statusFlags": [0, 0, 0, 0],
            "eventState": "normal",
            "reliability": "noFaultDetected",
            "outOfService": False,
            "priorityArray": [None] * 16,
            "relinquishDefault": 0,
            "eventEnable": [1, 1, 0],
            # Note: No min/max/high/low limits (binary object)
        }

        available = monitor.get_available_device_properties(object_properties)

        # Should include binary-appropriate properties
        expected = [
            "presentValue",
            "statusFlags",
            "eventState",
            "reliability",
            "outOfService",
            "priorityArray",
            "relinquishDefault",
            "eventEnable",
        ]

        for prop in expected:
            assert prop in available

        # Should not include analog-specific properties
        assert "highLimit" not in available
        assert "lowLimit" not in available
        assert "resolution" not in available

    @patch("src.utils.logger.logger.debug")
    def test_get_available_device_properties_logging(self, mock_debug):
        """Test: Proper logging of property detection logic."""
        monitor = BACnetMonitor()

        object_properties = {
            "presentValue": 22.5,
            "statusFlags": None,  # This should trigger debug log
            "eventState": "normal",
            "nonExistentProperty": "value",  # This won't be checked
        }

        monitor.get_available_device_properties(object_properties)

        # Should log debug messages for null properties
        mock_debug.assert_called()

        # Check that specific debug messages were logged
        debug_calls = [call[0][0] for call in mock_debug.call_args_list]
        null_log_found = any("null in configuration" in msg for msg in debug_calls)
        assert null_log_found

    def test_get_available_device_properties_preserves_original_health_behavior(self):
        """Test: Backward compatibility - original health properties still work."""
        monitor = BACnetMonitor()

        # Test original configuration format (just basic health properties)
        original_config = {
            "presentValue": 22.5,
            "statusFlags": [0, 1, 0, 0],
            "eventState": "fault",
            "outOfService": True,
            "reliability": "overRange",
        }

        available = monitor.get_available_device_properties(original_config)

        # Should work exactly as before - all original properties included
        assert "presentValue" in available
        assert "statusFlags" in available
        assert "eventState" in available
        assert "outOfService" in available
        assert "reliability" in available

        # Should be exactly 5 properties (no extras)
        assert len(available) == 5
