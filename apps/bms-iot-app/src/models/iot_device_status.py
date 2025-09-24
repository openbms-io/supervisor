from typing import Optional
from sqlmodel import SQLModel, Field, select
from datetime import datetime, timezone
from sqlalchemy import Column, Computed, BigInteger
import json

from src.models.device_status_enums import MonitoringStatusEnum, ConnectionStatusEnum
from src.network.sqlmodel_client import get_session, with_db_retry


class IotDeviceStatusModel(SQLModel, table=True):  # type: ignore[call-arg]
    __tablename__ = "iot_device_status"

    id: Optional[int] = Field(default=None, primary_key=True)
    iot_device_id: str = Field(description="IoT device ID", unique=True, index=True)
    organization_id: str = Field(description="Organization ID")
    site_id: str = Field(description="Site ID")

    # Device status fields
    monitoring_status: Optional[MonitoringStatusEnum] = Field(
        default=MonitoringStatusEnum.ACTIVE, description="Monitoring status"
    )

    # Connection status fields
    mqtt_connection_status: Optional[ConnectionStatusEnum] = Field(
        default=None, description="MQTT connection status"
    )
    bacnet_connection_status: Optional[ConnectionStatusEnum] = Field(
        default=None, description="BACnet connection status"
    )

    # System metrics
    cpu_usage_percent: Optional[float] = Field(
        default=None, description="CPU usage percentage"
    )
    memory_usage_percent: Optional[float] = Field(
        default=None, description="Memory usage percentage"
    )
    disk_usage_percent: Optional[float] = Field(
        default=None, description="Disk usage percentage"
    )
    temperature_celsius: Optional[float] = Field(
        default=None, description="Temperature in Celsius"
    )
    uptime_seconds: Optional[int] = Field(
        default=None, description="System uptime in seconds"
    )
    load_average: Optional[float] = Field(
        default=None, description="System load average"
    )

    # BACnet specific metrics
    bacnet_devices_connected: Optional[int] = Field(
        default=None, description="Number of BACnet devices connected"
    )
    bacnet_points_monitored: Optional[int] = Field(
        default=None, description="Number of BACnet points monitored"
    )

    # Full payload for compatibility
    payload: str = Field(default="{}", description="Full status payload as JSON")

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    received_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    created_at_unix_milli_timestamp: int = Field(
        sa_column=Column(
            "created_at_unix_milli_timestamp",
            BigInteger,
            Computed("(strftime('%s', created_at) * 1000)", persisted=True),
        ),
        description="Unix milli timestamp of creation",
    )


@with_db_retry(max_retries=3, base_delay=0.1)
async def upsert_iot_device_status(
    iot_device_id: str, status_data: dict
) -> IotDeviceStatusModel:
    """Upsert IoT device status. Only one row per device. Handles concurrent access safely."""
    async with get_session() as session:
        # Update timestamp
        status_data["updated_at"] = datetime.now(timezone.utc)
        status_data["received_at"] = datetime.now(timezone.utc)

        # Ensure payload is JSON string
        if "payload" in status_data and isinstance(status_data["payload"], dict):
            status_data["payload"] = json.dumps(status_data["payload"])

        try:
            # First, try to update existing record
            result = await session.execute(
                select(IotDeviceStatusModel).where(
                    IotDeviceStatusModel.iot_device_id == iot_device_id
                )
            )
            existing_status = result.scalars().first()

            if existing_status:
                # Update existing record
                for key, value in status_data.items():
                    if hasattr(existing_status, key):
                        setattr(existing_status, key, value)
                await session.commit()
                await session.refresh(existing_status)
                return existing_status
            else:
                # Create new record
                status_data["iot_device_id"] = iot_device_id
                if "created_at" not in status_data:
                    status_data["created_at"] = datetime.now(timezone.utc)

                new_status = IotDeviceStatusModel(**status_data)
                session.add(new_status)
                await session.commit()
                await session.refresh(new_status)
                return new_status

        except Exception as e:
            await session.rollback()
            error_msg = str(e).lower()

            # Handle concurrent insert race condition
            if "unique constraint failed" in error_msg and "iot_device_id" in error_msg:
                # Another concurrent operation inserted the record, try to update it
                result = await session.execute(
                    select(IotDeviceStatusModel).where(
                        IotDeviceStatusModel.iot_device_id == iot_device_id
                    )
                )
                existing_status = result.scalars().first()

                if existing_status:
                    # Update the record that was just created by another operation
                    for key, value in status_data.items():
                        if hasattr(existing_status, key) and key != "iot_device_id":
                            setattr(existing_status, key, value)
                    await session.commit()
                    await session.refresh(existing_status)
                    return existing_status

            # Re-raise other exceptions
            raise


@with_db_retry(max_retries=3, base_delay=0.1)
async def get_latest_iot_device_status(
    iot_device_id: str,
) -> Optional[IotDeviceStatusModel]:
    """Get the latest status for a specific IoT device."""
    async with get_session() as session:
        result = await session.execute(
            select(IotDeviceStatusModel).where(
                IotDeviceStatusModel.iot_device_id == iot_device_id
            )
        )
        return result.scalars().first()


async def update_system_metrics(
    iot_device_id: str, metrics: dict
) -> IotDeviceStatusModel:
    """Update system metrics for a device."""
    return await upsert_iot_device_status(iot_device_id, metrics)


async def update_connection_status(
    iot_device_id: str, connection_type: str, status: ConnectionStatusEnum
) -> IotDeviceStatusModel:
    """Update connection status for a specific connection type."""
    status_data = {}
    if connection_type == "mqtt":
        status_data["mqtt_connection_status"] = status
    elif connection_type == "bacnet":
        status_data["bacnet_connection_status"] = status

    return await upsert_iot_device_status(iot_device_id, status_data)
