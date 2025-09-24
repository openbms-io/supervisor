"""
Test BACnet monitoring controller logic.

User Story: As a developer, I want BACnet monitoring logic to work independently
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from src.actors.messages.message_type import BacnetReaderConfig
from src.controllers.monitoring.monitor import BACnetMonitor


class TestBACnetMonitor:
    """Test BACnetMonitor class functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.monitor = BACnetMonitor()

    def test_bacnet_monitor_initialization(self):
        """Test: BACnetMonitor initializes correctly"""
        monitor = BACnetMonitor()

        # BACnetMonitor initializes with minimal state
        assert monitor is not None
        assert hasattr(monitor, "initialize")
        assert hasattr(monitor, "initialize_bacnet_readers")
        assert hasattr(monitor, "discover_devices")

    @pytest.mark.asyncio
    async def test_initialize_method_compatibility(self):
        """Test: Initialize method exists for backward compatibility"""
        # Should not raise any exceptions
        await self.monitor.initialize()

        # Since it's a no-op method, just verify it completes
        assert True

    @pytest.mark.asyncio
    async def test_initialize_bacnet_readers_with_valid_configs(self):
        """Test: BACnet reader initialization with valid configurations"""
        # Create test reader configurations
        reader_configs = [
            BacnetReaderConfig(
                id="reader_1",
                ip_address="192.168.1.100",
                subnet_mask=24,
                bacnet_device_id=1001,
                port=47808,
                bbmd_enabled=False,
                is_active=True,
            ),
            BacnetReaderConfig(
                id="reader_2",
                ip_address="192.168.1.101",
                subnet_mask=24,
                bacnet_device_id=1002,
                port=47808,
                bbmd_enabled=True,
                bbmd_server_ip="192.168.1.200",
                is_active=True,
            ),
        ]

        with patch(
            "src.controllers.monitoring.monitor.bacnet_wrapper_manager"
        ) as mock_manager:
            # Mock successful initialization
            mock_manager.initialize_readers = AsyncMock()
            mock_manager.get_all_wrappers.return_value = {
                "reader_1": Mock(),
                "reader_2": Mock(),
            }

            await self.monitor.initialize_bacnet_readers(reader_configs)

            # Verify manager was called with correct configs
            mock_manager.initialize_readers.assert_called_once_with(reader_configs)
            mock_manager.get_all_wrappers.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_bacnet_readers_with_empty_configs(self):
        """Test: BACnet reader initialization with empty configuration list"""
        with patch(
            "src.controllers.monitoring.monitor.bacnet_wrapper_manager"
        ) as mock_manager:
            mock_manager.initialize_readers = AsyncMock()
            mock_manager.get_all_wrappers.return_value = {}

            await self.monitor.initialize_bacnet_readers([])

            # Should still call the manager methods
            mock_manager.initialize_readers.assert_called_once_with([])
            mock_manager.get_all_wrappers.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_bacnet_readers_with_manager_error(self):
        """Test: BACnet reader initialization handles manager errors"""
        reader_configs = [
            BacnetReaderConfig(
                id="reader_1",
                ip_address="192.168.1.100",
                subnet_mask=24,
                bacnet_device_id=1001,
                port=47808,
                bbmd_enabled=False,
                is_active=True,
            )
        ]

        with patch(
            "src.controllers.monitoring.monitor.bacnet_wrapper_manager"
        ) as mock_manager:
            # Mock manager initialization failure
            mock_manager.initialize_readers.side_effect = Exception(
                "Wrapper initialization failed"
            )

            # Should propagate the exception
            with pytest.raises(Exception, match="Wrapper initialization failed"):
                await self.monitor.initialize_bacnet_readers(reader_configs)

    @pytest.mark.asyncio
    async def test_discover_devices_with_single_address(self):
        """Test: Device discovery with single address"""
        device_addresses = ["192.168.1.100"]

        # Mock discovered device
        mock_device = Mock()
        mock_device.iAmDeviceIdentifier = (1, 12345)  # instance, device_id
        mock_device.vendorID = 999
        mock_device.pduSource = "192.168.1.100:47808"

        # Mock wrapper
        mock_wrapper = Mock()
        mock_wrapper.instance_id = "reader_1"
        mock_wrapper.who_is = AsyncMock(return_value=[mock_device])

        with patch(
            "src.controllers.monitoring.monitor.bacnet_wrapper_manager"
        ) as mock_manager:
            mock_manager.get_all_wrappers.return_value = {"reader_1": mock_wrapper}

            devices = await self.monitor.discover_devices(device_addresses)

            # Verify discovery was called
            mock_wrapper.who_is.assert_called_once_with(address="192.168.1.100")

            # Verify device information
            assert len(devices) == 1
            device = devices[0]
            assert device["iam_device_identifier"] == (1, 12345)
            assert device["vendor_id"] == 999
            assert device["device_id"] == 12345
            assert device["address"] == "192.168.1.100:47808"
            assert device["discovered_by_reader"] == "reader_1"

    @pytest.mark.asyncio
    async def test_discover_devices_with_multiple_addresses(self):
        """Test: Device discovery with multiple addresses"""
        device_addresses = ["192.168.1.100", "192.168.1.101", "192.168.1.102"]

        # Mock different devices for different addresses
        mock_device_1 = Mock()
        mock_device_1.iAmDeviceIdentifier = (1, 100)
        mock_device_1.vendorID = 999
        mock_device_1.pduSource = "192.168.1.100:47808"

        mock_device_2 = Mock()
        mock_device_2.iAmDeviceIdentifier = (1, 101)
        mock_device_2.vendorID = 888
        mock_device_2.pduSource = "192.168.1.101:47808"

        mock_wrapper = Mock()
        mock_wrapper.instance_id = "reader_1"

        # Different responses for different addresses
        async def mock_who_is(address):
            if address == "192.168.1.100":
                return [mock_device_1]
            elif address == "192.168.1.101":
                return [mock_device_2]
            else:
                return []  # No devices at third address

        mock_wrapper.who_is = AsyncMock(side_effect=mock_who_is)

        with patch(
            "src.controllers.monitoring.monitor.bacnet_wrapper_manager"
        ) as mock_manager:
            mock_manager.get_all_wrappers.return_value = {"reader_1": mock_wrapper}

            devices = await self.monitor.discover_devices(device_addresses)

            # Verify all addresses were queried
            assert mock_wrapper.who_is.call_count == 3

            # Verify two devices were discovered
            assert len(devices) == 2

            # Check device details
            device_ids = [d["device_id"] for d in devices]
            assert 100 in device_ids
            assert 101 in device_ids

    @pytest.mark.asyncio
    async def test_discover_devices_with_multiple_wrappers(self):
        """Test: Device discovery using multiple BACnet wrappers"""
        device_addresses = ["192.168.1.100"]

        # Mock device found by first wrapper
        mock_device_1 = Mock()
        mock_device_1.iAmDeviceIdentifier = (1, 100)
        mock_device_1.vendorID = 999
        mock_device_1.pduSource = "192.168.1.100:47808"

        # Mock device found by second wrapper
        mock_device_2 = Mock()
        mock_device_2.iAmDeviceIdentifier = (1, 200)
        mock_device_2.vendorID = 888
        mock_device_2.pduSource = "192.168.1.100:47809"

        # Mock two wrappers
        mock_wrapper_1 = Mock()
        mock_wrapper_1.instance_id = "reader_1"
        mock_wrapper_1.who_is = AsyncMock(return_value=[mock_device_1])

        mock_wrapper_2 = Mock()
        mock_wrapper_2.instance_id = "reader_2"
        mock_wrapper_2.who_is = AsyncMock(return_value=[mock_device_2])

        with patch(
            "src.controllers.monitoring.monitor.bacnet_wrapper_manager"
        ) as mock_manager:
            mock_manager.get_all_wrappers.return_value = {
                "reader_1": mock_wrapper_1,
                "reader_2": mock_wrapper_2,
            }

            devices = await self.monitor.discover_devices(device_addresses)

            # Both wrappers should be used
            mock_wrapper_1.who_is.assert_called_once_with(address="192.168.1.100")
            mock_wrapper_2.who_is.assert_called_once_with(address="192.168.1.100")

            # Should find devices from both wrappers
            assert len(devices) == 2

            # Check that devices were discovered by different readers
            readers = [d["discovered_by_reader"] for d in devices]
            assert "reader_1" in readers
            assert "reader_2" in readers

    @pytest.mark.asyncio
    async def test_discover_devices_with_wrapper_errors(self):
        """Test: Device discovery handles individual wrapper errors gracefully"""
        device_addresses = ["192.168.1.100"]

        # Mock successful device
        mock_device = Mock()
        mock_device.iAmDeviceIdentifier = (1, 100)
        mock_device.vendorID = 999
        mock_device.pduSource = "192.168.1.100:47808"

        # Mock two wrappers - one fails, one succeeds
        mock_wrapper_1 = Mock()
        mock_wrapper_1.instance_id = "reader_1"
        mock_wrapper_1.who_is = AsyncMock(side_effect=Exception("Network error"))

        mock_wrapper_2 = Mock()
        mock_wrapper_2.instance_id = "reader_2"
        mock_wrapper_2.who_is = AsyncMock(return_value=[mock_device])

        with patch(
            "src.controllers.monitoring.monitor.bacnet_wrapper_manager"
        ) as mock_manager:
            mock_manager.get_all_wrappers.return_value = {
                "reader_1": mock_wrapper_1,
                "reader_2": mock_wrapper_2,
            }

            devices = await self.monitor.discover_devices(device_addresses)

            # Should still get device from successful wrapper
            assert len(devices) == 1
            assert devices[0]["discovered_by_reader"] == "reader_2"

    @pytest.mark.asyncio
    async def test_discover_devices_with_no_wrappers(self):
        """Test: Device discovery with no available wrappers"""
        device_addresses = ["192.168.1.100"]

        with patch(
            "src.controllers.monitoring.monitor.bacnet_wrapper_manager"
        ) as mock_manager:
            mock_manager.get_all_wrappers.return_value = {}

            devices = await self.monitor.discover_devices(device_addresses)

            # Should return empty list
            assert len(devices) == 0

    @pytest.mark.asyncio
    async def test_discover_devices_with_no_devices_found(self):
        """Test: Device discovery when no devices respond"""
        device_addresses = ["192.168.1.100", "192.168.1.101"]

        mock_wrapper = Mock()
        mock_wrapper.instance_id = "reader_1"
        mock_wrapper.who_is = AsyncMock(return_value=[])  # No devices found

        with patch(
            "src.controllers.monitoring.monitor.bacnet_wrapper_manager"
        ) as mock_manager:
            mock_manager.get_all_wrappers.return_value = {"reader_1": mock_wrapper}

            devices = await self.monitor.discover_devices(device_addresses)

            # Should call who_is for each address
            assert mock_wrapper.who_is.call_count == 2

            # Should return empty list
            assert len(devices) == 0


