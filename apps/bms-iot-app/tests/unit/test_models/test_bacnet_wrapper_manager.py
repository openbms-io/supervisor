"""
Test BACnet wrapper manager functionality.

User Story: As a developer, I want wrapper management to handle multiple connections
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from src.actors.messages.message_type import BacnetReaderConfig
from src.models.bacnet_wrapper_manager import BACnetWrapperManager


class TestBACnetWrapperManager:
    """Test BACnetWrapperManager class functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.manager = BACnetWrapperManager()

    def test_bacnet_wrapper_manager_initialization(self):
        """Test: BACnetWrapperManager initializes correctly"""
        manager = BACnetWrapperManager()

        # Manager should start with empty wrapper dictionary and proper initialization
        assert hasattr(manager, "_wrappers")
        assert isinstance(manager._wrappers, dict)
        assert len(manager._wrappers) == 0
        assert hasattr(manager, "_load_balancer")
        assert hasattr(manager, "_initialized")
        assert manager._initialized is False
        assert manager._default_wrapper is None

    @pytest.mark.asyncio
    async def test_initialize_single_reader(self):
        """Test: Initialize a single BACnet reader"""
        reader_config = BacnetReaderConfig(
            id="reader_1",
            ip_address="192.168.1.100",
            subnet_mask=24,
            bacnet_device_id=1001,
            port=47808,
            bbmd_enabled=False,
            is_active=True,
        )

        with patch("src.models.bacnet_wrapper_manager.BACnetWrapper") as MockWrapper:
            mock_wrapper_instance = AsyncMock()
            mock_wrapper_instance.instance_id = "reader_1"
            mock_wrapper_instance.start = AsyncMock()
            MockWrapper.return_value = mock_wrapper_instance

            await self.manager.initialize_readers([reader_config])

            # Verify wrapper was created using public methods
            all_wrappers = self.manager.get_all_wrappers()
            assert "reader_1" in all_wrappers
            assert all_wrappers["reader_1"] == mock_wrapper_instance

            # Verify manager is initialized
            assert self.manager.is_initialized() is True

            # Verify start was called
            mock_wrapper_instance.start.assert_called_once()

            # Verify default wrapper was set
            default_wrapper = self.manager.get_wrapper()
            assert default_wrapper == mock_wrapper_instance

    @pytest.mark.asyncio
    async def test_initialize_multiple_readers(self):
        """Test: Initialize multiple BACnet readers"""
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
                port=47809,
                bbmd_enabled=True,
                bbmd_server_ip="192.168.1.200",
                is_active=True,
            ),
            BacnetReaderConfig(
                id="reader_3",
                ip_address="192.168.1.102",
                subnet_mask=24,
                bacnet_device_id=1003,
                port=47810,
                bbmd_enabled=False,
                is_active=False,  # Inactive reader
            ),
        ]

        with patch("src.models.bacnet_wrapper_manager.BACnetWrapper") as MockWrapper:
            # Create different mock instances for each active wrapper
            mock_wrappers = []
            for config in reader_configs:
                if config.is_active:
                    mock_wrapper = AsyncMock()
                    mock_wrapper.instance_id = config.id
                    mock_wrapper.start = AsyncMock()
                    mock_wrappers.append(mock_wrapper)

            # Return different instances for each call
            MockWrapper.side_effect = mock_wrappers

            await self.manager.initialize_readers(reader_configs)

            # Only active readers should be initialized
            all_wrappers = self.manager.get_all_wrappers()
            assert len(all_wrappers) == 2
            assert "reader_1" in all_wrappers
            assert "reader_2" in all_wrappers
            assert "reader_3" not in all_wrappers  # Inactive

            # Verify each active wrapper was started
            for wrapper in mock_wrappers:
                wrapper.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_existing_wrappers_before_reinit(self):
        """Test: Cleanup existing wrappers before reinitializing"""
        # Setup existing wrapper by directly setting it (simulate previous initialization)
        existing_wrapper = AsyncMock()
        existing_wrapper.is_connected = AsyncMock(return_value=True)
        existing_wrapper.disconnect = AsyncMock(return_value=True)
        self.manager._wrappers = {"old_reader": existing_wrapper}
        self.manager._default_wrapper = existing_wrapper
        self.manager._initialized = True

        # New reader configuration
        reader_config = BacnetReaderConfig(
            id="new_reader",
            ip_address="192.168.1.100",
            subnet_mask=24,
            bacnet_device_id=1001,
            port=47808,
            bbmd_enabled=False,
            is_active=True,
        )

        with patch("src.models.bacnet_wrapper_manager.BACnetWrapper") as MockWrapper:
            new_wrapper = AsyncMock()
            new_wrapper.instance_id = "new_reader"
            new_wrapper.start = AsyncMock()
            MockWrapper.return_value = new_wrapper

            await self.manager.initialize_readers([reader_config])

            # Old wrapper should be cleaned up
            existing_wrapper.disconnect.assert_called_once()

            # New wrapper should replace old ones
            all_wrappers = self.manager.get_all_wrappers()
            assert len(all_wrappers) == 1
            assert "new_reader" in all_wrappers
            assert "old_reader" not in all_wrappers

    @pytest.mark.asyncio
    async def test_get_wrapper_for_operation_single_wrapper(self):
        """Test: Get wrapper for operation with single wrapper available"""
        mock_wrapper = AsyncMock()
        mock_wrapper.instance_id = "reader_1"

        # Simulate having wrappers by setting them directly
        self.manager._wrappers = {"reader_1": mock_wrapper}

        # Mock the load balancer's select_wrapper method
        with patch.object(self.manager._load_balancer, "select_wrapper") as mock_select:
            mock_select.return_value = mock_wrapper

            result = await self.manager.get_wrapper_for_operation()

            assert result == mock_wrapper
            mock_select.assert_called_once_with({"reader_1": mock_wrapper})

    @pytest.mark.asyncio
    async def test_get_wrapper_for_operation_no_wrappers(self):
        """Test: Get wrapper when no wrappers available"""
        # No wrappers in manager
        self.manager._wrappers = {}

        result = await self.manager.get_wrapper_for_operation()

        assert result is None

    def test_get_all_wrappers(self):
        """Test: Get all available wrappers"""
        mock_wrapper_1 = AsyncMock()
        mock_wrapper_2 = AsyncMock()

        self.manager._wrappers = {
            "reader_1": mock_wrapper_1,
            "reader_2": mock_wrapper_2,
        }

        all_wrappers = self.manager.get_all_wrappers()

        assert len(all_wrappers) == 2
        assert all_wrappers["reader_1"] == mock_wrapper_1
        assert all_wrappers["reader_2"] == mock_wrapper_2

        # Should return a copy, not the original dict
        assert all_wrappers is not self.manager._wrappers

    def test_get_all_wrappers_empty(self):
        """Test: Get all wrappers when none exist"""
        self.manager._wrappers = {}

        all_wrappers = self.manager.get_all_wrappers()

        assert len(all_wrappers) == 0
        assert isinstance(all_wrappers, dict)

    def test_get_wrapper_by_id(self):
        """Test: Get specific wrapper by ID"""
        mock_wrapper_1 = AsyncMock()
        mock_wrapper_2 = AsyncMock()

        self.manager._wrappers = {
            "reader_1": mock_wrapper_1,
            "reader_2": mock_wrapper_2,
        }
        self.manager._default_wrapper = mock_wrapper_1

        # Get specific wrapper
        result = self.manager.get_wrapper("reader_2")
        assert result == mock_wrapper_2

        # Get default wrapper (no ID provided)
        result = self.manager.get_wrapper()
        assert result == mock_wrapper_1

        # Get non-existent wrapper
        result = self.manager.get_wrapper("non_existent")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_utilization_info(self):
        """Test: Get wrapper utilization information"""
        # Mock wrappers
        mock_wrapper_1 = AsyncMock()
        mock_wrapper_2 = AsyncMock()

        self.manager._wrappers = {
            "reader_1": mock_wrapper_1,
            "reader_2": mock_wrapper_2,
        }

        expected_utilization = {
            "reader_1": {"operations": 100, "connections": 5},
            "reader_2": {"operations": 150, "connections": 3},
        }

        # Mock the load balancer's get_utilization_info method
        with patch.object(
            self.manager._load_balancer, "get_utilization_info"
        ) as mock_util:
            mock_util.return_value = expected_utilization

            utilization = await self.manager.get_utilization_info()

            assert utilization == expected_utilization
            mock_util.assert_called_once_with(
                {"reader_1": mock_wrapper_1, "reader_2": mock_wrapper_2}
            )

    @pytest.mark.asyncio
    async def test_wrapper_initialization_error_handling(self):
        """Test: Handle errors during wrapper initialization"""
        reader_config = BacnetReaderConfig(
            id="failing_reader",
            ip_address="192.168.1.100",
            subnet_mask=24,
            bacnet_device_id=1001,
            port=47808,
            bbmd_enabled=False,
            is_active=True,
        )

        with patch("src.models.bacnet_wrapper_manager.BACnetWrapper") as MockWrapper:
            mock_wrapper = AsyncMock()
            mock_wrapper.instance_id = "failing_reader"
            mock_wrapper.start.side_effect = Exception("Initialization failed")
            MockWrapper.return_value = mock_wrapper

            # Should not raise exception but log error
            await self.manager.initialize_readers([reader_config])

            # Wrapper should not be added if initialization fails
            all_wrappers = self.manager.get_all_wrappers()
            assert "failing_reader" not in all_wrappers

    def test_is_initialized(self):
        """Test: Check initialization status"""
        # Initially not initialized
        assert self.manager.is_initialized() is False

        # After setting initialized flag
        self.manager._initialized = True
        assert self.manager.is_initialized() is True


