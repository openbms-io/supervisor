"""
Test utility functions.

User Story: As a developer, I want to ensure utility functions work correctly
"""

from unittest.mock import Mock
from src.utils.utils import (
    kebab_to_camel,
    normalize_value,
    extract_property_dict_camel,
    normalize_priority_value,
    normalize_timestamp,
)


class TestKebabToCamel:
    """Test kebab_to_camel conversion function"""

    def test_simple_kebab_case(self):
        """Test: Validate utility helper functions return expected results"""
        result = kebab_to_camel("hello-world")
        assert result == "helloWorld"

    def test_single_word(self):
        """Test: Single word should remain unchanged"""
        result = kebab_to_camel("hello")
        assert result == "hello"

    def test_multiple_hyphens(self):
        """Test: Multiple hyphens should be handled correctly"""
        result = kebab_to_camel("hello-world-test-case")
        assert result == "helloWorldTestCase"

    def test_empty_string(self):
        """Test: Edge cases and error handling in utility functions"""
        result = kebab_to_camel("")
        assert result == ""

    def test_with_numbers(self):
        """Test: Kebab case with numbers"""
        result = kebab_to_camel("test-123-value")
        assert result == "test123Value"


class TestNormalizeValue:
    """Test normalize_value function"""

    def test_simple_value(self):
        """Test: Simple values pass through unchanged"""
        assert normalize_value(42) == 42
        assert normalize_value("test") == "test"
        assert normalize_value(3.14) == 3.14
        assert normalize_value(True) is True

    def test_object_with_value_attribute(self):
        """Test: Objects with value attribute are extracted"""
        mock_obj = Mock()
        mock_obj.value = "extracted_value"

        result = normalize_value(mock_obj)
        assert result == "extracted_value"

    def test_object_with_asn1_attribute(self):
        """Test: Objects with asn1 attribute are converted to string"""
        mock_obj = Mock()
        mock_obj.asn1 = "asn1_value"
        del mock_obj.value  # Ensure it doesn't have value attribute

        result = normalize_value(mock_obj)
        assert result == "asn1_value"

    def test_object_with_dict_contents(self):
        """Test: Objects with dict_contents method are converted to dict"""
        mock_obj = Mock()
        mock_obj.dict_contents.return_value = {"key": "value"}
        del mock_obj.value  # Ensure it doesn't have value attribute
        del mock_obj.asn1  # Ensure it doesn't have asn1 attribute

        result = normalize_value(mock_obj)
        assert result == {"key": "value"}

    def test_tuple_with_asn1(self):
        """Test: Tuple with asn1 object is properly converted"""
        mock_obj = Mock()
        mock_obj.asn1 = "object_type"

        result = normalize_value((mock_obj, 123))
        assert result == ("object_type", 123)

    def test_none_value(self):
        """Test: None values are handled correctly"""
        result = normalize_value(None)
        assert result is None

    def test_list_value(self):
        """Test: List values pass through unchanged"""
        test_list = [1, 2, 3]
        result = normalize_value(test_list)
        assert result == test_list


class TestExtractPropertyDictCamel:
    """Test extract_property_dict_camel function"""

    def test_simple_property_extraction(self):
        """Test: Simple property extraction with camel case conversion"""
        mock_prop = Mock()
        mock_prop.asn1 = "property-name"

        prop_tuples = [
            ("value1", mock_prop),
        ]

        result = extract_property_dict_camel(prop_tuples)
        assert result == {"propertyName": "value1"}

    def test_multiple_properties(self):
        """Test: Multiple properties are extracted correctly"""
        mock_prop1 = Mock()
        mock_prop1.asn1 = "first-property"

        mock_prop2 = Mock()
        mock_prop2.asn1 = "second-property"

        prop_tuples = [
            ("value1", mock_prop1),
            ("value2", mock_prop2),
        ]

        result = extract_property_dict_camel(prop_tuples)
        assert result == {"firstProperty": "value1", "secondProperty": "value2"}

    def test_with_normalized_values(self):
        """Test: Values are normalized during extraction"""
        mock_prop = Mock()
        mock_prop.asn1 = "test-property"

        mock_value = Mock()
        mock_value.value = "normalized_value"

        prop_tuples = [
            (mock_value, mock_prop),
        ]

        result = extract_property_dict_camel(prop_tuples)
        assert result == {"testProperty": "normalized_value"}

    def test_empty_tuples(self):
        """Test: Empty property tuples return empty dict"""
        result = extract_property_dict_camel([])
        assert result == {}

    def test_property_without_asn1(self):
        """Test: Properties without asn1 use string representation"""
        prop_tuples = [
            ("value1", "simple-property"),
        ]

        result = extract_property_dict_camel(prop_tuples)
        assert result == {"simpleProperty": "value1"}


