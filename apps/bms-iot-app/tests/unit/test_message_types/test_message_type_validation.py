"""
Test message type validation and structure.

User Story: As a developer, I want message types to validate correctly
"""

import pytest
from pydantic import ValidationError

# Import the actual types from the codebase
from src.actors.messages.message_type import (
    ActorMessage,
    ActorName,
    ActorMessageType,
    ConfigUploadPayload,
    DeviceRebootPayload,
    ConfigUploadResponsePayload,
    SetValueToPointRequestPayload,
    HeartbeatStatusPayload,
)
from src.models.device_status_enums import (
    MonitoringStatusEnum,
    ConnectionStatusEnum,
)


class TestMessageTypeValidation:
    """Test message type validation using actual types from codebase"""

    def test_actor_name_enum_values(self):
        """Test: ActorName enum contains expected values"""
        expected_actors = {
            "MQTT",
            "BACNET",
            "BACNET_WRITER",
            "UPLOADER",
            "BROADCAST",
            "CLEANER",
            "HEARTBEAT",
            "SYSTEM_METRICS",
        }
        actual_actors = {actor.value for actor in ActorName}
        assert expected_actors.issubset(actual_actors)

    def test_actor_message_type_enum_values(self):
        """Test: ActorMessageType enum contains expected values"""
        expected_types = {
            "CONFIG_UPLOAD_REQUEST",
            "CONFIG_UPLOAD_RESPONSE",
            "DEVICE_REBOOT",
            "POINT_PUBLISH_REQUEST",
            "SET_VALUE_TO_POINT_REQUEST",
            "HEARTBEAT_STATUS",
        }
        actual_types = {msg_type.value for msg_type in ActorMessageType}
        assert expected_types.issubset(actual_types)

    def test_config_upload_payload_validation(self):
        """Test: ConfigUploadPayload validates correctly"""
        valid_payload = {
            "urlToUploadConfig": "https://api.example.com/upload",
            "jwtToken": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            "iotDeviceControllers": [{"controller_id": "ctrl_1", "points": []}],
        }

        payload = ConfigUploadPayload(**valid_payload)
        assert payload.urlToUploadConfig == "https://api.example.com/upload"
        assert len(payload.iotDeviceControllers) == 1

    def test_config_upload_payload_required_fields(self):
        """Test: ConfigUploadPayload requires all mandatory fields"""
        with pytest.raises(ValidationError) as exc_info:
            ConfigUploadPayload(urlToUploadConfig="https://api.example.com")

        errors = exc_info.value.errors()
        missing_fields = {
            error["loc"][0] for error in errors if error["type"] == "missing"
        }
        assert "jwtToken" in missing_fields
        assert "iotDeviceControllers" in missing_fields

    def test_device_reboot_payload_validation(self):
        """Test: DeviceRebootPayload validates correctly"""
        payload = DeviceRebootPayload(iot_device_id="device_123")
        assert payload.iot_device_id == "device_123"

        with pytest.raises(ValidationError):
            DeviceRebootPayload()  # Missing required field

    def test_set_value_to_point_payload_validation(self):
        """Test: SetValueToPointRequestPayload validates correctly"""
        valid_payload = {
            "iotDevicePointId": "point_123",
            "pointInstanceId": "instance_456",
            "controllerId": "ctrl_789",
            "presentValue": 25.5,
            "commandId": "cmd_001",
            "commandType": "set_value_to_point",  # Use string value
        }

        payload = SetValueToPointRequestPayload(**valid_payload)
        assert payload.presentValue == 25.5
        assert payload.commandType.value == "set_value_to_point"

    def test_set_value_to_point_payload_numeric_types(self):
        """Test: SetValueToPointRequestPayload accepts int and float"""
        base_payload = {
            "iotDevicePointId": "point_123",
            "pointInstanceId": "instance_456",
            "controllerId": "ctrl_789",
            "commandId": "cmd_001",
            "commandType": "set_value_to_point",
        }

        # Test float value
        float_payload = SetValueToPointRequestPayload(**base_payload, presentValue=25.7)
        assert float_payload.presentValue == 25.7

        # Test int value
        int_payload = SetValueToPointRequestPayload(**base_payload, presentValue=30)
        assert int_payload.presentValue == 30

    def test_heartbeat_status_payload_optional_fields(self):
        """Test: HeartbeatStatusPayload handles optional fields correctly"""
        # Test with no fields
        empty_payload = HeartbeatStatusPayload()
        assert empty_payload.cpu_usage_percent is None
        assert empty_payload.monitoring_status is None

        # Test with some fields
        partial_payload = HeartbeatStatusPayload(
            cpu_usage_percent=45.2, monitoring_status=MonitoringStatusEnum.ACTIVE
        )
        assert partial_payload.cpu_usage_percent == 45.2
        assert partial_payload.monitoring_status == MonitoringStatusEnum.ACTIVE
        assert partial_payload.memory_usage_percent is None

    def test_heartbeat_status_payload_enum_validation(self):
        """Test: HeartbeatStatusPayload validates enum fields"""
        # Valid enum values
        payload = HeartbeatStatusPayload(
            monitoring_status=MonitoringStatusEnum.ACTIVE,
            mqtt_connection_status=ConnectionStatusEnum.CONNECTED,
        )
        assert payload.monitoring_status == MonitoringStatusEnum.ACTIVE
        assert payload.mqtt_connection_status == ConnectionStatusEnum.CONNECTED

        # Invalid enum values should raise ValidationError
        with pytest.raises(ValidationError):
            HeartbeatStatusPayload(monitoring_status="invalid_status")

    def test_actor_message_structure(self):
        """Test: ActorMessage validates complete message structure"""
        config_payload = ConfigUploadPayload(
            urlToUploadConfig="https://api.example.com/upload",
            jwtToken="jwt_token_here",
            iotDeviceControllers=[],
        )

        message = ActorMessage(
            sender=ActorName.MQTT,
            receiver=ActorName.BACNET,
            message_type=ActorMessageType.CONFIG_UPLOAD_REQUEST,
            payload=config_payload,
        )

        assert message.sender == ActorName.MQTT
        assert message.receiver == ActorName.BACNET
        assert message.message_type == ActorMessageType.CONFIG_UPLOAD_REQUEST
        assert isinstance(message.payload, ConfigUploadPayload)

    def test_actor_message_without_payload(self):
        """Test: ActorMessage works without payload"""
        message = ActorMessage(
            sender=ActorName.HEARTBEAT,
            receiver=ActorName.BROADCAST,
            message_type=ActorMessageType.HEARTBEAT_STATUS,
            payload=None,
        )

        assert message.payload is None
        assert message.sender == ActorName.HEARTBEAT

    def test_actor_message_required_fields(self):
        """Test: ActorMessage requires sender, receiver, and message_type"""
        with pytest.raises(ValidationError) as exc_info:
            ActorMessage(sender=ActorName.MQTT)

        errors = exc_info.value.errors()
        missing_fields = {
            error["loc"][0] for error in errors if error["type"] == "missing"
        }
        assert "receiver" in missing_fields
        assert "message_type" in missing_fields

    def test_payload_union_type_validation(self):
        """Test: ActorMessage payload accepts different payload types"""
        # Test with DeviceRebootPayload
        reboot_message = ActorMessage(
            sender=ActorName.MQTT,
            receiver=ActorName.SYSTEM_METRICS,
            message_type=ActorMessageType.DEVICE_REBOOT,
            payload=DeviceRebootPayload(iot_device_id="device_123"),
        )
        assert isinstance(reboot_message.payload, DeviceRebootPayload)

        # Test with HeartbeatStatusPayload
        heartbeat_message = ActorMessage(
            sender=ActorName.HEARTBEAT,
            receiver=ActorName.BROADCAST,
            message_type=ActorMessageType.HEARTBEAT_STATUS,
            payload=HeartbeatStatusPayload(cpu_usage_percent=25.0),
        )
        assert isinstance(heartbeat_message.payload, HeartbeatStatusPayload)

    def test_enum_string_conversion(self):
        """Test: Enums convert to strings correctly"""
        actor = ActorName.MQTT
        message_type = ActorMessageType.CONFIG_UPLOAD_REQUEST

        # Note: str() returns the full enum representation, not just the value
        assert str(actor) == "ActorName.MQTT"
        assert actor.value == "MQTT"
        assert str(message_type) == "ActorMessageType.CONFIG_UPLOAD_REQUEST"
        assert message_type.value == "CONFIG_UPLOAD_REQUEST"

    def test_model_serialization(self):
        """Test: Models can be serialized to dict"""
        payload = ConfigUploadResponsePayload(success=True)
        message = ActorMessage(
            sender=ActorName.BACNET,
            receiver=ActorName.MQTT,
            message_type=ActorMessageType.CONFIG_UPLOAD_RESPONSE,
            payload=payload,
        )

        # Test serialization
        message_dict = message.model_dump()
        assert message_dict["sender"] == "BACNET"
        assert message_dict["receiver"] == "MQTT"
        assert message_dict["message_type"] == "CONFIG_UPLOAD_RESPONSE"
        assert message_dict["payload"]["success"] is True

    def test_model_deserialization(self):
        """Test: Models can be created from dict"""
        message_data = {
            "sender": "MQTT",
            "receiver": "BACNET",
            "message_type": "DEVICE_REBOOT",
            "payload": {"iot_device_id": "device_456"},
        }

        # This will work because Pydantic handles the enum conversion
        message = ActorMessage(**message_data)
        assert message.sender == ActorName.MQTT
        assert message.message_type == ActorMessageType.DEVICE_REBOOT
        assert isinstance(message.payload, DeviceRebootPayload)
        assert message.payload.iot_device_id == "device_456"


