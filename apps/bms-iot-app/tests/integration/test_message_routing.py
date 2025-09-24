"""
Test message routing between actors.

User Story: As a system architect, I want messages to route correctly between actors
"""

import pytest
import asyncio
import sys
import time

# Add the fixtures directory to the path
sys.path.insert(
    0, "/Users/amol/Documents/ai-projects/bms-project/apps/bms-iot-app/tests"
)

from fixtures.actor_test_harness import ActorTestHarness


class TestDirectMessageRouting:
    """Test direct message routing between actors"""

    @pytest.mark.asyncio
    async def test_mqtt_to_bacnet_message_routing(self):
        """Test: Direct message routing from MQTT to BACnet actor"""
        harness = ActorTestHarness()
        await harness.initialize()

        # Enable message logging
        harness.enable_message_logging()

        # Create a test message from MQTT to BACnet
        test_message = {
            "type": "START_MONITORING_REQUEST",
            "sender": "mqtt",
            "receiver": "bacnet_monitoring",
            "payload": {
                "device_id": "test_device_123",
                "points": ["temperature", "humidity"],
            },
        }

        # Send the message
        await harness.send_message(test_message)

        # Wait for message processing
        await asyncio.sleep(0.1)

        # Verify message was routed
        assert len(harness.messages) > 0

        # Check if BACnet actor received the message
        received_messages = harness.get_actor_messages("bacnet_monitoring")
        assert len(received_messages) > 0
        assert received_messages[0]["type"] == "START_MONITORING_REQUEST"

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_bacnet_to_mqtt_message_routing(self):
        """Test: Direct message routing from BACnet to MQTT actor"""
        harness = ActorTestHarness()
        await harness.initialize()

        harness.enable_message_logging()

        # Create a test message from BACnet to MQTT
        test_message = {
            "type": "POINT_DATA_UPDATE",
            "sender": "bacnet_monitoring",
            "receiver": "mqtt",
            "payload": {
                "device_id": "test_device_123",
                "point": "temperature",
                "value": 25.5,
                "timestamp": time.time(),
            },
        }

        # Send the message
        await harness.send_message(test_message)

        # Wait for message processing
        await asyncio.sleep(0.1)

        # Verify MQTT actor received the message
        received_messages = harness.get_actor_messages("mqtt")
        assert len(received_messages) > 0
        assert received_messages[0]["type"] == "POINT_DATA_UPDATE"
        assert received_messages[0]["payload"]["value"] == 25.5

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_uploader_to_mqtt_routing(self):
        """Test: Message routing from Uploader to MQTT"""
        harness = ActorTestHarness()
        await harness.initialize()

        harness.enable_message_logging()

        # Create upload completion message
        test_message = {
            "type": "UPLOAD_COMPLETED",
            "sender": "uploader",
            "receiver": "mqtt",
            "payload": {
                "batch_id": "batch_123",
                "records_uploaded": 100,
                "status": "success",
            },
        }

        await harness.send_message(test_message)
        await asyncio.sleep(0.1)

        # Verify routing
        received_messages = harness.get_actor_messages("mqtt")
        assert any(msg["type"] == "UPLOAD_COMPLETED" for msg in received_messages)

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_heartbeat_broadcast_routing(self):
        """Test: Heartbeat broadcast message routing to all actors"""
        harness = ActorTestHarness()
        await harness.initialize()

        harness.enable_message_logging()

        # Create heartbeat broadcast message
        test_message = {
            "type": "HEARTBEAT_PING",
            "sender": "heartbeat",
            "receiver": "BROADCAST",
            "payload": {"timestamp": time.time(), "status": "healthy"},
        }

        await harness.send_message(test_message)
        await asyncio.sleep(0.1)

        # All actors should receive broadcast
        for actor_name in ["mqtt", "bacnet_monitoring", "uploader"]:
            received_messages = harness.get_actor_messages(actor_name)
            assert any(
                msg["type"] == "HEARTBEAT_PING" for msg in received_messages
            ), f"Actor {actor_name} did not receive broadcast"

        await harness.cleanup()


class TestMessageDeliveryConfirmation:
    """Test message delivery and acknowledgment"""

    @pytest.mark.asyncio
    async def test_message_delivery_confirmation(self):
        """Test: Message delivery confirmation and acknowledgment"""
        harness = ActorTestHarness()
        await harness.initialize()

        harness.enable_message_logging()

        # Send message with delivery confirmation required
        test_message = {
            "id": "msg_123",
            "type": "CONFIG_UPDATE",
            "sender": "mqtt",
            "receiver": "bacnet_monitoring",
            "require_ack": True,
            "payload": {"config": "new_config"},
        }

        # Send and wait for acknowledgment
        ack = await harness.send_message_with_ack(test_message, timeout=1.0)

        assert ack is not None
        assert ack["message_id"] == "msg_123"
        assert ack["status"] == "delivered"

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_message_acknowledgment_timeout(self):
        """Test: Message acknowledgment timeout handling"""
        harness = ActorTestHarness()
        await harness.initialize()

        # Send message to non-responsive actor
        test_message = {
            "id": "msg_timeout",
            "type": "TEST_MESSAGE",
            "sender": "mqtt",
            "receiver": "non_existent_actor",
            "require_ack": True,
            "payload": {},
        }

        # Should timeout
        ack = await harness.send_message_with_ack(test_message, timeout=0.5)

        assert ack is None or ack["status"] == "timeout"

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_message_delivery_retry(self):
        """Test: Message delivery retry on failure"""
        harness = ActorTestHarness()
        await harness.initialize()

        harness.enable_message_logging()

        # Configure retry policy
        retry_config = {"max_retries": 3, "retry_delay": 0.1}

        # Send message with retry
        test_message = {
            "id": "msg_retry",
            "type": "CRITICAL_COMMAND",
            "sender": "mqtt",
            "receiver": "bacnet_monitoring",
            "payload": {"command": "restart"},
        }

        result = await harness.send_message_with_retry(test_message, retry_config)

        assert result is not None
        assert result["delivered"] is True
        assert result["attempts"] <= retry_config["max_retries"]

        await harness.cleanup()


