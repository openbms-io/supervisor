"""
BACnet Reader Load Balancer

Handles load balancing strategies and reader selection logic for BACnet operations.
Provides proper separation of concerns by isolating load balancing from wrapper management.
"""

from src.utils.logger import logger
from typing import Dict, Optional, TYPE_CHECKING
from enum import Enum

logging = logger

if TYPE_CHECKING:
    from src.models.bacnet_wrapper import BACnetWrapper


class LoadBalancingStrategy(Enum):
    """Load balancing strategies for reader selection."""

    ROUND_ROBIN = "round_robin"
    LEAST_BUSY = "least_busy"
    FIRST_AVAILABLE = "first_available"


class BACnetReaderLoadBalancer:
    """
    Manages load balancing strategies and reader selection for BACnet operations.

    Responsibilities:
    - Select optimal readers based on configured strategy
    - Handle reader discovery and fallback logic
    - Track reader utilization and performance
    - Provide clean abstraction for reader selection
    """

    def __init__(
        self, strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN
    ):
        """
        Initialize the load balancer with a specific strategy.

        Args:
            strategy: The load balancing strategy to use
        """
        self.strategy = strategy
        self._round_robin_index = 0

        logging.info(
            f"Initialized BACnetReaderLoadBalancer with strategy: {strategy.value}"
        )

    def set_strategy(self, strategy: LoadBalancingStrategy) -> None:
        """Change the load balancing strategy."""
        logging.info(
            f"Changing load balancing strategy from {self.strategy.value} to {strategy.value}"
        )
        self.strategy = strategy
        if strategy == LoadBalancingStrategy.ROUND_ROBIN:
            self._round_robin_index = 0  # Reset round-robin when switching to it

    async def select_wrapper(
        self, available_wrappers: Dict[str, "BACnetWrapper"]
    ) -> Optional["BACnetWrapper"]:
        """
        Select the best wrapper based on the configured load balancing strategy.

        Args:
            available_wrappers: Dictionary of available wrappers {wrapper_id: BACnetWrapper}

        Returns:
            Selected BACnetWrapper or None if no wrappers available
        """
        if not available_wrappers:
            logging.warning("No wrappers available for load balancing")
            return None

        # Select wrapper using configured strategy
        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            selected_wrapper = self._select_wrapper_round_robin(available_wrappers)
        elif self.strategy == LoadBalancingStrategy.LEAST_BUSY:
            selected_wrapper = await self._select_wrapper_least_busy(available_wrappers)
        else:  # FIRST_AVAILABLE
            selected_wrapper = self._select_wrapper_first_available(available_wrappers)

        if selected_wrapper:
            logging.debug(
                f"Load balancer selected wrapper {selected_wrapper.instance_id} using {self.strategy.value} strategy"
            )

        return selected_wrapper

    def _select_wrapper_round_robin(
        self, available_wrappers: Dict[str, "BACnetWrapper"]
    ) -> Optional["BACnetWrapper"]:
        """Select wrapper using round-robin algorithm."""
        wrapper_list = list(available_wrappers.values())
        if not wrapper_list:
            logging.warning("No wrappers available for round-robin selection")
            return None

        # Bounds check and reset index if needed (defensive programming)
        if self._round_robin_index >= len(wrapper_list):
            logging.warning(
                f"Round-robin index {self._round_robin_index} out of bounds for {len(wrapper_list)} wrappers, resetting to 0"
            )
            self._round_robin_index = 0

        # Get the next wrapper in round-robin fashion
        selected_wrapper = wrapper_list[self._round_robin_index]
        self._round_robin_index = (self._round_robin_index + 1) % len(wrapper_list)

        logging.debug(
            f"Round-robin selected wrapper {selected_wrapper.instance_id} (index {self._round_robin_index - 1} of {len(wrapper_list)})"
        )
        return selected_wrapper

    async def _select_wrapper_least_busy(
        self, available_wrappers: Dict[str, "BACnetWrapper"]
    ) -> Optional["BACnetWrapper"]:
        """Select wrapper with the fewest active operations."""
        least_busy_wrapper = None
        min_operations = float("inf")

        for wrapper in available_wrappers.values():
            operations_count = await wrapper.get_active_operations_count()
            if operations_count < min_operations:
                min_operations = operations_count
                least_busy_wrapper = wrapper

        return least_busy_wrapper

    def _select_wrapper_first_available(
        self, available_wrappers: Dict[str, "BACnetWrapper"]
    ) -> Optional["BACnetWrapper"]:
        """Select the first available wrapper (deterministic)."""
        return next(iter(available_wrappers.values())) if available_wrappers else None

    async def get_utilization_info(
        self, available_wrappers: Dict[str, "BACnetWrapper"]
    ) -> Dict[str, Dict]:
        """
        Get utilization information for all available wrappers.

        Args:
            available_wrappers: Dictionary of available wrappers

        Returns:
            Dictionary with utilization info for each wrapper
        """
        utilization_info = {}

        for wrapper_id, wrapper in available_wrappers.items():
            operations_count = await wrapper.get_active_operations_count()
            is_busy = await wrapper.is_busy()

            utilization_info[wrapper_id] = {
                "instance_id": wrapper.instance_id,
                "active_operations": operations_count,
                "is_busy": is_busy,
                "ip": wrapper.ip,
                "port": wrapper.port,
                "strategy": self.strategy.value,
            }

        return utilization_info

    async def get_available_wrappers(
        self, all_wrappers: Dict[str, "BACnetWrapper"], max_operations: int = 5
    ) -> Dict[str, "BACnetWrapper"]:
        """
        Filter wrappers that are not overloaded.

        Args:
            all_wrappers: All available wrappers
            max_operations: Maximum operations before considering a wrapper overloaded

        Returns:
            Dictionary of non-overloaded wrappers
        """
        available = {}

        for wrapper_id, wrapper in all_wrappers.items():
            operations_count = await wrapper.get_active_operations_count()
            if operations_count < max_operations:
                available[wrapper_id] = wrapper

        return available

    def reset_round_robin(self) -> None:
        """Reset the round-robin counter (useful when readers change)."""
        self._round_robin_index = 0
        logging.debug("Reset round-robin counter")
