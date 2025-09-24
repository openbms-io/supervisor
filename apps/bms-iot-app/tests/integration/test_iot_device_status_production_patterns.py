"""
Integration tests for IoT device status covering production usage patterns.
Tests how actors and main.py use upsert_iot_device_status in real scenarios.
"""

import pytest
import asyncio
import time

from src.models.iot_device_status import (
    upsert_iot_device_status,
    get_latest_iot_device_status,
    update_system_metrics,
)
from src.models.device_status_enums import MonitoringStatusEnum, ConnectionStatusEnum


# Database setup is now handled by global conftest.py fixture


class TestBacnetMonitoringActorPatterns:
    """Test patterns used by BacnetMonitoringActor"""

    @pytest.mark.asyncio
    async def test_monitoring_status_update_pattern(self):
        """Test the pattern used in BacnetMonitoringActor.update_monitoring_status"""
        device_id = f"bacnet-monitoring-{int(time.time())}"

        # Simulate BacnetMonitoringActor pattern for updating monitoring status
        status = MonitoringStatusEnum.ACTIVE
        status_data = {
            "organization_id": "test-org",
            "site_id": "test-site",
            "monitoring_status": status,
        }

        result = await upsert_iot_device_status(device_id, status_data)

        assert result is not None
        assert result.iot_device_id == device_id
        assert result.monitoring_status == status

        # Test transitioning to ERROR state
        error_status_data = {"monitoring_status": MonitoringStatusEnum.ERROR}

        error_result = await upsert_iot_device_status(device_id, error_status_data)

        assert error_result is not None
        assert error_result.iot_device_id == device_id
        assert error_result.monitoring_status == MonitoringStatusEnum.ERROR
        # Should preserve other fields
        assert error_result.organization_id == "test-org"
        assert error_result.site_id == "test-site"

    @pytest.mark.asyncio
    async def test_bacnet_status_update_pattern(self):
        """Test the pattern used in BacnetMonitoringActor.update_bacnet_status"""
        device_id = f"bacnet-status-{int(time.time())}"

        # Simulate the pattern from update_bacnet_status
        bacnet_readers = ["192.168.1.100", "192.168.1.101"]  # Mock readers
        status_data = {
            "organization_id": "test-org",
            "site_id": "test-site",
            "bacnet_devices_connected": len(bacnet_readers),  # Use correct field name
            "bacnet_connection_status": ConnectionStatusEnum.CONNECTED,
        }

        result = await upsert_iot_device_status(device_id, status_data)

        assert result is not None
        assert result.iot_device_id == device_id
        assert result.bacnet_devices_connected == 2  # Use correct field name
        assert result.bacnet_connection_status == ConnectionStatusEnum.CONNECTED

    @pytest.mark.asyncio
    async def test_bacnet_connection_status_update_pattern(self):
        """Test the pattern used in BacnetMonitoringActor.update_bacnet_connection_status"""
        device_id = f"bacnet-conn-{int(time.time())}"

        # First create device with required fields
        initial_data = {
            "organization_id": "test-org",
            "site_id": "test-site",
            "monitoring_status": MonitoringStatusEnum.ACTIVE,
        }
        await upsert_iot_device_status(device_id, initial_data)

        # Test CONNECTED status
        connected_status_data = {
            "bacnet_connection_status": ConnectionStatusEnum.CONNECTED
        }

        result = await upsert_iot_device_status(device_id, connected_status_data)

        assert result is not None
        assert result.iot_device_id == device_id
        assert result.bacnet_connection_status == ConnectionStatusEnum.CONNECTED

        # Test transitioning to DISCONNECTED
        disconnected_status_data = {
            "bacnet_connection_status": ConnectionStatusEnum.DISCONNECTED
        }

        result = await upsert_iot_device_status(device_id, disconnected_status_data)

        assert result is not None
        assert result.bacnet_connection_status == ConnectionStatusEnum.DISCONNECTED


class TestMQTTActorPatterns:
    """Test patterns used by MQTTActor"""

    @pytest.mark.asyncio
    async def test_mqtt_connection_status_update_pattern(self):
        """Test the pattern used in MQTTActor.update_mqtt_connection_status"""
        device_id = f"mqtt-conn-{int(time.time())}"

        # First create device with required fields
        initial_data = {
            "organization_id": "test-org",
            "site_id": "test-site",
            "monitoring_status": MonitoringStatusEnum.ACTIVE,
        }
        await upsert_iot_device_status(device_id, initial_data)

        # Test CONNECTED status (pattern from MQTTActor)
        status = ConnectionStatusEnum.CONNECTED
        status_data = {"mqtt_connection_status": status}

        result = await upsert_iot_device_status(device_id, status_data)

        assert result is not None
        assert result.iot_device_id == device_id
        assert result.mqtt_connection_status == status

        # Test transitioning to DISCONNECTED
        disconnect_status_data = {
            "mqtt_connection_status": ConnectionStatusEnum.DISCONNECTED
        }

        result = await upsert_iot_device_status(device_id, disconnect_status_data)

        assert result is not None
        assert result.mqtt_connection_status == ConnectionStatusEnum.DISCONNECTED


