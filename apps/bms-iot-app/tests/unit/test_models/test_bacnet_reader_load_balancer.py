"""
Test BACnet reader load balancer functionality.

User Story: As a developer, I want load balancing to distribute workload across readers
"""

import pytest
import asyncio
import sys
from unittest.mock import AsyncMock, MagicMock

# Mock BAC0 before importing BACnetWrapper
sys.modules["BAC0"] = MagicMock()


# Delayed imports after mocking
def _import_test_modules():
    from src.models.bacnet_reader_load_balancer import (
        BACnetReaderLoadBalancer,
        LoadBalancingStrategy,
    )

    return BACnetReaderLoadBalancer, LoadBalancingStrategy


BACnetReaderLoadBalancer, LoadBalancingStrategy = _import_test_modules()


class TestBACnetReaderLoadBalancer:
    """Test BACnetReaderLoadBalancer class functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.load_balancer = BACnetReaderLoadBalancer()

        # Create mock wrappers for testing
        self.mock_wrappers = {}
        for i in range(3):
            wrapper = AsyncMock()
            wrapper.instance_id = f"wrapper_{i}"
            wrapper.ip = f"192.168.1.{100 + i}"
            wrapper.port = 47808
            wrapper.get_active_operations_count = AsyncMock(
                return_value=i
            )  # Different load levels
            wrapper.is_busy = AsyncMock(return_value=i > 0)
            self.mock_wrappers[f"wrapper_{i}"] = wrapper

    def test_load_balancer_initialization(self):
        """Test: BACnetReaderLoadBalancer initializes with correct defaults"""
        lb = BACnetReaderLoadBalancer()

        assert lb.strategy == LoadBalancingStrategy.ROUND_ROBIN
        assert lb._round_robin_index == 0

    def test_load_balancer_with_custom_strategy(self):
        """Test: BACnetReaderLoadBalancer initializes with custom strategy"""
        lb = BACnetReaderLoadBalancer(LoadBalancingStrategy.LEAST_BUSY)

        assert lb.strategy == LoadBalancingStrategy.LEAST_BUSY
        assert lb._round_robin_index == 0

    def test_set_strategy(self):
        """Test: Set different load balancing strategies"""
        # Test changing to LEAST_BUSY
        self.load_balancer.set_strategy(LoadBalancingStrategy.LEAST_BUSY)
        assert self.load_balancer.strategy == LoadBalancingStrategy.LEAST_BUSY

        # Test changing to FIRST_AVAILABLE
        self.load_balancer.set_strategy(LoadBalancingStrategy.FIRST_AVAILABLE)
        assert self.load_balancer.strategy == LoadBalancingStrategy.FIRST_AVAILABLE

        # Test changing to ROUND_ROBIN (should reset index)
        self.load_balancer._round_robin_index = 5
        self.load_balancer.set_strategy(LoadBalancingStrategy.ROUND_ROBIN)
        assert self.load_balancer.strategy == LoadBalancingStrategy.ROUND_ROBIN
        assert self.load_balancer._round_robin_index == 0

    @pytest.mark.asyncio
    async def test_select_wrapper_empty_dict(self):
        """Test: Select wrapper with empty wrapper dictionary"""
        result = await self.load_balancer.select_wrapper({})
        assert result is None

    @pytest.mark.asyncio
    async def test_select_wrapper_round_robin(self):
        """Test: Round-robin wrapper selection"""
        self.load_balancer.set_strategy(LoadBalancingStrategy.ROUND_ROBIN)

        # Test multiple selections in round-robin fashion
        expected_order = [
            "wrapper_0",
            "wrapper_1",
            "wrapper_2",
            "wrapper_0",
            "wrapper_1",
        ]

        for expected_wrapper_id in expected_order:
            result = await self.load_balancer.select_wrapper(self.mock_wrappers)
            assert result is not None
            assert result.instance_id == expected_wrapper_id

    @pytest.mark.asyncio
    async def test_select_wrapper_round_robin_index_bounds_check(self):
        """Test: Round-robin index bounds checking"""
        self.load_balancer.set_strategy(LoadBalancingStrategy.ROUND_ROBIN)

        # Set index out of bounds
        self.load_balancer._round_robin_index = 10

        result = await self.load_balancer.select_wrapper(self.mock_wrappers)

        # Should reset index and select first wrapper
        assert result is not None
        assert result.instance_id == "wrapper_0"
        assert self.load_balancer._round_robin_index == 1  # Incremented after selection

    @pytest.mark.asyncio
    async def test_select_wrapper_least_busy(self):
        """Test: Least busy wrapper selection"""
        self.load_balancer.set_strategy(LoadBalancingStrategy.LEAST_BUSY)

        # wrapper_0 has 0 operations (least busy)
        result = await self.load_balancer.select_wrapper(self.mock_wrappers)

        assert result is not None
        assert result.instance_id == "wrapper_0"

        # Verify get_active_operations_count was called
        for wrapper in self.mock_wrappers.values():
            wrapper.get_active_operations_count.assert_called_once()

    @pytest.mark.asyncio
    async def test_select_wrapper_first_available(self):
        """Test: First available wrapper selection"""
        self.load_balancer.set_strategy(LoadBalancingStrategy.FIRST_AVAILABLE)

        result = await self.load_balancer.select_wrapper(self.mock_wrappers)

        # Should return the first wrapper in the dictionary
        assert result is not None
        # Dictionary iteration order in Python 3.7+ is insertion order
        assert result.instance_id == "wrapper_0"

    @pytest.mark.asyncio
    async def test_select_wrapper_single_wrapper(self):
        """Test: Wrapper selection with only one wrapper available"""
        single_wrapper = {"wrapper_0": self.mock_wrappers["wrapper_0"]}

        # Test all strategies with single wrapper
        for strategy in LoadBalancingStrategy:
            self.load_balancer.set_strategy(strategy)
            result = await self.load_balancer.select_wrapper(single_wrapper)

            assert result is not None
            assert result.instance_id == "wrapper_0"

    @pytest.mark.asyncio
    async def test_get_utilization_info(self):
        """Test: Get utilization information for wrappers"""
        self.load_balancer.set_strategy(LoadBalancingStrategy.LEAST_BUSY)

        utilization = await self.load_balancer.get_utilization_info(self.mock_wrappers)

        # Should return info for all wrappers
        assert len(utilization) == 3

        for wrapper_id, wrapper in self.mock_wrappers.items():
            assert wrapper_id in utilization
            info = utilization[wrapper_id]

            assert "instance_id" in info
            assert "active_operations" in info
            assert "is_busy" in info
            assert "ip" in info
            assert "port" in info
            assert "strategy" in info

            assert info["instance_id"] == wrapper.instance_id
            assert info["ip"] == wrapper.ip
            assert info["port"] == wrapper.port
            assert info["strategy"] == LoadBalancingStrategy.LEAST_BUSY.value

            # Verify async methods were called
            wrapper.get_active_operations_count.assert_called()
            wrapper.is_busy.assert_called()

    @pytest.mark.asyncio
    async def test_get_available_wrappers_all_available(self):
        """Test: Get available wrappers when all are under threshold"""
        # All wrappers have operations < 5 (default max_operations)
        available = await self.load_balancer.get_available_wrappers(
            self.mock_wrappers, max_operations=5
        )

        assert len(available) == 3
        assert available == self.mock_wrappers

    @pytest.mark.asyncio
    async def test_get_available_wrappers_some_overloaded(self):
        """Test: Get available wrappers when some are overloaded"""
        # Set wrapper_2 to have more operations
        self.mock_wrappers["wrapper_2"].get_active_operations_count = AsyncMock(
            return_value=5
        )

        available = await self.load_balancer.get_available_wrappers(
            self.mock_wrappers, max_operations=3
        )

        # Only wrappers with < 3 operations should be available
        assert len(available) == 2
        assert "wrapper_0" in available  # 0 operations
        assert "wrapper_1" in available  # 1 operation
        assert "wrapper_2" not in available  # 5 operations >= 3

    @pytest.mark.asyncio
    async def test_get_available_wrappers_all_overloaded(self):
        """Test: Get available wrappers when all are overloaded"""
        available = await self.load_balancer.get_available_wrappers(
            self.mock_wrappers, max_operations=0
        )

        # No wrappers should be available (all have >= 0 operations)
        assert len(available) == 0
        assert available == {}

    def test_reset_round_robin(self):
        """Test: Reset round-robin counter"""
        self.load_balancer._round_robin_index = 5

        self.load_balancer.reset_round_robin()

        assert self.load_balancer._round_robin_index == 0


class TestBACnetReaderLoadBalancerRoundRobin:
    """Test round-robin specific functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.load_balancer = BACnetReaderLoadBalancer(LoadBalancingStrategy.ROUND_ROBIN)

        # Create ordered mock wrappers
        self.ordered_wrappers = {}
        for i in range(4):  # Use 4 for better round-robin testing
            wrapper = AsyncMock()
            wrapper.instance_id = f"wrapper_{i}"
            self.ordered_wrappers[f"wrapper_{i}"] = wrapper

    @pytest.mark.asyncio
    async def test_round_robin_consistency(self):
        """Test: Round-robin provides consistent ordering"""
        # Test two complete cycles
        expected_sequence = ["wrapper_0", "wrapper_1", "wrapper_2", "wrapper_3"] * 2

        results = []
        for _ in range(8):  # Two complete cycles
            result = await self.load_balancer.select_wrapper(self.ordered_wrappers)
            results.append(result.instance_id)

        assert results == expected_sequence

    @pytest.mark.asyncio
    async def test_round_robin_with_wrapper_changes(self):
        """Test: Round-robin behavior when wrappers are added/removed"""
        # Start with 2 wrappers
        limited_wrappers = {
            "wrapper_0": self.ordered_wrappers["wrapper_0"],
            "wrapper_1": self.ordered_wrappers["wrapper_1"],
        }

        # Select from limited set
        result1 = await self.load_balancer.select_wrapper(limited_wrappers)
        result2 = await self.load_balancer.select_wrapper(limited_wrappers)

        assert result1.instance_id == "wrapper_0"
        assert result2.instance_id == "wrapper_1"

        # Add more wrappers - index should handle gracefully
        result3 = await self.load_balancer.select_wrapper(self.ordered_wrappers)
        assert result3.instance_id == "wrapper_0"  # Should wrap around or reset