class TestNormalizePriorityValue:
    """Test normalize_priority_value function for all PriorityValue Choice types"""

    def _create_priority_value_mock(self, **kwargs):
        """Helper to create a PriorityValue mock with specific attributes set"""

        class MockPriorityValue:
            def __init__(self):
                self.__class__.__name__ = "PriorityValue"
                # Set all attributes to None by default
                self.null = None
                self.real = None
                self.boolean = None
                self.unsigned = None
                self.integer = None
                self.double = None
                self.time = None
                self.characterString = None
                self.octetString = None
                self.bitString = None
                self.enumerated = None
                self.date = None
                self.objectIdentifier = None
                self.constructedValue = None

                # Override with specific values
                for attr, value in kwargs.items():
                    setattr(self, attr, value)

        return MockPriorityValue()

    def test_priority_value_null(self):
        """Test: PriorityValue with null type"""
        mock_priority_value = self._create_priority_value_mock(null=True)

        result = normalize_priority_value(mock_priority_value)
        assert result == {"type": "null", "value": None}

    def test_priority_value_real(self):
        """Test: PriorityValue with real type"""
        mock_priority_value = self._create_priority_value_mock(real=25.5)

        result = normalize_priority_value(mock_priority_value)
        assert result == {"type": "real", "value": 25.5}

    def test_priority_value_boolean_true(self):
        """Test: PriorityValue with boolean type (True)"""
        mock_priority_value = self._create_priority_value_mock(boolean=True)

        result = normalize_priority_value(mock_priority_value)
        assert result == {"type": "boolean", "value": True}

    def test_priority_value_boolean_false(self):
        """Test: PriorityValue with boolean type (False)"""
        mock_priority_value = self._create_priority_value_mock(boolean=False)

        result = normalize_priority_value(mock_priority_value)
        assert result == {"type": "boolean", "value": False}

    def test_priority_value_unsigned(self):
        """Test: PriorityValue with unsigned type"""
        mock_priority_value = self._create_priority_value_mock(unsigned=123)

        result = normalize_priority_value(mock_priority_value)
        assert result == {"type": "unsigned", "value": 123}

    def test_priority_value_integer(self):
        """Test: PriorityValue with integer type"""
        mock_priority_value = self._create_priority_value_mock(integer=-456)

        result = normalize_priority_value(mock_priority_value)
        assert result == {"type": "integer", "value": -456}

    def test_priority_value_double(self):
        """Test: PriorityValue with double type"""
        mock_priority_value = self._create_priority_value_mock(double=3.14159)

        result = normalize_priority_value(mock_priority_value)
        assert result == {"type": "double", "value": 3.14159}

    def test_priority_value_time(self):
        """Test: PriorityValue with time type"""

        # Create a proper time object that only has the attributes we want
        class MockTime:
            def __init__(self):
                self.hour = 14
                self.minute = 30
                self.second = 45

        mock_time = MockTime()
        mock_priority_value = self._create_priority_value_mock(time=mock_time)

        result = normalize_priority_value(mock_priority_value)
        assert result == {
            "type": "time",
            "value": {"hour": 14, "minute": 30, "second": 45},
        }

    def test_priority_value_character_string(self):
        """Test: PriorityValue with characterString type"""
        mock_priority_value = self._create_priority_value_mock(
            characterString="test string"
        )

        result = normalize_priority_value(mock_priority_value)
        assert result == {"type": "characterString", "value": "test string"}

    def test_priority_value_octet_string(self):
        """Test: PriorityValue with octetString type"""
        mock_priority_value = self._create_priority_value_mock(
            octetString=b"\x01\x02\x03"
        )

        result = normalize_priority_value(mock_priority_value)
        assert result == {"type": "octetString", "value": [1, 2, 3]}

    def test_priority_value_bit_string(self):
        """Test: PriorityValue with bitString type"""

        class MockBitString:
            def __str__(self):
                return "101010"

        mock_bit_string = MockBitString()
        mock_priority_value = self._create_priority_value_mock(
            bitString=mock_bit_string
        )

        result = normalize_priority_value(mock_priority_value)
        assert result == {"type": "bitString", "value": "101010"}

    def test_priority_value_enumerated(self):
        """Test: PriorityValue with enumerated type"""
        mock_priority_value = self._create_priority_value_mock(enumerated=5)

        result = normalize_priority_value(mock_priority_value)
        assert result == {"type": "enumerated", "value": 5}

    def test_priority_value_date(self):
        """Test: PriorityValue with date type"""
        mock_date = Mock()
        mock_date.year = 2024
        mock_date.month = 12
        mock_date.day = 25

        mock_priority_value = self._create_priority_value_mock(date=mock_date)

        result = normalize_priority_value(mock_priority_value)
        assert result == {
            "type": "date",
            "value": {"year": 2024, "month": 12, "day": 25},
        }

    def test_priority_value_object_identifier(self):
        """Test: PriorityValue with objectIdentifier type"""
        mock_object_id = Mock()
        mock_object_id.objectType = "analogValue"
        mock_object_id.instanceNumber = 123

        mock_priority_value = self._create_priority_value_mock(
            objectIdentifier=mock_object_id
        )

        result = normalize_priority_value(mock_priority_value)
        assert result == {
            "type": "objectIdentifier",
            "value": {"objectType": "analogValue", "instanceNumber": 123},
        }

    def test_priority_value_constructed_value(self):
        """Test: PriorityValue with constructedValue type"""

        class MockConstructedValue:
            def __str__(self):
                return "constructed_data"

        mock_constructed = MockConstructedValue()
        mock_priority_value = self._create_priority_value_mock(
            constructedValue=mock_constructed
        )

        result = normalize_priority_value(mock_priority_value)
        assert result == {"type": "constructedValue", "value": "constructed_data"}

    def test_priority_value_none_input(self):
        """Test: None input returns None"""
        result = normalize_priority_value(None)
        assert result is None

    def test_priority_value_non_priority_object(self):
        """Test: Non-PriorityValue object returns error result"""

        # Create a proper non-PriorityValue object (class name doesn't contain "PriorityValue")
        class SomeOtherObject:
            pass

        mock_obj = SomeOtherObject()

        result = normalize_priority_value(mock_obj)
        assert result["type"] == "error"
        assert result["value"] == "Not a PriorityValue object"

    def test_priority_value_exception_handling(self):
        """Test: Exception handling returns error result"""
        mock_priority_value = Mock()
        mock_priority_value.__class__.__name__ = "PriorityValue"
        # Simulate an exception when accessing properties
        mock_priority_value.real = Mock(side_effect=Exception("Test error"))

        result = normalize_priority_value(mock_priority_value)
        assert result["type"] == "error"
        assert isinstance(result["value"], str)

    def test_priority_value_all_none_attributes(self):
        """Test: PriorityValue with all None attributes returns unknown"""
        mock_priority_value = self._create_priority_value_mock()  # All None by default

        result = normalize_priority_value(mock_priority_value)
        assert result["type"] == "unknown"
        assert isinstance(result["value"], str)


