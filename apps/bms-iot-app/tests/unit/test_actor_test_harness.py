"""
Test the ActorTestHarness utility.

User Story: As a developer, I want the ActorTestHarness to work reliably for testing actor interactions.
"""

import pytest
import asyncio
from tests.fixtures.actor_test_harness import ActorTestHarness


def assert_message_sent(harness, sender, receiver, message_type):
    """Helper function to assert a message was sent"""
    messages = harness.get_message_log()
    for msg in messages:
        if (
            msg.sender == sender
            and msg.receiver == receiver
            and msg.message_type == message_type
        ):
            return msg
    return None


def assert_message_payload_contains(message, expected_payload):
    """Helper function to assert message payload contains specific data"""
    if not message:
        raise AssertionError("Message is None")
    payload = (
        message.payload if hasattr(message, "payload") else message.get("payload", {})
    )
    for key, value in expected_payload.items():
        if payload.get(key) != value:
            raise AssertionError(f"Expected {key}={value}, got {payload.get(key)}")
    return True


@pytest.mark.asyncio
async def test_actor_test_harness_setup():
    """Test: ActorTestHarness creates actors without errors"""
    harness = ActorTestHarness()

    await harness.setup_actors(["MQTT", "BACNET", "UPLOADER"])

    assert "MQTT" in harness.actors
    assert "BACNET" in harness.actors
    assert "UPLOADER" in harness.actors

    assert harness.actors["MQTT"].name == "MQTT"
    assert hasattr(harness.actors["MQTT"], "tell")
    assert hasattr(harness.actors["MQTT"], "received_messages")

    await harness.cleanup()


@pytest.mark.asyncio
async def test_send_message_between_actors():
    """Test: Send message between actors and verify receipt"""
    harness = ActorTestHarness()
    await harness.setup_actors(["MQTT", "BACNET"])

    # Send message
    success = await harness.send_message(
        "MQTT", "BACNET", "START_MONITORING", {"device_id": "123"}
    )

    assert success is True

    # Check message was received
    received_messages = harness.get_received_messages("BACNET")
    assert len(received_messages) == 1

    message = received_messages[0]
    assert message["sender"] == "MQTT"
    assert message["receiver"] == "BACNET"
    assert message["message_type"] == "START_MONITORING"
    assert message["payload"]["device_id"] == "123"

    await harness.cleanup()


@pytest.mark.asyncio
async def test_message_logging():
    """Test: Message logging functionality works correctly"""
    harness = ActorTestHarness()
    await harness.setup_actors(["MQTT", "BACNET", "UPLOADER"])

    # Send multiple messages
    await harness.send_message("MQTT", "BACNET", "CONFIG_UPLOAD", {})
    await harness.send_message("BACNET", "UPLOADER", "DATA_UPLOAD", {"data": [1, 2, 3]})

    # Check message log
    assert len(harness.message_log) == 2

    # Check specific messages
    mqtt_to_bacnet = harness.get_messages_between("MQTT", "BACNET")
    assert len(mqtt_to_bacnet) == 1
    assert mqtt_to_bacnet[0].message_type == "CONFIG_UPLOAD"

    bacnet_to_uploader = harness.get_messages_between("BACNET", "UPLOADER")
    assert len(bacnet_to_uploader) == 1
    assert bacnet_to_uploader[0].payload["data"] == [1, 2, 3]

    await harness.cleanup()


@pytest.mark.asyncio
async def test_wait_for_message():
    """Test: wait_for_message timeout functionality"""
    harness = ActorTestHarness()
    await harness.setup_actors(["MQTT", "BACNET"])

    # Send message in background after delay
    async def delayed_send():
        await asyncio.sleep(0.1)
        await harness.send_message("MQTT", "BACNET", "TEST_MESSAGE", {})

    # Start delayed send
    asyncio.create_task(delayed_send())

    # Wait for message (should succeed)
    message = await harness.wait_for_message("BACNET", "TEST_MESSAGE", timeout=0.5)
    assert message is not None
    assert (
        message.get("message_type") == "TEST_MESSAGE"
        or message.get("type") == "TEST_MESSAGE"
    )

    # Wait for non-existent message (should timeout)
    message = await harness.wait_for_message("BACNET", "NON_EXISTENT", timeout=0.1)
    assert message is None

    await harness.cleanup()


@pytest.mark.asyncio
async def test_message_handler_registration():
    """Test: Custom message handlers can be registered and called"""
    harness = ActorTestHarness()
    await harness.setup_actors(["MQTT", "BACNET"])

    # Track handler calls
    handler_calls = []

    async def custom_handler(message):
        handler_calls.append(message)

    # Register handler
    harness.register_message_handler("BACNET", custom_handler)

    # Send message
    await harness.send_message("MQTT", "BACNET", "TEST_MESSAGE", {"test": "data"})

    # Verify handler was called
    assert len(handler_calls) == 1
    assert handler_calls[0]["message_type"] == "TEST_MESSAGE"
    assert handler_calls[0]["payload"]["test"] == "data"

    await harness.cleanup()


@pytest.mark.asyncio
async def test_assert_message_sent_helper():
    """Test: assert_message_sent helper function works correctly"""
    harness = ActorTestHarness()
    await harness.setup_actors(["MQTT", "BACNET"])

    # Send message
    await harness.send_message("MQTT", "BACNET", "TEST_MESSAGE", {"field": "value"})

    # Assert message was sent (should succeed)
    message = assert_message_sent(harness, "MQTT", "BACNET", "TEST_MESSAGE")
    assert message is not None
    assert message.payload["field"] == "value"

    # Test assertion helpers
    assert_message_payload_contains(message, {"field": "value"})

    # Test assertion failure (should raise)
    with pytest.raises(AssertionError):
        assert_message_payload_contains(message, {"missing_field": "value"})

    await harness.cleanup()


@pytest.mark.asyncio
async def test_clear_message_log():
    """Test: Message log clearing works correctly"""
    harness = ActorTestHarness()
    await harness.setup_actors(["MQTT", "BACNET"])

    # Send some messages
    await harness.send_message("MQTT", "BACNET", "MESSAGE1", {})
    await harness.send_message("MQTT", "BACNET", "MESSAGE2", {})

    assert len(harness.message_log) == 2
    assert len(harness.get_received_messages("BACNET")) == 2

    # Clear logs
    harness.clear_message_log()

    assert len(harness.message_log) == 0
    assert len(harness.get_received_messages("BACNET")) == 0

    await harness.cleanup()
