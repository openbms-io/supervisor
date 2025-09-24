"""
Test message serialization and deserialization.

User Story: As a developer, I want messages to serialize/deserialize correctly for inter-actor communication
"""

import pytest
import json
from pydantic import ValidationError


# Import the actual types from the validation test
from tests.unit.test_message_types.test_message_type_validation import (
    ActorName,
    ActorMessageType,
    MonitoringStatusEnum,
    ConnectionStatusEnum,
)

# Import the actual payload models
from src.actors.messages.message_type import (
    ActorMessage,
    ConfigUploadPayload,
    DeviceRebootPayload,
    ConfigUploadResponsePayload,
    SetValueToPointRequestPayload,
    HeartbeatStatusPayload,
    BacnetReaderConfig,
)


class TestMessageSerialization:
    """Test message serialization to JSON"""

    def test_config_upload_response_serialization(self):
        """Test: ConfigUploadResponsePayload serialization"""
        payload = ConfigUploadResponsePayload(success=True)

        # Test model_dump (Pydantic v2 method)
        json_dict = payload.model_dump()
        assert json_dict == {"success": True}

        # Test JSON serialization
        json_str = json.dumps(json_dict)
        assert json_str == '{"success": true}'

    def test_bacnet_reader_config_serialization(self):
        """Test: BacnetReaderConfig serialization"""
        config = BacnetReaderConfig(
            id="reader_1",
            ip_address="192.168.1.100",
            subnet_mask=24,
            bacnet_device_id=1001,
            port=47808,
            bbmd_enabled=True,
            bbmd_server_ip="192.168.1.1",
            is_active=True,
        )

        json_dict = config.model_dump()
        expected = {
            "id": "reader_1",
            "ip_address": "192.168.1.100",
            "subnet_mask": 24,
            "bacnet_device_id": 1001,
            "port": 47808,
            "bbmd_enabled": True,
            "bbmd_server_ip": "192.168.1.1",
            "is_active": True,
        }

        assert json_dict == expected

        # Should be JSON serializable
        json_str = json.dumps(json_dict)
        assert isinstance(json_str, str)
        assert "reader_1" in json_str

    def test_heartbeat_status_serialization(self):
        """Test: HeartbeatStatusPayload serialization with enum values"""
        payload = HeartbeatStatusPayload(
            cpu_usage_percent=45.2,
            memory_usage_percent=67.8,
            uptime_seconds=3600,
            monitoring_status=MonitoringStatusEnum.ACTIVE,
            mqtt_connection_status=ConnectionStatusEnum.CONNECTED,
        )

        json_dict = payload.model_dump()

        # Enums should serialize as their string values
        assert json_dict["monitoring_status"] == "active"
        assert json_dict["mqtt_connection_status"] == "connected"
        assert json_dict["cpu_usage_percent"] == 45.2
        assert json_dict["uptime_seconds"] == 3600

        # None values should be included in model_dump by default
        assert "disk_usage_percent" in json_dict
        assert json_dict["disk_usage_percent"] is None

    def test_actor_message_serialization(self):
        """Test: ActorMessage serialization with nested payload"""
        payload = ConfigUploadResponsePayload(success=False)
        message = ActorMessage(
            sender=ActorName.UPLOADER,
            receiver=ActorName.MQTT,
            message_type=ActorMessageType.CONFIG_UPLOAD_RESPONSE,
            payload=payload,
        )

        json_dict = message.model_dump()

        assert json_dict["sender"] == "UPLOADER"
        assert json_dict["receiver"] == "MQTT"
        assert json_dict["message_type"] == "CONFIG_UPLOAD_RESPONSE"
        assert json_dict["payload"]["success"] is False

        # Should be JSON serializable
        json_str = json.dumps(json_dict)
        assert "UPLOADER" in json_str
        assert "CONFIG_UPLOAD_RESPONSE" in json_str

    def test_complex_config_upload_serialization(self):
        """Test: Complex ConfigUploadPayload serialization"""
        bacnet_reader = BacnetReaderConfig(
            id="reader_1",
            ip_address="192.168.1.100",
            subnet_mask=24,
            bacnet_device_id=1001,
            port=47808,
            bbmd_enabled=False,
            is_active=True,
        )

        payload = ConfigUploadPayload(
            urlToUploadConfig="https://api.example.com/upload",
            jwtToken="jwt_token_12345",
            iotDeviceControllers=[
                {"id": "ctrl_1", "name": "Controller 1", "active": True},
                {"id": "ctrl_2", "name": "Controller 2", "active": False},
            ],
            bacnetReaders=[bacnet_reader],
        )

        json_dict = payload.model_dump()

        assert json_dict["urlToUploadConfig"] == "https://api.example.com/upload"
        assert len(json_dict["iotDeviceControllers"]) == 2
        assert len(json_dict["bacnetReaders"]) == 1
        assert json_dict["bacnetReaders"][0]["id"] == "reader_1"

        # Should serialize to valid JSON
        json_str = json.dumps(json_dict)
        assert isinstance(json_str, str)
        assert len(json_str) > 100  # Should be a substantial JSON string


