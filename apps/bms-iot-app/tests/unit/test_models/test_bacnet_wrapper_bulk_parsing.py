"""
Test BAC0 bulk read parsing functions using real production data.

Based on actual BAC0 readMultiple response format from production logs.
"""

from unittest.mock import Mock
from bacpypes3.primitivedata import Real, Boolean, Unsigned
from bacpypes3.basetypes import (
    StatusFlags,
    EventState,
    Reliability,
    BinaryPV,
    PropertyIdentifier,
)

from src.models.bacnet_wrapper import BACnetWrapper
from src.actors.messages.message_type import BacnetReaderConfig


class TestBACnetWrapperBulkParsing:
    """Test BAC0 bulk read parsing with real production data formats"""

    def setup_method(self):
        """Setup test wrapper instance"""
        mock_config = Mock(spec=BacnetReaderConfig)
        mock_config.id = "test_reader"
        mock_config.ip_address = "192.168.100.96"
        mock_config.subnet_mask = "255.255.255.0"
        mock_config.bacnet_device_id = 123
        mock_config.port = 47808
        mock_config.bbmd_enabled = False
        mock_config.bbmd_server_ip = None

        self.wrapper = BACnetWrapper(mock_config)

    def create_real_bac0_response(self):
        """Create BAC0 response data exactly as received from production"""
        return {
            "analog-value,10": [
                (
                    PropertyIdentifier("present-value"),
                    (Real(25.0), PropertyIdentifier("present-value")),
                ),
                (
                    PropertyIdentifier("status-flags"),
                    (
                        StatusFlags("in-alarm;fault;overridden;out-of-service"),
                        PropertyIdentifier("status-flags"),
                    ),
                ),
                (
                    PropertyIdentifier("event-state"),
                    (EventState("fault"), PropertyIdentifier("event-state")),
                ),
                (
                    PropertyIdentifier("out-of-service"),
                    (Boolean(1), PropertyIdentifier("out-of-service")),
                ),
                (
                    PropertyIdentifier("reliability"),
                    (
                        Reliability("no-fault-detected"),
                        PropertyIdentifier("reliability"),
                    ),
                ),
            ],
            "analog-value,20": [
                (
                    PropertyIdentifier("present-value"),
                    (Real(23.299999237060547), PropertyIdentifier("present-value")),
                ),
                (
                    PropertyIdentifier("status-flags"),
                    (
                        StatusFlags("fault;out-of-service"),
                        PropertyIdentifier("status-flags"),
                    ),
                ),
                (
                    PropertyIdentifier("event-state"),
                    (
                        EventState("life-safety-alarm"),
                        PropertyIdentifier("event-state"),
                    ),
                ),
                (
                    PropertyIdentifier("out-of-service"),
                    (Boolean(1), PropertyIdentifier("out-of-service")),
                ),
                (
                    PropertyIdentifier("reliability"),
                    (Reliability("over-range"), PropertyIdentifier("reliability")),
                ),
            ],
            "analog-output,30": [
                (
                    PropertyIdentifier("present-value"),
                    (Real(70.0), PropertyIdentifier("present-value")),
                )
            ],
            "analog-output,40": [
                (
                    PropertyIdentifier("present-value"),
                    (Real(45.0), PropertyIdentifier("present-value")),
                )
            ],
            "analog-input,50": [
                (
                    PropertyIdentifier("present-value"),
                    (Real(550.0), PropertyIdentifier("present-value")),
                )
            ],
            "binary-input,60": [
                (
                    PropertyIdentifier("present-value"),
                    (BinaryPV("active"), PropertyIdentifier("present-value")),
                )
            ],
            "binary-output,70": [
                (
                    PropertyIdentifier("present-value"),
                    (BinaryPV("inactive"), PropertyIdentifier("present-value")),
                )
            ],
            "binary-value,80": [
                (
                    PropertyIdentifier("present-value"),
                    (BinaryPV("active"), PropertyIdentifier("present-value")),
                ),
                (
                    PropertyIdentifier("event-state"),
                    (EventState("fault"), PropertyIdentifier("event-state")),
                ),
                (
                    PropertyIdentifier("out-of-service"),
                    (Boolean(1), PropertyIdentifier("out-of-service")),
                ),
                (
                    PropertyIdentifier("reliability"),
                    (
                        Reliability("no-fault-detected"),
                        PropertyIdentifier("reliability"),
                    ),
                ),
            ],
            "multi-state-input,90": [
                (
                    PropertyIdentifier("present-value"),
                    (Unsigned(2), PropertyIdentifier("present-value")),
                )
            ],
            "multi-state-output,100": [
                (
                    PropertyIdentifier("present-value"),
                    (Unsigned(3), PropertyIdentifier("present-value")),
                )
            ],
            "multi-state-value,110": [
                (
                    PropertyIdentifier("present-value"),
                    (Unsigned(1), PropertyIdentifier("present-value")),
                )
            ],
        }

    def create_point_requests(self):
        """Create point requests matching the BAC0 response"""
        return [
            {
                "object_type": "analogValue",
                "object_id": 10,
                "properties": [
                    "presentValue",
                    "statusFlags",
                    "eventState",
                    "outOfService",
                    "reliability",
                ],
            },
            {
                "object_type": "analogValue",
                "object_id": 20,
                "properties": [
                    "presentValue",
                    "statusFlags",
                    "eventState",
                    "outOfService",
                    "reliability",
                ],
            },
            {
                "object_type": "analogOutput",
                "object_id": 30,
                "properties": ["presentValue"],
            },
            {
                "object_type": "analogOutput",
                "object_id": 40,
                "properties": ["presentValue"],
            },
            {
                "object_type": "analogInput",
                "object_id": 50,
                "properties": ["presentValue"],
            },
            {
                "object_type": "binaryInput",
                "object_id": 60,
                "properties": ["presentValue"],
            },
            {
                "object_type": "binaryOutput",
                "object_id": 70,
                "properties": ["presentValue"],
            },
            {
                "object_type": "binaryValue",
                "object_id": 80,
                "properties": [
                    "presentValue",
                    "eventState",
                    "outOfService",
                    "reliability",
                ],
            },
            {
                "object_type": "multiStateInput",
                "object_id": 90,
                "properties": ["presentValue"],
            },
            {
                "object_type": "multiStateOutput",
                "object_id": 100,
                "properties": ["presentValue"],
            },
            {
                "object_type": "multiStateValue",
                "object_id": 110,
                "properties": ["presentValue"],
            },
        ]

    def test_parse_bac0_bulk_result_complete_success(self):
        """Test: Parse complete BAC0 bulk result with all object types"""
        bac0_result = self.create_real_bac0_response()
        point_requests = self.create_point_requests()

        parsed_result = self.wrapper._parse_bac0_bulk_result(
            bac0_result, point_requests
        )

        # Verify all points are parsed
        assert len(parsed_result) == 11

        # Verify specific points have correct data
        analog_value_10 = parsed_result["analogValue:10"]
        assert analog_value_10["presentValue"] == 25.0
        assert analog_value_10["statusFlags"] == StatusFlags(
            "in-alarm;fault;overridden;out-of-service"
        )
        assert analog_value_10["eventState"] == "fault"
        assert analog_value_10["outOfService"] is True
        assert analog_value_10["reliability"] == "no-fault-detected"

        # Verify present-value-only points
        analog_output_30 = parsed_result["analogOutput:30"]
        assert analog_output_30["presentValue"] == 70.0
        assert len(analog_output_30) == 1  # Only presentValue

        # Verify binary values
        binary_input_60 = parsed_result["binaryInput:60"]
        assert binary_input_60["presentValue"] == BinaryPV("active")

        # Verify multi-state values
        multi_state_input_90 = parsed_result["multiStateInput:90"]
        assert multi_state_input_90["presentValue"] == 2

    def test_convert_bac0_properties_analog_value_full(self):
        """Test: Convert analog value with all health properties"""
        raw_properties = [
            (
                PropertyIdentifier("present-value"),
                (Real(25.0), PropertyIdentifier("present-value")),
            ),
            (
                PropertyIdentifier("status-flags"),
                (
                    StatusFlags("in-alarm;fault;overridden;out-of-service"),
                    PropertyIdentifier("status-flags"),
                ),
            ),
            (
                PropertyIdentifier("event-state"),
                (EventState("fault"), PropertyIdentifier("event-state")),
            ),
            (
                PropertyIdentifier("out-of-service"),
                (Boolean(1), PropertyIdentifier("out-of-service")),
            ),
            (
                PropertyIdentifier("reliability"),
                (Reliability("no-fault-detected"), PropertyIdentifier("reliability")),
            ),
        ]

        result = self.wrapper._convert_bac0_properties(raw_properties)

        assert result["presentValue"] == 25.0
        assert result["statusFlags"] == StatusFlags(
            "in-alarm;fault;overridden;out-of-service"
        )
        assert result["eventState"] == "fault"
        assert result["outOfService"] is True  # Boolean(1) -> True
        assert result["reliability"] == "no-fault-detected"
        assert len(result) == 5

    def test_convert_bac0_properties_present_value_only(self):
        """Test: Convert property with only present value"""
        raw_properties = [
            (
                PropertyIdentifier("present-value"),
                (Real(70.0), PropertyIdentifier("present-value")),
            )
        ]

        result = self.wrapper._convert_bac0_properties(raw_properties)

        assert result["presentValue"] == 70.0
        assert len(result) == 1

    def test_convert_bac0_properties_binary_values(self):
        """Test: Convert binary property values"""
        raw_properties = [
            (
                PropertyIdentifier("present-value"),
                (BinaryPV("active"), PropertyIdentifier("present-value")),
            )
        ]

        result = self.wrapper._convert_bac0_properties(raw_properties)

        assert result["presentValue"] == BinaryPV("active")

    def test_convert_bac0_properties_multi_state_values(self):
        """Test: Convert multi-state property values"""
        raw_properties = [
            (
                PropertyIdentifier("present-value"),
                (Unsigned(2), PropertyIdentifier("present-value")),
            )
        ]

        result = self.wrapper._convert_bac0_properties(raw_properties)

        assert result["presentValue"] == 2

    def test_parse_bac0_bulk_result_missing_point(self):
        """Test: Handle missing point in BAC0 result"""
        bac0_result = {
            "analog-value,10": [
                (
                    PropertyIdentifier("present-value"),
                    (Real(25.0), PropertyIdentifier("present-value")),
                )
            ]
            # Missing analog-value,20
        }

        point_requests = [
            {
                "object_type": "analogValue",
                "object_id": 10,
                "properties": ["presentValue"],
            },
            {
                "object_type": "analogValue",
                "object_id": 20,
                "properties": ["presentValue"],
            },
        ]

        parsed_result = self.wrapper._parse_bac0_bulk_result(
            bac0_result, point_requests
        )

        # Point 10 should have data
        assert parsed_result["analogValue:10"]["presentValue"] == 25.0

        # Point 20 should be empty dict
        assert parsed_result["analogValue:20"] == {}

    def test_parse_bac0_bulk_result_unknown_object_type(self):
        """Test: Handle unknown object type in BAC0 result"""
        bac0_result = {
            "unknown-object-type,99": [
                (
                    PropertyIdentifier("present-value"),
                    (Real(99.0), PropertyIdentifier("present-value")),
                )
            ]
        }

        point_requests = [
            {
                "object_type": "analogValue",
                "object_id": 10,
                "properties": ["presentValue"],
            }
        ]

        parsed_result = self.wrapper._parse_bac0_bulk_result(
            bac0_result, point_requests
        )

        # Should handle unknown object type gracefully
        assert parsed_result["analogValue:10"] == {}

    def test_parse_bac0_bulk_result_malformed_key(self):
        """Test: Handle malformed BAC0 key format"""
        bac0_result = {
            "analog-value-no-comma": [
                (
                    PropertyIdentifier("present-value"),
                    (Real(25.0), PropertyIdentifier("present-value")),
                )
            ],
            "analog-value,10": [
                (
                    PropertyIdentifier("present-value"),
                    (Real(30.0), PropertyIdentifier("present-value")),
                )
            ],
        }

        point_requests = [
            {
                "object_type": "analogValue",
                "object_id": 10,
                "properties": ["presentValue"],
            }
        ]

        parsed_result = self.wrapper._parse_bac0_bulk_result(
            bac0_result, point_requests
        )

        # Should parse valid key and ignore malformed one
        assert parsed_result["analogValue:10"]["presentValue"] == 30.0

    def test_convert_bac0_properties_malformed_property(self):
        """Test: Handle malformed property tuple"""
        raw_properties = [
            (
                PropertyIdentifier("present-value"),
                (Real(25.0), PropertyIdentifier("present-value")),
            ),
            (PropertyIdentifier("present-value"),),  # Missing value tuple - malformed
            # Note: Can't easily create invalid PropertyIdentifier due to strict validation
        ]

        result = self.wrapper._convert_bac0_properties(raw_properties)

        # Should parse valid property and handle malformed ones gracefully
        assert result["presentValue"] == 25.0
        assert len(result) >= 1  # Should have at least the valid property

    def test_convert_bac0_properties_empty_input(self):
        """Test: Handle empty property list"""
        raw_properties = []

        result = self.wrapper._convert_bac0_properties(raw_properties)

        assert result == {}

    def test_object_type_mapping_completeness(self):
        """Test: Verify all object types from POINT_TYPES are handled"""
        from src.models.bacnet_types import POINT_TYPES

        # Test that all POINT_TYPES are mapped correctly
        bac0_result = {}
        point_requests = []

        for bacpypes_key, enum_value in POINT_TYPES.items():
            # Create test data for each object type
            test_id = 100
            bac0_key = f"{bacpypes_key},{test_id}"
            bac0_result[bac0_key] = [
                (
                    PropertyIdentifier("present-value"),
                    (Real(99.0), PropertyIdentifier("present-value")),
                )
            ]

            point_requests.append(
                {
                    "object_type": enum_value.value,
                    "object_id": test_id,
                    "properties": ["presentValue"],
                }
            )

        parsed_result = self.wrapper._parse_bac0_bulk_result(
            bac0_result, point_requests
        )

        # Verify all object types are parsed successfully
        assert len(parsed_result) == len(POINT_TYPES)
        for _, enum_value in POINT_TYPES.items():
            key = f"{enum_value.value}:100"
            assert key in parsed_result
            assert parsed_result[key]["presentValue"] == 99.0

    def test_convert_bacnet_health_value_integration(self):
        """Test: Verify integration with existing convert_bacnet_health_value function"""
        # Test that health value conversion is applied correctly
        raw_properties = [
            (
                PropertyIdentifier("present-value"),
                (Real(25.0), PropertyIdentifier("present-value")),
            ),
            (
                PropertyIdentifier("out-of-service"),
                (Boolean(1), PropertyIdentifier("out-of-service")),
            ),
            (
                PropertyIdentifier("event-state"),
                (EventState("fault"), PropertyIdentifier("event-state")),
            ),
        ]

        result = self.wrapper._convert_bac0_properties(raw_properties)

        # Verify that convert_bacnet_health_value is applied
        assert result["presentValue"] == 25.0  # No conversion for presentValue
        assert result["outOfService"] is True  # Boolean conversion
        assert result["eventState"] == "fault"  # String conversion

    def test_parse_with_different_property_combinations(self):
        """Test: Parse points with different property combinations"""
        bac0_result = {
            "analog-value,10": [  # Full health properties
                (
                    PropertyIdentifier("present-value"),
                    (Real(25.0), PropertyIdentifier("present-value")),
                ),
                (
                    PropertyIdentifier("status-flags"),
                    (StatusFlags("in-alarm;fault"), PropertyIdentifier("status-flags")),
                ),
                (
                    PropertyIdentifier("reliability"),
                    (
                        Reliability("no-fault-detected"),
                        PropertyIdentifier("reliability"),
                    ),
                ),
            ],
            "analog-output,20": [  # Only presentValue
                (
                    PropertyIdentifier("present-value"),
                    (Real(50.0), PropertyIdentifier("present-value")),
                )
            ],
            "binary-value,30": [  # Partial health properties
                (
                    PropertyIdentifier("present-value"),
                    (BinaryPV("active"), PropertyIdentifier("present-value")),
                ),
                (
                    PropertyIdentifier("out-of-service"),
                    (Boolean(0), PropertyIdentifier("out-of-service")),
                ),
            ],
        }

        point_requests = [
            {
                "object_type": "analogValue",
                "object_id": 10,
                "properties": ["presentValue", "statusFlags", "reliability"],
            },
            {
                "object_type": "analogOutput",
                "object_id": 20,
                "properties": ["presentValue"],
            },
            {
                "object_type": "binaryValue",
                "object_id": 30,
                "properties": ["presentValue", "outOfService"],
            },
        ]

        parsed_result = self.wrapper._parse_bac0_bulk_result(
            bac0_result, point_requests
        )

        # Verify different property combinations
        av10 = parsed_result["analogValue:10"]
        assert av10["presentValue"] == 25.0
        assert av10["statusFlags"] == StatusFlags("in-alarm;fault")
        assert av10["reliability"] == "no-fault-detected"
        assert len(av10) == 3

        ao20 = parsed_result["analogOutput:20"]
        assert ao20["presentValue"] == 50.0
        assert len(ao20) == 1

        bv30 = parsed_result["binaryValue:30"]
        assert bv30["presentValue"] == BinaryPV("active")
        assert bv30["outOfService"] is False
        assert len(bv30) == 2

    def test_performance_with_large_dataset(self):
        """Test: Performance with large number of points"""
        # Create 100 points of mixed types
        bac0_result = {}
        point_requests = []

        for i in range(100):
            point_id = i + 1
            if i % 3 == 0:
                obj_type = "analog-value"
                our_type = "analogValue"
            elif i % 3 == 1:
                obj_type = "binary-input"
                our_type = "binaryInput"
            else:
                obj_type = "multi-state-output"
                our_type = "multiStateOutput"

            bac0_key = f"{obj_type},{point_id}"
            bac0_result[bac0_key] = [
                (
                    PropertyIdentifier("present-value"),
                    (Real(float(point_id)), PropertyIdentifier("present-value")),
                )
            ]

            point_requests.append(
                {
                    "object_type": our_type,
                    "object_id": point_id,
                    "properties": ["presentValue"],
                }
            )

        # Test parsing performance
        import time

        start_time = time.time()
        parsed_result = self.wrapper._parse_bac0_bulk_result(
            bac0_result, point_requests
        )
        end_time = time.time()

        # Verify correctness
        assert len(parsed_result) == 100
        assert parsed_result["analogValue:1"]["presentValue"] == 1.0
        assert parsed_result["multiStateOutput:99"]["presentValue"] == 99.0

        # Performance should be reasonable (less than 500ms for 100 points)
        assert (end_time - start_time) < 0.5
