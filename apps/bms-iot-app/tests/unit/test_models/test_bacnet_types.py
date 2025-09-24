"""
Test BACnet types and enums.

User Story: As a developer, I want BACnet data models to validate correctly
"""

from src.models.bacnet_types import (
    BacnetObjectTypeEnum,
    POINT_TYPES,
    get_point_types,
    convert_point_type_to_bacnet_object_type,
)


class TestBacnetObjectTypeEnum:
    """Test BACnet object type enumeration"""

    def test_bacnet_point_data_structure_creation(self):
        """Test: BACnet point data structure creation and validation"""
        # Test enum values exist and are correct
        assert BacnetObjectTypeEnum.ANALOG_INPUT == "analogInput"
        assert BacnetObjectTypeEnum.ANALOG_OUTPUT == "analogOutput"
        assert BacnetObjectTypeEnum.ANALOG_VALUE == "analogValue"
        assert BacnetObjectTypeEnum.BINARY_INPUT == "binaryInput"
        assert BacnetObjectTypeEnum.BINARY_OUTPUT == "binaryOutput"
        assert BacnetObjectTypeEnum.BINARY_VALUE == "binaryValue"
        assert BacnetObjectTypeEnum.MULTI_STATE_INPUT == "multiStateInput"
        assert BacnetObjectTypeEnum.MULTI_STATE_OUTPUT == "multiStateOutput"
        assert BacnetObjectTypeEnum.MULTI_STATE_VALUE == "multiStateValue"

    def test_enum_is_string_enum(self):
        """Test: BACnet device model field validation"""
        # Verify that enum values are strings
        assert isinstance(BacnetObjectTypeEnum.ANALOG_INPUT.value, str)
        assert BacnetObjectTypeEnum.ANALOG_INPUT.value == "analogInput"

    def test_enum_member_count(self):
        """Test: All expected enum members are present"""
        enum_members = list(BacnetObjectTypeEnum)
        assert len(enum_members) == 9


class TestPointTypes:
    """Test POINT_TYPES dictionary"""

    def test_point_types_mapping(self):
        """Test: Point types dictionary has correct mappings"""
        assert POINT_TYPES["analog-input"] == BacnetObjectTypeEnum.ANALOG_INPUT
        assert POINT_TYPES["analog-output"] == BacnetObjectTypeEnum.ANALOG_OUTPUT
        assert POINT_TYPES["analog-value"] == BacnetObjectTypeEnum.ANALOG_VALUE
        assert POINT_TYPES["binary-input"] == BacnetObjectTypeEnum.BINARY_INPUT
        assert POINT_TYPES["binary-output"] == BacnetObjectTypeEnum.BINARY_OUTPUT
        assert POINT_TYPES["binary-value"] == BacnetObjectTypeEnum.BINARY_VALUE
        assert (
            POINT_TYPES["multi-state-input"] == BacnetObjectTypeEnum.MULTI_STATE_INPUT
        )
        assert (
            POINT_TYPES["multi-state-output"] == BacnetObjectTypeEnum.MULTI_STATE_OUTPUT
        )
        assert (
            POINT_TYPES["multi-state-value"] == BacnetObjectTypeEnum.MULTI_STATE_VALUE
        )

    def test_point_types_completeness(self):
        """Test: All enum values have corresponding point type mappings"""
        assert len(POINT_TYPES) == 9

        # Verify all values in POINT_TYPES are valid enum members
        for point_type, enum_value in POINT_TYPES.items():
            assert enum_value in BacnetObjectTypeEnum


class TestGetPointTypes:
    """Test get_point_types function"""

    def test_returns_all_point_type_keys(self):
        """Test: Function returns all point type keys"""
        point_types = get_point_types()

        assert isinstance(point_types, list)
        assert len(point_types) == 9
        assert "analog-input" in point_types
        assert "analog-output" in point_types
        assert "analog-value" in point_types
        assert "binary-input" in point_types
        assert "binary-output" in point_types
        assert "binary-value" in point_types
        assert "multi-state-input" in point_types
        assert "multi-state-output" in point_types
        assert "multi-state-value" in point_types

    def test_returns_list_not_dict_keys(self):
        """Test: Function returns a proper list, not dict_keys object"""
        point_types = get_point_types()
        assert isinstance(point_types, list)


class TestConvertPointTypeToBacnetObjectType:
    """Test convert_point_type_to_bacnet_object_type function"""

    def test_valid_conversions(self):
        """Test: Data type conversions work correctly"""
        assert (
            convert_point_type_to_bacnet_object_type("analog-input")
            == BacnetObjectTypeEnum.ANALOG_INPUT
        )
        assert (
            convert_point_type_to_bacnet_object_type("analog-output")
            == BacnetObjectTypeEnum.ANALOG_OUTPUT
        )
        assert (
            convert_point_type_to_bacnet_object_type("analog-value")
            == BacnetObjectTypeEnum.ANALOG_VALUE
        )
        assert (
            convert_point_type_to_bacnet_object_type("binary-input")
            == BacnetObjectTypeEnum.BINARY_INPUT
        )
        assert (
            convert_point_type_to_bacnet_object_type("binary-output")
            == BacnetObjectTypeEnum.BINARY_OUTPUT
        )
        assert (
            convert_point_type_to_bacnet_object_type("binary-value")
            == BacnetObjectTypeEnum.BINARY_VALUE
        )
        assert (
            convert_point_type_to_bacnet_object_type("multi-state-input")
            == BacnetObjectTypeEnum.MULTI_STATE_INPUT
        )
        assert (
            convert_point_type_to_bacnet_object_type("multi-state-output")
            == BacnetObjectTypeEnum.MULTI_STATE_OUTPUT
        )
        assert (
            convert_point_type_to_bacnet_object_type("multi-state-value")
            == BacnetObjectTypeEnum.MULTI_STATE_VALUE
        )

    def test_invalid_point_type_returns_none(self):
        """Test: Invalid point type returns None"""
        assert convert_point_type_to_bacnet_object_type("invalid-type") is None
        assert convert_point_type_to_bacnet_object_type("") is None
        assert (
            convert_point_type_to_bacnet_object_type("analog_input") is None
        )  # underscore instead of hyphen

    def test_case_sensitivity(self):
        """Test: Function is case-sensitive"""
        assert convert_point_type_to_bacnet_object_type("Analog-Input") is None
        assert convert_point_type_to_bacnet_object_type("ANALOG-INPUT") is None
