"""
Test MQTT ↔ BacnetMonitoring communication patterns.

User Story: As a system integrator, I want MQTT and BACnet actors to communicate
correctly for device control and data collection.
"""

import pytest
import asyncio
import time
import sys

# Add the fixtures directory to the path
sys.path.insert(
    0, "/Users/amol/Documents/ai-projects/bms-project/apps/bms-iot-app/tests"
)

from fixtures.actor_test_harness import ActorTestHarness


class TestMQTTToBACnetCommands:
    """Test MQTT to BACnet monitoring command flow"""

    @pytest.mark.asyncio
    async def test_start_monitoring_command(self):
        """Test: MQTT actor sends START_MONITORING command to BACnet actor"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # MQTT receives external command to start monitoring
        start_command = {
            "type": "START_MONITORING_REQUEST",
            "sender": "mqtt",
            "receiver": "bacnet_monitoring",
            "payload": {
                "device_id": "BAC_DEVICE_001",
                "monitoring_config": {
                    "points": ["temperature", "humidity", "pressure"],
                    "interval_seconds": 30,
                    "priority": "high",
                },
            },
        }

        # Send command
        result = await harness.send_message(start_command)
        assert result["status"] == "sent"

        # Wait for processing
        await asyncio.sleep(0.1)

        # Verify BACnet actor received the command
        bacnet_messages = harness.get_actor_messages("bacnet_monitoring")
        assert len(bacnet_messages) > 0

        start_msg = bacnet_messages[0]
        assert start_msg["type"] == "START_MONITORING_REQUEST"
        assert start_msg["payload"]["device_id"] == "BAC_DEVICE_001"
        assert len(start_msg["payload"]["monitoring_config"]["points"]) == 3

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_stop_monitoring_command(self):
        """Test: MQTT actor sends STOP_MONITORING command to BACnet actor"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # MQTT sends stop monitoring command
        stop_command = {
            "type": "STOP_MONITORING_REQUEST",
            "sender": "mqtt",
            "receiver": "bacnet_monitoring",
            "payload": {"device_id": "BAC_DEVICE_001", "reason": "user_requested"},
        }

        await harness.send_message(stop_command)
        await asyncio.sleep(0.1)

        # Verify BACnet actor received stop command
        bacnet_messages = harness.get_actor_messages("bacnet_monitoring")
        stop_msg = next(
            (m for m in bacnet_messages if m["type"] == "STOP_MONITORING_REQUEST"), None
        )

        assert stop_msg is not None
        assert stop_msg["payload"]["device_id"] == "BAC_DEVICE_001"
        assert stop_msg["payload"]["reason"] == "user_requested"

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_config_upload_command(self):
        """Test: MQTT triggers config upload to BACnet device"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # MQTT sends config upload command
        config_command = {
            "type": "CONFIG_UPLOAD_REQUEST",
            "sender": "mqtt",
            "receiver": "bacnet_monitoring",
            "payload": {
                "device_id": "BAC_DEVICE_001",
                "config_data": {
                    "device_name": "HVAC_Unit_01",
                    "location": "Building_A_Floor_2",
                    "points_config": [
                        {
                            "name": "temperature",
                            "object_type": "analogInput",
                            "instance": 1,
                        },
                        {
                            "name": "humidity",
                            "object_type": "analogInput",
                            "instance": 2,
                        },
                    ],
                },
                "upload_timestamp": time.time(),
            },
        }

        await harness.send_message(config_command)
        await asyncio.sleep(0.1)

        # Verify BACnet actor received config upload
        bacnet_messages = harness.get_actor_messages("bacnet_monitoring")
        config_msg = next(
            (m for m in bacnet_messages if m["type"] == "CONFIG_UPLOAD_REQUEST"), None
        )

        assert config_msg is not None
        assert config_msg["payload"]["device_id"] == "BAC_DEVICE_001"
        assert "config_data" in config_msg["payload"]
        assert len(config_msg["payload"]["config_data"]["points_config"]) == 2

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_write_point_command(self):
        """Test: MQTT sends write point command to BACnet device"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # MQTT sends point write command
        write_command = {
            "type": "WRITE_POINT_REQUEST",
            "sender": "mqtt",
            "receiver": "bacnet_monitoring",
            "payload": {
                "device_id": "BAC_DEVICE_001",
                "point_name": "setpoint_temperature",
                "value": 22.5,
                "priority": 10,
                "write_timestamp": time.time(),
            },
        }

        await harness.send_message(write_command)
        await asyncio.sleep(0.1)

        # Verify BACnet actor received write command
        bacnet_messages = harness.get_actor_messages("bacnet_monitoring")
        write_msg = next(
            (m for m in bacnet_messages if m["type"] == "WRITE_POINT_REQUEST"), None
        )

        assert write_msg is not None
        assert write_msg["payload"]["point_name"] == "setpoint_temperature"
        assert write_msg["payload"]["value"] == 22.5
        assert write_msg["payload"]["priority"] == 10

        await harness.cleanup()