class TestBACnetMonitorIntegration:
    """Test BACnetMonitor integration scenarios"""

    def setup_method(self):
        """Set up test fixtures"""
        self.monitor = BACnetMonitor()

    @pytest.mark.asyncio
    async def test_full_initialization_and_discovery_flow(self):
        """Test: Complete flow from reader initialization to device discovery"""
        # Reader configurations
        reader_configs = [
            BacnetReaderConfig(
                id="reader_1",
                ip_address="192.168.1.100",
                subnet_mask=24,
                bacnet_device_id=1001,
                port=47808,
                bbmd_enabled=False,
                is_active=True,
            )
        ]

        # Mock discovered device
        mock_device = Mock()
        mock_device.iAmDeviceIdentifier = (1, 12345)
        mock_device.vendorID = 999
        mock_device.pduSource = "192.168.1.100:47808"

        # Mock wrapper
        mock_wrapper = Mock()
        mock_wrapper.instance_id = "reader_1"
        mock_wrapper.who_is = AsyncMock(return_value=[mock_device])

        with patch(
            "src.controllers.monitoring.monitor.bacnet_wrapper_manager"
        ) as mock_manager:
            # Mock initialization
            mock_manager.initialize_readers = AsyncMock()
            mock_manager.get_all_wrappers.return_value = {"reader_1": mock_wrapper}

            # Initialize readers
            await self.monitor.initialize_bacnet_readers(reader_configs)

            # Discover devices
            devices = await self.monitor.discover_devices(["192.168.1.100"])

            # Verify full flow
            mock_manager.initialize_readers.assert_called_once_with(reader_configs)
            mock_wrapper.who_is.assert_called_once()
            assert len(devices) == 1
            assert devices[0]["device_id"] == 12345

    @pytest.mark.asyncio
    async def test_multiple_readers_multiple_devices(self):
        """Test: Multiple readers discovering multiple devices"""
        reader_configs = [
            BacnetReaderConfig(
                id="reader_1",
                ip_address="192.168.1.100",
                subnet_mask=24,
                bacnet_device_id=1001,
                port=47808,
                bbmd_enabled=False,
                is_active=True,
            ),
            BacnetReaderConfig(
                id="reader_2",
                ip_address="192.168.1.101",
                subnet_mask=24,
                bacnet_device_id=1002,
                port=47808,
                bbmd_enabled=False,
                is_active=True,
            ),
        ]

        # Mock devices for different readers
        mock_device_1 = Mock()
        mock_device_1.iAmDeviceIdentifier = (1, 100)
        mock_device_1.vendorID = 999
        mock_device_1.pduSource = "192.168.1.100:47808"

        mock_device_2 = Mock()
        mock_device_2.iAmDeviceIdentifier = (1, 200)
        mock_device_2.vendorID = 888
        mock_device_2.pduSource = "192.168.1.101:47808"

        # Mock wrappers
        mock_wrapper_1 = Mock()
        mock_wrapper_1.instance_id = "reader_1"
        mock_wrapper_1.who_is = AsyncMock(return_value=[mock_device_1])

        mock_wrapper_2 = Mock()
        mock_wrapper_2.instance_id = "reader_2"
        mock_wrapper_2.who_is = AsyncMock(return_value=[mock_device_2])

        with patch(
            "src.controllers.monitoring.monitor.bacnet_wrapper_manager"
        ) as mock_manager:
            mock_manager.initialize_readers = AsyncMock()
            mock_manager.get_all_wrappers.return_value = {
                "reader_1": mock_wrapper_1,
                "reader_2": mock_wrapper_2,
            }

            # Initialize readers
            await self.monitor.initialize_bacnet_readers(reader_configs)

            # Discover devices on network
            devices = await self.monitor.discover_devices(["192.168.1.0/24"])

            # Verify results
            assert len(devices) == 2
            device_ids = [d["device_id"] for d in devices]
            assert 100 in device_ids
            assert 200 in device_ids

            readers = [d["discovered_by_reader"] for d in devices]
            assert "reader_1" in readers
            assert "reader_2" in readers

    @pytest.mark.asyncio
    async def test_reader_initialization_failure_recovery(self):
        """Test: Recovery when some reader initialization fails"""
        reader_configs = [
            BacnetReaderConfig(
                id="reader_1",
                ip_address="192.168.1.100",
                subnet_mask=24,
                bacnet_device_id=1001,
                port=47808,
                bbmd_enabled=False,
                is_active=True,
            ),
            BacnetReaderConfig(
                id="reader_2",
                ip_address="192.168.1.101",
                subnet_mask=24,
                bacnet_device_id=1002,
                port=47808,
                bbmd_enabled=False,
                is_active=True,
            ),
        ]

        # Mock only one wrapper initialized successfully
        mock_wrapper_1 = Mock()
        mock_wrapper_1.instance_id = "reader_1"
        mock_wrapper_1.who_is = AsyncMock(return_value=[])

        with patch(
            "src.controllers.monitoring.monitor.bacnet_wrapper_manager"
        ) as mock_manager:
            mock_manager.initialize_readers = AsyncMock()
            # Only one wrapper available (reader_2 failed to initialize)
            mock_manager.get_all_wrappers.return_value = {"reader_1": mock_wrapper_1}

            # Initialize readers (some may fail internally)
            await self.monitor.initialize_bacnet_readers(reader_configs)

            # Discovery should still work with available wrapper
            devices = await self.monitor.discover_devices(["192.168.1.100"])

            # Should not crash, even if no devices found
            assert isinstance(devices, list)
            mock_wrapper_1.who_is.assert_called_once()