class TestMainAppInitializationPatterns:
    """Test patterns used in main.py for app initialization"""

    @pytest.mark.asyncio
    async def test_main_app_initialization_pattern(self):
        """Test the pattern used in main.py for initializing device status"""
        device_id = f"main-init-{int(time.time())}"

        # Simulate the pattern from main.py initialization
        organization_id = "test-org-main"
        site_id = "test-site-main"

        status_data = {
            "organization_id": organization_id,
            "site_id": site_id,
            "monitoring_status": MonitoringStatusEnum.INITIALIZING,
            "mqtt_connection_status": ConnectionStatusEnum.DISCONNECTED,
            "bacnet_connection_status": ConnectionStatusEnum.DISCONNECTED,
        }

        result = await upsert_iot_device_status(device_id, status_data)

        assert result is not None
        assert result.iot_device_id == device_id
        assert result.organization_id == organization_id
        assert result.site_id == site_id
        assert result.monitoring_status == MonitoringStatusEnum.INITIALIZING
        assert result.mqtt_connection_status == ConnectionStatusEnum.DISCONNECTED
        assert result.bacnet_connection_status == ConnectionStatusEnum.DISCONNECTED

        # Simulate transitioning to ACTIVE after successful initialization
        active_status_data = {
            "monitoring_status": MonitoringStatusEnum.ACTIVE,
            "mqtt_connection_status": ConnectionStatusEnum.CONNECTED,
        }

        active_result = await upsert_iot_device_status(device_id, active_status_data)

        assert active_result is not None
        assert active_result.monitoring_status == MonitoringStatusEnum.ACTIVE
        assert active_result.mqtt_connection_status == ConnectionStatusEnum.CONNECTED
        # Should preserve initialization values
        assert active_result.organization_id == organization_id
        assert active_result.site_id == site_id


class TestSystemMetricsUpdatePatterns:
    """Test patterns for system metrics updates"""

    @pytest.mark.asyncio
    async def test_system_metrics_helper_function(self):
        """Test the update_system_metrics helper function used by actors"""
        device_id = f"system-metrics-{int(time.time())}"

        # First create device with required fields
        initial_data = {
            "organization_id": "test-org",
            "site_id": "test-site",
            "monitoring_status": MonitoringStatusEnum.ACTIVE,
        }
        await upsert_iot_device_status(device_id, initial_data)

        # Test initial metrics update
        initial_metrics = {
            "cpu_usage_percent": 25.5,
            "memory_usage_percent": 45.2,
            "disk_usage_percent": 67.8,
        }

        result = await update_system_metrics(device_id, initial_metrics)

        assert result is not None
        assert result.iot_device_id == device_id
        assert result.cpu_usage_percent == 25.5
        assert result.memory_usage_percent == 45.2
        assert result.disk_usage_percent == 67.8

        # Test updating only some metrics
        partial_metrics = {"cpu_usage_percent": 85.0, "memory_usage_percent": 92.1}

        partial_result = await update_system_metrics(device_id, partial_metrics)

        assert partial_result is not None
        assert partial_result.cpu_usage_percent == 85.0
        assert partial_result.memory_usage_percent == 92.1
        # Should preserve other metrics
        assert partial_result.disk_usage_percent == 67.8