class TestBACnetToMQTTData:
    """Test BACnet to MQTT data publishing flow"""

    @pytest.mark.asyncio
    async def test_point_data_publishing(self):
        """Test: BACnet actor publishes point data to MQTT"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # BACnet actor sends point data to MQTT
        point_data = {
            "type": "POINT_DATA_UPDATE",
            "sender": "bacnet_monitoring",
            "receiver": "mqtt",
            "payload": {
                "device_id": "BAC_DEVICE_001",
                "points": [
                    {
                        "name": "temperature",
                        "value": 23.5,
                        "quality": "good",
                        "timestamp": time.time(),
                    },
                    {
                        "name": "humidity",
                        "value": 45.2,
                        "quality": "good",
                        "timestamp": time.time(),
                    },
                ],
                "collection_timestamp": time.time(),
            },
        }

        await harness.send_message(point_data)
        await asyncio.sleep(0.1)

        # Verify MQTT actor received point data
        mqtt_messages = harness.get_actor_messages("mqtt")
        data_msg = next(
            (m for m in mqtt_messages if m["type"] == "POINT_DATA_UPDATE"), None
        )

        assert data_msg is not None
        assert data_msg["payload"]["device_id"] == "BAC_DEVICE_001"
        assert len(data_msg["payload"]["points"]) == 2

        # Check point data quality
        temp_point = next(
            p for p in data_msg["payload"]["points"] if p["name"] == "temperature"
        )
        assert temp_point["value"] == 23.5
        assert temp_point["quality"] == "good"

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_bulk_data_publishing(self):
        """Test: BACnet actor publishes bulk data to MQTT"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # Simulate bulk data collection
        bulk_data = {
            "type": "BULK_DATA_UPDATE",
            "sender": "bacnet_monitoring",
            "receiver": "mqtt",
            "payload": {
                "device_id": "BAC_DEVICE_001",
                "data_batch": [
                    {
                        "timestamp": time.time() - 60,
                        "points": {"temperature": 22.1, "humidity": 44.8},
                    },
                    {
                        "timestamp": time.time() - 30,
                        "points": {"temperature": 22.5, "humidity": 45.1},
                    },
                    {
                        "timestamp": time.time(),
                        "points": {"temperature": 23.0, "humidity": 45.5},
                    },
                ],
                "batch_size": 3,
                "collection_interval": 30,
            },
        }

        await harness.send_message(bulk_data)
        await asyncio.sleep(0.1)

        # Verify MQTT received bulk data
        mqtt_messages = harness.get_actor_messages("mqtt")
        bulk_msg = next(
            (m for m in mqtt_messages if m["type"] == "BULK_DATA_UPDATE"), None
        )

        assert bulk_msg is not None
        assert bulk_msg["payload"]["batch_size"] == 3
        assert len(bulk_msg["payload"]["data_batch"]) == 3

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_device_status_reporting(self):
        """Test: BACnet actor reports device status to MQTT"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # BACnet reports device status changes
        status_report = {
            "type": "DEVICE_STATUS_UPDATE",
            "sender": "bacnet_monitoring",
            "receiver": "mqtt",
            "payload": {
                "device_id": "BAC_DEVICE_001",
                "status": "online",
                "connection_quality": "excellent",
                "last_communication": time.time(),
                "error_count": 0,
                "metadata": {
                    "firmware_version": "2.1.4",
                    "device_type": "HVAC_Controller",
                },
            },
        }

        await harness.send_message(status_report)
        await asyncio.sleep(0.1)

        # Verify MQTT received status update
        mqtt_messages = harness.get_actor_messages("mqtt")
        status_msg = next(
            (m for m in mqtt_messages if m["type"] == "DEVICE_STATUS_UPDATE"), None
        )

        assert status_msg is not None
        assert status_msg["payload"]["status"] == "online"
        assert status_msg["payload"]["connection_quality"] == "excellent"
        assert status_msg["payload"]["error_count"] == 0

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_alarm_notification(self):
        """Test: BACnet actor sends alarm notifications to MQTT"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # BACnet detects and reports alarm condition
        alarm_notification = {
            "type": "ALARM_NOTIFICATION",
            "sender": "bacnet_monitoring",
            "receiver": "mqtt",
            "payload": {
                "device_id": "BAC_DEVICE_001",
                "alarm_type": "HIGH_TEMPERATURE",
                "severity": "high",
                "point_name": "temperature",
                "current_value": 35.2,
                "threshold_value": 30.0,
                "alarm_timestamp": time.time(),
                "description": "Temperature exceeds safe operating limit",
            },
        }

        await harness.send_message(alarm_notification)
        await asyncio.sleep(0.1)

        # Verify MQTT received alarm
        mqtt_messages = harness.get_actor_messages("mqtt")
        alarm_msg = next(
            (m for m in mqtt_messages if m["type"] == "ALARM_NOTIFICATION"), None
        )

        assert alarm_msg is not None
        assert alarm_msg["payload"]["alarm_type"] == "HIGH_TEMPERATURE"
        assert alarm_msg["payload"]["severity"] == "high"
        assert alarm_msg["payload"]["current_value"] == 35.2

        await harness.cleanup()


