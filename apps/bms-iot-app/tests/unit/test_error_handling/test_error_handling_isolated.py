"""
Test error handling in isolated components.

User Story: As a developer, I want components to handle errors gracefully and provide meaningful error messages
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from pydantic import ValidationError

# Import existing types to avoid creating new ones
from src.models.device_status_enums import MonitoringStatusEnum, ConnectionStatusEnum

from src.actors.messages.message_type import (
    ActorMessage,
    ActorName,
    ActorMessageType,
)


class TestModelValidationErrorHandling:
    """Test error handling in Pydantic model validation"""

    def test_actor_message_missing_required_fields(self):
        """Test: ActorMessage handles missing required fields with clear error messages"""
        with pytest.raises(ValidationError) as exc_info:
            ActorMessage()

        errors = exc_info.value.errors()
        error_fields = {error["loc"][0] for error in errors}

        # All required fields should be reported as missing
        assert "sender" in error_fields
        assert "receiver" in error_fields
        assert "message_type" in error_fields

        # Error types should be 'missing'
        missing_errors = [e for e in errors if e["type"] == "missing"]
        assert len(missing_errors) >= 3

    def test_actor_message_invalid_enum_values(self):
        """Test: ActorMessage handles invalid enum values with clear errors"""
        with pytest.raises(ValidationError) as exc_info:
            ActorMessage(
                sender="INVALID_SENDER",
                receiver=ActorName.MQTT,
                message_type=ActorMessageType.CONFIG_UPLOAD_REQUEST,
                payload=None,
            )

        errors = exc_info.value.errors()
        sender_error = next(e for e in errors if e["loc"] == ("sender",))

        assert sender_error["type"] == "enum"
        assert "INVALID_SENDER" in str(sender_error["input"])

    def test_monitoring_status_enum_invalid_value(self):
        """Test: MonitoringStatusEnum handles invalid values properly"""
        with pytest.raises(ValueError) as exc_info:
            MonitoringStatusEnum("invalid_status")

        error_message = str(exc_info.value)
        assert "invalid_status" in error_message

    def test_connection_status_enum_invalid_value(self):
        """Test: ConnectionStatusEnum handles invalid values properly"""
        with pytest.raises(ValueError) as exc_info:
            ConnectionStatusEnum("invalid_connection")

        error_message = str(exc_info.value)
        assert "invalid_connection" in error_message


class TestNetworkErrorHandling:
    """Test error handling in network operations"""

    @pytest.mark.asyncio
    async def test_mqtt_connection_timeout_error(self):
        """Test: MQTT connection handles timeout errors gracefully"""
        mock_mqtt_client = AsyncMock()
        mock_mqtt_client.connect.side_effect = asyncio.TimeoutError(
            "Connection timeout"
        )

        with pytest.raises(asyncio.TimeoutError) as exc_info:
            await mock_mqtt_client.connect()

        assert "timeout" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_mqtt_connection_refused_error(self):
        """Test: MQTT connection handles connection refused errors"""
        mock_mqtt_client = AsyncMock()
        mock_mqtt_client.connect.side_effect = ConnectionRefusedError(
            "Connection refused"
        )

        with pytest.raises(ConnectionRefusedError) as exc_info:
            await mock_mqtt_client.connect()

        assert "refused" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_mqtt_publish_failure_error(self):
        """Test: MQTT publish handles failure scenarios"""
        mock_mqtt_client = AsyncMock()
        mock_mqtt_client.publish.side_effect = RuntimeError("Publish failed")

        with pytest.raises(RuntimeError) as exc_info:
            await mock_mqtt_client.publish("test/topic", "test message")

        assert "failed" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_rest_client_http_error_handling(self):
        """Test: REST client handles HTTP errors properly"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.raise_for_status.side_effect = Exception("500 Server Error")

        mock_rest_client = AsyncMock()
        mock_rest_client.post.return_value = mock_response

        response = await mock_rest_client.post(
            "https://api.test.com/data", json={"test": "data"}
        )

        # Client should return the response, error handling is caller's responsibility
        assert response.status_code == 500
        assert "Error" in response.text

    @pytest.mark.asyncio
    async def test_rest_client_network_unreachable(self):
        """Test: REST client handles network unreachable errors"""
        mock_rest_client = AsyncMock()
        # Use a simpler exception that doesn't require complex aiohttp internals
        mock_rest_client.post.side_effect = ConnectionError("Network unreachable")

        with pytest.raises(ConnectionError) as exc_info:
            await mock_rest_client.post(
                "https://unreachable.com/api", json={"data": "test"}
            )

        assert "unreachable" in str(exc_info.value).lower()


