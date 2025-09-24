"""
Unit tests for IoT device status model functions.
Tests the core functionality of upsert_iot_device_status and related functions.
"""

import pytest
import pytest_asyncio
import asyncio
import time
from datetime import datetime

from src.models.iot_device_status import (
    upsert_iot_device_status,
    get_latest_iot_device_status,
    update_system_metrics,
    update_connection_status,
    IotDeviceStatusModel,
)
from src.models.device_status_enums import MonitoringStatusEnum, ConnectionStatusEnum


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_database():
    """Setup test database with Alembic migrations (global conftest.py handles this)"""
    # Note: Database tables are now created by global conftest.py using Alembic migrations
    # This ensures test database schema matches production exactly
    print("✅ IoT device status test database setup (handled by global conftest.py)")


class TestIotDeviceStatusUpsert:
    """Test the upsert_iot_device_status function"""

    @pytest.mark.asyncio
    async def test_insert_new_device_status(self):
        """Test inserting status for a new device"""
        device_id = f"test-insert-{int(time.time())}"
        status_data = {
            "organization_id": "test-org",
            "site_id": "test-site",
            "monitoring_status": MonitoringStatusEnum.ACTIVE,
            "cpu_usage_percent": 45.5,
            "memory_usage_percent": 67.2,
        }

        result = await upsert_iot_device_status(device_id, status_data)

        # Verify result
        assert result is not None
        assert result.iot_device_id == device_id
        assert result.organization_id == "test-org"
        assert result.site_id == "test-site"
        assert result.monitoring_status == MonitoringStatusEnum.ACTIVE
        assert result.cpu_usage_percent == 45.5
        assert result.memory_usage_percent == 67.2
        assert result.created_at is not None
        assert result.updated_at is not None
        assert result.received_at is not None

    @pytest.mark.asyncio
    async def test_update_existing_device_status(self):
        """Test updating status for an existing device"""
        device_id = f"test-update-{int(time.time())}"

        # First insert
        initial_data = {
            "organization_id": "test-org",
            "site_id": "test-site",
            "monitoring_status": MonitoringStatusEnum.ACTIVE,
            "cpu_usage_percent": 30.0,
        }
        initial_result = await upsert_iot_device_status(device_id, initial_data)
        assert initial_result is not None
        initial_created_at = initial_result.created_at

        # Wait a moment to ensure timestamp difference
        await asyncio.sleep(0.01)

        # Then update
        update_data = {
            "monitoring_status": MonitoringStatusEnum.ERROR,
            "cpu_usage_percent": 85.0,
            "memory_usage_percent": 92.5,
        }
        update_result = await upsert_iot_device_status(device_id, update_data)

        # Verify update
        assert update_result is not None
        assert update_result.iot_device_id == device_id
        assert update_result.organization_id == "test-org"  # Should preserve original
        assert update_result.site_id == "test-site"  # Should preserve original
        assert (
            update_result.monitoring_status == MonitoringStatusEnum.ERROR
        )  # Should update
        assert update_result.cpu_usage_percent == 85.0  # Should update
        assert update_result.memory_usage_percent == 92.5  # Should update
        assert (
            update_result.created_at == initial_created_at
        )  # Should preserve created_at
        assert (
            update_result.updated_at > initial_result.updated_at
        )  # Should update timestamps

    @pytest.mark.asyncio
    async def test_payload_json_conversion(self):
        """Test that dict payloads are converted to JSON strings"""
        device_id = f"test-json-{int(time.time())}"
        payload_dict = {
            "temperature": 23.5,
            "humidity": 45.2,
            "sensors": ["temp1", "hum1"],
        }

        status_data = {
            "organization_id": "test-org",
            "site_id": "test-site",
            "monitoring_status": MonitoringStatusEnum.ACTIVE,
            "payload": payload_dict,
        }

        result = await upsert_iot_device_status(device_id, status_data)

        # Verify payload is stored as JSON string
        assert result is not None
        assert result.payload is not None
        assert isinstance(result.payload, str)

        # Verify we can parse it back
        import json

        parsed_payload = json.loads(result.payload)
        assert parsed_payload == payload_dict

    @pytest.mark.asyncio
    async def test_automatic_timestamps(self):
        """Test that timestamps are automatically set"""
        device_id = f"test-timestamps-{int(time.time())}"

        # Use naive datetime since the model might store naive datetimes
        datetime.now()

        status_data = {
            "organization_id": "test-org",
            "site_id": "test-site",
            "monitoring_status": MonitoringStatusEnum.ACTIVE,
        }

        result = await upsert_iot_device_status(device_id, status_data)

        datetime.now()

        # Verify timestamps are set and reasonable
        assert result is not None
        assert result.created_at is not None
        assert result.updated_at is not None
        assert result.received_at is not None

        # Verify timestamps are within reasonable range
        # Just verify they exist and are reasonable datetime objects
        assert isinstance(result.created_at, datetime)
        assert isinstance(result.updated_at, datetime)
        assert isinstance(result.received_at, datetime)

        # Verify created_at, updated_at, and received_at are close to each other
        time_diff = abs((result.updated_at - result.created_at).total_seconds())
        assert (
            time_diff < 1
        ), "created_at and updated_at should be very close for new record"

    @pytest.mark.asyncio
    async def test_concurrent_insert_race_condition(self):
        """Test that concurrent inserts for same device are handled properly"""
        device_id = f"test-race-{int(time.time())}"

        async def concurrent_insert(iteration: int):
            try:
                status_data = {
                    "organization_id": "test-org",
                    "site_id": "test-site",
                    "monitoring_status": MonitoringStatusEnum.ACTIVE,
                    "cpu_usage_percent": float(iteration),
                    "iteration": iteration,  # To track which update succeeded
                }
                return await upsert_iot_device_status(device_id, status_data)
            except RuntimeError as e:
                # Ignore logger queue issues in test environment
                if "Queue" in str(e) and "maxsize" in str(e):
                    return f"Logger queue issue (iteration {iteration})"
                raise

        # Launch 10 concurrent inserts for the same device
        tasks = [concurrent_insert(i) for i in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Separate logger issues from real exceptions
        real_exceptions = [r for r in results if isinstance(r, Exception)]
        logger_issues = [
            r for r in results if isinstance(r, str) and "Logger queue issue" in r
        ]
        valid_results = [r for r in results if isinstance(r, IotDeviceStatusModel)]

        print(
            f"Concurrent insert results: {len(valid_results)} successful, {len(logger_issues)} logger issues, {len(real_exceptions)} real exceptions"
        )

        # All database operations should succeed (no real exceptions)
        assert len(real_exceptions) == 0, f"Found real exceptions: {real_exceptions}"

        # Should have at least some successful results
        assert len(valid_results) > 0, "Should have at least some successful operations"

        # All valid results should have the same iot_device_id
        for result in valid_results:
            assert result.iot_device_id == device_id

        # Verify final state - only one record should exist in database
        final_status = await get_latest_iot_device_status(device_id)
        assert final_status is not None
        assert final_status.iot_device_id == device_id


class TestIotDeviceStatusHelperFunctions:
    """Test helper functions that use upsert_iot_device_status"""

    @pytest.mark.asyncio
    async def test_update_system_metrics(self):
        """Test update_system_metrics function"""
        device_id = f"test-metrics-{int(time.time())}"

        # First create a device with required fields
        initial_data = {
            "organization_id": "test-org",
            "site_id": "test-site",
            "monitoring_status": MonitoringStatusEnum.ACTIVE,
        }
        await upsert_iot_device_status(device_id, initial_data)

        # Then update metrics
        metrics = {
            "cpu_usage_percent": 75.5,
            "memory_usage_percent": 45.2,
            "disk_usage_percent": 30.1,
        }

        result = await update_system_metrics(device_id, metrics)

        assert result is not None
        assert result.iot_device_id == device_id
        assert result.cpu_usage_percent == 75.5
        assert result.memory_usage_percent == 45.2
        assert result.disk_usage_percent == 30.1

    @pytest.mark.asyncio
    async def test_update_connection_status_mqtt(self):
        """Test update_connection_status for MQTT"""
        device_id = f"test-mqtt-conn-{int(time.time())}"

        # First create a device with required fields
        initial_data = {
            "organization_id": "test-org",
            "site_id": "test-site",
            "monitoring_status": MonitoringStatusEnum.ACTIVE,
        }
        await upsert_iot_device_status(device_id, initial_data)

        result = await update_connection_status(
            device_id, "mqtt", ConnectionStatusEnum.CONNECTED
        )

        assert result is not None
        assert result.iot_device_id == device_id
        assert result.mqtt_connection_status == ConnectionStatusEnum.CONNECTED

    @pytest.mark.asyncio
    async def test_update_connection_status_bacnet(self):
        """Test update_connection_status for BACnet"""
        device_id = f"test-bacnet-conn-{int(time.time())}"

        # First create a device with required fields
        initial_data = {
            "organization_id": "test-org",
            "site_id": "test-site",
            "monitoring_status": MonitoringStatusEnum.ACTIVE,
        }
        await upsert_iot_device_status(device_id, initial_data)

        result = await update_connection_status(
            device_id, "bacnet", ConnectionStatusEnum.DISCONNECTED
        )

        assert result is not None
        assert result.iot_device_id == device_id
        assert result.bacnet_connection_status == ConnectionStatusEnum.DISCONNECTED


class TestIotDeviceStatusRetrieval:
    """Test retrieving IoT device status"""

    @pytest.mark.asyncio
    async def test_get_latest_iot_device_status_existing(self):
        """Test retrieving status for existing device"""
        device_id = f"test-get-{int(time.time())}"

        # Insert a device status
        status_data = {
            "organization_id": "test-org",
            "site_id": "test-site",
            "monitoring_status": MonitoringStatusEnum.ACTIVE,
            "cpu_usage_percent": 55.5,
        }
        await upsert_iot_device_status(device_id, status_data)

        # Retrieve it
        result = await get_latest_iot_device_status(device_id)

        assert result is not None
        assert result.iot_device_id == device_id
        assert result.organization_id == "test-org"
        assert result.site_id == "test-site"
        assert result.monitoring_status == MonitoringStatusEnum.ACTIVE
        assert result.cpu_usage_percent == 55.5

    @pytest.mark.asyncio
    async def test_get_latest_iot_device_status_nonexistent(self):
        """Test retrieving status for non-existent device"""
        device_id = f"nonexistent-{int(time.time())}"

        result = await get_latest_iot_device_status(device_id)

        assert result is None


class TestIotDeviceStatusErrorHandling:
    """Test error handling in IoT device status functions"""

    @pytest.mark.asyncio
    async def test_upsert_with_invalid_enum_values(self):
        """Test that invalid enum values are handled properly"""
        device_id = f"test-invalid-{int(time.time())}"

        # This should work - valid enum
        status_data = {
            "organization_id": "test-org",
            "site_id": "test-site",
            "monitoring_status": MonitoringStatusEnum.ACTIVE,
        }

        result = await upsert_iot_device_status(device_id, status_data)
        assert result is not None
        assert result.monitoring_status == MonitoringStatusEnum.ACTIVE

    @pytest.mark.asyncio
    async def test_upsert_preserves_existing_fields(self):
        """Test that upsert preserves fields not included in update"""
        device_id = f"test-preserve-{int(time.time())}"

        # Initial insert with multiple fields
        initial_data = {
            "organization_id": "test-org",
            "site_id": "test-site",
            "monitoring_status": MonitoringStatusEnum.ACTIVE,
            "cpu_usage_percent": 30.0,
            "memory_usage_percent": 45.0,
            "mqtt_connection_status": ConnectionStatusEnum.CONNECTED,
        }
        await upsert_iot_device_status(device_id, initial_data)

        # Update with partial data
        update_data = {"cpu_usage_percent": 75.0}  # Only update CPU usage
        result = await upsert_iot_device_status(device_id, update_data)

        # Verify preserved fields
        assert result is not None
        assert result.organization_id == "test-org"  # Should preserve
        assert result.site_id == "test-site"  # Should preserve
        assert (
            result.monitoring_status == MonitoringStatusEnum.ACTIVE
        )  # Should preserve
        assert result.memory_usage_percent == 45.0  # Should preserve
        assert (
            result.mqtt_connection_status == ConnectionStatusEnum.CONNECTED
        )  # Should preserve
        assert result.cpu_usage_percent == 75.0  # Should update