class TestNormalizeTimestamp:
    """Test normalize_timestamp function for all TimeStamp Choice types"""

    def _create_timestamp_mock(self, **kwargs):
        """Helper to create a TimeStamp mock with specific attributes set"""

        class MockTimeStamp:
            def __init__(self):
                self.__class__.__name__ = "TimeStamp"
                # Set all attributes to None by default
                self.time = None
                self.sequenceNumber = None
                self.dateTime = None

                # Override with specific values
                for attr, value in kwargs.items():
                    setattr(self, attr, value)

        return MockTimeStamp()

    def test_timestamp_time(self):
        """Test: TimeStamp with time type (context=0) - now returns ISO format"""
        mock_time = Mock()
        mock_time.isoformat.return_value = "14:30:45.500000"

        mock_timestamp = self._create_timestamp_mock(time=mock_time)

        result = normalize_timestamp(mock_timestamp)
        assert result == {"type": "time", "value": "14:30:45.500000"}

    def test_timestamp_sequence_number(self):
        """Test: TimeStamp with sequenceNumber type (context=1)"""
        mock_timestamp = self._create_timestamp_mock(sequenceNumber=12345)

        result = normalize_timestamp(mock_timestamp)
        assert result == {"type": "sequenceNumber", "value": 12345}

    def test_timestamp_datetime(self):
        """Test: TimeStamp with dateTime type (context=2) - now returns ISO format"""
        mock_datetime = Mock()
        mock_datetime.isoformat.return_value = "2024-12-25T14:30:45.000000"

        mock_timestamp = Mock()
        mock_timestamp.__class__.__name__ = "TimeStamp"
        mock_timestamp.dateTime = mock_datetime
        mock_timestamp.time = None
        mock_timestamp.sequenceNumber = None

        result = normalize_timestamp(mock_timestamp)
        assert result == {"type": "dateTime", "value": "2024-12-25T14:30:45.000000"}

    def test_timestamp_time_minimal(self):
        """Test: TimeStamp with time type - minimal attributes - ISO format"""
        mock_time = Mock()
        mock_time.isoformat.return_value = "09:15:00.000000"

        mock_timestamp = self._create_timestamp_mock(time=mock_time)

        result = normalize_timestamp(mock_timestamp)
        assert result == {"type": "time", "value": "09:15:00.000000"}

    def test_timestamp_datetime_minimal(self):
        """Test: TimeStamp with dateTime type - minimal attributes - ISO format"""
        mock_datetime = Mock()
        mock_datetime.isoformat.return_value = "2023-06-15T00:00:00.000000"

        mock_timestamp = self._create_timestamp_mock(dateTime=mock_datetime)

        result = normalize_timestamp(mock_timestamp)
        assert result == {"type": "dateTime", "value": "2023-06-15T00:00:00.000000"}

    def test_timestamp_none_input(self):
        """Test: None input returns None"""
        result = normalize_timestamp(None)
        assert result is None

    def test_timestamp_non_timestamp_object(self):
        """Test: Non-TimeStamp object returns error result"""

        class SomeOtherObject:
            pass

        mock_obj = SomeOtherObject()

        result = normalize_timestamp(mock_obj)
        assert result == {"type": "error", "value": "Not a TimeStamp object"}

    def test_timestamp_exception_handling(self):
        """Test: Exception handling when hasattr itself throws exception"""

        class BadTimeStamp:
            def __init__(self):
                self.__class__.__name__ = "TimeStamp"

            def __getattribute__(self, name):
                if name in ["time", "sequenceNumber", "dateTime"]:
                    raise Exception("Attribute access error")
                return super().__getattribute__(name)

        mock_timestamp = BadTimeStamp()

        result = normalize_timestamp(mock_timestamp)
        assert result["type"] == "error"
        assert isinstance(result["value"], str)

    def test_timestamp_all_none_attributes(self):
        """Test: TimeStamp with all None attributes returns unknown"""
        mock_timestamp = self._create_timestamp_mock()  # All None by default

        result = normalize_timestamp(mock_timestamp)
        assert result["type"] == "unknown"
        assert isinstance(result["value"], str)

    def test_timestamp_string_fallback(self):
        """Test: TimeStamp object that can't be parsed falls back to string"""

        class MockTimeStampWithStr:
            def __init__(self):
                self.__class__.__name__ = "TimeStamp"
                self.time = None
                self.sequenceNumber = None
                self.dateTime = None

            def __str__(self):
                return "2024-12-25T14:30:45Z"

        mock_timestamp = MockTimeStampWithStr()

        result = normalize_timestamp(mock_timestamp)
        assert result["type"] == "unknown"
        assert result["value"] == "2024-12-25T14:30:45Z"

    def test_timestamp_datetime_no_isoformat_fallback(self):
        """Test: DateTime object without isoformat method falls back to string"""
        mock_datetime = Mock()
        # Remove isoformat to test fallback
        del mock_datetime.isoformat
        mock_datetime.__str__ = Mock(return_value="2024-12-25 14:30:45")

        mock_timestamp = Mock()
        mock_timestamp.__class__.__name__ = "TimeStamp"
        mock_timestamp.dateTime = mock_datetime
        mock_timestamp.time = None
        mock_timestamp.sequenceNumber = None

        result = normalize_timestamp(mock_timestamp)
        assert result == {"type": "dateTime", "value": "2024-12-25 14:30:45"}

    def test_timestamp_time_isoformat_exception_fallback(self):
        """Test: TimeStamp with time that has isoformat exception falls back to string"""
        mock_time = Mock()
        # Make isoformat throw an exception to test the try/catch at the top level
        mock_time.isoformat.side_effect = Exception("isoformat error")
        mock_time.__str__ = Mock(return_value="14:30:45 fallback")

        mock_timestamp = Mock()
        mock_timestamp.__class__.__name__ = "TimeStamp"
        mock_timestamp.time = mock_time
        mock_timestamp.sequenceNumber = None
        mock_timestamp.dateTime = None

        result = normalize_timestamp(mock_timestamp)
        # Should catch the exception and return error type
        assert result["type"] == "error"
        assert isinstance(result["value"], str)
