"""
Test SQLite session concurrency fixes to verify they resolve production issues.

This test suite validates the complete solution for SQLAlchemy session concurrency
violations including:
- InvalidRequestError: Could not refresh instance (session detachment)
- Defensive id=0 handling for future-proofing
- Fetch-instead-of-refresh patterns
- Error classification improvements
- Concurrent operation safety
"""

import pytest
import asyncio
from src.models.controller_points import (
    ControllerPointsModel,
    bulk_insert_controller_points,
)
from src.models.bacnet_types import BacnetObjectTypeEnum


class TestSQLiteSessionConcurrencyFixes:
    """Test SQLite session concurrency fixes: defensive ID validation + fetch instead of refresh"""

    @pytest.mark.asyncio
    async def test_setup_database(self):
        """Create the database table for testing"""
        from sqlmodel import SQLModel
        from src.network.sqlmodel_client import get_engine

        # Import all models to register them with SQLModel

        # Create all tables using SQLModel metadata
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        print("✅ Database tables created")

    @pytest.mark.asyncio
    async def test_bulk_insert_with_session_fixes(self):
        """Test that the new implementation eliminates refresh errors"""

        # Ensure table exists
        await self.test_setup_database()

        # Create 11 points (same as production error) including some with id=0
        points = []
        for i in range(11):
            point = ControllerPointsModel(
                controller_ip_address="192.168.1.100",
                bacnet_object_type=BacnetObjectTypeEnum.ANALOG_INPUT,
                point_id=5000 + i,
                iot_device_point_id=f"phase5_point_{i}",
                controller_id="phase5_controller",
                controller_device_id="phase5_device",
                present_value=f"{100.0 + i}",
            )

            # Simulate problematic id=0 for some points (defensive test)
            if i % 3 == 0:  # Every 3rd point gets id=0
                point.id = 0
                print(f"🔍 Set point {i} to have id=0 (will test defensive fix)")

            points.append(point)

        print(f"🔍 Created {len(points)} points, some with id=0 for defensive testing")

        # This should work with session concurrency fixes
        try:
            await bulk_insert_controller_points(points)
            print(
                f"✅ Session concurrency fixes succeeded! Processed {len(points)} points"
            )

            # Verify all points have valid database IDs (assigned in-place)
            for i, point in enumerate(points):
                assert point.id is not None
                assert point.id > 0
                print(f"📋 Point {i}: id={point.id}, point_id={point.point_id}")

            print("🎉 Session concurrency fixes successfully handled all edge cases!")
            return points

        except Exception as e:
            print(f"❌ Session concurrency fixes failed: {e}")
            raise

    @pytest.mark.asyncio
    async def test_concurrent_bulk_operations(self):
        """Test concurrent bulk operations don't cause session issues"""

        # Ensure table exists
        await self.test_setup_database()

        async def concurrent_bulk_insert(batch_id: int):
            """Simulate concurrent bulk insert operations"""
            points = []
            for i in range(5):
                point = ControllerPointsModel(
                    controller_ip_address="192.168.1.100",
                    bacnet_object_type=BacnetObjectTypeEnum.BINARY_INPUT,
                    point_id=6000 + (batch_id * 100) + i,
                    iot_device_point_id=f"concurrent_point_{batch_id}_{i}",
                    controller_id=f"concurrent_controller_{batch_id}",
                    controller_device_id=f"concurrent_device_{batch_id}",
                    present_value=f"{batch_id}.{i}",
                )
                points.append(point)

            await bulk_insert_controller_points(points)
            return points

        # Run multiple concurrent bulk inserts
        print("🔍 Starting concurrent bulk insert operations...")
        tasks = [concurrent_bulk_insert(i) for i in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Analyze results
        successes = [r for r in results if isinstance(r, list)]
        exceptions = [r for r in results if isinstance(r, Exception)]

        print(
            f"📊 Concurrent Results: {len(successes)} successes, {len(exceptions)} exceptions"
        )

        if exceptions:
            print("❌ Found exceptions in concurrent operations:")
            for exc in exceptions:
                print(f"   {type(exc).__name__}: {exc}")
            raise AssertionError(f"Concurrent operations failed: {exceptions}")

        # Verify all operations succeeded
        assert (
            len(successes) == 5
        ), f"Expected 5 successful operations, got {len(successes)}"

        total_points = sum(len(batch) for batch in successes)
        print(
            f"✅ Concurrent operations successful! Total points processed: {total_points}"
        )

        # Verify all points have unique IDs
        all_ids = []
        for batch in successes:
            for point in batch:
                all_ids.append(point.id)

        unique_ids = set(all_ids)
        assert len(unique_ids) == len(
            all_ids
        ), f"Found duplicate IDs: {len(unique_ids)} unique vs {len(all_ids)} total"

        print("🎉 All concurrent operations completed without session errors!")

    @pytest.mark.asyncio
    async def test_id_zero_defensive_handling(self):
        """Test that id=0 is properly handled defensively"""

        # Ensure table exists
        await self.test_setup_database()

        # Create points with explicit id=0 (edge case)
        points = []
        for i in range(3):
            point = ControllerPointsModel(
                id=0,  # Explicitly set problematic id=0
                controller_ip_address="192.168.1.100",
                bacnet_object_type=BacnetObjectTypeEnum.ANALOG_OUTPUT,
                point_id=7000 + i,
                iot_device_point_id=f"id_zero_point_{i}",
                controller_id="id_zero_controller",
                controller_device_id="id_zero_device",
                present_value=f"zero_{i}",
            )
            points.append(point)
            print(f"🔍 Created point {i} with explicit id=0: {point.id}")

        # Session concurrency fixes should handle this defensively
        await bulk_insert_controller_points(points)

        # Verify defensive handling worked (points modified in-place)
        assert len(points) == 3
        for i, point in enumerate(points):
            assert point.id is not None
            assert point.id > 0
            print(f"✅ Defensive handling: point {i} now has valid id={point.id}")

        print("🎉 Defensive id=0 handling successful!")

    @pytest.mark.asyncio
    async def test_error_classification(self):
        """Test that InvalidRequestError is properly classified as non-retryable"""

        from src.network.sqlmodel_client import _is_retryable_error

        # Test InvalidRequestError patterns
        session_errors = [
            Exception("InvalidRequestError: Could not refresh instance"),
            Exception("Instance is not persistent within this Session"),
            Exception("object is not bound to a session"),
            Exception("object is already attached to session"),
        ]

        for error in session_errors:
            is_retryable = _is_retryable_error(error)
            assert not is_retryable, f"Session error should be non-retryable: {error}"
            print(f"✅ Correctly classified as non-retryable: {error}")

        # Test that database lock errors are still retryable
        retryable_errors = [
            Exception("database is locked"),
            Exception("database table is locked"),
            Exception("connection was invalidated"),
        ]

        for error in retryable_errors:
            is_retryable = _is_retryable_error(error)
            assert is_retryable, f"Database lock error should be retryable: {error}"
            print(f"✅ Correctly classified as retryable: {error}")

        print("🎉 Error classification working correctly!")


if __name__ == "__main__":
    # Run the tests manually for debugging
    import asyncio

    async def run_session_concurrency_tests():
        test_instance = TestSQLiteSessionConcurrencyFixes()

        print("🔍 Testing SQLite session concurrency fixes")
        print("=" * 60)

        print("\n1. Testing bulk insert with session concurrency fixes...")
        await test_instance.test_bulk_insert_with_session_fixes()

        print("\n2. Testing concurrent bulk operations...")
        await test_instance.test_concurrent_bulk_operations()

        print("\n3. Testing defensive id=0 handling...")
        await test_instance.test_id_zero_defensive_handling()

        print("\n4. Testing error classification...")
        await test_instance.test_error_classification()

        print(
            "\n🎉 All session concurrency tests passed! Implementation ready for production."
        )

    # Run if executed directly
    asyncio.run(run_session_concurrency_tests())
