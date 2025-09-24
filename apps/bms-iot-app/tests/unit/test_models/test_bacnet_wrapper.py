"""
Test BACnet wrapper functionality.

User Story: As a developer, I want BACnet wrapper to abstract BAC0 complexity
"""

import pytest
import asyncio
import sys
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# Mock BAC0 before importing BACnetWrapper
sys.modules["BAC0"] = MagicMock()


# Delayed imports after mocking
def _import_test_modules():
    from src.actors.messages.message_type import BacnetReaderConfig
    from src.models.bacnet_wrapper import BACnetWrapper

    return BacnetReaderConfig, BACnetWrapper


BacnetReaderConfig, BACnetWrapper = _import_test_modules()


class TestBACnetWrapper:
    """Test BACnetWrapper class functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.reader_config = BacnetReaderConfig(
            id="test_wrapper",
            ip_address="192.168.1.100",
            subnet_mask=24,
            bacnet_device_id=1001,
            port=47808,
            bbmd_enabled=False,
            is_active=True,
        )
        self.wrapper = BACnetWrapper(self.reader_config)

    def test_bacnet_wrapper_initialization(self):
        """Test: BACnetWrapper initializes with correct parameters"""
        reader_config = BacnetReaderConfig(
            id="wrapper_1",
            ip_address="192.168.1.100",
            subnet_mask=24,
            bacnet_device_id=1001,
            port=47808,
            bbmd_enabled=False,
            is_active=True,
        )

        wrapper = BACnetWrapper(reader_config)

        assert wrapper.reader_config == reader_config
        assert wrapper.ip == "192.168.1.100"
        assert wrapper.subnet_mask == 24
        assert wrapper.device_id == 1001
        assert wrapper.port == 47808
        assert wrapper.bbmd_enabled is False
        assert wrapper._bacnet is None  # Not connected yet
        assert wrapper._bacnet_connected is False

    def test_bacnet_wrapper_with_bbmd(self):
        """Test: BACnetWrapper initialization with BBMD enabled"""
        reader_config = BacnetReaderConfig(
            id="wrapper_bbmd",
            ip_address="192.168.1.101",
            subnet_mask=24,
            bacnet_device_id=1002,
            port=47808,
            bbmd_enabled=True,
            bbmd_server_ip="192.168.1.200",
            is_active=True,
        )

        wrapper = BACnetWrapper(reader_config)

        assert wrapper.bbmd_enabled is True
        assert wrapper.bbmd_server_ip == "192.168.1.200"

    def test_instance_id_property(self):
        """Test: instance_id property returns correct format"""
        reader_config = BacnetReaderConfig(
            id="test_reader",
            ip_address="192.168.1.100",
            subnet_mask=24,
            bacnet_device_id=1001,
            port=47808,
            bbmd_enabled=False,
            is_active=True,
        )

        wrapper = BACnetWrapper(reader_config)

        expected_id = "test_reader(192.168.1.100:47808)"
        assert wrapper.instance_id == expected_id

    @pytest.mark.asyncio
    async def test_start_connection(self):
        """Test: Start BACnet connection"""
        with patch("src.models.bacnet_wrapper.BAC0.connect") as mock_bac0_connect:
            mock_network = AsyncMock()
            mock_bac0_connect.return_value = mock_network

            await self.wrapper.start()

            # Verify BAC0.connect was called
            mock_bac0_connect.assert_called_once()
            call_kwargs = mock_bac0_connect.call_args.kwargs

            # Check connection parameters
            assert "ip" in call_kwargs
            assert call_kwargs["ip"] == "192.168.1.100"

            # Verify connection state
            assert self.wrapper._bacnet == mock_network
            assert self.wrapper._bacnet_connected is True

    @pytest.mark.asyncio
    async def test_start_with_bbmd_connection(self):
        """Test: Start BACnet connection with BBMD"""
        reader_config = BacnetReaderConfig(
            id="wrapper_bbmd",
            ip_address="192.168.1.101",
            subnet_mask=24,
            bacnet_device_id=1002,
            port=47808,
            bbmd_enabled=True,
            bbmd_server_ip="192.168.1.200",
            is_active=True,
        )
        wrapper = BACnetWrapper(reader_config)

        with patch("src.models.bacnet_wrapper.BAC0.connect") as mock_bac0_connect:
            mock_network = AsyncMock()
            mock_bac0_connect.return_value = mock_network

            await wrapper.start()

            # Verify BBMD configuration was included
            mock_bac0_connect.assert_called_once()
            call_kwargs = mock_bac0_connect.call_args.kwargs
            assert "bbmdAddress" in call_kwargs
            assert call_kwargs["bbmdAddress"] == "192.168.1.200"

    @pytest.mark.asyncio
    async def test_is_busy(self):
        """Test: Check if wrapper is busy"""
        # Initially not busy
        is_busy = await self.wrapper.is_busy()
        assert is_busy is False

        # Simulate active operations
        self.wrapper._active_operations = 2
        is_busy = await self.wrapper.is_busy()
        assert is_busy is True

    @pytest.mark.asyncio
    async def test_who_is_device_discovery(self):
        """Test: Device discovery using who_is"""
        # Mock BAC0 network and discovered devices
        mock_network = AsyncMock()
        mock_device_1 = Mock()
        mock_device_1.iAmDeviceIdentifier = (1, 12345)
        mock_device_1.vendorID = 999
        mock_device_1.pduSource = "192.168.1.100:47808"

        mock_network.who_is = AsyncMock(return_value=[mock_device_1])
        self.wrapper._bacnet = mock_network
        self.wrapper._bacnet_connected = True

        devices = await self.wrapper.who_is("192.168.1.100")

        # Verify who_is was called
        mock_network.who_is.assert_called_once_with("192.168.1.100")

        # Verify devices returned
        assert len(devices) == 1
        assert devices[0].iAmDeviceIdentifier == (1, 12345)

    @pytest.mark.asyncio
    async def test_read_present_value(self):
        """Test: Read present value from a point"""
        mock_network = AsyncMock()
        mock_network.read = AsyncMock(return_value=25.5)
        self.wrapper._bacnet = mock_network
        self.wrapper._bacnet_connected = True

        value = await self.wrapper.read_present_value("192.168.1.100", "analogInput", 1)

        # Verify read was called
        mock_network.read.assert_called_once()

        assert value == 25.5

    @pytest.mark.asyncio
    async def test_read_properties(self):
        """Test: Read multiple properties from a point"""
        mock_network = AsyncMock()
        # Mock readMultiple to return list of values
        mock_network.readMultiple = AsyncMock(
            return_value=[
                (25.5,),  # presentValue as tuple
                ([0, 0, 0, 0],),  # statusFlags as tuple
                ("degreesCelsius",),  # units as tuple
            ]
        )
        self.wrapper._bacnet = mock_network
        self.wrapper._bacnet_connected = True

        properties = await self.wrapper.read_properties(
            device_ip="192.168.1.100",
            object_type="analogInput",
            object_id=1,
            properties=["presentValue", "statusFlags", "units"],
        )

        # Verify readMultiple was called
        mock_network.readMultiple.assert_called_once()

        # Verify properties were extracted correctly
        assert properties["presentValue"] == 25.5
        assert properties["statusFlags"] == [0, 0, 0, 0]
        assert properties["units"] == "degreesCelsius"

    @pytest.mark.asyncio
    async def test_write_with_priority(self):
        """Test: Write value to point with priority"""
        mock_network = AsyncMock()
        mock_network._write = AsyncMock(return_value=True)
        mock_network.read = AsyncMock(return_value=30.0)  # Verification read
        self.wrapper._bacnet = mock_network
        self.wrapper._bacnet_connected = True

        result = await self.wrapper.write_with_priority(
            ip="192.168.1.100",
            objectType="analogOutput",
            point_id=1,
            present_value=30.0,
            priority=8,
        )

        # Verify write was called
        mock_network._write.assert_called_once()

        # Verify read was called for verification
        mock_network.read.assert_called_once()

        assert result == 30.0

    @pytest.mark.asyncio
    async def test_read_object_list(self):
        """Test: Read object list from device"""
        mock_network = AsyncMock()
        mock_object_list = [
            ("analogInput", 1),
            ("analogInput", 2),
            ("analogOutput", 1),
            ("binaryInput", 1),
        ]
        mock_network.read = AsyncMock(return_value=mock_object_list)
        self.wrapper._bacnet = mock_network
        self.wrapper._bacnet_connected = True

        object_list = await self.wrapper.read_object_list(
            ip="192.168.1.100", device_id=12345
        )

        # Verify read was called with correct parameters
        mock_network.read.assert_called_once()
        call_kwargs = mock_network.read.call_args.kwargs
        assert "args" in call_kwargs
        assert "192.168.1.100 device 12345 objectList" in call_kwargs["args"]

        assert object_list == mock_object_list

    @pytest.mark.asyncio
    async def test_is_connected(self):
        """Test: Check connection status"""
        # Initially not connected
        assert await self.wrapper.is_connected() is False

        # After setting connected flag
        self.wrapper._bacnet_connected = True
        assert await self.wrapper.is_connected() is True

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test: Disconnect network connection"""
        mock_network = AsyncMock()
        mock_network._disconnect = AsyncMock()
        self.wrapper._bacnet = mock_network
        self.wrapper._bacnet_connected = True

        with patch("asyncio.sleep"):  # Mock sleep to speed up test
            result = await self.wrapper.disconnect()

        # Verify disconnect was called
        mock_network._disconnect.assert_called_once()

        # Connection should be cleared
        assert self.wrapper._bacnet_connected is False
        assert self.wrapper._bacnet is None
        assert result is True