class TestProductionScenarioSimulation:
    """Simulate realistic production scenarios"""

    @pytest.mark.asyncio
    async def test_full_device_lifecycle_simulation(self):
        """Simulate a complete device lifecycle from startup to active monitoring"""
        device_id = f"lifecycle-{int(time.time())}"
        org_id = "production-org"
        site_id = "production-site"

        # Step 1: Application startup - Initialize device status (main.py pattern)
        init_data = {
            "organization_id": org_id,
            "site_id": site_id,
            "monitoring_status": MonitoringStatusEnum.INITIALIZING,
            "mqtt_connection_status": ConnectionStatusEnum.DISCONNECTED,
            "bacnet_connection_status": ConnectionStatusEnum.DISCONNECTED,
        }

        init_result = await upsert_iot_device_status(device_id, init_data)
        assert init_result is not None
        assert init_result.monitoring_status == MonitoringStatusEnum.INITIALIZING

        # Step 2: MQTT connection established (MQTTActor pattern)
        mqtt_connected_data = {"mqtt_connection_status": ConnectionStatusEnum.CONNECTED}

        mqtt_result = await upsert_iot_device_status(device_id, mqtt_connected_data)
        assert mqtt_result is not None
        assert mqtt_result.mqtt_connection_status == ConnectionStatusEnum.CONNECTED
        # Should preserve init data
        assert mqtt_result.organization_id == org_id
        assert mqtt_result.monitoring_status == MonitoringStatusEnum.INITIALIZING

        # Step 3: BACnet connection established (BacnetMonitoringActor pattern)
        bacnet_connected_data = {
            "bacnet_connection_status": ConnectionStatusEnum.CONNECTED,
            "bacnet_devices_connected": 3,  # Use correct field name
        }

        bacnet_result = await upsert_iot_device_status(device_id, bacnet_connected_data)
        assert bacnet_result is not None
        assert bacnet_result.bacnet_connection_status == ConnectionStatusEnum.CONNECTED
        assert bacnet_result.bacnet_devices_connected == 3

        # Step 4: System becomes active (BacnetMonitoringActor pattern)
        active_data = {"monitoring_status": MonitoringStatusEnum.ACTIVE}

        active_result = await upsert_iot_device_status(device_id, active_data)
        assert active_result is not None
        assert active_result.monitoring_status == MonitoringStatusEnum.ACTIVE
        # Should preserve all connection statuses
        assert active_result.mqtt_connection_status == ConnectionStatusEnum.CONNECTED
        assert active_result.bacnet_connection_status == ConnectionStatusEnum.CONNECTED
        assert active_result.bacnet_devices_connected == 3

        # Step 5: Regular system metrics updates
        metrics_data = {
            "cpu_usage_percent": 45.2,
            "memory_usage_percent": 67.8,
            "disk_usage_percent": 23.1,
        }

        metrics_result = await update_system_metrics(device_id, metrics_data)
        assert metrics_result is not None
        assert metrics_result.cpu_usage_percent == 45.2
        # Should preserve all previous state
        assert metrics_result.monitoring_status == MonitoringStatusEnum.ACTIVE
        assert metrics_result.mqtt_connection_status == ConnectionStatusEnum.CONNECTED
        assert metrics_result.bacnet_connection_status == ConnectionStatusEnum.CONNECTED

    @pytest.mark.asyncio
    async def test_concurrent_actor_updates(self):
        """Test concurrent updates from multiple actors (realistic production scenario)"""
        device_id = f"concurrent-actors-{int(time.time())}"

        # First create device with required fields
        initial_data = {
            "organization_id": "test-org",
            "site_id": "test-site",
            "monitoring_status": MonitoringStatusEnum.ACTIVE,
        }
        await upsert_iot_device_status(device_id, initial_data)

        async def mqtt_actor_simulation():
            """Simulate MQTT actor updates"""
            for i in range(5):
                status_data = {
                    "mqtt_connection_status": ConnectionStatusEnum.CONNECTED,
                }
                await upsert_iot_device_status(device_id, status_data)
                await asyncio.sleep(0.01)

        async def bacnet_actor_simulation():
            """Simulate BACnet monitoring actor updates"""
            for i in range(5):
                status_data = {
                    "bacnet_connection_status": ConnectionStatusEnum.CONNECTED,
                    "bacnet_devices_connected": i + 1,  # Use correct field name
                }
                await upsert_iot_device_status(device_id, status_data)
                await asyncio.sleep(0.01)

        async def system_metrics_simulation():
            """Simulate system metrics updates"""
            for i in range(5):
                metrics = {
                    "cpu_usage_percent": float(10 + i * 5),
                    "memory_usage_percent": float(20 + i * 10),
                }
                await update_system_metrics(device_id, metrics)
                await asyncio.sleep(0.01)

        # Run all actor simulations concurrently
        results = await asyncio.gather(
            mqtt_actor_simulation(),
            bacnet_actor_simulation(),
            system_metrics_simulation(),
            return_exceptions=True,
        )

        # Verify no exceptions occurred
        exceptions = [r for r in results if isinstance(r, Exception)]
        assert len(exceptions) == 0, f"Concurrent actor updates failed: {exceptions}"

        # Verify final state
        final_status = await get_latest_iot_device_status(device_id)
        assert final_status is not None
        assert final_status.iot_device_id == device_id
        # Should have data from all actors
        assert final_status.mqtt_connection_status == ConnectionStatusEnum.CONNECTED
        assert final_status.bacnet_connection_status == ConnectionStatusEnum.CONNECTED
        assert final_status.cpu_usage_percent is not None
        assert final_status.memory_usage_percent is not None