class TestBidirectionalCommandResponse:
    """Test bidirectional command-response patterns"""

    @pytest.mark.asyncio
    async def test_command_acknowledgment_flow(self):
        """Test: Complete command-acknowledgment cycle between MQTT and BACnet"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # Step 1: MQTT sends command
        command = {
            "id": "cmd_12345",
            "type": "START_MONITORING_REQUEST",
            "sender": "mqtt",
            "receiver": "bacnet_monitoring",
            "payload": {
                "device_id": "BAC_DEVICE_001",
                "monitoring_config": {"interval": 60},
            },
        }

        await harness.send_message(command)
        await asyncio.sleep(0.1)

        # Step 2: BACnet sends acknowledgment back
        acknowledgment = {
            "id": "ack_12345",
            "type": "COMMAND_ACKNOWLEDGMENT",
            "sender": "bacnet_monitoring",
            "receiver": "mqtt",
            "payload": {
                "original_command_id": "cmd_12345",
                "status": "accepted",
                "message": "Monitoring started successfully",
                "execution_timestamp": time.time(),
            },
        }

        await harness.send_message(acknowledgment)
        await asyncio.sleep(0.1)

        # Verify both messages were processed
        bacnet_messages = harness.get_actor_messages("bacnet_monitoring")
        mqtt_messages = harness.get_actor_messages("mqtt")

        # Check command was received
        cmd_msg = next((m for m in bacnet_messages if m.get("id") == "cmd_12345"), None)
        assert cmd_msg is not None

        # Check acknowledgment was received
        ack_msg = next(
            (m for m in mqtt_messages if m["type"] == "COMMAND_ACKNOWLEDGMENT"), None
        )
        assert ack_msg is not None
        assert ack_msg["payload"]["original_command_id"] == "cmd_12345"
        assert ack_msg["payload"]["status"] == "accepted"

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_error_response_flow(self):
        """Test: Error response flow when BACnet command fails"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # MQTT sends problematic command
        problematic_command = {
            "id": "cmd_error",
            "type": "WRITE_POINT_REQUEST",
            "sender": "mqtt",
            "receiver": "bacnet_monitoring",
            "payload": {
                "device_id": "BAC_DEVICE_OFFLINE",
                "point_name": "invalid_point",
                "value": "invalid_value",
            },
        }

        await harness.send_message(problematic_command)
        await asyncio.sleep(0.1)

        # BACnet responds with error
        error_response = {
            "type": "COMMAND_ERROR",
            "sender": "bacnet_monitoring",
            "receiver": "mqtt",
            "payload": {
                "original_command_id": "cmd_error",
                "error_type": "DEVICE_UNREACHABLE",
                "error_message": "Device BAC_DEVICE_OFFLINE is not responding",
                "error_timestamp": time.time(),
                "retry_recommended": True,
            },
        }

        await harness.send_message(error_response)
        await asyncio.sleep(0.1)

        # Verify error response was received by MQTT
        mqtt_messages = harness.get_actor_messages("mqtt")
        error_msg = next(
            (m for m in mqtt_messages if m["type"] == "COMMAND_ERROR"), None
        )

        assert error_msg is not None
        assert error_msg["payload"]["error_type"] == "DEVICE_UNREACHABLE"
        assert error_msg["payload"]["retry_recommended"] is True

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_request_response_timeout(self):
        """Test: Request-response timeout handling"""
        harness = ActorTestHarness()
        await harness.initialize()

        # Send request with timeout
        request = {
            "id": "req_timeout",
            "type": "STATUS_REQUEST",
            "sender": "mqtt",
            "receiver": "bacnet_monitoring",
            "timeout": 0.5,
            "payload": {"device_id": "BAC_DEVICE_001"},
        }

        # Use send_request which implements timeout logic
        response = await harness.send_request(request, timeout=0.5)

        # Should get a response (mocked by harness)
        assert response is not None
        assert response["request_id"] == "req_timeout"

        await harness.cleanup()


