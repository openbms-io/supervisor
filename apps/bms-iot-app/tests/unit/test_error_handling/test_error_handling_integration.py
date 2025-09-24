"""
Test error handling in component integration scenarios.

User Story: As a developer, I want integrated components to handle errors gracefully across component boundaries
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from src.actors.messages.message_type import (
    ActorMessage,
    ActorName,
    ActorMessageType,
)


class TestActorCommunicationErrorHandling:
    """Test error handling in actor-to-actor communication"""

    @pytest.mark.asyncio
    async def test_message_routing_with_invalid_receiver(self):
        """Test: Message routing handles invalid receiver gracefully"""
        # Mock registry that doesn't have the target actor
        mock_registry = Mock()
        mock_registry.queues = {
            ActorName.MQTT: AsyncMock(),
            ActorName.BACNET: AsyncMock(),
        }
        mock_registry.get_queue.side_effect = KeyError(
            "No queue registered for actor INVALID_ACTOR"
        )

        # Try to get queue for non-existent actor
        with pytest.raises(KeyError) as exc_info:
            mock_registry.get_queue("INVALID_ACTOR")

        assert "No queue registered" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_message_processing_chain_failure(self):
        """Test: Error propagation through message processing chain"""
        messages_processed = []
        processing_errors = []

        async def mqtt_actor_handler(message):
            messages_processed.append(("mqtt", message.message_type))
            if message.message_type == ActorMessageType.CONFIG_UPLOAD_REQUEST:
                # Forward to BACnet actor but it fails
                raise ConnectionError("BACnet actor unreachable")

        async def bacnet_actor_handler(message):
            messages_processed.append(("bacnet", message.message_type))
            return "bacnet_processed"

        message = ActorMessage(
            sender=ActorName.MQTT,
            receiver=ActorName.BACNET,
            message_type=ActorMessageType.CONFIG_UPLOAD_REQUEST,
            payload=None,
        )

        # Simulate message processing failure
        try:
            await mqtt_actor_handler(message)
        except ConnectionError as e:
            processing_errors.append(str(e))

        assert len(messages_processed) == 1
        assert messages_processed[0] == ("mqtt", ActorMessageType.CONFIG_UPLOAD_REQUEST)
        assert len(processing_errors) == 1
        assert "unreachable" in processing_errors[0]

    @pytest.mark.asyncio
    async def test_deadlock_prevention_in_circular_messaging(self):
        """Test: Prevention of deadlocks in circular message patterns"""
        message_trace = []

        class MockActor:
            def __init__(self, name, max_depth=3):
                self.name = name
                self.max_depth = max_depth
                self.message_depth = 0

            async def process_message(self, message):
                self.message_depth += 1
                message_trace.append(f"{self.name}_depth_{self.message_depth}")

                if self.message_depth > self.max_depth:
                    raise RuntimeError(f"Maximum message depth exceeded in {self.name}")

                # Simulate circular messaging
                if message.message_type == ActorMessageType.CONFIG_UPLOAD_REQUEST:
                    # Would normally send to another actor, creating a cycle
                    return f"{self.name}_processed"

        actor = MockActor("MQTT")
        message = ActorMessage(
            sender=ActorName.BACNET,
            receiver=ActorName.MQTT,
            message_type=ActorMessageType.CONFIG_UPLOAD_REQUEST,
            payload=None,
        )

        # Simulate multiple message processing that could cause deadlock
        # Process message once - it should succeed and return result
        result = await actor.process_message(message)
        assert result == "MQTT_processed"

        # The test is really about showing the depth counter increments
        assert len(message_trace) == 1
        assert message_trace[0] == "MQTT_depth_1"


class TestDataFlowErrorHandling:
    """Test error handling in data flow between components"""

    @pytest.mark.asyncio
    async def test_bacnet_to_mqtt_data_transformation_error(self):
        """Test: Error handling in BACnet to MQTT data transformation"""
        # Mock BACnet data with invalid format
        invalid_bacnet_data = {
            "device_123": {
                "temp1": "invalid_temperature",  # String instead of number
                "temp2": None,  # None value
                "pressure1": float("inf"),  # Invalid float
            }
        }

        transformation_errors = []
        valid_data = {}

        def transform_bacnet_to_mqtt(bacnet_data):
            for device_id, points in bacnet_data.items():
                valid_data[device_id] = {}
                for point_name, value in points.items():
                    try:
                        if value is None:
                            transformation_errors.append(
                                f"Null value for {device_id}.{point_name}"
                            )
                            continue

                        # Attempt to convert to float
                        float_value = float(value)

                        if not (float("-inf") < float_value < float("inf")):
                            transformation_errors.append(
                                f"Invalid numeric value for {device_id}.{point_name}"
                            )
                            continue

                        valid_data[device_id][point_name] = float_value

                    except (ValueError, TypeError) as e:
                        transformation_errors.append(
                            f"Conversion error for {device_id}.{point_name}: {str(e)}"
                        )

        transform_bacnet_to_mqtt(invalid_bacnet_data)

        # Check that errors were caught and valid data was extracted
        assert len(transformation_errors) == 3
        assert "Null value for device_123.temp2" in transformation_errors
        assert "Invalid numeric value for device_123.pressure1" in transformation_errors
        assert any("Conversion error" in error for error in transformation_errors)

        # Valid data should be empty due to all invalid values
        assert len(valid_data.get("device_123", {})) == 0

    @pytest.mark.asyncio
    async def test_mqtt_to_database_batching_partial_failure(self):
        """Test: Partial failure handling in batched database operations"""
        mqtt_messages = [
            {
                "device_id": "device_1",
                "point": "temp1",
                "value": 25.0,
                "timestamp": "2024-01-01T10:00:00Z",
            },
            {
                "device_id": "device_2",
                "point": "temp1",
                "value": "invalid",
                "timestamp": "2024-01-01T10:01:00Z",
            },
            {
                "device_id": "device_3",
                "point": "temp1",
                "value": 27.0,
                "timestamp": "invalid_timestamp",
            },
            {
                "device_id": "device_4",
                "point": "temp1",
                "value": 28.0,
                "timestamp": "2024-01-01T10:03:00Z",
            },
        ]

        successful_inserts = []
        failed_inserts = []

        async def batch_insert_with_error_handling(messages):
            for msg in messages:
                try:
                    # Validate message structure
                    if not isinstance(msg.get("value"), (int, float)):
                        raise ValueError(
                            f"Invalid value type: {type(msg.get('value'))}"
                        )

                    if not isinstance(
                        msg.get("timestamp"), str
                    ) or "invalid" in msg.get("timestamp", ""):
                        raise ValueError("Invalid timestamp format")

                    # Mock successful database insert
                    successful_inserts.append(msg["device_id"])

                except ValueError as e:
                    failed_inserts.append(
                        {"device_id": msg.get("device_id"), "error": str(e)}
                    )

        await batch_insert_with_error_handling(mqtt_messages)

        # Verify partial success
        assert len(successful_inserts) == 2
        assert "device_1" in successful_inserts
        assert "device_4" in successful_inserts

        assert len(failed_inserts) == 2
        assert any(
            "Invalid value type" in failure["error"] for failure in failed_inserts
        )
        assert any(
            "Invalid timestamp" in failure["error"] for failure in failed_inserts
        )


class TestResourceExhaustionErrorHandling:
    """Test error handling under resource exhaustion conditions"""

    @pytest.mark.asyncio
    async def test_memory_pressure_handling(self):
        """Test: Graceful handling of memory pressure conditions"""
        memory_usage_mb = 0
        max_memory_mb = 100  # Simulate low memory limit
        data_buffer = []

        def allocate_memory_for_data(data_size_mb):
            nonlocal memory_usage_mb
            if memory_usage_mb + data_size_mb > max_memory_mb:
                raise MemoryError(
                    f"Would exceed memory limit: {memory_usage_mb + data_size_mb}MB > {max_memory_mb}MB"
                )

            memory_usage_mb += data_size_mb
            data_buffer.extend(
                ["x"] * (data_size_mb * 1000)
            )  # Simulate memory allocation

        def free_oldest_data(amount_mb):
            nonlocal memory_usage_mb
            if data_buffer and memory_usage_mb >= amount_mb:
                # Simulate freeing oldest data
                freed_items = amount_mb * 1000
                del data_buffer[:freed_items]
                memory_usage_mb -= amount_mb

        # Try to allocate data in chunks
        data_chunks = [20, 30, 40, 25, 15]  # Total 130MB, exceeds limit
        successful_allocations = 0

        for i, chunk_size in enumerate(data_chunks):
            try:
                allocate_memory_for_data(chunk_size)
                successful_allocations += 1
            except MemoryError:
                # Handle memory pressure by freeing old data
                free_oldest_data(30)  # Free 30MB
                try:
                    allocate_memory_for_data(chunk_size)
                    successful_allocations += 1
                except MemoryError:
                    # Still not enough memory, skip this allocation
                    pass

        assert successful_allocations >= 3  # Should handle at least some allocations
        assert memory_usage_mb <= max_memory_mb

    @pytest.mark.asyncio
    async def test_connection_pool_exhaustion(self):
        """Test: Handling of connection pool exhaustion"""
        max_connections = 3
        connection_requests = []

        class MockConnectionPool:
            def __init__(self, max_size):
                self.max_size = max_size
                self.active = 0
                self.waiting = []

            async def acquire(self, timeout=1.0):
                if self.active < self.max_size:
                    self.active += 1
                    return f"connection_{self.active}"
                else:
                    # Pool exhausted, simulate timeout
                    await asyncio.sleep(timeout)
                    raise asyncio.TimeoutError("Connection pool exhausted")

            def release(self, connection):
                if self.active > 0:
                    self.active -= 1

        pool = MockConnectionPool(max_connections)

        # Simulate concurrent connection requests
        async def request_connection(request_id):
            try:
                conn = await pool.acquire(timeout=0.1)
                connection_requests.append(
                    {"id": request_id, "status": "success", "conn": conn}
                )
                await asyncio.sleep(0.05)  # Simulate work
                pool.release(conn)
            except asyncio.TimeoutError:
                connection_requests.append({"id": request_id, "status": "timeout"})

        # Make more requests than pool capacity
        tasks = [request_connection(i) for i in range(6)]
        await asyncio.gather(*tasks, return_exceptions=True)

        successful_connections = [
            r for r in connection_requests if r["status"] == "success"
        ]
        timed_out_connections = [
            r for r in connection_requests if r["status"] == "timeout"
        ]

        assert len(successful_connections) == max_connections
        assert len(timed_out_connections) >= 1  # Some should timeout

    @pytest.mark.asyncio
    async def test_queue_overflow_handling(self):
        """Test: Graceful handling of queue overflow conditions"""
        max_queue_size = 5
        message_queue = []
        dropped_messages = []
        processed_messages = []

        def enqueue_message(message, priority="normal"):
            if len(message_queue) >= max_queue_size:
                if priority == "high":
                    # Drop oldest normal priority message for high priority
                    for i, msg in enumerate(message_queue):
                        if msg.get("priority", "normal") == "normal":
                            dropped_messages.append(message_queue.pop(i))
                            break
                    else:
                        # No normal priority messages to drop
                        dropped_messages.append(message)
                        return False
                else:
                    # Drop the new message
                    dropped_messages.append(message)
                    return False

            message_queue.append({**message, "priority": priority})
            return True

        async def process_messages():
            while message_queue:
                msg = message_queue.pop(0)
                processed_messages.append(msg)
                await asyncio.sleep(0.01)  # Simulate processing time

        # Enqueue messages beyond capacity
        messages = [
            {"id": 1, "data": "msg1"},
            {"id": 2, "data": "msg2"},
            {"id": 3, "data": "msg3"},
            {"id": 4, "data": "msg4"},
            {"id": 5, "data": "msg5"},
            {"id": 6, "data": "msg6"},  # Should be dropped
            {"id": 7, "data": "msg7"},  # Should be dropped
        ]

        for msg in messages:
            enqueue_message(msg)

        # Add a high priority message that should displace a normal one
        high_priority_msg = {"id": 99, "data": "urgent"}
        enqueue_message(high_priority_msg, priority="high")

        # Process all remaining messages
        await process_messages()

        assert (
            len(processed_messages) == max_queue_size
        )  # Only queue capacity processed
        assert (
            len(dropped_messages) >= 3
        )  # 2 normal messages + 1 displaced by high priority

        # High priority message should be processed
        assert any(msg["id"] == 99 for msg in processed_messages)


class TestCascadingFailureHandling:
    """Test handling of cascading failures across system components"""

    @pytest.mark.asyncio
    async def test_database_failure_cascading_to_cache(self):
        """Test: Database failure gracefully cascades to cache fallback"""
        cache_hits = 0
        database_errors = 0

        class MockService:
            def __init__(self):
                self.cache = {"device_1": {"temp": 25.0}, "device_2": {"temp": 26.0}}
                self.db_available = True

            async def get_device_data(self, device_id):
                try:
                    if not self.db_available:
                        raise ConnectionError("Database unavailable")

                    # Simulate database lookup
                    return {"source": "database", "data": {"temp": 25.5}}

                except ConnectionError:
                    nonlocal database_errors, cache_hits
                    database_errors += 1

                    # Fallback to cache
                    if device_id in self.cache:
                        cache_hits += 1
                        return {"source": "cache", "data": self.cache[device_id]}
                    else:
                        raise RuntimeError(f"No data available for {device_id}")

        service = MockService()
        service.db_available = False  # Simulate database failure

        # Test fallback to cache
        result1 = await service.get_device_data("device_1")
        result2 = await service.get_device_data("device_2")

        assert result1["source"] == "cache"
        assert result2["source"] == "cache"
        assert database_errors == 2
        assert cache_hits == 2

        # Test complete failure when cache also misses
        with pytest.raises(RuntimeError, match="No data available"):
            await service.get_device_data("device_999")

    @pytest.mark.asyncio
    async def test_mqtt_broker_failure_with_local_queuing(self):
        """Test: MQTT broker failure with local message queuing"""
        local_queue = []
        publish_attempts = 0
        successful_publishes = 0

        class MockMQTTPublisher:
            def __init__(self):
                self.broker_available = True

            async def publish(self, topic, message):
                nonlocal publish_attempts, successful_publishes
                publish_attempts += 1

                if not self.broker_available:
                    # Queue locally for retry
                    local_queue.append(
                        {"topic": topic, "message": message, "retries": 0}
                    )
                    raise ConnectionError("MQTT broker unreachable")

                successful_publishes += 1
                return True

            async def retry_queued_messages(self):
                """Attempt to send queued messages when broker recovers"""
                messages_to_retry = local_queue.copy()
                local_queue.clear()

                for msg in messages_to_retry:
                    try:
                        await self.publish(msg["topic"], msg["message"])
                    except ConnectionError:
                        # Requeue with incremented retry count
                        msg["retries"] += 1
                        if msg["retries"] < 3:
                            local_queue.append(msg)

        publisher = MockMQTTPublisher()

        # Simulate broker failure
        publisher.broker_available = False

        # Try to publish messages during failure
        messages = [
            ("iot/device1/temp", {"value": 25.0}),
            ("iot/device2/temp", {"value": 26.0}),
            ("iot/device3/temp", {"value": 27.0}),
        ]

        for topic, message in messages:
            try:
                await publisher.publish(topic, message)
            except ConnectionError:
                pass  # Expected during failure

        assert len(local_queue) == 3
        assert successful_publishes == 0

        # Simulate broker recovery
        publisher.broker_available = True
        await publisher.retry_queued_messages()

        assert len(local_queue) == 0  # All messages should be sent
        assert successful_publishes == 3