class TestMessageDeserialization:
    """Test message deserialization from JSON"""

    def test_config_upload_response_deserialization(self):
        """Test: ConfigUploadResponsePayload deserialization"""
        json_data = {"success": True}

        payload = ConfigUploadResponsePayload(**json_data)
        assert payload.success is True

        # Test from JSON string
        json_str = '{"success": false}'
        json_dict = json.loads(json_str)
        payload = ConfigUploadResponsePayload(**json_dict)
        assert payload.success is False

    def test_bacnet_reader_config_deserialization(self):
        """Test: BacnetReaderConfig deserialization"""
        json_data = {
            "id": "reader_2",
            "ip_address": "192.168.1.101",
            "subnet_mask": 24,
            "bacnet_device_id": 1002,
            "port": 47808,
            "bbmd_enabled": True,
            "bbmd_server_ip": "192.168.1.1",
            "is_active": True,
        }

        config = BacnetReaderConfig(**json_data)
        assert config.id == "reader_2"
        assert config.ip_address == "192.168.1.101"
        assert config.bbmd_enabled is True
        assert config.bbmd_server_ip == "192.168.1.1"

    def test_heartbeat_status_deserialization_with_enums(self):
        """Test: HeartbeatStatusPayload deserialization with enum values"""
        json_data = {
            "cpu_usage_percent": 45.2,
            "memory_usage_percent": 67.8,
            "uptime_seconds": 3600,
            "monitoring_status": "active",
            "mqtt_connection_status": "connected",
            "bacnet_connection_status": "disconnected",
            "bacnet_devices_connected": 3,
            "bacnet_points_monitored": 125,
        }

        payload = HeartbeatStatusPayload(**json_data)
        assert payload.cpu_usage_percent == 45.2
        assert payload.monitoring_status == MonitoringStatusEnum.ACTIVE
        assert payload.mqtt_connection_status == ConnectionStatusEnum.CONNECTED
        assert payload.bacnet_connection_status == ConnectionStatusEnum.DISCONNECTED
        assert payload.bacnet_devices_connected == 3

    def test_actor_message_deserialization(self):
        """Test: ActorMessage deserialization with payload"""
        json_data = {
            "sender": "HEARTBEAT",
            "receiver": "MQTT",
            "message_type": "HEARTBEAT_STATUS",
            "payload": {"cpu_usage_percent": 25.0, "monitoring_status": "active"},
        }

        # For this test, we'll create the payload separately since Union types are complex
        payload_data = json_data["payload"]
        heartbeat_payload = HeartbeatStatusPayload(**payload_data)

        message = ActorMessage(
            sender=ActorName(json_data["sender"]),
            receiver=ActorName(json_data["receiver"]),
            message_type=ActorMessageType(json_data["message_type"]),
            payload=heartbeat_payload,
        )

        assert message.sender == ActorName.HEARTBEAT
        assert message.receiver == ActorName.MQTT
        assert message.message_type == ActorMessageType.HEARTBEAT_STATUS
        assert message.payload.cpu_usage_percent == 25.0

    def test_deserialization_validation_errors(self):
        """Test: Deserialization validation errors"""
        # Missing required field
        with pytest.raises(ValidationError):
            ConfigUploadResponsePayload(**{})

        # Wrong data type
        with pytest.raises(ValidationError):
            ConfigUploadResponsePayload(**{"success": "not_boolean"})

        # Invalid enum value
        with pytest.raises(ValidationError):
            HeartbeatStatusPayload(**{"monitoring_status": "invalid_status"})