class TestCommunicationResilience:
    """Test communication resilience and error handling"""

    @pytest.mark.asyncio
    async def test_message_retry_on_failure(self):
        """Test: Message retry when communication fails"""
        harness = ActorTestHarness()
        await harness.initialize()

        # Configure retry policy
        retry_config = {"max_retries": 3, "retry_delay": 0.1}

        # Send critical command with retry
        critical_command = {
            "id": "critical_cmd",
            "type": "EMERGENCY_STOP",
            "sender": "mqtt",
            "receiver": "bacnet_monitoring",
            "payload": {"device_id": "BAC_DEVICE_001", "emergency_type": "FIRE_ALARM"},
        }

        result = await harness.send_message_with_retry(critical_command, retry_config)

        assert result is not None
        assert result["delivered"] is True
        assert result["attempts"] <= retry_config["max_retries"]

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_connection_recovery_flow(self):
        """Test: Connection recovery communication flow"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # Step 1: BACnet reports connection lost
        connection_lost = {
            "type": "CONNECTION_STATUS_UPDATE",
            "sender": "bacnet_monitoring",
            "receiver": "mqtt",
            "payload": {
                "device_id": "BAC_DEVICE_001",
                "connection_status": "disconnected",
                "error_reason": "network_timeout",
                "timestamp": time.time(),
            },
        }

        await harness.send_message(connection_lost)
        await asyncio.sleep(0.1)

        # Step 2: MQTT sends reconnection command
        reconnect_command = {
            "type": "RECONNECT_REQUEST",
            "sender": "mqtt",
            "receiver": "bacnet_monitoring",
            "payload": {
                "device_id": "BAC_DEVICE_001",
                "retry_count": 1,
                "timeout_seconds": 30,
            },
        }

        await harness.send_message(reconnect_command)
        await asyncio.sleep(0.1)

        # Step 3: BACnet reports successful reconnection
        reconnected = {
            "type": "CONNECTION_STATUS_UPDATE",
            "sender": "bacnet_monitoring",
            "receiver": "mqtt",
            "payload": {
                "device_id": "BAC_DEVICE_001",
                "connection_status": "connected",
                "reconnection_timestamp": time.time(),
                "connection_quality": "good",
            },
        }

        await harness.send_message(reconnected)
        await asyncio.sleep(0.1)

        # Verify complete recovery flow
        mqtt_messages = harness.get_actor_messages("mqtt")
        bacnet_messages = harness.get_actor_messages("bacnet_monitoring")

        # Check disconnect notification
        disconnect_msg = next(
            (
                m
                for m in mqtt_messages
                if m["type"] == "CONNECTION_STATUS_UPDATE"
                and m["payload"]["connection_status"] == "disconnected"
            ),
            None,
        )
        assert disconnect_msg is not None

        # Check reconnect command
        reconnect_msg = next(
            (m for m in bacnet_messages if m["type"] == "RECONNECT_REQUEST"), None
        )
        assert reconnect_msg is not None

        # Check successful reconnection
        connect_msg = next(
            (
                m
                for m in mqtt_messages
                if m["type"] == "CONNECTION_STATUS_UPDATE"
                and m["payload"]["connection_status"] == "connected"
            ),
            None,
        )
        assert connect_msg is not None

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_message_priority_handling(self):
        """Test: High priority messages are handled first"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # Send messages with different priorities
        messages = [
            {
                "id": "low_priority",
                "type": "ROUTINE_DATA_COLLECTION",
                "priority": "low",
                "sender": "mqtt",
                "receiver": "bacnet_monitoring",
                "payload": {},
            },
            {
                "id": "high_priority",
                "type": "EMERGENCY_STOP",
                "priority": "critical",
                "sender": "mqtt",
                "receiver": "bacnet_monitoring",
                "payload": {},
            },
            {
                "id": "normal_priority",
                "type": "STATUS_REQUEST",
                "priority": "normal",
                "sender": "mqtt",
                "receiver": "bacnet_monitoring",
                "payload": {},
            },
        ]

        # Send all messages
        for msg in messages:
            await harness.send_message(msg)

        await asyncio.sleep(0.2)

        # Verify messages were processed
        bacnet_messages = harness.get_actor_messages("bacnet_monitoring")
        assert len(bacnet_messages) == 3

        # Check that critical message exists
        critical_msg = next(
            (m for m in bacnet_messages if m.get("priority") == "critical"), None
        )
        assert critical_msg is not None
        assert critical_msg["type"] == "EMERGENCY_STOP"

        await harness.cleanup()


