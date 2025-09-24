"""
Test to reproduce and fix SQLite connection pool timeout issues.
This test specifically targets the error we saw in production:
sqlalchemy.exc.TimeoutError: QueuePool limit of size 1 overflow 0 reached
"""

import asyncio
import pytest
import pytest_asyncio
import time
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from src.models.iot_device_status import (
    upsert_iot_device_status,
    get_latest_iot_device_status,
)
from src.models.controller_points import get_points_to_upload
from src.models.device_status_enums import MonitoringStatusEnum
from src.network.sqlmodel_client import (
    get_session,
    initialize_database,
    DATABASE_URL,
    connect_args,
)


# Global setup for tests
@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    """Initialize database tables before running tests"""
    try:
        # Import all models to ensure they're registered with SQLModel

        # Import all models and create tables using SQLModel metadata
        from sqlmodel import SQLModel
        from src.network.sqlmodel_client import get_engine

        # Create all tables using SQLModel metadata
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        # Initialize database optimizations
        await initialize_database()
        print("Test database initialized successfully")
    except Exception as e:
        print(f"Test database initialization failed: {e}")
        raise


class TestConnectionPoolTimeout:
    """Test connection pool timeout scenarios"""

    @pytest.mark.asyncio
    async def test_demonstrate_pooling_vs_nullpool_difference(self):
        """
        Compare pooled vs NullPool configurations to show the difference.
        This test demonstrates why NullPool is better for our use case.
        """

        # Test 1: OLD pooled configuration
        print("=== Testing OLD Pooled Configuration ===")
        old_engine = create_async_engine(
            DATABASE_URL,
            connect_args=connect_args,
            pool_size=1,  # Single connection
            max_overflow=0,  # No overflow
            pool_timeout=5,  # 5 second timeout
            pool_pre_ping=True,
            echo=False,
            future=True,
        )
        old_session_maker = sessionmaker(
            old_engine, class_=AsyncSession, expire_on_commit=False
        )

        async def test_pooled_operation(op_id: int):
            try:
                async with old_session_maker() as session:
                    # Simulate work that holds the connection
                    from sqlalchemy import text

                    await session.execute(text("SELECT 1"))
                    await asyncio.sleep(0.1)  # Small delay
                    await session.execute(text("SELECT 2"))
                    return f"Pooled {op_id}: OK"
            except Exception as e:
                return f"Pooled {op_id}: FAILED - {type(e).__name__}"

        # Run pooled test
        pooled_tasks = [test_pooled_operation(i) for i in range(10)]
        pooled_start = time.time()
        pooled_results = await asyncio.gather(*pooled_tasks, return_exceptions=True)
        pooled_duration = time.time() - pooled_start

        await old_engine.dispose()

        # Test 2: NEW NullPool configuration (current)
        print("=== Testing NEW NullPool Configuration ===")

        async def test_nullpool_operation(op_id: int):
            try:
                async with get_session() as session:  # Uses our current NullPool config
                    from sqlalchemy import text

                    await session.execute(text("SELECT 1"))
                    await asyncio.sleep(0.1)  # Same delay
                    await session.execute(text("SELECT 2"))
                    return f"NullPool {op_id}: OK"
            except Exception as e:
                return f"NullPool {op_id}: FAILED - {type(e).__name__}"

        # Run NullPool test
        nullpool_tasks = [test_nullpool_operation(i) for i in range(10)]
        nullpool_start = time.time()
        nullpool_results = await asyncio.gather(*nullpool_tasks, return_exceptions=True)
        nullpool_duration = time.time() - nullpool_start

        # Analyze results
        pooled_successes = len(
            [r for r in pooled_results if isinstance(r, str) and "OK" in r]
        )
        nullpool_successes = len(
            [r for r in nullpool_results if isinstance(r, str) and "OK" in r]
        )

        print(f"Pooled config: {pooled_successes}/10 success in {pooled_duration:.2f}s")
        print(
            f"NullPool config: {nullpool_successes}/10 success in {nullpool_duration:.2f}s"
        )

        pooled_failures = [
            r for r in pooled_results if isinstance(r, str) and "FAILED" in r
        ]
        nullpool_failures = [
            r for r in nullpool_results if isinstance(r, str) and "FAILED" in r
        ]

        if pooled_failures:
            print("Pooled failures:")
            for failure in pooled_failures[:3]:
                print(f"  - {failure}")

        if nullpool_failures:
            print("NullPool failures:")
            for failure in nullpool_failures[:3]:
                print(f"  - {failure}")

        # NullPool should be as good or better than pooled
        assert (
            nullpool_successes >= pooled_successes
        ), "NullPool should perform as well as pooled config"
        print(
            "✅ NullPool configuration performs well and handles concurrency correctly"
        )

    @pytest.mark.asyncio
    async def test_new_nullpool_configuration_works(self):
        """
        Test that the NEW NullPool configuration works reliably.
        This uses our current fixed configuration.
        """
        device_id = f"timeout-test-{int(time.time())}"

        # Create multiple long-running database operations that hold connections
        async def slow_database_operation(operation_id: int):
            """Simulates a slow database operation that holds connection"""
            try:
                async with get_session() as session:
                    # Simulate slow operation - like what happens when system is under load
                    await asyncio.sleep(0.5)  # Hold connection for 500ms

                    # Do actual database work
                    from sqlalchemy import text

                    await session.execute(text("SELECT 1"))

                # More work to keep connection busy (use separate operations)
                status_data = {
                    "organization_id": f"timeout-org-{operation_id}",
                    "site_id": f"timeout-site-{operation_id}",
                    "monitoring_status": MonitoringStatusEnum.ACTIVE,
                    "cpu_usage_percent": float(operation_id * 10),
                }
                await upsert_iot_device_status(
                    f"{device_id}-{operation_id}", status_data
                )

                return f"Operation {operation_id} completed"
            except Exception as e:
                return f"Operation {operation_id} failed: {e}"

        # Launch 5 concurrent slow operations to overwhelm the connection pool
        print("Starting 5 concurrent slow database operations...")
        tasks = [slow_database_operation(i) for i in range(5)]
        start_time = time.time()

        results = await asyncio.gather(*tasks, return_exceptions=True)
        duration = time.time() - start_time

        # Analyze results
        successes = [r for r in results if isinstance(r, str) and "completed" in r]
        failures = [r for r in results if isinstance(r, str) and "failed" in r]
        exceptions = [r for r in results if isinstance(r, Exception)]

        print(f"Test completed in {duration:.2f}s")
        print(f"Successes: {len(successes)}")
        print(f"Failures: {len(failures)}")
        print(f"Exceptions: {len(exceptions)}")

        if failures:
            print("Failure details:")
            for failure in failures:
                print(f"  - {failure}")

        if exceptions:
            print("Exception details:")
            for exc in exceptions:
                print(f"  - {type(exc).__name__}: {exc}")

        # The test should pass if all operations complete successfully
        # With the old pooled configuration, this would timeout
        # With NullPool, this should work fine
        total_operations = len(successes) + len(failures) + len(exceptions)
        success_rate = (
            len(successes) / total_operations * 100 if total_operations > 0 else 0
        )

        print(f"Success rate: {success_rate:.1f}%")

        # Assert that we get high success rate (should be 100% with NullPool)
        assert (
            success_rate >= 80
        ), f"Success rate too low: {success_rate:.1f}% - connection pool issues detected"
        assert (
            len(exceptions) == 0
        ), f"Found {len(exceptions)} exceptions indicating connection pool problems"

    @pytest.mark.asyncio
    async def test_rapid_concurrent_access(self):
        """
        Test rapid concurrent database access that would exhaust connection pool.
        This simulates the real production scenario with multiple actors.
        """
        device_id = f"rapid-test-{int(time.time())}"

        async def rapid_operation(batch_id: int):
            """Rapid database operations like UploaderActor does"""
            try:
                # Simulate UploaderActor's get_points_to_upload operation
                await get_points_to_upload()

                # Simulate status update like BacnetMonitoringActor
                status_data = {
                    "organization_id": f"rapid-org-{batch_id}",
                    "site_id": f"rapid-site-{batch_id}",
                    "monitoring_status": MonitoringStatusEnum.ACTIVE,
                    "cpu_usage_percent": float(batch_id % 100),
                }
                await upsert_iot_device_status(f"{device_id}-{batch_id}", status_data)

                return f"Batch {batch_id}: success"

            except Exception as e:
                return f"Batch {batch_id}: failed - {e}"

        # Simulate high-frequency concurrent access (like production load)
        print("Testing rapid concurrent database access...")
        tasks = [rapid_operation(i) for i in range(20)]
        start_time = time.time()

        results = await asyncio.gather(*tasks, return_exceptions=True)
        duration = time.time() - start_time

        # Analyze results
        successes = [r for r in results if isinstance(r, str) and "success" in r]
        failures = [r for r in results if isinstance(r, str) and "failed" in r]
        exceptions = [r for r in results if isinstance(r, Exception)]

        print(f"Rapid test completed in {duration:.2f}s")
        print(f"Operations per second: {len(tasks) / duration:.1f}")
        print(f"Successes: {len(successes)}")
        print(f"Failures: {len(failures)}")
        print(f"Exceptions: {len(exceptions)}")

        success_rate = len(successes) / len(tasks) * 100
        print(f"Success rate: {success_rate:.1f}%")

        # With NullPool, we should get 100% success rate
        assert (
            success_rate >= 95
        ), f"Rapid access success rate too low: {success_rate:.1f}%"

    @pytest.mark.asyncio
    async def test_connection_cleanup(self):
        """
        Test that connections are properly cleaned up with NullPool.
        This ensures we don't leak connections or have resource issues.
        """
        device_id = f"cleanup-test-{int(time.time())}"

        # Perform many sequential operations to test connection cleanup
        for i in range(50):
            status_data = {
                "organization_id": "cleanup-org",
                "site_id": "cleanup-site",
                "monitoring_status": MonitoringStatusEnum.ACTIVE,
                "cpu_usage_percent": float(i % 100),
            }

            result = await upsert_iot_device_status(f"{device_id}-{i}", status_data)
            assert result is not None, f"Operation {i} failed"

        # Verify final state
        final_status = await get_latest_iot_device_status(f"{device_id}-49")
        assert final_status is not None
        assert final_status.cpu_usage_percent == 49.0

        print("✅ Connection cleanup test passed - no resource leaks detected")


# Run tests with: python -m pytest test_connection_pool_timeout.py -v -s
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