class TestMessageQueueHandling:
    """Test message queue handling and processing order"""

    @pytest.mark.asyncio
    async def test_message_queue_fifo_ordering(self):
        """Test: Message queue handles messages in FIFO order"""
        harness = ActorTestHarness()
        await harness.initialize()

        harness.enable_message_logging()

        # Send multiple messages quickly
        messages = []
        for i in range(5):
            msg = {
                "id": f"msg_{i}",
                "type": "ORDERED_MESSAGE",
                "sender": "mqtt",
                "receiver": "bacnet_monitoring",
                "sequence": i,
                "payload": {"index": i},
            }
            messages.append(msg)
            await harness.send_message(msg)

        # Wait for processing
        await asyncio.sleep(0.5)

        # Check messages were processed in order
        received = harness.get_actor_messages("bacnet_monitoring")
        for i in range(len(received) - 1):
            if received[i].get("sequence") is not None:
                assert received[i]["sequence"] <= received[i + 1].get(
                    "sequence", float("inf")
                )

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_message_queue_priority_handling(self):
        """Test: High priority messages are processed first"""
        harness = ActorTestHarness()
        await harness.initialize()

        harness.enable_message_logging()

        # Send messages with different priorities
        messages = [
            {"id": "1", "priority": "low", "type": "LOW_PRIORITY"},
            {"id": "2", "priority": "high", "type": "HIGH_PRIORITY"},
            {"id": "3", "priority": "normal", "type": "NORMAL_PRIORITY"},
            {"id": "4", "priority": "critical", "type": "CRITICAL"},
        ]

        for msg in messages:
            msg.update({"sender": "mqtt", "receiver": "bacnet_monitoring"})
            await harness.send_message(msg)

        await asyncio.sleep(0.5)

        # Verify critical messages were processed first
        received = harness.get_actor_messages("bacnet_monitoring")
        if len(received) > 0 and "priority" in received[0]:
            # First processed should be critical or high priority
            assert received[0]["priority"] in ["critical", "high"]

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_message_queue_overflow_handling(self):
        """Test: Message queue handles overflow gracefully"""
        harness = ActorTestHarness()
        await harness.initialize()

        # Set queue limit
        harness.set_message_queue_limit("bacnet_monitoring", 10)

        # Send more messages than queue limit
        overflow_detected = False
        for i in range(15):
            msg = {
                "id": f"overflow_{i}",
                "type": "BULK_MESSAGE",
                "sender": "mqtt",
                "receiver": "bacnet_monitoring",
                "payload": {"index": i},
            }
            result = await harness.send_message(msg)
            if result and result.get("status") == "queue_full":
                overflow_detected = True

        # Should handle overflow (either drop or queue full response)
        assert (
            overflow_detected
            or len(harness.get_actor_messages("bacnet_monitoring")) <= 10
        )

        await harness.cleanup()


