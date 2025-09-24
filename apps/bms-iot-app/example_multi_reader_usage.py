#!/usr/bin/env python3
"""
Example script demonstrating the new multi-reader BACnet implementation.

This script shows how the BMS IoT app now supports multiple BACnet readers
based on the configuration received from GET_CONFIG.
"""

import logging
from src.actors.messages.message_type import BacnetReaderConfig
from src.models.bacnet_wrapper_manager import bacnet_wrapper_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_multi_reader_usage():
    """Demonstrate multi-reader BACnet functionality."""

    # Example BACnet readers configuration (would come from GET_CONFIG in real usage)
    example_readers = [
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
            ip_address="192.168.2.100",
            subnet_mask=24,
            bacnet_device_id=1002,
            port=47809,  # Different port to avoid conflicts
            bbmd_enabled=True,
            bbmd_server_ip="192.168.2.1",
            is_active=True,
        ),
        BacnetReaderConfig(
            id="reader_3",
            ip_address="192.168.3.100",
            subnet_mask=24,
            bacnet_device_id=1003,
            port=47810,
            bbmd_enabled=False,
            is_active=False,  # Inactive reader - should be skipped
        ),
    ]

    logger.info("Initializing BACnet readers...")

    try:
        # Initialize all readers
        await bacnet_wrapper_manager.initialize_readers(example_readers)

        # Check which readers were successfully initialized
        initialized_wrappers = bacnet_wrapper_manager.get_all_wrappers()
        logger.info(f"Successfully initialized {len(initialized_wrappers)} readers:")

        for reader_id, wrapper in initialized_wrappers.items():
            logger.info(
                f"  - Reader {reader_id}: IP={wrapper.ip}, Port={wrapper.port}, DeviceID={wrapper.device_id}"
            )

        # Get default wrapper
        default_wrapper = bacnet_wrapper_manager.get_wrapper()
        if default_wrapper:
            logger.info(f"Default wrapper: Reader with IP {default_wrapper.ip}")

        # Example: Get specific wrapper
        reader_1_wrapper = bacnet_wrapper_manager.get_wrapper("reader_1")
        if reader_1_wrapper:
            logger.info(f"Reader 1 wrapper: IP={reader_1_wrapper.ip}")

        # Example: Try to read a value (would normally be called from monitoring actor)
        # This is just to show the interface - actual device communication would happen here
        logger.info("Multi-reader BACnet system is ready for device communication!")

    except Exception as e:
        logger.error(f"Failed to initialize readers: {e}")

    finally:
        # Cleanup
        await bacnet_wrapper_manager.cleanup()
        logger.info("Cleaned up BACnet readers")


def print_system_overview():
    """Print an overview of the new multi-reader system."""
    print(
        """
=== BMS IoT App - Multi-Reader BACnet Implementation ===

Key Features Implemented:
✅ Multiple BAC0 instances (one per BACnet reader)
✅ Automatic reader initialization from GET_CONFIG
✅ Network interface binding (each reader has specific IP)
✅ BBMD support when enabled
✅ Port conflict detection and handling
✅ Graceful error handling for reader failures
✅ Backward compatibility with existing code

Architecture Changes:
• BACnetWrapperManager: Manages multiple BACnet wrapper instances
• BACnetWrapper: Individual wrapper per reader configuration
• BACnetMonitor: Updated to use multiple readers for discovery and monitoring
• BACnetWriter: Updated to find appropriate reader for each write operation
• BacnetMonitoringActor: Processes bacnetReaders from CONFIG_UPLOAD_REQUEST

Configuration Flow:
1. MQTT receives GET_CONFIG with bacnetReaders array
2. BacnetMonitoringActor processes CONFIG_UPLOAD_REQUEST
3. BACnetWrapperManager initializes BAC0 instances for active readers
4. Monitoring uses all readers to discover and read devices
5. Writing finds the best reader for each controller IP

Error Handling:
• Skips inactive readers (is_active=false)
• Handles port conflicts (BAC0 limitation: one instance per port)
• Falls back to other readers if one fails
• Logs which readers are successfully initialized
• Graceful degradation to single reader if needed

Usage in monitoring:
• Device discovery tries all readers
• Point reading tries readers until one succeeds
• Writing finds best reader based on controller IP network
    """
    )


if __name__ == "__main__":
    print_system_overview()

    # Uncomment to run the actual example (requires BAC0 and network setup)
    # asyncio.run(example_multi_reader_usage())

    print("\nTo test with real BACnet devices:")
    print("1. Update the example_readers with your actual device IPs")
    print("2. Ensure your BACnet devices are accessible on the network")
    print("3. Uncomment the asyncio.run() line above")
    print("4. Run: python example_multi_reader_usage.py")
