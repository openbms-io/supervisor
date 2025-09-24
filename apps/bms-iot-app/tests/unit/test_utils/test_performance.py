"""
Test performance metrics decorator functionality.
"""

import pytest
import asyncio
import time
import re
from unittest.mock import patch
from src.utils.performance import performance_metrics


class TestPerformanceMetricsDecorator:
    """Test the performance_metrics decorator"""

    def test_sync_function_success(self):
        """Test decorator on synchronous function that succeeds"""
        with patch("src.utils.performance.logger") as mock_logger:

            @performance_metrics("test_operation")
            def test_function():
                time.sleep(0.01)  # Small delay for timing
                return "success"

            result = test_function()

            assert result == "success"
            mock_logger.info.assert_called_once()

            # Check log message format
            call_args = mock_logger.info.call_args[0][0]
            assert "[PERF_METRICS] test_operation" in call_args
            assert "function=test_function" in call_args
            assert "duration_ms=" in call_args

    @pytest.mark.asyncio
    async def test_async_function_success(self):
        """Test decorator on async function that succeeds"""
        with patch("src.utils.performance.logger") as mock_logger:

            @performance_metrics("async_operation")
            async def test_async_function():
                await asyncio.sleep(0.01)  # Small delay for timing
                return ["result1", "result2"]

            result = await test_async_function()

            assert result == ["result1", "result2"]
            mock_logger.info.assert_called_once()

            # Check log message format
            call_args = mock_logger.info.call_args[0][0]
            assert "[PERF_METRICS] async_operation" in call_args
            assert "function=test_async_function" in call_args
            assert "duration_ms=" in call_args
            assert "result_count=2" in call_args

    def test_sync_function_with_context(self):
        """Test decorator with context extraction"""
        with patch("src.utils.performance.logger") as mock_logger:

            @performance_metrics(
                "test_operation", {"device": "device_ip", "count": "items"}
            )
            def test_function_with_context(device_ip, items):
                return {"processed": len(items)}

            result = test_function_with_context(
                device_ip="192.168.1.100", items=["item1", "item2", "item3"]
            )

            assert result == {"processed": 3}
            mock_logger.info.assert_called_once()

            # Check context in log message
            call_args = mock_logger.info.call_args[0][0]
            assert "device=192.168.1.100" in call_args
            assert "count=3" in call_args
            assert "avg_per_item_ms=" in call_args

    @pytest.mark.asyncio
    async def test_async_function_with_context(self):
        """Test decorator on async function with context extraction"""
        with patch("src.utils.performance.logger") as mock_logger:

            @performance_metrics(
                "bulk_read", {"device": "device_ip", "count": "point_requests"}
            )
            async def read_multiple_points(device_ip, point_requests):
                await asyncio.sleep(0.01)
                return [f"result_{i}" for i in range(len(point_requests))]

            result = await read_multiple_points(
                device_ip="192.168.1.100",
                point_requests=[{"id": 1}, {"id": 2}, {"id": 3}],
            )

            assert len(result) == 3
            mock_logger.info.assert_called_once()

            # Check context in log message
            call_args = mock_logger.info.call_args[0][0]
            assert "device=192.168.1.100" in call_args
            assert "count=3" in call_args
            assert "result_count=3" in call_args
            assert "avg_per_item_ms=" in call_args

    def test_sync_function_failure(self):
        """Test decorator on function that raises exception"""
        with patch("src.utils.performance.logger") as mock_logger:

            @performance_metrics("failing_operation")
            def failing_function():
                raise ValueError("Test error")

            with pytest.raises(ValueError, match="Test error"):
                failing_function()

            mock_logger.error.assert_called_once()

            # Check error log message format
            call_args = mock_logger.error.call_args[0][0]
            assert "[PERF_METRICS] failing_operation_FAILED" in call_args
            assert "function=failing_function" in call_args
            assert "duration_ms=" in call_args
            assert "error=ValueError" in call_args

    @pytest.mark.asyncio
    async def test_async_function_failure(self):
        """Test decorator on async function that raises exception"""
        with patch("src.utils.performance.logger") as mock_logger:

            @performance_metrics("async_failing", {"device": "device_ip"})
            async def failing_async_function(device_ip):
                await asyncio.sleep(0.01)
                raise ConnectionError("Network timeout")

            with pytest.raises(ConnectionError, match="Network timeout"):
                await failing_async_function(device_ip="192.168.1.100")

            mock_logger.error.assert_called_once()

            # Check error log message format
            call_args = mock_logger.error.call_args[0][0]
            assert "[PERF_METRICS] async_failing_FAILED" in call_args
            assert "function=failing_async_function" in call_args
            assert "duration_ms=" in call_args
            assert "error=ConnectionError" in call_args
            assert "device=192.168.1.100" in call_args

    def test_no_context_keys(self):
        """Test decorator without context extraction"""
        with patch("src.utils.performance.logger") as mock_logger:

            @performance_metrics("simple_operation")
            def simple_function(param1, param2):
                return param1 + param2

            result = simple_function("hello", "world")

            assert result == "helloworld"
            mock_logger.info.assert_called_once()

            # Check that no context keys are in log
            call_args = mock_logger.info.call_args[0][0]
            assert "param1=" not in call_args
            assert "param2=" not in call_args

    def test_missing_context_keys(self):
        """Test decorator when context keys are not found in function parameters"""
        with patch("src.utils.performance.logger") as mock_logger:

            @performance_metrics("test_operation", {"missing": "nonexistent_param"})
            def test_function(actual_param):
                return actual_param

            result = test_function(actual_param="value")

            assert result == "value"
            mock_logger.info.assert_called_once()

            # Check that missing context key is not in log
            call_args = mock_logger.info.call_args[0][0]
            assert "missing=" not in call_args

    def test_context_with_string_value(self):
        """Test context extraction with string values (should not get length)"""
        with patch("src.utils.performance.logger") as mock_logger:

            @performance_metrics("test_operation", {"name": "operation_name"})
            def test_function(operation_name):
                return "done"

            result = test_function(operation_name="bulk_read_operation")

            assert result == "done"
            mock_logger.info.assert_called_once()

            # Check string value is preserved
            call_args = mock_logger.info.call_args[0][0]
            assert "name=bulk_read_operation" in call_args

    def test_preserves_function_metadata(self):
        """Test that decorator preserves original function metadata"""

        @performance_metrics("test_operation")
        def original_function():
            """Original docstring"""
            return "result"

        assert original_function.__name__ == "original_function"
        assert original_function.__doc__ == "Original docstring"

    @pytest.mark.asyncio
    async def test_timing_accuracy(self):
        """Test that timing measurements are reasonably accurate"""
        with patch("src.utils.performance.logger") as mock_logger:
            expected_delay = 0.1  # 100ms

            @performance_metrics("timing_test")
            async def timed_function():
                await asyncio.sleep(expected_delay)
                return "done"

            await timed_function()

            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]

            # Extract duration from log message
            duration_match = re.search(r"duration_ms=([0-9.]+)", call_args)
            assert duration_match is not None

            measured_duration = float(duration_match.group(1))
            expected_duration_ms = expected_delay * 1000

            # Allow 10% tolerance for timing accuracy
            tolerance = expected_duration_ms * 0.1
            assert abs(measured_duration - expected_duration_ms) <= tolerance

    def test_none_result_handling(self):
        """Test decorator handles None result correctly"""
        with patch("src.utils.performance.logger") as mock_logger:

            @performance_metrics("void_operation")
            def void_function():
                return None

            result = void_function()

            assert result is None
            mock_logger.info.assert_called_once()

            # Check that result_count is not added for None result
            call_args = mock_logger.info.call_args[0][0]
            assert "result_count=" not in call_args

    def test_empty_list_context(self):
        """Test decorator handles empty list in context correctly"""
        with patch("src.utils.performance.logger") as mock_logger:

            @performance_metrics("empty_list_operation", {"count": "items"})
            def empty_list_function(items):
                return "processed"

            result = empty_list_function(items=[])

            assert result == "processed"
            mock_logger.info.assert_called_once()

            # Check context with empty list
            call_args = mock_logger.info.call_args[0][0]
            assert "count=0" in call_args
            # Should not have avg_per_item_ms when count is 0
            assert "avg_per_item_ms=" not in call_args


