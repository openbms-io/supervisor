from src.utils.logger import logger
import asyncio
import psutil
import time
from typing import Dict, Any

from src.actors.messages.actor_queue_registry import ActorQueueRegistry
from src.actors.messages.message_type import ActorName, ActorMessage
from src.models.iot_device_status import update_system_metrics

logging = logger


class SystemMetricsActor:
    def __init__(
        self,
        actor_queue_registry: ActorQueueRegistry,
        organization_id: str,
        site_id: str,
        iot_device_id: str,
    ):
        self.keep_running = True
        self.actor_queue_registry = actor_queue_registry
        self.actor_name = ActorName.SYSTEM_METRICS
        self.organization_id = organization_id
        self.site_id = site_id
        self.iot_device_id = iot_device_id
        self.collection_interval = 30  # Collect metrics every 30 seconds

    async def start(self):
        await self._run_metrics_loop()

    async def _run_metrics_loop(self):
        logger.info(
            f"[SystemMetricsActor] Starting metrics collection for device: {self.iot_device_id}"
        )
        queue = self.actor_queue_registry.get_queue(self.actor_name)

        while self.keep_running:
            try:
                # 1. Collect system metrics
                await self._collect_and_store_metrics()

                # 2. Check for incoming messages (non-blocking)
                while not queue.empty():
                    msg: ActorMessage = await queue.get()
                    await self._handle_message(msg)

                await asyncio.sleep(0)  # Yield control to event loop

            except Exception as e:
                logger.error(f"SystemMetricsActor error: {e}")

            await asyncio.sleep(self.collection_interval)

    async def _collect_and_store_metrics(self):
        """Collect system metrics and store them in local iot_device_status."""
        try:
            metrics = await self._collect_system_metrics()

            # Add required fields
            metrics["organization_id"] = self.organization_id
            metrics["site_id"] = self.site_id

            # Store in local database
            await update_system_metrics(self.iot_device_id, metrics)

            logger.debug(
                f"[SystemMetricsActor] Updated system metrics for device: {self.iot_device_id}"
            )

        except Exception as e:
            logger.error(f"[SystemMetricsActor] Failed to collect/store metrics: {e}")

    async def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system metrics using psutil."""
        metrics = {}

        try:
            # CPU usage
            metrics["cpu_usage_percent"] = psutil.cpu_percent(interval=1)

            # Memory usage
            memory = psutil.virtual_memory()
            metrics["memory_usage_percent"] = memory.percent

            # Disk usage
            disk = psutil.disk_usage("/")
            metrics["disk_usage_percent"] = (disk.used / disk.total) * 100

            # System uptime
            boot_time = psutil.boot_time()
            metrics["uptime_seconds"] = int(time.time() - boot_time)

            # Load average (Unix-like systems)
            try:
                load_avg = psutil.getloadavg()
                metrics["load_average"] = load_avg[0]  # 1-minute load average
            except (AttributeError, OSError):
                # Not available on all platforms
                metrics["load_average"] = None

            # Temperature (if available)
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    # Get the first available temperature sensor
                    for name, entries in temps.items():
                        if entries:
                            metrics["temperature_celsius"] = entries[0].current
                            break
                    else:
                        metrics["temperature_celsius"] = None
                else:
                    metrics["temperature_celsius"] = None
            except (AttributeError, OSError):
                metrics["temperature_celsius"] = None

        except Exception as e:
            logger.error(f"[SystemMetricsActor] Error collecting system metrics: {e}")

        return metrics

    def on_stop(self):
        self.keep_running = False

    async def _handle_message(self, msg: ActorMessage):
        """Handle incoming messages (currently none expected)."""
        logger.info(f"[SystemMetricsActor] Received message: {msg}")
        logger.warning(
            f"[SystemMetricsActor] Unhandled message type: {msg.message_type}"
        )
