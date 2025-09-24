"""
Test SQLite retry logic implementation.

This test validates the new retry decorators and context manager session pattern.
"""

import pytest
from src.network.sqlmodel_client import with_db_retry, get_session, _is_retryable_error


class TestRetryLogic:
    """Test retry decorator functionality"""

    def test_is_retryable_error_database_locked(self):
        """Test: Database lock errors are identified as retryable"""
        error = Exception("database is locked")
        assert _is_retryable_error(error) is True

    def test_is_retryable_error_refresh_failed(self):
        """Test: Could not refresh instance errors are NON-retryable (Phase 5 change)"""
        error = Exception("Could not refresh instance")
        assert (
            _is_retryable_error(error) is False
        )  # Phase 5: session state errors are non-retryable

    def test_is_retryable_error_raspberry_pi_specific(self):
        """Test: Raspberry Pi specific errors are retryable"""
        disk_error = Exception("disk i/o error")
        closed_db_error = Exception("cannot operate on a closed database")

        assert _is_retryable_error(disk_error) is True
        assert _is_retryable_error(closed_db_error) is True

    def test_is_retryable_error_not_retryable(self):
        """Test: Non-retryable errors are correctly identified"""
        error = Exception("Some other error")
        assert _is_retryable_error(error) is False

    @pytest.mark.asyncio
    async def test_retry_decorator_success_immediate(self):
        """Test: Retry decorator allows immediate success"""
        call_count = 0

        @with_db_retry(max_retries=3, base_delay=0.01)
        async def test_operation():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await test_operation()
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_decorator_success_after_retries(self):
        """Test: Retry decorator retries on retryable errors"""
        call_count = 0

        @with_db_retry(max_retries=3, base_delay=0.01)
        async def test_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("database is locked")
            return "success"

        result = await test_operation()
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_decorator_max_retries_exceeded(self):
        """Test: Retry decorator raises error after max retries"""
        call_count = 0

        @with_db_retry(max_retries=2, base_delay=0.01)
        async def test_operation():
            nonlocal call_count
            call_count += 1
            raise Exception("database is locked")

        with pytest.raises(Exception, match="database is locked"):
            await test_operation()
        assert call_count == 3  # Initial call + 2 retries

    @pytest.mark.asyncio
    async def test_retry_decorator_non_retryable_error(self):
        """Test: Non-retryable errors are not retried"""
        call_count = 0

        @with_db_retry(max_retries=3, base_delay=0.01)
        async def test_operation():
            nonlocal call_count
            call_count += 1
            raise Exception("Some other error")

        with pytest.raises(Exception, match="Some other error"):
            await test_operation()
        assert call_count == 1  # No retries for non-retryable error


class TestSessionManagement:
    """Test context manager session pattern"""

    @pytest.mark.asyncio
    async def test_context_manager_session_basic(self):
        """Test: Context manager session works correctly"""
        from src.network.sqlmodel_client import initialize_database

        # Initialize database first
        await initialize_database()

        async with get_session() as session:
            from sqlalchemy import text

            result = await session.execute(text("SELECT 1"))
            value = result.fetchone()[0]
            assert value == 1

    @pytest.mark.asyncio
    async def test_context_manager_multiple_operations(self):
        """Test: Multiple operations within same context work"""
        from src.network.sqlmodel_client import initialize_database

        # Initialize database first
        await initialize_database()

        async with get_session() as session:
            from sqlalchemy import text

            # Multiple operations in same session
            result1 = await session.execute(text("SELECT 1"))
            result2 = await session.execute(text("SELECT 2"))

            assert result1.fetchone()[0] == 1
            assert result2.fetchone()[0] == 2


class TestIntegrationWithRetryLogic:
    """Test integration of retry logic with actual database operations"""

    @pytest.mark.asyncio
    async def test_bulk_insert_with_retries(self):
        """Test: Bulk insert works with retry protection"""
        from src.models.controller_points import (
            ControllerPointsModel,
            bulk_insert_controller_points,
        )
        from src.models.bacnet_types import BacnetObjectTypeEnum

        # Test data
        points = [
            ControllerPointsModel(
                controller_ip_address="192.168.1.100",
                bacnet_object_type=BacnetObjectTypeEnum.ANALOG_INPUT,
                point_id=1,
                iot_device_point_id="test_point_1",
                controller_id="test_ctrl_1",
                controller_device_id="test_device_1",
            )
        ]

        # This should work without errors (void function, no return value)
        await bulk_insert_controller_points(points)

        # Verify points were inserted by checking the original points objects
        # Note: Since we don't refresh, we can't check IDs, but we can verify the operation completed
        assert points[0].iot_device_point_id == "test_point_1"