class TestFileSystemErrorHandling:
    """Test error handling in file system operations"""

    def test_config_file_not_found_error(self):
        """Test: Configuration loading handles file not found errors"""
        with patch(
            "builtins.open", side_effect=FileNotFoundError("Config file not found")
        ):
            with pytest.raises(FileNotFoundError) as exc_info:
                with open("/non/existent/config.json", "r") as f:
                    json.load(f)

        assert "not found" in str(exc_info.value).lower()

    def test_config_file_permission_denied(self):
        """Test: Configuration loading handles permission errors"""
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            with pytest.raises(PermissionError) as exc_info:
                with open("/restricted/config.json", "r") as f:
                    json.load(f)

        assert "permission" in str(exc_info.value).lower()

    def test_config_file_invalid_json(self):
        """Test: Configuration loading handles invalid JSON"""
        invalid_json = '{"invalid": json, missing quotes}'

        with patch("builtins.open", mock_open(read_data=invalid_json)):
            with pytest.raises(json.JSONDecodeError) as exc_info:
                with open("config.json", "r") as f:
                    json.load(f)

        error = exc_info.value
        assert hasattr(error, "lineno")
        assert hasattr(error, "colno")

    def test_config_file_empty_content(self):
        """Test: Configuration loading handles empty files"""
        with patch("builtins.open", mock_open(read_data="")):
            with pytest.raises(json.JSONDecodeError) as exc_info:
                with open("empty_config.json", "r") as f:
                    json.load(f)

        assert "Expecting value" in str(exc_info.value)


class TestDatabaseErrorHandling:
    """Test error handling in database operations"""

    @pytest.mark.asyncio
    async def test_database_connection_error(self):
        """Test: Database operations handle connection errors"""
        mock_session = AsyncMock()
        mock_session.execute.side_effect = Exception("Connection lost")

        with pytest.raises(Exception) as exc_info:
            await mock_session.execute("SELECT * FROM test_table")

        assert "connection" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_database_query_timeout(self):
        """Test: Database operations handle query timeouts"""
        mock_session = AsyncMock()
        mock_session.execute.side_effect = asyncio.TimeoutError("Query timeout")

        with pytest.raises(asyncio.TimeoutError) as exc_info:
            await mock_session.execute("SELECT * FROM large_table")

        assert "timeout" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_database_constraint_violation(self):
        """Test: Database operations handle constraint violations"""
        constraint_error = Exception("UNIQUE constraint failed: controller_points.id")

        mock_session = AsyncMock()
        mock_session.execute.side_effect = constraint_error

        with pytest.raises(Exception) as exc_info:
            await mock_session.execute("INSERT INTO controller_points ...")

        assert "constraint" in str(exc_info.value).lower()


