from typing import Optional, Dict, Tuple
from src.actors.messages.message_type import BacnetReaderConfig
from src.models.bacnet_wrapper import BACnetWrapper
from src.models.bacnet_reader_load_balancer import (
    BACnetReaderLoadBalancer,
    LoadBalancingStrategy,
)
from src.utils.logger import logger


class BACnetWrapperManager:
    """Manager for multiple BACnet wrapper instances."""

    def __init__(
        self,
        load_balancing_strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN,
    ):
        self._wrappers: Dict[str, BACnetWrapper] = {}
        self._default_wrapper: Optional[BACnetWrapper] = None
        self._initialized = False

        # Initialize private load balancer for wrapper selection
        self._load_balancer = BACnetReaderLoadBalancer(load_balancing_strategy)

    async def initialize_readers(
        self, reader_configs: list[BacnetReaderConfig]
    ) -> None:
        """Initialize BAC0 instances for all active reader configurations.

        Automatically cleans up any existing connections before initializing new ones.
        """
        logger.info(f"Initializing {len(reader_configs)} BACnet readers")

        # INTERNAL: Always cleanup before reinitializing - caller doesn't need to know
        await self.cleanup()

        # Track used endpoints (IP+port combinations) to detect actual conflicts
        used_endpoints: Dict[Tuple[str, int], str] = {}

        for reader_config in reader_configs:
            if not reader_config.is_active:
                logger.info(f"Skipping inactive reader {reader_config.id}")
                continue

            # Check for endpoint conflicts (same IP + same port combination)
            endpoint = (reader_config.ip_address, reader_config.port)
            if endpoint in used_endpoints:
                logger.warning(
                    f"Endpoint conflict: Reader {reader_config.id} and {used_endpoints[endpoint]} "
                    f"both trying to use endpoint {reader_config.ip_address}:{reader_config.port}. Skipping {reader_config.id}."
                )
                continue

            try:
                wrapper = BACnetWrapper(reader_config)
                await wrapper.start()
                self._wrappers[reader_config.id] = wrapper
                used_endpoints[endpoint] = reader_config.id

                # Set the first successfully initialized wrapper as default
                if self._default_wrapper is None:
                    self._default_wrapper = wrapper
                    logger.info(f"Set reader {reader_config.id} as default wrapper")

                logger.info(f"Successfully initialized reader {reader_config.id}")
            except Exception as e:
                logger.error(f"Failed to initialize reader {reader_config.id}: {e}")
                continue

        logger.info(
            f"Successfully initialized {len(self._wrappers)} out of {len([r for r in reader_configs if r.is_active])} active readers"
        )
        self._initialized = True

    def get_wrapper(self, reader_id: Optional[str] = None) -> Optional[BACnetWrapper]:
        """Get a specific wrapper by reader ID, or the default wrapper if no ID provided."""
        if reader_id:
            return self._wrappers.get(reader_id)
        return self._default_wrapper

    def get_all_wrappers(self) -> Dict[str, BACnetWrapper]:
        """Get all initialized wrappers."""
        return self._wrappers.copy()

    def is_initialized(self) -> bool:
        """Check if the manager has been initialized with readers."""
        return self._initialized

    async def get_wrapper_for_operation(self) -> Optional[BACnetWrapper]:
        """Get the best wrapper for an operation using load balancing."""
        if not self._wrappers:
            logger.warning("No wrappers available for operation")
            return None

        # Use private load balancer to select the best wrapper
        return await self._load_balancer.select_wrapper(self._wrappers)

    async def get_utilization_info(self) -> Dict[str, Dict]:
        """Get utilization information for all wrappers."""
        return await self._load_balancer.get_utilization_info(self._wrappers)

    def set_load_balancing_strategy(self, strategy: LoadBalancingStrategy) -> None:
        """Change the load balancing strategy."""
        self._load_balancer.set_strategy(strategy)

    def reset_load_balancing(self) -> None:
        """Reset load balancing state (useful when readers change)."""
        self._load_balancer.reset_round_robin()

    async def cleanup(self) -> None:
        """Cleanup all existing BAC0 connections."""
        logger.info("STARTED: Cleaning up all BAC0 connections")
        for reader_id, wrapper in self._wrappers.items():
            try:
                if await wrapper.is_connected():
                    success = await wrapper.disconnect()
                    if success:
                        logger.info(f"Cleaned up reader {reader_id}")
                    else:
                        logger.warning(f"Failed to cleanup reader {reader_id}")
            except Exception as e:
                logger.error(f"Error cleaning up reader {reader_id}: {e}")

        self._wrappers.clear()
        self._default_wrapper = None
        self._initialized = False

        # Reset load balancer state to prevent index out of range errors
        self.reset_load_balancing()

        logger.info(
            "FINISHED: Cleaning up all BAC0 connections and reset load balancer state"
        )


# Global manager instance with default load balancing strategy
bacnet_wrapper_manager = BACnetWrapperManager(LoadBalancingStrategy.ROUND_ROBIN)


# Backward compatibility - get default wrapper
def get_default_bacnet_wrapper() -> Optional[BACnetWrapper]:
    """Get the default BACnet wrapper for backward compatibility."""
    return bacnet_wrapper_manager.get_wrapper()