class TestBACnetMonitorEdgeCases:
    """Test BACnetMonitor edge cases and error conditions"""

    def setup_method(self):
        """Set up test fixtures"""
        self.monitor = BACnetMonitor()

    @pytest.mark.asyncio
    async def test_discover_devices_with_malformed_device_response(self):
        """Test: Device discovery handles malformed device responses"""
        device_addresses = ["192.168.1.100"]

        # Mock malformed device response
        mock_device = Mock()
        # Missing or invalid required attributes
        mock_device.iAmDeviceIdentifier = None
        mock_device.vendorID = "invalid"
        mock_device.pduSource = 12345  # Should be string

        mock_wrapper = Mock()
        mock_wrapper.instance_id = "reader_1"
        mock_wrapper.who_is = AsyncMock(return_value=[mock_device])

        with patch(
            "src.controllers.monitoring.monitor.bacnet_wrapper_manager"
        ) as mock_manager:
            mock_manager.get_all_wrappers.return_value = {"reader_1": mock_wrapper}

            # Should handle malformed response gracefully
            devices = await self.monitor.discover_devices(device_addresses)

            # May return empty or partial results depending on error handling
            assert isinstance(devices, list)

    @pytest.mark.asyncio
    async def test_discover_devices_with_empty_address_list(self):
        """Test: Device discovery with empty address list"""
        mock_wrapper = Mock()
        mock_wrapper.instance_id = "reader_1"
        mock_wrapper.who_is = AsyncMock()

        with patch(
            "src.controllers.monitoring.monitor.bacnet_wrapper_manager"
        ) as mock_manager:
            mock_manager.get_all_wrappers.return_value = {"reader_1": mock_wrapper}

            devices = await self.monitor.discover_devices([])

            # Should return empty list without calling who_is
            assert len(devices) == 0
            mock_wrapper.who_is.assert_not_called()

    @pytest.mark.asyncio
    async def test_concurrent_discovery_operations(self):
        """Test: Concurrent device discovery operations"""

        mock_device = Mock()
        mock_device.iAmDeviceIdentifier = (1, 100)
        mock_device.vendorID = 999
        mock_device.pduSource = "192.168.1.100:47808"

        mock_wrapper = Mock()
        mock_wrapper.instance_id = "reader_1"
        mock_wrapper.who_is = AsyncMock(return_value=[mock_device])

        with patch(
            "src.controllers.monitoring.monitor.bacnet_wrapper_manager"
        ) as mock_manager:
            mock_manager.get_all_wrappers.return_value = {"reader_1": mock_wrapper}

            # Run multiple concurrent discovery operations
            tasks = [
                self.monitor.discover_devices(["192.168.1.100"]),
                self.monitor.discover_devices(["192.168.1.101"]),
                self.monitor.discover_devices(["192.168.1.102"]),
            ]

            results = await asyncio.gather(*tasks)

            # All operations should complete
            assert len(results) == 3
            for result in results:
                assert isinstance(result, list)

            # Verify who_is was called for each operation
            assert mock_wrapper.who_is.call_count >= 3
