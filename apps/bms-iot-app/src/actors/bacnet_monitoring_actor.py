from src.controllers.monitoring.monitor import BACnetMonitor
import asyncio
from src.actors.messages.actor_queue_registry import ActorQueueRegistry
from src.actors.messages.message_type import (
    ActorName,
    ActorMessage,
    ActorMessageType,
    ConfigUploadPayload,
    MonitoringControlPayload,
    MonitoringControlResponsePayload,
    ForceHeartbeatPayload,
)
from src.models.iot_device_status import (
    upsert_iot_device_status,
    get_latest_iot_device_status,
)
from src.models.device_status_enums import MonitoringStatusEnum, ConnectionStatusEnum
from src.models.bacnet_config import save_bacnet_readers, get_bacnet_readers
from src.utils.logger import logger


class BacnetMonitoringActor:
    def __init__(
        self,
        actor_queue_registry: ActorQueueRegistry,
        organization_id: str,
        site_id: str,
        iot_device_id: str,
    ):
        self.monitor = BACnetMonitor()
        self.keep_running = True
        self.monitoring_enabled = True  # Default to monitoring enabled
        self._monitor_initialized = False  # Track if monitor has been initialized
        self.actor_queue_registry = actor_queue_registry
        self.actor_name = ActorName.BACNET
        self.organization_id = organization_id
        self.site_id = site_id
        self.iot_device_id = iot_device_id

    async def start(self):
        await self._run_monitor_loop()

    async def _run_monitor_loop(self):
        queue = self.actor_queue_registry.get_queue(self.actor_name)
        logger.info("BACnet Monitoring Actor started, waiting for configuration...")
        logger.info(
            f"Monitoring enabled: {self.monitoring_enabled}, Monitor initialized: {self._monitor_initialized}"
        )

        # Initialize monitoring status in local database
        # Get monitoring status from local database
        latest_status = await get_latest_iot_device_status(self.iot_device_id)
        if not latest_status:
            raise Exception(
                f"No monitoring status found for device {self.iot_device_id}"
            )

        self.monitoring_enabled = (
            latest_status.monitoring_status == MonitoringStatusEnum.ACTIVE
        )

        # Try to load BACnet readers from database on startup
        await self._load_readers_from_database()

        async def handle_messages_loop():
            logger.info("Message handler loop started")
            while self.keep_running:
                if not queue.empty():
                    msg: ActorMessage = await queue.get()
                    await self._handle_message(msg)
                await asyncio.sleep(0)

        async def monitor_loop():
            logger.info("Monitor loop started")
            while self.keep_running:
                try:
                    logger.info(
                        f"Monitoring loop running, monitoring enabled: {self.monitoring_enabled}, monitor initialized: {self._monitor_initialized}"
                    )
                    # 1. Perform regular monitoring only if enabled and initialized
                    if self.monitoring_enabled and self._monitor_initialized:
                        logger.info("Starting monitor_all_devices")
                        await self.monitor.monitor_all_devices()
                        logger.info("Completed monitor_all_devices")
                        await self._update_bacnet_status()

                    # # 2. Check for incoming messages (non-blocking)
                    # while not queue.empty():
                    #     msg: ActorMessage = await queue.get()
                    #     await self._handle_message(msg)

                    await asyncio.sleep(0)  # Yield control to event loop

                except Exception as e:
                    logger.error(f"BACnetMonitor error: {e}", exc_info=True)
                    await self._update_bacnet_connection_status(
                        ConnectionStatusEnum.ERROR
                    )

                logger.info("Monitoring loop sleeping for 5 seconds")
                await asyncio.sleep(5)

        handle_messages_task = asyncio.create_task(handle_messages_loop())
        monitor_loop_task = asyncio.create_task(monitor_loop())

        await asyncio.gather(handle_messages_task, monitor_loop_task)

    def on_stop(self):
        self.keep_running = False

    async def _handle_message(self, msg: ActorMessage):
        logger.info(f"[BacnetMonitoringActor] Received message: {msg}")

        if msg.message_type == ActorMessageType.CONFIG_UPLOAD_REQUEST:
            if isinstance(msg.payload, ConfigUploadPayload):
                payload: ConfigUploadPayload = msg.payload
                logger.info(
                    f"Handling CONFIG_UPLOAD inside BacnetMonitoringActor with {len(payload.iotDeviceControllers)} controllers and {len(payload.bacnetReaders or [])} readers"
                )

                # PAUSE monitoring during reconfiguration to prevent race conditions
                old_monitoring_enabled = self.monitoring_enabled
                old_monitor_initialized = self._monitor_initialized
                self.monitoring_enabled = False
                self._monitor_initialized = False
                logger.info(
                    "PAUSED monitoring during CONFIG_UPLOAD processing to prevent race conditions"
                )

                try:
                    # Initialize BACnet readers if provided
                    if payload.bacnetReaders:
                        # Save readers to database for persistence
                        save_success = await save_bacnet_readers(
                            payload.bacnetReaders, self.iot_device_id
                        )
                        if save_success:
                            logger.info(
                                f"Saved {len(payload.bacnetReaders)}: {payload.bacnetReaders} BACnet readers to database"
                            )
                        else:
                            logger.warning("Failed to save BACnet readers to database")

                        await self.monitor.initialize_bacnet_readers(
                            payload.bacnetReaders
                        )
                        # Also initialize the monitor now that we have readers
                        await self.monitor.initialize()
                        # Update the flag in the monitoring loop
                        self._monitor_initialized = True
                        logger.info(
                            "BACnet monitor initialized with readers configuration"
                        )

                        # RESUME monitoring if it was previously enabled
                        if old_monitoring_enabled:
                            self.monitoring_enabled = True
                            logger.info(
                                "RESUMED monitoring after successful CONFIG_UPLOAD with readers"
                            )
                        else:
                            logger.info(
                                "Keeping monitoring disabled as it was disabled before CONFIG_UPLOAD"
                            )
                    else:
                        logger.warning(
                            "No BACnet readers provided in config - monitoring will be disabled"
                        )
                        # Set monitoring to disabled if no readers
                        self.monitoring_enabled = False
                        await self._update_monitoring_status(
                            MonitoringStatusEnum.STOPPED
                        )

                    # Fetch and save device controller config
                    await self.monitor.fetch_from_bacnet_network_and_save_config(
                        iotDeviceControllers=payload.iotDeviceControllers
                    )

                    logger.info(
                        f"CONFIG_UPLOAD processing completed successfully. Monitoring: {self.monitoring_enabled}, Initialized: {self._monitor_initialized}"
                    )

                except Exception as config_error:
                    logger.error(
                        f"Error during CONFIG_UPLOAD processing: {config_error}",
                        exc_info=True,
                    )
                    # On error, restore previous state to prevent system deadlock
                    self.monitoring_enabled = old_monitoring_enabled
                    self._monitor_initialized = old_monitor_initialized
                    logger.warning(
                        f"Restored previous monitoring state due to CONFIG_UPLOAD error: monitoring={self.monitoring_enabled}, initialized={self._monitor_initialized}"
                    )
                    await self._update_monitoring_status(MonitoringStatusEnum.ERROR)

                logger.info("Sending CONFIG_UPLOAD_RESPONSE to UPLOADER")
                await self.actor_queue_registry.send_from(
                    sender=self.actor_name,
                    receiver=ActorName.UPLOADER,
                    type=ActorMessageType.CONFIG_UPLOAD_RESPONSE,
                    payload=ConfigUploadPayload(
                        urlToUploadConfig=payload.urlToUploadConfig,
                        jwtToken=payload.jwtToken,
                        iotDeviceControllers=payload.iotDeviceControllers,
                        bacnetReaders=payload.bacnetReaders,
                    ),
                )
            else:
                logger.warning(
                    "Received CONFIG_UPLOAD_REQUEST with unexpected payload type"
                )

        elif msg.message_type == ActorMessageType.START_MONITORING_REQUEST:
            await self._handle_start_monitoring(msg)

        elif msg.message_type == ActorMessageType.STOP_MONITORING_REQUEST:
            await self._handle_stop_monitoring(msg)

        else:
            logger.warning(f"Unhandled message type: {msg.message_type}")

    async def _handle_start_monitoring(self, msg: ActorMessage):
        """Handle start monitoring command."""
        try:
            if isinstance(msg.payload, MonitoringControlPayload):
                payload: MonitoringControlPayload = msg.payload
                logger.info(
                    f"[BacnetMonitoringActor] Starting monitoring - Command ID: {payload.commandId}"
                )

                self.monitoring_enabled = True
                await self._update_monitoring_status(MonitoringStatusEnum.ACTIVE)

                # Trigger force heartbeat to immediately update UI
                await self._trigger_force_heartbeat("monitoring_started")

                # Send response
                response = MonitoringControlResponsePayload(
                    success=True,
                    message="Monitoring started successfully",
                    commandId=payload.commandId,
                )

                await self.actor_queue_registry.send_from(
                    sender=self.actor_name,
                    receiver=msg.sender,
                    type=ActorMessageType.START_MONITORING_RESPONSE,
                    payload=response,
                )

                logger.info("[BacnetMonitoringActor] Monitoring started successfully")
            else:
                logger.warning(
                    "Received START_MONITORING_REQUEST with unexpected payload type"
                )
        except Exception as e:
            logger.error(f"[BacnetMonitoringActor] Error starting monitoring: {e}")
            await self._update_monitoring_status(MonitoringStatusEnum.ERROR)

    async def _handle_stop_monitoring(self, msg: ActorMessage):
        """Handle stop monitoring command."""
        try:
            if isinstance(msg.payload, MonitoringControlPayload):
                payload: MonitoringControlPayload = msg.payload
                logger.info(
                    f"[BacnetMonitoringActor] Stopping monitoring - Command ID: {payload.commandId}"
                )

                self.monitoring_enabled = False
                await self._update_monitoring_status(MonitoringStatusEnum.STOPPED)

                # Trigger force heartbeat to immediately update UI
                await self._trigger_force_heartbeat("monitoring_stopped")

                # Send response
                response = MonitoringControlResponsePayload(
                    success=True,
                    message="Monitoring stopped successfully",
                    commandId=payload.commandId,
                )

                await self.actor_queue_registry.send_from(
                    sender=self.actor_name,
                    receiver=msg.sender,
                    type=ActorMessageType.STOP_MONITORING_RESPONSE,
                    payload=response,
                )

                logger.info("[BacnetMonitoringActor] Monitoring stopped successfully")
            else:
                logger.warning(
                    "Received STOP_MONITORING_REQUEST with unexpected payload type"
                )
        except Exception as e:
            logger.error(f"[BacnetMonitoringActor] Error stopping monitoring: {e}")
            await self._update_monitoring_status(MonitoringStatusEnum.ERROR)

    async def _update_monitoring_status(self, status: MonitoringStatusEnum):
        """Update monitoring status in local database."""
        try:
            status_data = {
                "organization_id": self.organization_id,
                "site_id": self.site_id,
                "monitoring_status": status,
            }
            await upsert_iot_device_status(self.iot_device_id, status_data)
            logger.debug(
                f"[BacnetMonitoringActor] Updated monitoring status to: {status}"
            )
        except Exception as e:
            logger.error(
                f"[BacnetMonitoringActor] Failed to update monitoring status: {e}"
            )

    async def _update_bacnet_status(self):
        # TODO: This implementation is not correct.
        # Figure out how to get the number of connected devices and points monitored via BAC0.
        """Update BACnet-specific status in local database."""
        try:
            # Get current monitoring metrics from the monitor
            connected_devices = len(getattr(self.monitor, "connected_devices", []))
            monitored_points = getattr(self.monitor, "monitored_points_count", 0)

            status_data = {
                "organization_id": self.organization_id,
                "site_id": self.site_id,
                "bacnet_connection_status": ConnectionStatusEnum.CONNECTED,
                "bacnet_devices_connected": connected_devices,
                "bacnet_points_monitored": monitored_points,
            }

            await upsert_iot_device_status(self.iot_device_id, status_data)
            logger.debug("[BacnetMonitoringActor] Updated BACnet status")
        except Exception as e:
            logger.error(f"[BacnetMonitoringActor] Failed to update BACnet status: {e}")
            await self._update_bacnet_connection_status(ConnectionStatusEnum.ERROR)

    async def _update_bacnet_connection_status(self, status: ConnectionStatusEnum):
        """Update BACnet connection status in local database."""
        try:
            status_data = {
                "organization_id": self.organization_id,
                "site_id": self.site_id,
                "bacnet_connection_status": status,
            }
            await upsert_iot_device_status(self.iot_device_id, status_data)
            logger.debug(
                f"[BacnetMonitoringActor] Updated BACnet connection status to: {status}"
            )
        except Exception as e:
            logger.error(
                f"[BacnetMonitoringActor] Failed to update BACnet connection status: {e}"
            )

    async def _trigger_force_heartbeat(self, reason: str):
        """Trigger an immediate heartbeat upload to reflect status changes."""
        try:
            force_heartbeat_payload = ForceHeartbeatPayload(reason=reason)
            await self.actor_queue_registry.send_from(
                sender=self.actor_name,
                receiver=ActorName.HEARTBEAT,
                type=ActorMessageType.FORCE_HEARTBEAT_REQUEST,
                payload=force_heartbeat_payload,
            )
            logger.info(f"[BacnetMonitoringActor] Triggered force heartbeat: {reason}")
        except Exception as e:
            logger.error(
                f"[BacnetMonitoringActor] Failed to trigger force heartbeat: {e}"
            )

    async def _load_readers_from_database(self):
        """Load BACnet readers from database on startup."""
        try:
            # Note: Database tables are created at application startup in main.py
            # bacnet_readers table is managed manually due to MQTT dependency issues

            # Load saved readers
            saved_readers = await get_bacnet_readers(self.iot_device_id)
            if saved_readers:
                logger.info(f"Loaded {len(saved_readers)} BACnet readers from database")
                await self.monitor.initialize_bacnet_readers(saved_readers)
                await self.monitor.initialize()
                self._monitor_initialized = True

                # Only initialize monitoring if the monitoring state is already ACTIVE
                if self.monitoring_enabled:
                    logger.info(
                        "BACnet monitor initialized with saved readers from database - monitoring already enabled"
                    )
                else:
                    logger.info(
                        "BACnet monitor initialized with saved readers from database - monitoring disabled (waiting for start command)"
                    )
            else:
                logger.info(
                    "No saved BACnet readers found in database, waiting for GET_CONFIG"
                )
        except Exception as e:
            logger.warning(f"Failed to load BACnet readers from database: {e}")
            logger.info("Will wait for GET_CONFIG command instead")
