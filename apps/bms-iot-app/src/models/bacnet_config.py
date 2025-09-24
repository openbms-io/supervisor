from typing import Optional, Any, List
from sqlmodel import SQLModel, Field, select
from sqlalchemy import JSON
from pydantic import BaseModel
from datetime import datetime, timezone

from src.network.sqlmodel_client import get_session, with_db_retry
from src.actors.messages.message_type import BacnetReaderConfig
from src.utils.logger import logger


class BacnetObjectInfo(BaseModel):
    type: str
    point_id: int
    iot_device_point_id: str  # This is the uuid of the iot device point to tie in supabase and we can upsert.
    properties: Any  # Want to store all properties as a json object.


class BacnetDeviceInfo(BaseModel):
    vendor_id: int
    device_id: int
    controller_ip_address: str
    controller_id: str
    object_list: List[BacnetObjectInfo]


class BacnetConfigModel(SQLModel, table=True):  # type: ignore[call-arg]
    __tablename__ = "bacnet_config"

    id: Optional[int] = Field(default=None, primary_key=True)
    bacnet_devices: Optional[List[dict]] = Field(default=None, sa_type=JSON)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BacnetReaderConfigModel(SQLModel, table=True):  # type: ignore[call-arg]
    __tablename__ = "bacnet_readers"

    id: str = Field(primary_key=True)  # Reader UUID from Supabase
    iot_device_id: str = Field(index=True)
    ip_address: str
    subnet_mask: int = Field(default=24)
    bacnet_device_id: int
    port: int = Field(default=47808)
    bbmd_enabled: bool = Field(default=False)
    bbmd_server_ip: Optional[str] = Field(default=None)
    is_active: bool = Field(default=True)
    connection_status: Optional[str] = Field(default="disconnected")
    last_connected_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def bacnet_device_infos_to_json(devices: List[BacnetDeviceInfo]) -> List[dict]:
    return [device.model_dump() for device in devices]


def json_to_bacnet_device_infos(data: List[dict]) -> List[BacnetDeviceInfo]:
    return [BacnetDeviceInfo(**d) for d in data]


# Example async CRUD functions
@with_db_retry(max_retries=3, base_delay=0.1)
async def insert_bacnet_config_json(
    devices: List[BacnetDeviceInfo],
) -> BacnetConfigModel:
    json_data = bacnet_device_infos_to_json(devices)
    config = BacnetConfigModel(bacnet_devices=json_data)
    async with get_session() as session:
        session.add(config)
        await session.commit()
        await session.refresh(config)
        return config


@with_db_retry(max_retries=3, base_delay=0.1)
async def get_latest_bacnet_config_json() -> Optional[BacnetConfigModel]:
    async with get_session() as session:
        result = await session.execute(
            select(BacnetConfigModel).order_by(BacnetConfigModel.created_at.desc())  # type: ignore
        )
        config = result.scalars().first()
        return config


async def get_latest_bacnet_config_json_as_list() -> Optional[List[BacnetDeviceInfo]]:
    config = await get_latest_bacnet_config_json()
    if not config or not config.bacnet_devices:
        return None
    return json_to_bacnet_device_infos(config.bacnet_devices)


# BACnet Reader Configuration Functions


def bacnet_reader_config_to_model(
    reader_config: BacnetReaderConfig, iot_device_id: str
) -> BacnetReaderConfigModel:
    """Convert BacnetReaderConfig to SQLModel."""
    return BacnetReaderConfigModel(
        id=reader_config.id,
        iot_device_id=iot_device_id,
        ip_address=reader_config.ip_address,
        subnet_mask=reader_config.subnet_mask,
        bacnet_device_id=reader_config.bacnet_device_id,
        port=reader_config.port,
        bbmd_enabled=reader_config.bbmd_enabled,
        bbmd_server_ip=reader_config.bbmd_server_ip,
        is_active=reader_config.is_active,
        connection_status="disconnected",  # Default status
        updated_at=datetime.now(timezone.utc),
    )