class TestBACnetReaderLoadBalancerLeastBusy:
    """Test least busy specific functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.load_balancer = BACnetReaderLoadBalancer(LoadBalancingStrategy.LEAST_BUSY)

    @pytest.mark.asyncio
    async def test_least_busy_selection_with_varying_loads(self):
        """Test: Least busy selects wrapper with minimum operations"""
        wrappers = {}
        operation_counts = [5, 2, 8, 1, 3]  # wrapper_3 has least (1)

        for i, count in enumerate(operation_counts):
            wrapper = AsyncMock()
            wrapper.instance_id = f"wrapper_{i}"
            wrapper.get_active_operations_count = AsyncMock(return_value=count)
            wrappers[f"wrapper_{i}"] = wrapper

        result = await self.load_balancer.select_wrapper(wrappers)

        assert result is not None
        assert result.instance_id == "wrapper_3"  # Has 1 operation (minimum)

    @pytest.mark.asyncio
    async def test_least_busy_with_tied_loads(self):
        """Test: Least busy selection when multiple wrappers have same load"""
        wrappers = {}
        for i in range(3):
            wrapper = AsyncMock()
            wrapper.instance_id = f"wrapper_{i}"
            wrapper.get_active_operations_count = AsyncMock(
                return_value=2
            )  # All have same load
            wrappers[f"wrapper_{i}"] = wrapper

        result = await self.load_balancer.select_wrapper(wrappers)

        # Should return one of the wrappers (implementation dependent)
        assert result is not None
        assert result.instance_id in ["wrapper_0", "wrapper_1", "wrapper_2"]

    @pytest.mark.asyncio
    async def test_least_busy_with_zero_operations(self):
        """Test: Least busy selection with some wrappers having zero operations"""
        wrappers = {}
        operation_counts = [3, 0, 5, 0, 1]  # wrapper_1 and wrapper_3 have 0

        for i, count in enumerate(operation_counts):
            wrapper = AsyncMock()
            wrapper.instance_id = f"wrapper_{i}"
            wrapper.get_active_operations_count = AsyncMock(return_value=count)
            wrappers[f"wrapper_{i}"] = wrapper

        result = await self.load_balancer.select_wrapper(wrappers)

        assert result is not None
        # Should select one of the wrappers with 0 operations
        assert result.instance_id in ["wrapper_1", "wrapper_3"]


class TestBACnetReaderLoadBalancerIntegration:
    """Test load balancer integration scenarios"""

    @pytest.mark.asyncio
    async def test_strategy_switching_during_operation(self):
        """Test: Switching strategies during operation"""
        load_balancer = BACnetReaderLoadBalancer(LoadBalancingStrategy.ROUND_ROBIN)

        wrappers = {}
        for i in range(3):
            wrapper = AsyncMock()
            wrapper.instance_id = f"wrapper_{i}"
            wrapper.get_active_operations_count = AsyncMock(return_value=i)
            wrappers[f"wrapper_{i}"] = wrapper

        # Round-robin selections
        result1 = await load_balancer.select_wrapper(wrappers)
        result2 = await load_balancer.select_wrapper(wrappers)

        assert result1.instance_id == "wrapper_0"
        assert result2.instance_id == "wrapper_1"

        # Switch to least busy
        load_balancer.set_strategy(LoadBalancingStrategy.LEAST_BUSY)

        result3 = await load_balancer.select_wrapper(wrappers)

        # Should now use least busy (wrapper_0 with 0 operations)
        assert result3.instance_id == "wrapper_0"

    @pytest.mark.asyncio
    async def test_concurrent_wrapper_selection(self):
        """Test: Concurrent wrapper selection operations"""
        load_balancer = BACnetReaderLoadBalancer(LoadBalancingStrategy.FIRST_AVAILABLE)

        wrappers = {}
        for i in range(3):
            wrapper = AsyncMock()
            wrapper.instance_id = f"wrapper_{i}"
            wrappers[f"wrapper_{i}"] = wrapper

        # Concurrent selections
        async def select_wrapper():
            return await load_balancer.select_wrapper(wrappers)

        tasks = [select_wrapper() for _ in range(10)]
        results = await asyncio.gather(*tasks)

        # All should complete successfully
        assert len(results) == 10
        assert all(result is not None for result in results)

        # With FIRST_AVAILABLE, all should return the same wrapper
        assert all(result.instance_id == "wrapper_0" for result in results)

    @pytest.mark.asyncio
    async def test_utilization_tracking_across_strategies(self):
        """Test: Utilization tracking works across different strategies"""
        wrappers = {}
        for i in range(2):
            wrapper = AsyncMock()
            wrapper.instance_id = f"wrapper_{i}"
            wrapper.ip = f"192.168.1.{100 + i}"
            wrapper.port = 47808
            wrapper.get_active_operations_count = AsyncMock(return_value=i + 1)
            wrapper.is_busy = AsyncMock(return_value=True)
            wrappers[f"wrapper_{i}"] = wrapper

        # Test utilization with different strategies
        for strategy in LoadBalancingStrategy:
            load_balancer = BACnetReaderLoadBalancer(strategy)

            utilization = await load_balancer.get_utilization_info(wrappers)

            assert len(utilization) == 2
            for wrapper_id in wrappers:
                assert wrapper_id in utilization
                assert utilization[wrapper_id]["strategy"] == strategy.value


class TestBACnetReaderLoadBalancerErrorHandling:
    """Test load balancer error handling"""

    def setup_method(self):
        """Set up test fixtures"""
        self.load_balancer = BACnetReaderLoadBalancer()

    @pytest.mark.asyncio
    async def test_wrapper_operations_count_error(self):
        """Test: Handle errors when getting operations count"""
        wrapper = AsyncMock()
        wrapper.instance_id = "error_wrapper"
        wrapper.get_active_operations_count.side_effect = Exception("Connection error")

        wrappers = {"error_wrapper": wrapper}

        self.load_balancer.set_strategy(LoadBalancingStrategy.LEAST_BUSY)

        # Should handle error gracefully
        with pytest.raises(Exception):
            await self.load_balancer.select_wrapper(wrappers)

    @pytest.mark.asyncio
    async def test_wrapper_is_busy_error(self):
        """Test: Handle errors when checking if wrapper is busy"""
        wrapper = AsyncMock()
        wrapper.instance_id = "error_wrapper"
        wrapper.ip = "192.168.1.100"
        wrapper.port = 47808
        wrapper.get_active_operations_count = AsyncMock(return_value=5)
        wrapper.is_busy.side_effect = Exception("Status check error")

        wrappers = {"error_wrapper": wrapper}

        # Should handle error gracefully during utilization info
        with pytest.raises(Exception):
            await self.load_balancer.get_utilization_info(wrappers)

    @pytest.mark.asyncio
    async def test_empty_wrapper_list_operations(self):
        """Test: Operations with empty wrapper list"""
        # select_wrapper with empty list
        result = await self.load_balancer.select_wrapper({})
        assert result is None

        # get_utilization_info with empty list
        utilization = await self.load_balancer.get_utilization_info({})
        assert utilization == {}

        # get_available_wrappers with empty list
        available = await self.load_balancer.get_available_wrappers({})
        assert available == {}


class TestBACnetReaderLoadBalancerEdgeCases:
    """Test load balancer edge cases"""

    def setup_method(self):
        """Set up test fixtures"""
        self.load_balancer = BACnetReaderLoadBalancer()

    @pytest.mark.asyncio
    async def test_wrapper_with_none_operations_count(self):
        """Test: Wrapper that returns None for operations count"""
        wrapper = AsyncMock()
        wrapper.instance_id = "none_ops_wrapper"
        wrapper.get_active_operations_count = AsyncMock(return_value=None)

        wrappers = {"none_ops_wrapper": wrapper}

        self.load_balancer.set_strategy(LoadBalancingStrategy.LEAST_BUSY)

        # Should handle None operations count
        try:
            await self.load_balancer.select_wrapper(wrappers)
            # Implementation dependent whether it handles None gracefully
        except (TypeError, ValueError):
            # Acceptable to raise error for invalid operations count
            pass

    @pytest.mark.asyncio
    async def test_wrapper_with_negative_operations_count(self):
        """Test: Wrapper with negative operations count"""
        wrapper = AsyncMock()
        wrapper.instance_id = "negative_ops_wrapper"
        wrapper.get_active_operations_count = AsyncMock(return_value=-1)

        wrappers = {"negative_ops_wrapper": wrapper}

        self.load_balancer.set_strategy(LoadBalancingStrategy.LEAST_BUSY)

        # Should handle negative operations count
        result = await self.load_balancer.select_wrapper(wrappers)
        # Might select wrapper with "least" (most negative) operations
        assert result is not None

    @pytest.mark.asyncio
    async def test_very_large_operations_counts(self):
        """Test: Wrappers with very large operations counts"""
        wrappers = {}
        for i, count in enumerate([999999, 1000000, 1000001]):
            wrapper = AsyncMock()
            wrapper.instance_id = f"large_ops_wrapper_{i}"
            wrapper.get_active_operations_count = AsyncMock(return_value=count)
            wrappers[f"large_ops_wrapper_{i}"] = wrapper

        self.load_balancer.set_strategy(LoadBalancingStrategy.LEAST_BUSY)

        result = await self.load_balancer.select_wrapper(wrappers)

        # Should select wrapper with smallest large number
        assert result is not None
        assert result.instance_id == "large_ops_wrapper_0"  # 999999 is smallest

    def test_round_robin_index_overflow(self):
        """Test: Round-robin index overflow handling"""
        self.load_balancer.set_strategy(LoadBalancingStrategy.ROUND_ROBIN)

        # Set index to very large number
        self.load_balancer._round_robin_index = 2**63 - 1  # Max int

        wrapper = AsyncMock()
        wrapper.instance_id = "test_wrapper"
        wrappers = {"test_wrapper": wrapper}

        # Should handle large index gracefully
        asyncio.run(self.load_balancer.select_wrapper(wrappers))

        # Index should be reset or handled without overflow
        assert self.load_balancer._round_robin_index >= 0