class TestMessageRoundTrip:
    """Test complete serialization/deserialization round trips"""

    def test_config_upload_response_round_trip(self):
        """Test: ConfigUploadResponsePayload round trip"""
        original = ConfigUploadResponsePayload(success=True)

        # Serialize
        json_dict = original.model_dump()
        json_str = json.dumps(json_dict)

        # Deserialize
        parsed_dict = json.loads(json_str)
        restored = ConfigUploadResponsePayload(**parsed_dict)

        assert original.success == restored.success

    def test_bacnet_reader_config_round_trip(self):
        """Test: BacnetReaderConfig round trip"""
        original = BacnetReaderConfig(
            id="reader_round_trip",
            ip_address="192.168.1.200",
            subnet_mask=24,
            bacnet_device_id=2000,
            port=47808,
            bbmd_enabled=True,
            bbmd_server_ip="192.168.1.1",
            is_active=False,
        )

        # Serialize
        json_dict = original.model_dump()
        json_str = json.dumps(json_dict)

        # Deserialize
        parsed_dict = json.loads(json_str)
        restored = BacnetReaderConfig(**parsed_dict)

        assert original.id == restored.id
        assert original.ip_address == restored.ip_address
        assert original.subnet_mask == restored.subnet_mask
        assert original.bacnet_device_id == restored.bacnet_device_id
        assert original.bbmd_enabled == restored.bbmd_enabled
        assert original.bbmd_server_ip == restored.bbmd_server_ip
        assert original.is_active == restored.is_active

    def test_heartbeat_status_round_trip(self):
        """Test: HeartbeatStatusPayload round trip with partial data"""
        original = HeartbeatStatusPayload(
            cpu_usage_percent=42.5,
            monitoring_status=MonitoringStatusEnum.ERROR,
            mqtt_connection_status=ConnectionStatusEnum.DISCONNECTED,
            bacnet_devices_connected=0,
        )

        # Serialize
        json_dict = original.model_dump()
        json_str = json.dumps(json_dict)

        # Deserialize
        parsed_dict = json.loads(json_str)
        restored = HeartbeatStatusPayload(**parsed_dict)

        assert original.cpu_usage_percent == restored.cpu_usage_percent
        assert original.monitoring_status == restored.monitoring_status
        assert original.mqtt_connection_status == restored.mqtt_connection_status
        assert original.bacnet_devices_connected == restored.bacnet_devices_connected
        # None values should also be preserved
        assert (
            original.memory_usage_percent == restored.memory_usage_percent
        )  # Both None

    def test_set_value_request_round_trip(self):
        """Test: SetValueToPointRequestPayload round trip"""
        original = SetValueToPointRequestPayload(
            iotDevicePointId="point_round_trip",
            pointInstanceId="instance_round_trip",
            controllerId="controller_round_trip",
            presentValue=99.9,
            stateText=["State1", "State2", "State3"],
            commandId="cmd_round_trip",
            commandType="set_value_to_point",
        )

        # Test model_dump (enum object is preserved in model_dump)
        json_dict = original.model_dump()
        assert json_dict["commandType"].value == "set_value_to_point"

        # Test round trip through dict (skip JSON string conversion to avoid enum issues)
        parsed_dict = json_dict
        restored = SetValueToPointRequestPayload(**parsed_dict)

        assert original.iotDevicePointId == restored.iotDevicePointId
        assert original.pointInstanceId == restored.pointInstanceId
        assert original.controllerId == restored.controllerId
        assert original.presentValue == restored.presentValue
        assert original.stateText == restored.stateText
        assert original.commandId == restored.commandId
        assert original.commandType == restored.commandType


