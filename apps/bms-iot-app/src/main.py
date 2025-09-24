import asyncio
from typing import Callable, Awaitable

from src.network.mqtt_config import load_config

from src.actors.bacnet_monitoring_actor import BacnetMonitoringActor
from src.actors.bacnet_writer_actor import BacnetWriterActor
from src.actors.mqtt_actor import MQTTActor
from src.actors.heartbeat_actor import HeartbeatActor
from src.actors.system_metrics_actor import SystemMetricsActor
from src.actors.messages.actor_queue_registry import ActorQueueRegistry
from src.actors.messages.message_type import ActorName
from src.actors.uploader_actor import UploaderActor
from src.models.iot_device_status import (
    get_latest_iot_device_status,
    upsert_iot_device_status,
)
from src.actors.cleaner_actor import CleanerActor
from src.models.device_status_enums import MonitoringStatusEnum
from src.models.deployment_config import (
    get_current_deployment_config_as_dict,
    has_valid_deployment_config,
)
from src.config.deployment_runtime_config import DeploymentRuntimeConfig
from src.utils.logger import logger


async def supervise_actor(
    name: str, start_fn: Callable[[], Awaitable[None]], delay: int = 5
):
    retry_count = 0
    while True:
        try:
            logger.info(f"[Supervisor] Starting {name}")
            await start_fn()
        except Exception as e:
            logger.exception(f"[Supervisor] {name} crashed: {e}")
            await asyncio.sleep(delay)
            retry_count += 1
            if retry_count > 3:
                logger.error(f"[Supervisor] {name} crashed 3 times, exiting")
                raise e


async def load_deployment_config() -> DeploymentRuntimeConfig:
    """Load deployment configuration from database and validate it"""
    is_valid, errors = await has_valid_deployment_config()
    if not is_valid:
        logger.error("No valid deployment configuration found!")
        logger.error("Please run one of the following commands to configure:")
        logger.error(
            "  python -m src.cli config set --org-id <id> --site-id <id> --device-id <id>"
        )
        logger.error("  python -m src.cli config setup --interactive")
        logger.error("")
        logger.error("Validation errors:")
        for error in errors:
            logger.error(f"  - {error}")
        raise RuntimeError("Missing deployment configuration")

    # Load configuration
    config_dict = await get_current_deployment_config_as_dict()
    if not config_dict:
        raise RuntimeError("Failed to load deployment configuration")

    # Create configuration object
    config = DeploymentRuntimeConfig(
        organization_id=config_dict["organization_id"],
        site_id=config_dict["site_id"],
        device_id=config_dict["device_id"],
        config_metadata=config_dict.get("config_metadata"),
    )

    logger.info("Deployment configuration loaded successfully:")
    logger.info(f"  Organization ID: {config.organization_id}")
    logger.info(f"  Site ID: {config.site_id}")
    logger.info(f"  Device ID: {config.device_id}")
    if config.config_metadata:
        logger.info(f"  Metadata: {config.config_metadata}")

    return config


async def initialize_device_status(config: DeploymentRuntimeConfig):
    latest_status = await get_latest_iot_device_status(config.device_id)
    logger.info(f"Latest status: {latest_status}")

    # If no monitoring status is found, set it to active.
    # This is to have an initial state for ALL iot_device_status.
    if not latest_status:
        logger.info(
            f"[BacnetMonitoringActor] No monitoring status found for device {config.device_id}, setting to active"
        )
        status_data = {
            "organization_id": config.organization_id,
            "site_id": config.site_id,
            "monitoring_status": MonitoringStatusEnum.ACTIVE,
        }
        logger.info(
            f"Initializing iot_device_status for device {config.device_id}, data: {status_data}"
        )
        await upsert_iot_device_status(config.device_id, status_data)


async def main():
    config = await load_deployment_config()

    await initialize_device_status(config)

    # Extract individual values for actors (keeping actor interfaces unchanged)
    organization_id = config.organization_id
    site_id = config.site_id
    iot_device_id = config.device_id

    actor_queue_registry = ActorQueueRegistry()
    actor_queue_registry.register(ActorName.MQTT)
    actor_queue_registry.register(ActorName.BACNET)
    actor_queue_registry.register(ActorName.BACNET_WRITER)
    actor_queue_registry.register(ActorName.BROADCAST)
    actor_queue_registry.register(ActorName.UPLOADER)
    actor_queue_registry.register(ActorName.CLEANER)
    actor_queue_registry.register(ActorName.HEARTBEAT)
    actor_queue_registry.register(ActorName.SYSTEM_METRICS)

    mqtt_config = load_config()

    async def start_mqtt():
        mqtt_actor = MQTTActor(
            mqtt_config=mqtt_config,
            organization_id=organization_id,
            site_id=site_id,
            iot_device_id=iot_device_id,
            actor_queue_registry=actor_queue_registry,
        )
        await mqtt_actor.start()

    async def start_bacnet():
        bacnet_monitoring_actor = BacnetMonitoringActor(
            actor_queue_registry=actor_queue_registry,
            organization_id=organization_id,
            site_id=site_id,
            iot_device_id=iot_device_id,
        )
        await bacnet_monitoring_actor.start()

    async def start_uploader():
        uploader_actor = UploaderActor(actor_queue_registry=actor_queue_registry)
        await uploader_actor.start()

    async def start_bacnet_writer():
        bacnet_writer_actor = BacnetWriterActor(
            actor_queue_registry=actor_queue_registry
        )
        await bacnet_writer_actor.start()

    async def start_cleaner():
        cleaner_actor = CleanerActor(actor_queue_registry=actor_queue_registry)
        await cleaner_actor.start()

    async def start_heartbeat():
        heartbeat_actor = HeartbeatActor(
            actor_queue_registry=actor_queue_registry,
            organization_id=organization_id,
            site_id=site_id,
            iot_device_id=iot_device_id,
        )
        await heartbeat_actor.start()

    async def start_system_metrics():
        system_metrics_actor = SystemMetricsActor(
            actor_queue_registry=actor_queue_registry,
            organization_id=organization_id,
            site_id=site_id,
            iot_device_id=iot_device_id,
        )
        await system_metrics_actor.start()

    await asyncio.gather(
        supervise_actor("MQTTActor", start_mqtt),
        supervise_actor("BACnetMonitoringActor", start_bacnet),
        supervise_actor("BACnetWriterActor", start_bacnet_writer),
        supervise_actor("UploaderActor", start_uploader),
        supervise_actor("CleanerActor", start_cleaner),
        supervise_actor("HeartbeatActor", start_heartbeat),
        supervise_actor("SystemMetricsActor", start_system_metrics),
    )