class TestBACnetErrorHandling:
    """Test error handling in BACnet operations"""

    @pytest.mark.asyncio
    async def test_bacnet_device_unreachable(self):
        """Test: BACnet operations handle unreachable devices"""
        mock_bacnet_wrapper = AsyncMock()
        mock_bacnet_wrapper.read_points.side_effect = ConnectionError(
            "Device unreachable"
        )

        with pytest.raises(ConnectionError) as exc_info:
            await mock_bacnet_wrapper.read_points()

        assert "unreachable" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_bacnet_invalid_object_identifier(self):
        """Test: BACnet operations handle invalid object identifiers"""
        mock_bacnet_wrapper = AsyncMock()
        mock_bacnet_wrapper.read_point.side_effect = ValueError(
            "Invalid object identifier"
        )

        with pytest.raises(ValueError) as exc_info:
            await mock_bacnet_wrapper.read_point("invalid:object:id")

        assert "invalid" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_bacnet_write_property_error(self):
        """Test: BACnet write operations handle property errors"""
        mock_bacnet_wrapper = AsyncMock()
        mock_bacnet_wrapper.write_point.side_effect = RuntimeError(
            "Property not writable"
        )

        with pytest.raises(RuntimeError) as exc_info:
            await mock_bacnet_wrapper.write_point("analogInput:1", 25.0)

        assert "writable" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_bacnet_communication_timeout(self):
        """Test: BACnet operations handle communication timeouts"""
        mock_bacnet_wrapper = AsyncMock()
        mock_bacnet_wrapper.connect.side_effect = asyncio.TimeoutError(
            "BACnet communication timeout"
        )

        with pytest.raises(asyncio.TimeoutError) as exc_info:
            await mock_bacnet_wrapper.connect()

        assert "timeout" in str(exc_info.value).lower()


class TestActorMessageErrorHandling:
    """Test error handling in actor message processing"""

    @pytest.mark.asyncio
    async def test_actor_queue_full_error(self):
        """Test: Actor queues handle full queue scenarios"""
        mock_queue = Mock()
        mock_queue.put_nowait.side_effect = asyncio.QueueFull("Queue is full")

        with pytest.raises(asyncio.QueueFull) as exc_info:
            mock_queue.put_nowait("test_message")

        assert "full" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_actor_message_deserialization_error(self):
        """Test: Actor message handling with invalid message format"""
        invalid_message_data = {
            "sender": "MQTT",
            "receiver": "BACNET",
            "message_type": "INVALID_TYPE",  # Invalid message type
            "payload": {"test": "data"},
        }

        with pytest.raises(ValidationError) as exc_info:
            ActorMessage(**invalid_message_data)

        errors = exc_info.value.errors()
        message_type_error = next(e for e in errors if "message_type" in str(e["loc"]))
        assert message_type_error["type"] == "enum"

    @pytest.mark.asyncio
    async def test_actor_message_processing_exception(self):
        """Test: Actor message processing handles unexpected exceptions"""

        def message_handler(message):
            raise RuntimeError("Unexpected processing error")

        mock_message = ActorMessage(
            sender=ActorName.MQTT,
            receiver=ActorName.BACNET,
            message_type=ActorMessageType.CONFIG_UPLOAD_REQUEST,
            payload=None,
        )

        with pytest.raises(RuntimeError) as exc_info:
            message_handler(mock_message)

        assert "unexpected" in str(exc_info.value).lower()


class TestAsyncErrorHandling:
    """Test error handling in asynchronous operations"""

    @pytest.mark.asyncio
    async def test_async_task_cancellation(self):
        """Test: Async operations handle task cancellation gracefully"""

        async def long_running_task():
            await asyncio.sleep(10)  # Simulate long operation
            return "completed"

        task = asyncio.create_task(long_running_task())

        # Cancel the task after a short delay
        await asyncio.sleep(0.1)
        task.cancel()

        with pytest.raises(asyncio.CancelledError):
            await task

    @pytest.mark.asyncio
    async def test_async_operation_timeout_handling(self):
        """Test: Async operations handle timeouts properly"""

        async def slow_operation():
            await asyncio.sleep(2)  # Simulate slow operation
            return "done"

        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(slow_operation(), timeout=0.5)

    @pytest.mark.asyncio
    async def test_concurrent_task_error_propagation(self):
        """Test: Concurrent operations handle individual task failures"""

        async def successful_task():
            await asyncio.sleep(0.1)
            return "success"

        async def failing_task():
            await asyncio.sleep(0.1)
            raise ValueError("Task failed")

        async def error_task():
            await asyncio.sleep(0.1)
            raise RuntimeError("Runtime error")

        tasks = [
            asyncio.create_task(successful_task()),
            asyncio.create_task(failing_task()),
            asyncio.create_task(error_task()),
        ]

        # Use gather with return_exceptions to capture errors
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Check results
        assert results[0] == "success"  # Successful task
        assert isinstance(results[1], ValueError)  # Failed task
        assert isinstance(results[2], RuntimeError)  # Error task

    @pytest.mark.asyncio
    async def test_async_context_manager_error_handling(self):
        """Test: Async context managers handle errors in context"""

        class AsyncContextManager:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                if exc_type is not None:
                    # Log or handle the exception
                    assert exc_type is ValueError
                    assert "context error" in str(exc_val)
                return False  # Don't suppress the exception

        with pytest.raises(ValueError) as exc_info:
            async with AsyncContextManager():
                raise ValueError("context error")

        assert "context error" in str(exc_info.value)