class TestMessageTypeEdgeCases:
    """Test edge cases and error conditions for message types"""

    def test_invalid_enum_values(self):
        """Test: Invalid enum values raise ValidationError"""
        with pytest.raises(ValidationError):
            ActorMessage(
                sender="INVALID_ACTOR",
                receiver=ActorName.MQTT,
                message_type=ActorMessageType.CONFIG_UPLOAD_REQUEST,
            )

        with pytest.raises(ValidationError):
            ActorMessage(
                sender=ActorName.MQTT,
                receiver=ActorName.BACNET,
                message_type="INVALID_MESSAGE_TYPE",
            )

    def test_payload_type_mismatch(self):
        """Test: Wrong payload type for message"""
        # This tests that the Union type validation works
        config_payload = ConfigUploadPayload(
            urlToUploadConfig="https://api.example.com",
            jwtToken="token",
            iotDeviceControllers=[],
        )

        # This should work - correct payload type
        message = ActorMessage(
            sender=ActorName.MQTT,
            receiver=ActorName.BACNET,
            message_type=ActorMessageType.CONFIG_UPLOAD_REQUEST,
            payload=config_payload,
        )
        assert isinstance(message.payload, ConfigUploadPayload)

    def test_numeric_value_boundaries(self):
        """Test: Numeric values handle boundaries correctly"""
        payload_data = {
            "iotDevicePointId": "point_123",
            "pointInstanceId": "instance_456",
            "controllerId": "ctrl_789",
            "commandId": "cmd_001",
            "commandType": "set_value_to_point",
        }

        # Test very large numbers
        large_payload = SetValueToPointRequestPayload(
            **payload_data, presentValue=999999.99
        )
        assert large_payload.presentValue == 999999.99

        # Test negative numbers
        negative_payload = SetValueToPointRequestPayload(
            **payload_data, presentValue=-273.15
        )
        assert negative_payload.presentValue == -273.15

        # Test zero
        zero_payload = SetValueToPointRequestPayload(**payload_data, presentValue=0)
        assert zero_payload.presentValue == 0

    def test_string_field_edge_cases(self):
        """Test: String fields handle edge cases"""
        # Test empty strings (should be allowed)
        payload = DeviceRebootPayload(iot_device_id="")
        assert payload.iot_device_id == ""

        # Test very long strings
        long_id = "x" * 1000
        payload = DeviceRebootPayload(iot_device_id=long_id)
        assert len(payload.iot_device_id) == 1000

    def test_list_field_validation(self):
        """Test: List fields validate correctly"""
        # Empty list should be allowed
        payload = ConfigUploadPayload(
            urlToUploadConfig="https://api.example.com",
            jwtToken="token",
            iotDeviceControllers=[],
        )
        assert len(payload.iotDeviceControllers) == 0

        # List with items
        controllers = [
            {"controller_id": "ctrl_1", "points": []},
            {"controller_id": "ctrl_2", "points": []},
        ]
        payload = ConfigUploadPayload(
            urlToUploadConfig="https://api.example.com",
            jwtToken="token",
            iotDeviceControllers=controllers,
        )
        assert len(payload.iotDeviceControllers) == 2