class TestBACnetWrapperManagerLoadBalancing:
    """Test load balancing functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.manager = BACnetWrapperManager()

    def test_set_load_balancing_strategy(self):
        """Test: Set different load balancing strategies"""
        from src.models.bacnet_reader_load_balancer import LoadBalancingStrategy

        # Test setting different strategies
        self.manager.set_load_balancing_strategy(LoadBalancingStrategy.LEAST_BUSY)
        # Can't directly test the internal strategy, but method should not raise exception

        self.manager.set_load_balancing_strategy(LoadBalancingStrategy.FIRST_AVAILABLE)
        # Should work without exception

    def test_reset_load_balancing(self):
        """Test: Reset load balancing state"""
        # Should not raise exception
        self.manager.reset_load_balancing()

        # Mock the load balancer to verify method is called
        with patch.object(
            self.manager._load_balancer, "reset_round_robin"
        ) as mock_reset:
            self.manager.reset_load_balancing()
            mock_reset.assert_called_once()


class TestBACnetWrapperManagerIntegration:
    """Test BACnetWrapperManager integration scenarios"""

    def setup_method(self):
        """Set up test fixtures"""
        self.manager = BACnetWrapperManager()

    @pytest.mark.asyncio
    async def test_concurrent_wrapper_operations(self):
        """Test: Concurrent operations on multiple wrappers"""
        # Setup mock wrappers
        mock_wrappers = {}
        for i in range(3):
            wrapper = AsyncMock()
            wrapper.instance_id = f"reader_{i}"
            mock_wrappers[f"reader_{i}"] = wrapper

        self.manager._wrappers = mock_wrappers

        # Mock load balancer to return wrappers in round-robin fashion
        with patch.object(self.manager._load_balancer, "select_wrapper") as mock_select:
            mock_select.side_effect = (
                list(mock_wrappers.values()) * 4
            )  # Enough for 10 calls

            # Simulate concurrent wrapper requests
            async def get_wrapper():
                return await self.manager.get_wrapper_for_operation()

            # Execute concurrent operations
            tasks = [get_wrapper() for _ in range(10)]
            results = await asyncio.gather(*tasks)

            # All operations should complete
            assert all(result is not None for result in results)
            assert len(results) == 10

    @pytest.mark.asyncio
    async def test_dynamic_wrapper_reconfiguration(self):
        """Test: Dynamic reconfiguration of wrappers"""
        # Initial configuration with one reader
        initial_config = BacnetReaderConfig(
            id="reader_1",
            ip_address="192.168.1.100",
            subnet_mask=24,
            bacnet_device_id=1001,
            port=47808,
            bbmd_enabled=False,
            is_active=True,
        )

        with patch("src.models.bacnet_wrapper_manager.BACnetWrapper") as MockWrapper:
            mock_wrapper_1 = AsyncMock()
            mock_wrapper_1.instance_id = "reader_1"
            mock_wrapper_1.start = AsyncMock()
            mock_wrapper_1.is_connected = AsyncMock(
                return_value=False
            )  # Not connected for cleanup
            MockWrapper.return_value = mock_wrapper_1

            await self.manager.initialize_readers([initial_config])

            # Verify initial wrapper
            all_wrappers = self.manager.get_all_wrappers()
            assert len(all_wrappers) == 1
            assert "reader_1" in all_wrappers

            # Reconfigure with different readers
            new_configs = [
                BacnetReaderConfig(
                    id="reader_2",
                    ip_address="192.168.1.101",
                    subnet_mask=24,
                    bacnet_device_id=1002,
                    port=47808,
                    bbmd_enabled=False,
                    is_active=True,
                ),
                BacnetReaderConfig(
                    id="reader_3",
                    ip_address="192.168.1.102",
                    subnet_mask=24,
                    bacnet_device_id=1003,
                    port=47808,
                    bbmd_enabled=False,
                    is_active=True,
                ),
            ]

            # Create new mock wrappers for the reconfiguration
            mock_wrappers = []
            for config in new_configs:
                wrapper = AsyncMock()
                wrapper.instance_id = config.id
                wrapper.start = AsyncMock()
                mock_wrappers.append(wrapper)

            MockWrapper.side_effect = mock_wrappers

            await self.manager.initialize_readers(new_configs)

            # Verify new configuration
            all_wrappers = self.manager.get_all_wrappers()
            assert len(all_wrappers) == 2
            assert "reader_2" in all_wrappers
            assert "reader_3" in all_wrappers
            assert "reader_1" not in all_wrappers  # Should be cleaned up


class TestBACnetWrapperManagerEdgeCases:
    """Test BACnetWrapperManager edge cases and error conditions"""

    def setup_method(self):
        """Set up test fixtures"""
        self.manager = BACnetWrapperManager()

    @pytest.mark.asyncio
    async def test_empty_reader_configuration(self):
        """Test: Handle empty reader configuration list"""
        await self.manager.initialize_readers([])

        all_wrappers = self.manager.get_all_wrappers()
        assert len(all_wrappers) == 0

        wrapper = await self.manager.get_wrapper_for_operation()
        assert wrapper is None

        # Manager should still be considered initialized even with no readers
        assert self.manager.is_initialized() is True

    @pytest.mark.asyncio
    async def test_all_inactive_readers(self):
        """Test: Handle configuration with all inactive readers"""
        reader_configs = [
            BacnetReaderConfig(
                id="inactive_1",
                ip_address="192.168.1.100",
                subnet_mask=24,
                bacnet_device_id=1001,
                port=47808,
                bbmd_enabled=False,
                is_active=False,
            ),
            BacnetReaderConfig(
                id="inactive_2",
                ip_address="192.168.1.101",
                subnet_mask=24,
                bacnet_device_id=1002,
                port=47809,
                bbmd_enabled=False,
                is_active=False,
            ),
        ]

        await self.manager.initialize_readers(reader_configs)

        # No wrappers should be created for inactive readers
        all_wrappers = self.manager.get_all_wrappers()
        assert len(all_wrappers) == 0

        # Getting wrapper should return None
        wrapper = await self.manager.get_wrapper_for_operation()
        assert wrapper is None

    @pytest.mark.asyncio
    async def test_cleanup_wrapper_error_handling(self):
        """Test: Handle errors during wrapper cleanup"""
        # Setup wrapper that fails during cleanup
        failing_wrapper = AsyncMock()
        failing_wrapper.is_connected = AsyncMock(return_value=True)
        failing_wrapper.disconnect = AsyncMock(side_effect=Exception("Cleanup failed"))

        self.manager._wrappers = {"failing_cleanup": failing_wrapper}
        self.manager._default_wrapper = failing_wrapper
        self.manager._initialized = True

        # Should not crash during cleanup
        await self.manager.cleanup()

        # Wrapper dictionary should still be cleared despite error
        all_wrappers = self.manager.get_all_wrappers()
        assert len(all_wrappers) == 0
        assert self.manager._default_wrapper is None
        assert self.manager._initialized is False

    @pytest.mark.asyncio
    async def test_duplicate_endpoint_handling(self):
        """Test: Handle readers with duplicate IP+port combinations"""
        reader_configs = [
            BacnetReaderConfig(
                id="reader_1",
                ip_address="192.168.1.100",
                subnet_mask=24,
                bacnet_device_id=1001,
                port=47808,  # Same IP+port
                bbmd_enabled=False,
                is_active=True,
            ),
            BacnetReaderConfig(
                id="reader_2",
                ip_address="192.168.1.100",
                subnet_mask=24,
                bacnet_device_id=1002,
                port=47808,  # Same IP+port as reader_1
                bbmd_enabled=False,
                is_active=True,
            ),
        ]

        with patch("src.models.bacnet_wrapper_manager.BACnetWrapper") as MockWrapper:
            mock_wrapper = AsyncMock()
            mock_wrapper.instance_id = "reader_1"
            mock_wrapper.start = AsyncMock()
            MockWrapper.return_value = mock_wrapper

            await self.manager.initialize_readers(reader_configs)

            # Only first reader with unique endpoint should be initialized
            all_wrappers = self.manager.get_all_wrappers()
            assert len(all_wrappers) == 1
            assert "reader_1" in all_wrappers
            assert "reader_2" not in all_wrappers