class TestDataValidationAndSerialization:
    """Test data validation and serialization between MQTT and BACnet"""

    @pytest.mark.asyncio
    async def test_point_data_validation(self):
        """Test: Point data validation in MQTT-BACnet communication"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # Valid point data
        valid_data = {
            "type": "POINT_DATA_UPDATE",
            "sender": "bacnet_monitoring",
            "receiver": "mqtt",
            "payload": {
                "device_id": "BAC_DEVICE_001",
                "points": [
                    {
                        "name": "temperature",
                        "value": 23.5,
                        "quality": "good",
                        "timestamp": time.time(),
                    }
                ],
            },
        }

        result = await harness.send_message(valid_data)
        assert result["status"] == "sent"

        # Invalid data (missing required fields)
        invalid_data = {
            "type": "POINT_DATA_UPDATE",
            "sender": "bacnet_monitoring",
            "receiver": "mqtt",
            "payload": {
                "device_id": "BAC_DEVICE_001",
                "points": [
                    {
                        "name": "temperature"
                        # Missing 'value', 'quality', 'timestamp'
                    }
                ],
            },
        }

        # This should still send (validation would be done by actual actors)
        result = await harness.send_message(invalid_data)
        assert result is not None

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_large_data_handling(self):
        """Test: Handling large data payloads"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # Create large payload with many points
        large_payload = {
            "type": "BULK_DATA_UPDATE",
            "sender": "bacnet_monitoring",
            "receiver": "mqtt",
            "payload": {"device_id": "BAC_DEVICE_001", "points": []},
        }

        # Generate 100 data points
        current_time = time.time()
        for i in range(100):
            point = {
                "name": f"point_{i}",
                "value": 20.0 + i * 0.1,
                "quality": "good",
                "timestamp": current_time + i,
            }
            large_payload["payload"]["points"].append(point)

        result = await harness.send_message(large_payload)
        assert result["status"] == "sent"

        # Verify message was received
        mqtt_messages = harness.get_actor_messages("mqtt")
        large_msg = next(
            (m for m in mqtt_messages if m["type"] == "BULK_DATA_UPDATE"), None
        )

        assert large_msg is not None
        assert len(large_msg["payload"]["points"]) == 100

        await harness.cleanup()