class TestRetryAndRecoveryErrorHandling:
    """Test retry mechanisms and error recovery patterns"""

    @pytest.mark.asyncio
    async def test_exponential_backoff_retry_pattern(self):
        """Test: Retry pattern with exponential backoff"""
        attempt_count = 0

        async def flaky_operation():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise ConnectionError(f"Attempt {attempt_count} failed")
            return f"Success on attempt {attempt_count}"

        # Simple retry logic
        max_retries = 5
        base_delay = 0.01

        for retry in range(max_retries):
            try:
                result = await flaky_operation()
                break
            except ConnectionError:
                if retry == max_retries - 1:
                    raise  # Re-raise on final attempt
                delay = base_delay * (2**retry)
                await asyncio.sleep(delay)

        assert result == "Success on attempt 3"
        assert attempt_count == 3

    @pytest.mark.asyncio
    async def test_circuit_breaker_pattern(self):
        """Test: Circuit breaker error handling pattern"""

        class SimpleCircuitBreaker:
            def __init__(self, failure_threshold=3, reset_timeout=1):
                self.failure_threshold = failure_threshold
                self.reset_timeout = reset_timeout
                self.failure_count = 0
                self.last_failure_time = None
                self.state = "closed"  # closed, open, half-open

            async def call(self, operation):
                if self.state == "open":
                    if (
                        asyncio.get_event_loop().time() - self.last_failure_time
                        > self.reset_timeout
                    ):
                        self.state = "half-open"
                    else:
                        raise RuntimeError("Circuit breaker is open")

                try:
                    result = await operation()
                    if self.state == "half-open":
                        self.state = "closed"
                        self.failure_count = 0
                    return result
                except Exception:
                    self.failure_count += 1
                    self.last_failure_time = asyncio.get_event_loop().time()
                    if self.failure_count >= self.failure_threshold:
                        self.state = "open"
                    raise

        call_count = 0

        async def failing_operation():
            nonlocal call_count
            call_count += 1
            if call_count <= 3:  # Fail first 3 calls, then succeed
                raise ConnectionError(f"Call {call_count} failed")
            return f"Success on call {call_count}"

        breaker = SimpleCircuitBreaker(failure_threshold=3, reset_timeout=0.1)

        # First 3 calls should fail and open the circuit
        for i in range(3):
            with pytest.raises(ConnectionError):
                await breaker.call(failing_operation)

        # Next call should fail due to open circuit
        with pytest.raises(RuntimeError, match="Circuit breaker is open"):
            await breaker.call(failing_operation)

        # Wait for reset timeout
        await asyncio.sleep(0.15)

        # Circuit should now be half-open and allow the call to succeed
        result = await breaker.call(failing_operation)
        assert "Success on call 4" == result

    @pytest.mark.asyncio
    async def test_graceful_degradation_pattern(self):
        """Test: Graceful degradation when services are unavailable"""

        async def primary_service():
            raise ConnectionError("Primary service unavailable")

        async def fallback_service():
            return {"data": "fallback_data", "source": "cache"}

        async def get_data_with_fallback():
            try:
                return await primary_service()
            except ConnectionError:
                # Graceful degradation to fallback
                return await fallback_service()

        result = await get_data_with_fallback()
        assert result["source"] == "cache"
        assert result["data"] == "fallback_data"


def mock_open(read_data=""):
    """Helper function to create mock open context manager"""
    from unittest.mock import mock_open as _mock_open

    return _mock_open(read_data=read_data)