class TestBACnetWrapperErrorHandling:
    """Test BACnetWrapper error handling"""

    def setup_method(self):
        """Set up test fixtures"""
        self.reader_config = BacnetReaderConfig(
            id="test_wrapper",
            ip_address="192.168.1.100",
            subnet_mask=24,
            bacnet_device_id=1001,
            port=47808,
            bbmd_enabled=False,
            is_active=True,
        )
        self.wrapper = BACnetWrapper(self.reader_config)

    @pytest.mark.asyncio
    async def test_start_failure(self):
        """Test: Handle start/connection failure"""
        with patch("src.models.bacnet_wrapper.BAC0.connect") as mock_bac0_connect:
            mock_bac0_connect.side_effect = Exception("Network initialization failed")

            with pytest.raises(Exception, match="Network initialization failed"):
                await self.wrapper.start()

            # Connection state should remain False
            assert self.wrapper._bacnet_connected is False
            assert self.wrapper._bacnet is None

    @pytest.mark.asyncio
    async def test_read_error_handling(self):
        """Test: Handle read operation errors"""
        mock_network = AsyncMock()
        mock_network.read.side_effect = Exception("Read timeout")
        self.wrapper._bacnet = mock_network
        self.wrapper._bacnet_connected = True

        with pytest.raises(Exception, match="Read timeout"):
            await self.wrapper.read_present_value("192.168.1.100", "analogInput", 1)

    @pytest.mark.asyncio
    async def test_write_error_handling(self):
        """Test: Handle write operation errors"""
        mock_network = AsyncMock()
        mock_network._write.side_effect = Exception("Write failed")
        self.wrapper._bacnet = mock_network
        self.wrapper._bacnet_connected = True

        with pytest.raises(Exception, match="Write failed"):
            await self.wrapper.write(
                "192.168.1.100 analogOutput 1 presentValue 30.0 - 8"
            )

    @pytest.mark.asyncio
    async def test_who_is_error_handling(self):
        """Test: Handle who_is discovery errors"""
        mock_network = AsyncMock()
        mock_network.who_is.side_effect = Exception("Discovery failed")
        self.wrapper._bacnet = mock_network
        self.wrapper._bacnet_connected = True

        with pytest.raises(Exception, match="Discovery failed"):
            await self.wrapper.who_is("192.168.1.100")

    @pytest.mark.asyncio
    async def test_read_with_no_network(self):
        """Test: Read operation with no network initialized"""
        # Network is None (not connected)
        self.wrapper._bacnet = None
        self.wrapper._bacnet_connected = False

        # Mock BAC0.connect to fail to prevent auto-connection
        with patch(
            "src.models.bacnet_wrapper.BAC0.connect",
            side_effect=Exception("Connection failed"),
        ):
            with pytest.raises(Exception):  # Could be RuntimeError or connection error
                await self.wrapper.read_present_value("192.168.1.100", "analogInput", 1)

    @pytest.mark.asyncio
    async def test_disconnect_with_no_network(self):
        """Test: Disconnect when no network exists"""
        self.wrapper._bacnet = None
        self.wrapper._bacnet_connected = False

        # Should return False (already disconnected)
        result = await self.wrapper.disconnect()
        assert result is False

    @pytest.mark.asyncio
    async def test_disconnect_error_handling(self):
        """Test: Handle errors during disconnect"""
        mock_network = AsyncMock()
        mock_network._disconnect.side_effect = Exception("Disconnect failed")
        self.wrapper._bacnet = mock_network
        self.wrapper._bacnet_connected = True

        with patch("asyncio.sleep"):  # Mock sleep to speed up test
            result = await self.wrapper.disconnect()

        # Should return False on error
        assert result is False


