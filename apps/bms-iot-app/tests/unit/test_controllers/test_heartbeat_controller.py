"""
Test heartbeat controller logic.

User Story: As a developer, I want heartbeat controller logic to work correctly
"""

import pytest
import asyncio
from unittest.mock import Mock, patch

# Import existing types
from src.models.device_status_enums import MonitoringStatusEnum, ConnectionStatusEnum

from src.actors.messages.message_type import HeartbeatStatusPayload
from src.controllers.heartbeat_controller.heartbeat import (
    HeartbeatController,
)


class TestHeartbeatController:
    """Test HeartbeatController class functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.org_id = "test_org"
        self.site_id = "test_site"
        self.device_id = "test_device_123"
        self.controller = HeartbeatController(self.org_id, self.site_id, self.device_id)

    def test_heartbeat_controller_initialization(self):
        """Test: HeartbeatController initializes with correct parameters"""
        controller = HeartbeatController("org1", "site1", "device1")

        assert controller.organization_id == "org1"
        assert controller.site_id == "site1"
        assert controller.iot_device_id == "device1"

    @pytest.mark.asyncio
    async def test_start_method_executes_without_error(self):
        """Test: HeartbeatController start method runs successfully"""
        # Should not raise any exceptions
        await self.controller.start()

        # Start method doesn't return anything or modify state
        assert self.controller.organization_id == self.org_id
        assert self.controller.site_id == self.site_id
        assert self.controller.iot_device_id == self.device_id

    @pytest.mark.asyncio
    async def test_collect_heartbeat_data_with_valid_status_record(self):
        """Test: Heartbeat data collection with valid database record"""
        # Mock status record from database
        mock_status_record = Mock()
        mock_status_record.cpu_usage_percent = 45.2
        mock_status_record.memory_usage_percent = 67.8
        mock_status_record.disk_usage_percent = 23.1
        mock_status_record.temperature_celsius = 42.5
        mock_status_record.uptime_seconds = 86400
        mock_status_record.load_average = 1.25
        mock_status_record.monitoring_status = MonitoringStatusEnum.ACTIVE
        mock_status_record.mqtt_connection_status = ConnectionStatusEnum.CONNECTED
        mock_status_record.bacnet_connection_status = ConnectionStatusEnum.CONNECTED
        mock_status_record.bacnet_devices_connected = 3
        mock_status_record.bacnet_points_monitored = 125

        with patch(
            "src.controllers.heartbeat_controller.heartbeat.get_latest_iot_device_status"
        ) as mock_get_status:
            mock_get_status.return_value = mock_status_record

            result = await self.controller.collect_heartbeat_data()

            # Verify the method was called with correct device ID
            mock_get_status.assert_called_once_with(self.device_id)

            # Verify returned payload has correct data
            assert isinstance(result, HeartbeatStatusPayload)
            assert result.cpu_usage_percent == 45.2
            assert result.memory_usage_percent == 67.8
            assert result.disk_usage_percent == 23.1
            assert result.temperature_celsius == 42.5
            assert result.uptime_seconds == 86400
            assert result.load_average == 1.25
            assert result.monitoring_status == MonitoringStatusEnum.ACTIVE
            assert result.mqtt_connection_status == ConnectionStatusEnum.CONNECTED
            assert result.bacnet_connection_status == ConnectionStatusEnum.CONNECTED
            assert result.bacnet_devices_connected == 3
            assert result.bacnet_points_monitored == 125

    @pytest.mark.asyncio
    async def test_collect_heartbeat_data_with_no_status_record(self):
        """Test: Heartbeat data collection when no database record exists"""
        with patch(
            "src.controllers.heartbeat_controller.heartbeat.get_latest_iot_device_status"
        ) as mock_get_status:
            mock_get_status.return_value = None

            result = await self.controller.collect_heartbeat_data()

            # Verify the method was called
            mock_get_status.assert_called_once_with(self.device_id)

            # Verify returned payload is empty but valid
            assert isinstance(result, HeartbeatStatusPayload)
            assert result.cpu_usage_percent is None
            assert result.memory_usage_percent is None
            assert result.monitoring_status is None
            assert result.mqtt_connection_status is None

    @pytest.mark.asyncio
    async def test_collect_heartbeat_data_with_database_error(self):
        """Test: Heartbeat data collection handles database errors gracefully"""
        with patch(
            "src.controllers.heartbeat_controller.heartbeat.get_latest_iot_device_status"
        ) as mock_get_status:
            mock_get_status.side_effect = Exception("Database connection error")

            result = await self.controller.collect_heartbeat_data()

            # Verify error handling
            assert isinstance(result, HeartbeatStatusPayload)
            assert result.mqtt_connection_status == ConnectionStatusEnum.ERROR
            assert result.bacnet_connection_status == ConnectionStatusEnum.ERROR
            # Other fields should be None
            assert result.cpu_usage_percent is None
            assert result.memory_usage_percent is None

    @pytest.mark.asyncio
    async def test_collect_heartbeat_data_with_partial_status_record(self):
        """Test: Heartbeat data collection with partial database record"""
        # Mock status record with only some fields populated
        mock_status_record = Mock()
        mock_status_record.cpu_usage_percent = 25.0
        mock_status_record.memory_usage_percent = None  # Missing value
        mock_status_record.disk_usage_percent = None
        mock_status_record.temperature_celsius = 35.5
        mock_status_record.uptime_seconds = None
        mock_status_record.load_average = None
        mock_status_record.monitoring_status = MonitoringStatusEnum.ACTIVE
        mock_status_record.mqtt_connection_status = ConnectionStatusEnum.CONNECTED
        mock_status_record.bacnet_connection_status = ConnectionStatusEnum.DISCONNECTED
        mock_status_record.bacnet_devices_connected = 0
        mock_status_record.bacnet_points_monitored = 0

        with patch(
            "src.controllers.heartbeat_controller.heartbeat.get_latest_iot_device_status"
        ) as mock_get_status:
            mock_get_status.return_value = mock_status_record

            result = await self.controller.collect_heartbeat_data()

            # Verify partial data is handled correctly
            assert result.cpu_usage_percent == 25.0
            assert result.memory_usage_percent is None
            assert result.temperature_celsius == 35.5
            assert result.monitoring_status == MonitoringStatusEnum.ACTIVE
            assert result.bacnet_connection_status == ConnectionStatusEnum.DISCONNECTED
            assert result.bacnet_devices_connected == 0

    @pytest.mark.asyncio
    async def test_force_heartbeat_with_valid_reason(self):
        """Test: Force heartbeat with valid reason"""
        # Mock the collect_heartbeat_data method
        expected_payload = HeartbeatStatusPayload(
            cpu_usage_percent=30.0,
            monitoring_status=MonitoringStatusEnum.ACTIVE,
            mqtt_connection_status=ConnectionStatusEnum.CONNECTED,
        )

        with patch.object(
            self.controller, "collect_heartbeat_data", return_value=expected_payload
        ) as mock_collect:
            result = await self.controller.force_heartbeat("status_change")

            # Verify collect_heartbeat_data was called
            mock_collect.assert_called_once()

            # Verify result is the same as collect_heartbeat_data
            assert result == expected_payload
            assert result.cpu_usage_percent == 30.0
            assert result.monitoring_status == MonitoringStatusEnum.ACTIVE
            assert result.mqtt_connection_status == ConnectionStatusEnum.CONNECTED

    @pytest.mark.asyncio
    async def test_force_heartbeat_with_collection_error(self):
        """Test: Force heartbeat handles errors in data collection"""
        with patch.object(self.controller, "collect_heartbeat_data") as mock_collect:
            mock_collect.side_effect = Exception("Collection failed")

            result = await self.controller.force_heartbeat("test_reason")

            # Verify error handling
            assert isinstance(result, HeartbeatStatusPayload)
            assert result.mqtt_connection_status == ConnectionStatusEnum.ERROR
            assert result.bacnet_connection_status == ConnectionStatusEnum.ERROR
            # Other fields should be None
            assert result.cpu_usage_percent is None

    @pytest.mark.asyncio
    async def test_force_heartbeat_various_reasons(self):
        """Test: Force heartbeat works with various reason strings"""
        mock_payload = HeartbeatStatusPayload(
            monitoring_status=MonitoringStatusEnum.ACTIVE
        )

        reasons = [
            "status_change",
            "monitoring_change",
            "connection_change",
            "periodic_check",
            "manual_trigger",
            "",  # Empty string
        ]

        with patch.object(
            self.controller, "collect_heartbeat_data", return_value=mock_payload
        ) as mock_collect:
            for reason in reasons:
                result = await self.controller.force_heartbeat(reason)

                assert result == mock_payload
                assert result.monitoring_status == MonitoringStatusEnum.ACTIVE

            # Verify collect was called for each reason
            assert mock_collect.call_count == len(reasons)


class TestHeartbeatControllerIntegration:
    """Test HeartbeatController integration with dependencies"""

    def setup_method(self):
        """Set up test fixtures"""
        self.controller = HeartbeatController("org1", "site1", "device1")

    @pytest.mark.asyncio
    async def test_heartbeat_data_collection_end_to_end(self):
        """Test: End-to-end heartbeat data collection flow"""
        # Create a realistic status record
        mock_status_record = Mock()
        mock_status_record.cpu_usage_percent = 55.5
        mock_status_record.memory_usage_percent = 72.3
        mock_status_record.disk_usage_percent = 45.8
        mock_status_record.temperature_celsius = 38.9
        mock_status_record.uptime_seconds = 172800  # 2 days
        mock_status_record.load_average = 0.85
        mock_status_record.monitoring_status = MonitoringStatusEnum.ACTIVE
        mock_status_record.mqtt_connection_status = ConnectionStatusEnum.CONNECTED
        mock_status_record.bacnet_connection_status = ConnectionStatusEnum.CONNECTED
        mock_status_record.bacnet_devices_connected = 5
        mock_status_record.bacnet_points_monitored = 250

        with patch(
            "src.controllers.heartbeat_controller.heartbeat.get_latest_iot_device_status"
        ) as mock_get_status:
            mock_get_status.return_value = mock_status_record

            # Test regular heartbeat collection
            regular_result = await self.controller.collect_heartbeat_data()

            # Test force heartbeat
            force_result = await self.controller.force_heartbeat("integration_test")

            # Both should return the same data structure
            assert (
                regular_result.cpu_usage_percent
                == force_result.cpu_usage_percent
                == 55.5
            )
            assert (
                regular_result.memory_usage_percent
                == force_result.memory_usage_percent
                == 72.3
            )
            assert (
                regular_result.bacnet_devices_connected
                == force_result.bacnet_devices_connected
                == 5
            )
            assert (
                regular_result.monitoring_status
                == force_result.monitoring_status
                == MonitoringStatusEnum.ACTIVE
            )

            # Verify database was called for both operations
            assert mock_get_status.call_count >= 2

    @pytest.mark.asyncio
    async def test_heartbeat_controller_with_different_device_ids(self):
        """Test: HeartbeatController works with different device IDs"""
        device_ids = ["device_1", "device_2", "device_3"]

        for device_id in device_ids:
            controller = HeartbeatController("test_org", "test_site", device_id)

            # Mock different status for each device
            mock_status = Mock()
            mock_status.cpu_usage_percent = hash(device_id) % 100  # Different CPU usage
            mock_status.memory_usage_percent = 60.0
            mock_status.disk_usage_percent = 30.0
            mock_status.temperature_celsius = 40.0
            mock_status.uptime_seconds = 3600
            mock_status.load_average = 1.0
            mock_status.monitoring_status = MonitoringStatusEnum.ACTIVE
            mock_status.mqtt_connection_status = ConnectionStatusEnum.CONNECTED
            mock_status.bacnet_connection_status = ConnectionStatusEnum.CONNECTED
            mock_status.bacnet_devices_connected = len(
                device_id
            )  # Use string length as device count
            mock_status.bacnet_points_monitored = len(device_id) * 10

            with patch(
                "src.controllers.heartbeat_controller.heartbeat.get_latest_iot_device_status"
            ) as mock_get_status:
                mock_get_status.return_value = mock_status

                result = await controller.collect_heartbeat_data()

                # Verify correct device ID was used in query
                mock_get_status.assert_called_once_with(device_id)

                # Verify result has expected device-specific data
                assert result.cpu_usage_percent == hash(device_id) % 100
                assert result.bacnet_devices_connected == len(device_id)

    @pytest.mark.asyncio
    async def test_concurrent_heartbeat_operations(self):
        """Test: HeartbeatController handles concurrent operations correctly"""
        mock_status = Mock()
        mock_status.cpu_usage_percent = 40.0
        mock_status.memory_usage_percent = 65.0
        mock_status.disk_usage_percent = 25.0
        mock_status.temperature_celsius = 38.0
        mock_status.uptime_seconds = 7200
        mock_status.load_average = 0.8
        mock_status.monitoring_status = MonitoringStatusEnum.ACTIVE
        mock_status.mqtt_connection_status = ConnectionStatusEnum.CONNECTED
        mock_status.bacnet_connection_status = ConnectionStatusEnum.CONNECTED
        mock_status.bacnet_devices_connected = 2
        mock_status.bacnet_points_monitored = 50

        with patch(
            "src.controllers.heartbeat_controller.heartbeat.get_latest_iot_device_status"
        ) as mock_get_status:
            mock_get_status.return_value = mock_status

            # Run multiple concurrent operations
            tasks = [
                self.controller.collect_heartbeat_data(),
                self.controller.force_heartbeat("concurrent_test_1"),
                self.controller.collect_heartbeat_data(),
                self.controller.force_heartbeat("concurrent_test_2"),
            ]

            results = await asyncio.gather(*tasks)

            # All results should be identical and valid
            for result in results:
                assert isinstance(result, HeartbeatStatusPayload)
                assert result.cpu_usage_percent == 40.0
                assert result.monitoring_status == MonitoringStatusEnum.ACTIVE
                assert result.bacnet_devices_connected == 2

            # Database should have been called for each operation
            assert mock_get_status.call_count >= 4


class TestHeartbeatControllerErrorScenarios:
    """Test HeartbeatController error handling and edge cases"""

    def setup_method(self):
        """Set up test fixtures"""
        self.controller = HeartbeatController("org1", "site1", "device1")

    @pytest.mark.asyncio
    async def test_database_timeout_error(self):
        """Test: HeartbeatController handles database timeout errors"""
        with patch(
            "src.controllers.heartbeat_controller.heartbeat.get_latest_iot_device_status"
        ) as mock_get_status:
            mock_get_status.side_effect = asyncio.TimeoutError("Database query timeout")

            result = await self.controller.collect_heartbeat_data()

            # Should return error state payload
            assert result.mqtt_connection_status == ConnectionStatusEnum.ERROR
            assert result.bacnet_connection_status == ConnectionStatusEnum.ERROR
            assert result.cpu_usage_percent is None

    @pytest.mark.asyncio
    async def test_database_connection_error(self):
        """Test: HeartbeatController handles database connection errors"""
        with patch(
            "src.controllers.heartbeat_controller.heartbeat.get_latest_iot_device_status"
        ) as mock_get_status:
            mock_get_status.side_effect = ConnectionError(
                "Failed to connect to database"
            )

            result = await self.controller.force_heartbeat("connection_test")

            # Should return error state payload
            assert result.mqtt_connection_status == ConnectionStatusEnum.ERROR
            assert result.bacnet_connection_status == ConnectionStatusEnum.ERROR

    @pytest.mark.asyncio
    async def test_invalid_status_record_data(self):
        """Test: HeartbeatController handles invalid status record data"""
        # Mock status record with invalid/corrupted data
        mock_status_record = Mock()
        mock_status_record.cpu_usage_percent = "invalid_cpu"  # String instead of float
        mock_status_record.memory_usage_percent = 150.0  # Invalid percentage > 100
        mock_status_record.monitoring_status = "invalid_status"  # Invalid enum value
        mock_status_record.mqtt_connection_status = None
        mock_status_record.bacnet_connection_status = ConnectionStatusEnum.CONNECTED
        mock_status_record.bacnet_devices_connected = -1  # Negative value

        with patch(
            "src.controllers.heartbeat_controller.heartbeat.get_latest_iot_device_status"
        ) as mock_get_status:
            mock_get_status.return_value = mock_status_record

            # Should handle invalid data gracefully (Pydantic validation will catch issues)
            try:
                result = await self.controller.collect_heartbeat_data()
                # If Pydantic validation passes, result should be valid
                assert isinstance(result, HeartbeatStatusPayload)
            except Exception:
                # If validation fails, should catch and return error payload
                result = await self.controller.collect_heartbeat_data()
                assert result.mqtt_connection_status == ConnectionStatusEnum.ERROR

    @pytest.mark.asyncio
    async def test_empty_device_id_initialization(self):
        """Test: HeartbeatController with empty device ID"""
        controller = HeartbeatController("org", "site", "")

        with patch(
            "src.controllers.heartbeat_controller.heartbeat.get_latest_iot_device_status"
        ) as mock_get_status:
            mock_get_status.return_value = None

            result = await controller.collect_heartbeat_data()

            # Should call database with empty string
            mock_get_status.assert_called_once_with("")

            # Should return empty payload
            assert isinstance(result, HeartbeatStatusPayload)
            assert result.cpu_usage_percent is None

    @pytest.mark.asyncio
    async def test_none_values_in_status_record(self):
        """Test: HeartbeatController handles None values in status record"""
        mock_status_record = Mock()
        # All optional fields set to None
        mock_status_record.cpu_usage_percent = None
        mock_status_record.memory_usage_percent = None
        mock_status_record.disk_usage_percent = None
        mock_status_record.temperature_celsius = None
        mock_status_record.uptime_seconds = None
        mock_status_record.load_average = None
        mock_status_record.monitoring_status = None
        mock_status_record.mqtt_connection_status = None
        mock_status_record.bacnet_connection_status = None
        mock_status_record.bacnet_devices_connected = None
        mock_status_record.bacnet_points_monitored = None

        with patch(
            "src.controllers.heartbeat_controller.heartbeat.get_latest_iot_device_status"
        ) as mock_get_status:
            mock_get_status.return_value = mock_status_record

            result = await self.controller.collect_heartbeat_data()

            # Should handle None values gracefully
            assert isinstance(result, HeartbeatStatusPayload)
            assert result.cpu_usage_percent is None
            assert result.memory_usage_percent is None
            assert result.monitoring_status is None
            assert result.mqtt_connection_status is None
            assert result.bacnet_devices_connected is None