def bacnet_reader_model_to_config(
    reader_model: BacnetReaderConfigModel,
) -> BacnetReaderConfig:
    """Convert SQLModel to BacnetReaderConfig."""
    return BacnetReaderConfig(
        id=reader_model.id,
        ip_address=reader_model.ip_address,
        subnet_mask=reader_model.subnet_mask,
        bacnet_device_id=reader_model.bacnet_device_id,
        port=reader_model.port,
        bbmd_enabled=reader_model.bbmd_enabled,
        bbmd_server_ip=reader_model.bbmd_server_ip,
        is_active=reader_model.is_active,
    )


@with_db_retry(max_retries=3, base_delay=0.1)
async def save_bacnet_readers(
    readers: List[BacnetReaderConfig], iot_device_id: str
) -> bool:
    """Save/update BACnet readers for a device."""
    try:
        async with get_session() as session:
            # Delete existing readers for this device
            existing_readers = await session.execute(
                select(BacnetReaderConfigModel).where(
                    BacnetReaderConfigModel.iot_device_id == iot_device_id
                )
            )
            for reader in existing_readers.scalars().all():
                await session.delete(reader)

            # Insert new readers
            for reader_config in readers:
                reader_model = bacnet_reader_config_to_model(
                    reader_config, iot_device_id
                )
                session.add(reader_model)

            await session.commit()
            return True
    except Exception as e:
        logger.error(f"Error saving BACnet readers: {e}")
        return False


@with_db_retry(max_retries=3, base_delay=0.1)
async def get_bacnet_readers(iot_device_id: str) -> List[BacnetReaderConfig]:
    """Get all BACnet readers for a device."""
    try:
        async with get_session() as session:
            result = await session.execute(
                select(BacnetReaderConfigModel)
                .where(BacnetReaderConfigModel.iot_device_id == iot_device_id)
                .where(BacnetReaderConfigModel.is_active is True)
                .order_by(BacnetReaderConfigModel.created_at.asc())  # type: ignore
            )
            readers = result.scalars().all()
            return [bacnet_reader_model_to_config(reader) for reader in readers]
    except Exception as e:
        logger.error(f"Error getting BACnet readers: {e}")
        return []


@with_db_retry(max_retries=3, base_delay=0.1)
async def get_all_active_readers() -> List[BacnetReaderConfig]:
    """Get all active BACnet readers across all devices."""
    try:
        async with get_session() as session:
            result = await session.execute(
                select(BacnetReaderConfigModel)
                .where(BacnetReaderConfigModel.is_active is True)
                .order_by(
                    BacnetReaderConfigModel.iot_device_id.asc(),
                    BacnetReaderConfigModel.created_at.asc(),
                )  # type: ignore
            )
            readers = result.scalars().all()
            return [bacnet_reader_model_to_config(reader) for reader in readers]
    except Exception as e:
        logger.error(f"Error getting all active readers: {e}")
        return []


@with_db_retry(max_retries=3, base_delay=0.1)
async def update_reader_connection_status(
    reader_id: str, status: str, error_message: Optional[str] = None
) -> bool:
    """Update connection status for a specific reader."""
    try:
        async with get_session() as session:
            result = await session.execute(
                select(BacnetReaderConfigModel).where(
                    BacnetReaderConfigModel.id == reader_id
                )
            )
            reader = result.scalars().first()
            if reader:
                reader.connection_status = status
                reader.updated_at = datetime.now(timezone.utc)
                if status == "connected":
                    reader.last_connected_at = datetime.now(timezone.utc)
                await session.commit()
                return True
    except Exception as e:
        logger.error(f"Error updating reader connection status: {e}")
        return False
    return False


@with_db_retry(max_retries=3, base_delay=0.1)
async def delete_reader(reader_id: str) -> bool:
    """Delete a BACnet reader."""
    try:
        async with get_session() as session:
            result = await session.execute(
                select(BacnetReaderConfigModel).where(
                    BacnetReaderConfigModel.id == reader_id
                )
            )
            reader = result.scalars().first()
            if reader:
                await session.delete(reader)
                await session.commit()
                return True
    except Exception as e:
        logger.error(f"Error deleting reader: {e}")
        return False
    return False
