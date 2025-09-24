import logging
from src.actors.messages.message_type import HeartbeatStatusPayload
from src.models.iot_device_status import get_latest_iot_device_status
from src.models.device_status_enums import ConnectionStatusEnum

logger = logging.getLogger(__name__)


class HeartbeatController:
    def __init__(self, organization_id: str, site_id: str, iot_device_id: str):
        self.organization_id = organization_id
        self.site_id = site_id
        self.iot_device_id = iot_device_id

    async def start(self):
        """Initialize the heartbeat controller and its dependencies."""
        logger.info(
            f"[HeartbeatController] Starting heartbeat controller for device {self.iot_device_id}"
        )
        # No external dependencies to initialize for heartbeat controller
        pass

    async def collect_heartbeat_data(self) -> HeartbeatStatusPayload:
        """
        Collect comprehensive heartbeat data from local database cache.

        Returns:
            HeartbeatStatusPayload: Complete heartbeat data for the device
        """
        try:
            logger.debug(
                f"[HeartbeatController] Collecting heartbeat data for device {self.iot_device_id}"
            )

            # Read latest status from local database
            status_record = await get_latest_iot_device_status(self.iot_device_id)

            if status_record:
                # Convert database record to HeartbeatStatusPayload
                heartbeat_payload = HeartbeatStatusPayload(
                    # System metrics
                    cpu_usage_percent=status_record.cpu_usage_percent,
                    memory_usage_percent=status_record.memory_usage_percent,
                    disk_usage_percent=status_record.disk_usage_percent,
                    temperature_celsius=status_record.temperature_celsius,
                    uptime_seconds=status_record.uptime_seconds,
                    load_average=status_record.load_average,
                    # BMS-specific metrics
                    monitoring_status=status_record.monitoring_status,
                    mqtt_connection_status=status_record.mqtt_connection_status,
                    bacnet_connection_status=status_record.bacnet_connection_status,
                    bacnet_devices_connected=status_record.bacnet_devices_connected,
                    bacnet_points_monitored=status_record.bacnet_points_monitored,
                )

                logger.debug(
                    "[HeartbeatController] Successfully collected heartbeat data from local cache"
                )
                return heartbeat_payload
            else:
                # Fallback if no status record exists
                logger.warning(
                    f"[HeartbeatController] No status record found for device {self.iot_device_id}"
                )
                return HeartbeatStatusPayload()

        except Exception as e:
            logger.error(f"[HeartbeatController] Error collecting heartbeat data: {e}")

            # Return minimal heartbeat on error
            return HeartbeatStatusPayload(
                mqtt_connection_status=ConnectionStatusEnum.ERROR,
                bacnet_connection_status=ConnectionStatusEnum.ERROR,
            )

    async def force_heartbeat(self, reason: str) -> HeartbeatStatusPayload:
        """
        Immediately collect and return heartbeat data for force heartbeat requests.

        Args:
            reason: The reason for the force heartbeat request

        Returns:
            HeartbeatStatusPayload: Complete heartbeat data for the device
        """
        try:
            logger.info(
                f"[HeartbeatController] Force heartbeat requested for device {self.iot_device_id} - Reason: {reason}"
            )

            # Delegate to the main heartbeat data collection method
            heartbeat_payload = await self.collect_heartbeat_data()

            logger.info(
                f"[HeartbeatController] Force heartbeat completed successfully for device {self.iot_device_id}"
            )
            return heartbeat_payload

        except Exception as e:
            logger.error(
                f"[HeartbeatController] Error during force heartbeat for device {self.iot_device_id}: {e}"
            )

            # Return minimal heartbeat on error
            return HeartbeatStatusPayload(
                mqtt_connection_status=ConnectionStatusEnum.ERROR,
                bacnet_connection_status=ConnectionStatusEnum.ERROR,
            )