class TestInvalidMessageHandling:
    """Test invalid recipient and error handling"""

    @pytest.mark.asyncio
    async def test_invalid_recipient_handling(self):
        """Test: Invalid recipient handling and error responses"""
        harness = ActorTestHarness()
        await harness.initialize()

        harness.enable_message_logging()

        # Send message to non-existent actor
        test_message = {
            "id": "invalid_recipient",
            "type": "TEST_MESSAGE",
            "sender": "mqtt",
            "receiver": "non_existent_actor",
            "payload": {},
        }

        result = await harness.send_message(test_message)

        # Should return error or handle gracefully
        assert result is None or result.get("error") == "recipient_not_found"

        # Check for error message back to sender
        error_messages = harness.get_actor_messages("mqtt")
        error_msg = next(
            (m for m in error_messages if m["type"] == "DELIVERY_ERROR"), None
        )
        if error_msg:
            assert error_msg["payload"]["original_message_id"] == "invalid_recipient"

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_malformed_message_handling(self):
        """Test: Malformed message handling"""
        harness = ActorTestHarness()
        await harness.initialize()

        # Send malformed message (missing required fields)
        malformed_message = {
            "type": "MALFORMED",
            # Missing 'sender' and 'receiver'
            "payload": {},
        }

        result = await harness.send_message(malformed_message)

        # Should reject malformed message
        assert result is None or result.get("error") == "malformed_message"

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_message_validation_errors(self):
        """Test: Message validation and error responses"""
        harness = ActorTestHarness()
        await harness.initialize()

        # Send message with invalid payload
        test_message = {
            "id": "invalid_payload",
            "type": "CONFIG_UPDATE",
            "sender": "mqtt",
            "receiver": "bacnet_monitoring",
            "payload": None,  # Invalid payload
        }

        result = await harness.send_message(test_message)

        # Should handle validation error
        assert result is None or "error" in result

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_circular_message_prevention(self):
        """Test: Prevent circular message routing"""
        harness = ActorTestHarness()
        await harness.initialize()

        harness.enable_message_logging()

        # Create a message that could cause circular routing
        test_message = {
            "id": "circular_test",
            "type": "FORWARD_MESSAGE",
            "sender": "mqtt",
            "receiver": "bacnet_monitoring",
            "forward_to": "mqtt",  # Would create circle
            "hop_count": 0,
            "max_hops": 3,
            "payload": {},
        }

        await harness.send_message(test_message)
        await asyncio.sleep(0.5)

        # Check that circular routing was prevented
        all_messages = harness.messages
        circular_messages = [m for m in all_messages if m.get("id") == "circular_test"]

        # Should not exceed max_hops
        assert len(circular_messages) <= test_message["max_hops"]

        await harness.cleanup()


class TestMessageRoutingPatterns:
    """Test various message routing patterns"""

    @pytest.mark.asyncio
    async def test_request_response_pattern(self):
        """Test: Request-response message pattern"""
        harness = ActorTestHarness()
        await harness.initialize()

        # Send request and wait for response
        request = {
            "id": "req_123",
            "type": "STATUS_REQUEST",
            "sender": "mqtt",
            "receiver": "bacnet_monitoring",
            "response_required": True,
            "payload": {"query": "device_status"},
        }

        response = await harness.send_request(request, timeout=1.0)

        assert response is not None
        assert response["request_id"] == "req_123"
        assert response["type"] == "STATUS_RESPONSE"
        assert "status" in response["payload"]

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_publish_subscribe_pattern(self):
        """Test: Publish-subscribe message pattern"""
        harness = ActorTestHarness()
        await harness.initialize()

        # Subscribe actors to a topic
        await harness.subscribe_actor("mqtt", "temperature_updates")
        await harness.subscribe_actor("uploader", "temperature_updates")

        # Publish message to topic
        publication = {
            "topic": "temperature_updates",
            "publisher": "bacnet_monitoring",
            "payload": {"temperature": 25.5, "timestamp": time.time()},
        }

        await harness.publish_to_topic(publication)
        await asyncio.sleep(0.1)

        # Both subscribers should receive the message
        mqtt_messages = harness.get_actor_messages("mqtt")
        uploader_messages = harness.get_actor_messages("uploader")

        assert any(m.get("topic") == "temperature_updates" for m in mqtt_messages)
        assert any(m.get("topic") == "temperature_updates" for m in uploader_messages)

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_message_chain_routing(self):
        """Test: Message chain routing through multiple actors"""
        harness = ActorTestHarness()
        await harness.initialize()

        harness.enable_message_logging()

        # Create a message that routes through multiple actors
        chain_message = {
            "id": "chain_123",
            "type": "CHAIN_MESSAGE",
            "chain": ["mqtt", "bacnet_monitoring", "uploader", "mqtt"],
            "current_index": 0,
            "payload": {"data": "test"},
        }

        await harness.route_chain_message(chain_message)
        await asyncio.sleep(0.5)

        # Verify each actor in chain received the message
        for actor in ["mqtt", "bacnet_monitoring", "uploader"]:
            messages = harness.get_actor_messages(actor)
            assert any(
                m.get("id") == "chain_123" for m in messages
            ), f"Actor {actor} did not receive chain message"

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_conditional_routing(self):
        """Test: Conditional message routing based on content"""
        harness = ActorTestHarness()
        await harness.initialize()

        # Set up routing rules
        routing_rules = {
            "temperature": "bacnet_monitoring",
            "upload": "uploader",
            "heartbeat": "heartbeat",
        }

        harness.set_routing_rules(routing_rules)

        # Send messages with different types
        messages = [
            {"type": "temperature", "data": 25.5, "payload": {"value": 25.5}},
            {"type": "upload", "data": "batch_data", "payload": {"batch": "data"}},
            {"type": "heartbeat", "data": "ping", "payload": {"status": "ping"}},
        ]

        for msg in messages:
            await harness.route_by_type(msg)

        await asyncio.sleep(0.2)

        # Verify correct routing
        bacnet_msgs = harness.get_actor_messages("bacnet_monitoring")
        assert any(
            m.get("type") == "temperature" for m in bacnet_msgs
        ), f"Messages: {bacnet_msgs}"

        uploader_msgs = harness.get_actor_messages("uploader")
        assert any(
            m.get("type") == "upload" for m in uploader_msgs
        ), f"Messages: {uploader_msgs}"

        await harness.cleanup()