class TestPerformanceMetricsIntegration:
    """Integration tests for performance metrics in real scenarios"""

    @pytest.mark.asyncio
    async def test_bacnet_wrapper_integration(self):
        """Test integration with BACnet wrapper pattern"""
        with patch("src.utils.performance.logger") as mock_logger:

            @performance_metrics(
                "bacnet_bulk_read", {"device": "device_ip", "count": "point_requests"}
            )
            async def mock_read_multiple_points(device_ip, point_requests):
                # Simulate processing time proportional to point count
                await asyncio.sleep(len(point_requests) * 0.01)
                return {f"point_{i}": f"value_{i}" for i in range(len(point_requests))}

            result = await mock_read_multiple_points(
                device_ip="192.168.1.100",
                point_requests=[{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}, {"id": 5}],
            )

            assert len(result) == 5
            mock_logger.info.assert_called_once()

            call_args = mock_logger.info.call_args[0][0]
            assert "[PERF_METRICS] bacnet_bulk_read" in call_args
            assert "device=192.168.1.100" in call_args
            assert "count=5" in call_args
            assert "result_count=5" in call_args
            assert "avg_per_item_ms=" in call_args

    @pytest.mark.asyncio
    async def test_database_operation_integration(self):
        """Test integration with database operation pattern"""
        with patch("src.utils.performance.logger") as mock_logger:

            @performance_metrics("database_bulk_insert", {"count": "points"})
            async def mock_bulk_insert_controller_points(points):
                # Simulate database operation time
                await asyncio.sleep(len(points) * 0.005)
                # Return void (like real implementation)
                return None

            await mock_bulk_insert_controller_points(
                points=[{"id": i} for i in range(10)]
            )

            mock_logger.info.assert_called_once()

            call_args = mock_logger.info.call_args[0][0]
            assert "[PERF_METRICS] database_bulk_insert" in call_args
            assert "count=10" in call_args
            assert "avg_per_item_ms=" in call_args
            # Should not have result_count for None return
            assert "result_count=" not in call_args

    def test_multiple_context_keys(self):
        """Test decorator with multiple context keys"""
        with patch("src.utils.performance.logger") as mock_logger:

            @performance_metrics(
                "complex_operation",
                {"device": "device_ip", "count": "items", "mode": "operation_mode"},
            )
            def complex_function(device_ip, items, operation_mode):
                return {"status": "success"}

            result = complex_function(
                device_ip="192.168.1.100",
                items=["a", "b", "c", "d"],
                operation_mode="bulk",
            )

            assert result == {"status": "success"}
            mock_logger.info.assert_called_once()

            call_args = mock_logger.info.call_args[0][0]
            assert "device=192.168.1.100" in call_args
            assert "count=4" in call_args
            assert "mode=bulk" in call_args
            assert "avg_per_item_ms=" in call_args

    @pytest.mark.asyncio
    async def test_concurrent_decorated_functions(self):
        """Test that multiple concurrent decorated functions work correctly"""
        with patch("src.utils.performance.logger") as mock_logger:

            @performance_metrics("concurrent_test", {"id": "task_id"})
            async def concurrent_task(task_id):
                await asyncio.sleep(0.01)
                return f"result_{task_id}"

            # Run multiple tasks concurrently
            tasks = [concurrent_task(task_id=i) for i in range(3)]
            results = await asyncio.gather(*tasks)

            assert len(results) == 3
            assert mock_logger.info.call_count == 3

            # Check that all tasks were logged with correct IDs
            call_args_list = [call[0][0] for call in mock_logger.info.call_args_list]
            for i, call_args in enumerate(call_args_list):
                assert f"id={i}" in call_args
                assert "[PERF_METRICS] concurrent_test" in call_args