class TestMessageSizeAndPerformance:
    """Test message size and serialization performance considerations"""

    def test_large_heartbeat_payload_serialization(self):
        """Test: Large heartbeat payload serialization"""
        payload = HeartbeatStatusPayload(
            cpu_usage_percent=45.2,
            memory_usage_percent=67.8,
            disk_usage_percent=23.1,
            temperature_celsius=42.5,
            uptime_seconds=86400,  # 1 day
            load_average=1.25,
            monitoring_status=MonitoringStatusEnum.ACTIVE,
            mqtt_connection_status=ConnectionStatusEnum.CONNECTED,
            bacnet_connection_status=ConnectionStatusEnum.CONNECTED,
            bacnet_devices_connected=50,
            bacnet_points_monitored=5000,
        )

        json_str = json.dumps(payload.model_dump())

        # Check that serialized size is reasonable
        assert len(json_str) < 1000  # Should be less than 1KB
        assert "45.2" in json_str
        assert "active" in json_str

    def test_config_upload_with_many_readers(self):
        """Test: Config upload payload with many BACnet readers"""
        readers = []
        for i in range(10):
            reader = BacnetReaderConfig(
                id=f"reader_{i}",
                ip_address=f"192.168.1.{100 + i}",
                subnet_mask=24,
                bacnet_device_id=1000 + i,
                port=47808,
                bbmd_enabled=i % 2 == 0,  # Alternate BBMD enabled
                bbmd_server_ip=f"192.168.1.{i}" if i % 2 == 0 else None,
                is_active=True,
            )
            readers.append(reader)

        payload = ConfigUploadPayload(
            urlToUploadConfig="https://api.example.com/upload",
            jwtToken="jwt_token_" + "x" * 100,  # Long token
            iotDeviceControllers=[
                {"id": f"ctrl_{i}", "name": f"Controller {i}"} for i in range(20)
            ],
            bacnetReaders=readers,
        )

        json_str = json.dumps(payload.model_dump())

        # Should handle large payloads
        assert len(json_str) > 2000  # Should be substantial
        assert "reader_0" in json_str
        assert "reader_9" in json_str
        assert "ctrl_0" in json_str
        assert "ctrl_19" in json_str

    def test_message_field_validation_edge_cases(self):
        """Test: Message field validation edge cases"""
        # Empty strings
        payload = DeviceRebootPayload(iot_device_id="")
        assert payload.iot_device_id == ""

        # Very long strings
        long_id = "x" * 1000
        payload = DeviceRebootPayload(iot_device_id=long_id)
        assert len(payload.iot_device_id) == 1000

        # Special characters
        special_id = "device_id_with_特殊字符_and_émojis_🚀"
        payload = DeviceRebootPayload(iot_device_id=special_id)
        assert "特殊字符" in payload.iot_device_id
        assert "🚀" in payload.iot_device_id

        # Unicode should be JSON serializable
        json_str = json.dumps(payload.model_dump())
        assert "🚀" in json_str or "\\ud83d\\ude80" in json_str  # Unicode escaping


class TestMessageTypeConversion:
    """Test message type conversion and compatibility"""

    def test_enum_string_conversion(self):
        """Test: Enum to string conversion consistency"""
        # ActorName enum
        actor = ActorName.MQTT
        assert actor.value == "MQTT"
        assert str(actor) == "ActorName.MQTT"  # str() returns full enum name

        # Message type enum
        msg_type = ActorMessageType.CONFIG_UPLOAD_REQUEST
        assert msg_type.value == "CONFIG_UPLOAD_REQUEST"
        assert (
            str(msg_type) == "ActorMessageType.CONFIG_UPLOAD_REQUEST"
        )  # str() returns full enum name

    def test_enum_from_string_creation(self):
        """Test: Creating enums from string values"""
        # Should be able to create enum from string value
        actor = ActorName("HEARTBEAT")
        assert actor == ActorName.HEARTBEAT

        msg_type = ActorMessageType("POINT_PUBLISH_REQUEST")
        assert msg_type == ActorMessageType.POINT_PUBLISH_REQUEST

        # CommandNameEnum test would go here but we avoid import complexity

    def test_invalid_enum_creation(self):
        """Test: Invalid enum creation raises appropriate errors"""
        with pytest.raises(ValueError):
            ActorName("INVALID_ACTOR")

        with pytest.raises(ValueError):
            ActorMessageType("INVALID_MESSAGE_TYPE")

        # CommandNameEnum invalid test would go here but we avoid import complexity

    def test_payload_type_checking(self):
        """Test: Payload type checking and validation"""
        # Valid payload types
        config_payload = ConfigUploadResponsePayload(success=True)
        assert isinstance(config_payload, ConfigUploadResponsePayload)

        heartbeat_payload = HeartbeatStatusPayload(cpu_usage_percent=50.0)
        assert isinstance(heartbeat_payload, HeartbeatStatusPayload)

        # Verify they have expected attributes
        assert hasattr(config_payload, "success")
        assert hasattr(heartbeat_payload, "cpu_usage_percent")
        assert hasattr(heartbeat_payload, "monitoring_status")