class TestBACnetWrapperIntegration:
    """Test BACnetWrapper integration scenarios"""

    @pytest.mark.asyncio
    async def test_complete_read_workflow(self):
        """Test: Complete workflow from initialization to read"""
        reader_config = BacnetReaderConfig(
            id="integration_wrapper",
            ip_address="192.168.1.100",
            subnet_mask=24,
            bacnet_device_id=1001,
            port=47808,
            bbmd_enabled=False,
            is_active=True,
        )
        wrapper = BACnetWrapper(reader_config)

        with patch("src.models.bacnet_wrapper.BAC0.connect") as mock_bac0_connect:
            mock_network = AsyncMock()
            mock_network.read = AsyncMock(return_value=25.5)
            mock_network._disconnect = AsyncMock()
            mock_bac0_connect.return_value = mock_network

            # Start connection
            await wrapper.start()

            # Read value
            value = await wrapper.read_present_value("192.168.1.100", "analogInput", 1)

            # Disconnect
            with patch("asyncio.sleep"):  # Mock sleep
                await wrapper.disconnect()

            assert value == 25.5
            mock_network._disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_multiple_operations(self):
        """Test: Multiple operations on same wrapper"""
        reader_config = BacnetReaderConfig(
            id="multi_op_wrapper",
            ip_address="192.168.1.100",
            subnet_mask=24,
            bacnet_device_id=1001,
            port=47808,
            bbmd_enabled=False,
            is_active=True,
        )
        wrapper = BACnetWrapper(reader_config)

        mock_network = AsyncMock()
        mock_network.read = AsyncMock(side_effect=[20.0, 21.0, 22.0])
        mock_network._write = AsyncMock(return_value=True)
        wrapper._bacnet = mock_network
        wrapper._bacnet_connected = True

        # Multiple reads
        value1 = await wrapper.read_present_value("192.168.1.100", "analogInput", 1)
        value2 = await wrapper.read_present_value("192.168.1.100", "analogInput", 2)
        value3 = await wrapper.read_present_value("192.168.1.100", "analogInput", 3)

        # Write operation
        await wrapper.write("192.168.1.100 analogOutput 1 presentValue 25.0 - 8")

        assert value1 == 20.0
        assert value2 == 21.0
        assert value3 == 22.0
        assert mock_network.read.call_count == 3
        mock_network._write.assert_called_once()

    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test: Concurrent operations on wrapper"""
        reader_config = BacnetReaderConfig(
            id="concurrent_wrapper",
            ip_address="192.168.1.100",
            subnet_mask=24,
            bacnet_device_id=1001,
            port=47808,
            bbmd_enabled=False,
            is_active=True,
        )
        wrapper = BACnetWrapper(reader_config)

        mock_network = AsyncMock()
        mock_network.read = AsyncMock(return_value=25.0)
        wrapper._bacnet = mock_network
        wrapper._bacnet_connected = True

        # Concurrent read operations
        tasks = [
            wrapper.read_present_value("192.168.1.100", "analogInput", i)
            for i in range(5)
        ]

        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        assert all(r == 25.0 for r in results)
        assert mock_network.read.call_count == 5

    @pytest.mark.asyncio
    async def test_operation_counting(self):
        """Test: Active operation counting for load balancing"""
        reader_config = BacnetReaderConfig(
            id="counting_wrapper",
            ip_address="192.168.1.100",
            subnet_mask=24,
            bacnet_device_id=1001,
            port=47808,
            bbmd_enabled=False,
            is_active=True,
        )
        wrapper = BACnetWrapper(reader_config)

        # Initially no active operations
        assert wrapper._active_operations == 0
        assert await wrapper.is_busy() is False

        # Test simpler case - after operation completes, count should be reset
        mock_network = AsyncMock()
        mock_network.read = AsyncMock(return_value=25.0)
        wrapper._bacnet = mock_network
        wrapper._bacnet_connected = True

        # Perform operation
        result = await wrapper.read_present_value("192.168.1.100", "analogInput", 1)

        # After operation completes, should not be busy
        assert await wrapper.is_busy() is False
        assert wrapper._active_operations == 0
        assert result == 25.0

        # Test multiple concurrent operations (though they'll be serialized by the lock)
        tasks = []
        for i in range(3):
            task = asyncio.create_task(
                wrapper.read_present_value("192.168.1.100", "analogInput", i)
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        # All operations should complete successfully
        assert len(results) == 3
        assert all(r == 25.0 for r in results)

        # After all operations complete, should not be busy
        assert await wrapper.is_busy() is False
        assert wrapper._active_operations == 0


class TestBACnetWrapperEdgeCases:
    """Test BACnetWrapper edge cases"""

    @pytest.mark.asyncio
    async def test_write_verification_mismatch(self):
        """Test: Write operation with verification mismatch"""
        reader_config = BacnetReaderConfig(
            id="test_wrapper",
            ip_address="192.168.1.100",
            subnet_mask=24,
            bacnet_device_id=1001,
            port=47808,
            bbmd_enabled=False,
            is_active=True,
        )
        wrapper = BACnetWrapper(reader_config)

        mock_network = AsyncMock()
        mock_network._write = AsyncMock(return_value=True)
        mock_network.read = AsyncMock(return_value=25.0)  # Different from written value
        wrapper._bacnet = mock_network
        wrapper._bacnet_connected = True

        # Should raise exception due to verification mismatch
        with pytest.raises(Exception, match="Write failed"):
            await wrapper.write_with_priority(
                ip="192.168.1.100",
                objectType="analogOutput",
                point_id=1,
                present_value=30.0,  # Different from read result
                priority=8,
            )

    @pytest.mark.asyncio
    async def test_read_properties_error_handling(self):
        """Test: Handle errors in property extraction"""
        reader_config = BacnetReaderConfig(
            id="test_wrapper",
            ip_address="192.168.1.100",
            subnet_mask=24,
            bacnet_device_id=1001,
            port=47808,
            bbmd_enabled=False,
            is_active=True,
        )
        wrapper = BACnetWrapper(reader_config)

        mock_network = AsyncMock()
        # Mock malformed response that could cause extraction errors
        mock_network.readMultiple = AsyncMock(return_value=[])  # Empty response
        wrapper._bacnet = mock_network
        wrapper._bacnet_connected = True

        # Should handle empty response gracefully
        properties = await wrapper.read_properties(
            device_ip="192.168.1.100",
            object_type="analogInput",
            object_id=1,
            properties=["presentValue", "statusFlags"],
        )

        # Should set missing properties to None
        assert properties["presentValue"] is None
        assert properties["statusFlags"] is None
